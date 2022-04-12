import numpy as np
import pandas as pd
from typing import Union


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
    df["recentness"] = _calculate_recentness(df.date_unix, year) if year else 1
    return df


def solver_season(df: pd.DataFrame, year: Union[int, bool] = 1):
    df = clean_data(df, year)
