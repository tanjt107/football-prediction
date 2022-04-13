import mysql.connector
import pathlib
import re
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List, Tuple
from common.pipeline import Pipeline, filter_dict_keys
from common.source import FootyStats


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
        if team == "home":
            home += 1
            home_adj += (
                0.5 + remain / 20 * 0.5
                if (remain := played - timing < 20) and home - away > 1
                else 1
            )
        elif team == "away":
            away += 1
            away_adj += (
                0.5 + remain / 20 * 0.5
                if (remain := played - timing < 20) and away - home > 1
                else 1
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


def transform(data: List[dict]) -> List[dict]:
    data["date_time"] = datetime.fromtimestamp(data["date_unix"]).strftime(
        "%Y/%m/%d %H:%M"
    )

    if data["goal_timings_recorded"] == 1:
        _goal_timings = get_goal_timings_dict(data["homeGoals"], data["awayGoals"])
        home_adj, away_adj = reduce_goal_value(_goal_timings)
        data["home_adj"] = calculate_adjusted_goal(home_adj)
        data["away_adj"] = calculate_adjusted_goal(away_adj)
    else:
        data["home_adj"], data["away_adj"] = (
            data["homeGoalCount"],
            data["awayGoalCount"],
        )

    if data["total_xg"]:
        data["home_avg"] = calculate_average_goal(data["home_adj"], data["team_a_xg"])
        data["away_avg"] = calculate_average_goal(data["away_adj"], data["team_b_xg"])
    else:
        data["home_avg"], data["away_avg"] = data["home_adj"], data["away_adj"]

    for goals in ["homeGoals", "awayGoals"]:
        data[goals] = ",".join(data[goals])

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
        "date_time",
        "home_adj",
        "away_adj",
        "home_avg",
        "away_avg",
        "modified_on",
    ]
    return filter_dict_keys(data, keys)


def matches():
    sql_create = pathlib.Path("sql/matches_create.sql").read_text()
    sql_insert = pathlib.Path("sql/matches_insert.sql").read_text()

    pipeline = Pipeline("matches")

    db = mysql.connector.connect(
        host="127.0.0.1", user="root", password="password", database="footystats"
    )
    cursor = db.cursor()

    fs = FootyStats()
    season_ids = fs.league_id_list_filtered()
    cursor.execute(sql_create)
    for season_id in (pbar := tqdm(season_ids)):
        pbar.set_description(pipeline.folder)
        pipeline.extract(fs.matches, season_id)
    pipeline.transform(transform)
    pipeline.load(sql_insert, cursor)

    db.commit()
    db.close()


if __name__ == "__main__":
    matches()
