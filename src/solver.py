import numpy as np
import pandas as pd
import re
from api import FootyStats
from typing import Dict, List, Optional, Protocol, Tuple, Union


def _calculate_recentness(ts: pd.Series, year: float) -> pd.Series:
    """
    Recentness factor gives less weight to games that were played further back in time.
    A bouns of up to 25 percent is also given to games played within past past 25 days to reflect a team's most recent form.

    Parameters:
    ts: Series of epoch timestamps.
    year: Cut off number of year.

    Return:
    Series of recentness factor.
    """
    max_ts = ts.max()
    cut_off_ts = max_ts - 31536000 * year  # 365 * 24 * 60 * 60
    bouns_ts = 2160000 * year  # 25 * 24 * 60 * 60
    bouns = np.where(
        max_ts - ts < bouns_ts, 1 + (bouns_ts - max_ts + ts) / bouns_ts * 0.25, 1
    )
    recentness = (ts - cut_off_ts) / (max_ts - cut_off_ts) * bouns
    return np.where(recentness > 0, recentness, 0)


def _get_goal_timings_dict(home: list, away: list) -> dict:
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


def _reduce_goal_value(goal_timings: Dict[int, str]) -> Tuple[float]:
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
        # TODO Use switch case from Python 3.10
        if team == "home":
            home += 1
            if remain := played - timing < 20 and home - away > 1:
                home_adj += 0.5 + remain / 20 * 0.5
            else:
                home_adj += 1
        elif team == "away":
            away += 1
            if remain := played - timing < 20 and away - home > 1:
                away_adj += 0.5 + remain / 20 * 0.5
            else:
                away_adj += 1
    return home_adj, away_adj


def _calculate_adjusted_goal(
    adj_goals: pd.DataFrame, goals: pd.DataFrame
) -> pd.DataFrame:
    """
    Increase value of all other goals to make total number of adjusted goals equal to total number of actual goals.

    Parameters:
    adj_goals: Series of home and away team adjusted goals before increment.
    goals: Series of home and away team real goals.

    Return:
    home_adj: Series of home and away team adjusted goals after increment.
    """
    ratio = goals.values.sum() / adj_goals.values.sum()
    return adj_goals * ratio


def _calculate_average_goal(adj_goals: float, xg: float) -> float:
    """
    Calculate average of the two metrics.

    Parameters:
    adj_goal: Adjusted goals.
    xg: Expected goals calculated by data points such as shot accuracy, shot frequency, attack dangerousness, overall attack pressure.

    Return:
    Average of the two metrics.
    """
    return (adj_goals + xg * 2) / 3


def clean_data(df: pd.DataFrame, year: Union[int, bool] = 1) -> pd.DataFrame:
    """
    Clean data of solver.

    Parameters:
    df: Match DataFrame.
    year: Cut off number of year. Recentness factor is not applied if value is None.

    Return:
    Solver ready DataFrame.
    """
    if "previous_season" not in df.columns:
        df["previous_season"] = 0
    # TODO Market value?
    df["recentness"] = _calculate_recentness(df.date_unix, year) if year else 1
    df["goal_timings"] = df.apply(
        lambda s: _get_goal_timings_dict(s.homeGoals, s.awayGoals)
        if s.goal_timings_recorded == 1
        else {},
        axis=1,
    )
    df[["home_adj_goal", "away_adj_goal"]] = df.apply(
        lambda s: _reduce_goal_value(s.goal_timings)
        if s.goal_timings_recorded == 1
        else [s.homeGoalCount, s.awayGoalCount],
        axis=1,
        # result_type="expand",
    )
    df[["home_adj_goal", "away_adj_goal"]] = _calculate_adjusted_goal(
        df[["home_adj_goal", "away_adj_goal"]], df[["homeGoalCount", "awayGoalCount"]]
    )
    df["home_avg_goal"] = df.apply(
        lambda s: _calculate_average_goal(s.home_adj_goal, s.team_a_xg)
        if s.total_xg > 0
        else s.home_adj_goal,
        axis=1,
    )
    df["away_avg_goal"] = df.apply(
        lambda s: _calculate_average_goal(s.away_adj_goal, s.team_b_xg)
        if s.total_xg > 0
        else s.away_adj_goal,
        axis=1,
    )
    return df


def solver_season(df: pd.DataFrame, year: Union[int, bool] = 1):
    df = clean_data(df, year)


def test():
    data = FootyStats("example").matches(1625)["data"]
    df = pd.DataFrame.from_dict(data)
    df = solver_season(df)
    print(df)


if __name__ == "__main__":
    test()
