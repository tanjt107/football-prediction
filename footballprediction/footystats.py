import aiohttp
import asyncio
import itertools
import re
import sqlite3
from datetime import datetime
from typing import Callable, Optional
from . import pipeline
from .util import read_file


async def get_league_list(key: str, session: aiohttp.ClientSession) -> list[dict]:
    """
    Returns a JSON array of all leagues chosen.

    Parameters:
        key: The footystats API key.
        session: The aiohttp session for making requests.

    Returns:
        List of leagues. Each season of a competition gives a unique ID.
    """
    response = await pipeline.extract(
        "https://api.football-data-api.com/league-list",
        session,
        {"key": key, "chosen_leagues_only": "true"},
    )
    return response["data"]


def filter_season_id(
    league_list: list,
    years: Optional[int] = None,
    latest_year: int = datetime.now().year,
) -> list[int]:
    """
    Filter recent seasons based on a year offset.

    Parameters:
        league_list: The data response from `league-list` endpoint.
        years: The offset number of years that will be selected. For instance, years=1 will return the most recent season and last season.
        latest_year: Set this number if you would like the years counted from certain time. Default is today's year.

    Returns:
        List of chosen season IDs.
    """
    season_ids = []

    for league in league_list:
        for season in league["season"]:
            end_year = season["year"] % 10000
            if years is None or (latest_year - years) <= end_year:
                season_ids.extend([season["id"]])
    return season_ids


async def get_season_data(
    endpoint: str, season_id: int, key: str, session: aiohttp.ClientSession
) -> list[dict]:
    """
    Get data in a league season.

    Parameters:
        endpoint: The Footystats API endpoint. Can be `seasons`, `matches` or `teams`.
        season_id: The ID of the league season.
        key: The footystats API key.
        session: The aiohttp session for making requests.

    Returns:
        The data in a JSON array.
    """
    response = await pipeline.extract(
        f"https://api.football-data-api.com/league-{endpoint}",
        session,
        {"key": key, "season_id": season_id},
    )
    return response["data"]


def get_goal_timings_dict(home: list[str], away: list[str]) -> list[tuple]:
    """
    Return a dictionary of goal timings.

    Parameters:
        home: List of goal timings for home team goals.
        away: List of goal timings for away team goals.

    Return:
        Tuple of (Goal Timings: Team).
    """
    timings = [
        (int(re.search(r"(^1?\d{1,2})", minute).group()), "home") for minute in home
    ]
    timings.extend(
        (int(re.search(r"(^1?\d{1,2})", minute).group()), "away") for minute in away
    )
    return sorted(timings)


def reduce_goal_value(
    goal_timings: list[tuple], reduce_from_minute: int = 70, goal_value: int = 0.5
) -> tuple[float]:
    """
    Reduce the value of goals scored late in a match when a team is already leading. The value of a goal when a team is leading decreases linearly to the end of the game when a real-life goal is worth `goal_value` in this function. For example, if `reduce_from` = 70 and `goal_value = 0.5, a 70th-minute goal when leading is worth a full goal, an 80th-minute goal is worth 0.75 goals, and a goal in the 90th minute or later is worth 0.5 goals.

    Parameters:
        goal_timings: Dictionary of Tuple of (Goal Timings: Team).
        reduce_from_minute: The minute from where value of a goal starts reducing.
        goal_value: The value of goal at 90th minute or later.

    Return:
        Adjusted goal of home team.
        Adjusted goal of away team.
    """
    if not goal_timings:
        return 0, 0
    home = home_adj = away = away_adj = 0
    for timing, team in goal_timings:
        timing = min(timing, 90)
        if team == "away":
            away += 1
            away_adj += 1
            if timing > reduce_from_minute and away - home > 1:
                away_adj -= (
                    (timing - reduce_from_minute)
                    / (90 - reduce_from_minute)
                    * (1 - goal_value)
                )
        elif team == "home":
            home += 1
            home_adj += 1
            if timing > reduce_from_minute and home - away > 1:
                home_adj -= 1 - (timing - reduce_from_minute) / (
                    90 - reduce_from_minute
                ) * (1 - goal_value)
        else:
            raise ValueError("Team must be 'home' or 'away'")
    return home_adj, away_adj


