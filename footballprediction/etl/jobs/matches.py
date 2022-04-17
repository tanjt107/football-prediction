import json
import mysql.connector
import re
from tqdm import tqdm
from typing import Dict, Tuple, Optional
from footballprediction.etl.pipeline import Pipeline
from footballprediction.etl.source.footystats import FootyStats


def get_goal_timings_dict(home: list, away: list) -> dict:
    """
    Return a dictionary of goal timings.

    Parameters:
    home: List of goal timings for home team goals.
    away: List of goal timings for away team goals.

    Return:
    Dictionary of {Goal Timings: Team}.
    """
    home = [re.search(r"(^1?\d{1,2})", minute).group() for minute in home]
    home = {int(minute): "home" for minute in home}

    away = [re.search(r"(^1?\d{1,2})", minute).group() for minute in away]
    away = {int(minute): "away" for minute in away}

    home.update(away)
    return {int(minute): home[minute] for minute in sorted(home.keys())}


def reduce_goal_value(goal_timings: Dict[int, str]) -> Tuple[float]:
    """
    Reduce the value of goals scored late in a match when a team is already leading.

    Parameters:
    goal_timings: Dictionary of {Goal Timings: Team}.

    Return:
    home_adj: Adjusted goal of home team.
    away_adj: Adjusted goal of away team.
    """
    if not goal_timings:
        return 0, 0
    played = 120 if list(goal_timings)[-1] > 90 else 90
    home = home_adj = away = away_adj = 0
    for timing, team in goal_timings.items():
        remain = played - timing
        if team == "home":
            home += 1
            home_adj += (
                0.5 + remain / 20 * 0.5 if remain < 20 and home - away > 1 else 1
            )
        elif team == "away":
            away += 1
            away_adj += (
                0.5 + remain / 20 * 0.5 if remain < 20 and away - home > 1 else 1
            )
    return home_adj, away_adj


def calculate_adjusted_goal(adj_goals: float) -> float:
    """
    Increase value of all other goals to make total number of adjusted goals equal to total number of actual goals.
    """
    return adj_goals * 1.05


def calculate_average_goal(adj_goals: float, xg: float) -> float:
    """
    Calculate average of the two metrics.

    Parameters:
    adj_goal: Adjusted goals.
    xg: Expected goals calculated by data points such as shot accuracy, shot frequency, attack dangerousness, overall attack pressure.

    Return:
    Average of the two metrics.
    """
    return (adj_goals + xg * 2) / 3


def transform(match):
    if match["goal_timings_recorded"] == 1:
        goal_timings = get_goal_timings_dict(match["homeGoals"], match["awayGoals"])
        home_adj, away_adj = reduce_goal_value(goal_timings)
        match["home_adj"] = calculate_adjusted_goal(home_adj)
        match["away_adj"] = calculate_adjusted_goal(away_adj)
    else:
        match["home_adj"], match["away_adj"] = (
            match["homeGoalCount"],
            match["awayGoalCount"],
        )

    if match["total_xg"]:
        match["home_avg"] = calculate_average_goal(
            match["home_adj"], match["team_a_xg"]
        )
        match["away_avg"] = calculate_average_goal(
            match["away_adj"], match["team_b_xg"]
        )
    else:
        match["home_avg"] = match["home_adj"]
        match["away_avg"] = match["away_adj"]

    for goals in ["homeGoals", "awayGoals"]:
        match[goals] = ",".join(match[goals])

    return match


def main(years: Optional[int] = 0):
    keys = [
        "id",
        "homeID",
        "awayID",
        "status",
        "homeGoals",
        "awayGoals",
        "homeGoalCount",
        "awayGoalCount",
        "date_unix",
        "no_home_away",
        "team_a_xg",
        "team_b_xg",
        "total_xg",
        "goal_timings_recorded",
        "competition_id",
        "home_adj",
        "away_adj",
        "home_avg",
        "away_avg",
        "modified_on",
    ]

    with open("credentials/footystats.json") as f:
        key = json.load(f)["key"]
    fs = FootyStats(key)
    season_ids = fs.chosen_season_id(years)

    sql_create = open("sql/footystats/tables/matches/create.sql").read()
    sql_insert = open("sql/footystats/tables/matches/insert.sql").read()

    conn = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="footystats"
    )
    conn.cursor().execute(sql_create)

    pbar = tqdm(season_ids)
    pbar.set_description("Ingesting match data")

    for season_id in pbar:
        p = Pipeline(season_id, "matches", initial=years is None)
        p.extract(fs.matches, season_id)
        p.transform(transform, keys)
        p.load(sql_insert, conn)

    conn.commit()
    conn.close()