def transform_matches(
    matches: list[dict],
    *,
    reduce_from_minute: int = 70,
    min_goal_value: int = 0.5,
    adj_factor: float = 1.05,
    xg_weight: float = 0.67,
) -> list[dict]:
    """
    Transforms matches data.

    Parameters:
        matches: Matches data.
        reduce_from_minute: The minute from where value of a goal starts reducing.
        min_goal_value: The minimum value of reduced_goal.
        adj_factor: The factor to multiply all goals after reducing value.
        xg_weight: The weight of the xg metric.

    Returns:
        Transformed matches.
    """
    records = []
    for match in matches:
        match["home_adj"], match["away_adj"] = (
            match["homeGoalCount"],
            match["awayGoalCount"],
        )
        if (
            match["goal_timings_recorded"] == 1
            and "None" not in match["homeGoals"]
            and "None" not in match["awayGoals"]
        ):
            goal_timings = get_goal_timings_dict(match["homeGoals"], match["awayGoals"])
            home_adj, away_adj = reduce_goal_value(
                goal_timings, reduce_from_minute, min_goal_value
            )
            match["home_adj"] = home_adj * adj_factor
            match["away_adj"] = away_adj * adj_factor

        if match["total_xg"] > 0:
            match["home_adj"] = (
                match["home_adj"] * (1 - xg_weight) + match["team_a_xg"] * xg_weight
            )
            match["away_adj"] = (
                match["away_adj"] * (1 - xg_weight) + match["team_b_xg"] * xg_weight
            )

        records.append(match)

    return records


async def etl(
    endpoint: str,
    season_ids: list[str],
    *,
    insert_sql: str,
    session: aiohttp.ClientSession,
    key: str,
    con: sqlite3.Connection,
    transform_func: Optional[Callable] = None,
    create_sql: Optional[str] = None,
) -> None:
    """
    ETL of footystats API data.

    Parameter
        endpoint: The Footystats API league endpoint. Can be `seasons`, `matches` or `teams`.
        season_ids: List of the league sesaon IDs
        insert_sql: The insert SQL query.
        session: The aiohttp session for making requests.
        key: The Footystats API key.
        con: The SQLite connection object.
        transform_func: The transformation function.
        create_sql: The create SQL query.

    Returns:
        None.
    """
    data = await asyncio.gather(
        *(
            get_season_data(endpoint, season_id, key, session)
            for season_id in season_ids
        )
    )
    if all(isinstance(x, list) for x in data):
        data = list(itertools.chain.from_iterable(data))
    if transform_func:
        data = transform_func(data)
    pipeline.load(data, con, insert_sql, create_sql)


def get_match_details(
    con: sqlite3.Connection,
    max_time: Optional[int] = None,
    cut_off_year: int = 1,
    inter_league_cut_off_year: int = 5,
) -> dict:
    """
    Get match details in database for solver input.

    Parameter:
        con: The SQLite connection object.
        max_time: UNIX Timestamp. Set this number if you would like to return the data up to a certain time. For example, if max_time=1537984169, then the output is stats up to September 26th, 2018.
        cut_off_year: The cut off year for non league matches.
        inter_league_cut_off_year: The cut off year for inter-league matches.

    Return:
        Match details needed for solver.
    """

    cur = con.cursor()
    if not max_time:
        cur.execute("SELECT MAX(date_unix) FROM matches WHERE status = 'complete'")
        max_time = cur.fetchone()[0]

    params = {
        "max_time": max_time,
        "cut_off_year": cut_off_year,
        "inter_league_cut_off_year": inter_league_cut_off_year,
    }

    cur.execute(read_file("sql/footystats/match_details.sql"), params)
    cols = [col[0] for col in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
