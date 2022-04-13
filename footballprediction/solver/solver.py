import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from scipy import optimize
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Tuple
from constraints import avg_off, avg_def, min_home_adv, sum_strength


def calculate_recentness(dt: pd.Series, years: float) -> pd.Series:
    """
    Recentness factor gives less weight to games that were played further back in time.
    A bouns of up to 25 percent is also given to games played within past past 25 days to reflect a team's most recent form.

    Parameters:
    ts: Series of epoch timestamps.
    year: Cut off number of year.

    Return:
    Series of recentness factor.
    """
    max_dt = dt.max()
    cut_off_dt = max_dt - years * 31536000  # 365 * 24 * 60 * 60
    # a bonus of up to 25 percent is given
    # to games played within past past 25 days to reflect a team's most recent form
    bonus_dt = years * 2160000  # 25 * 24 * 60 * 60
    bonus = np.where(
        max_dt - dt < bonus_dt, 1 + (bonus_dt - max_dt + dt) / bonus_dt * 0.25, 1
    )
    recent = (dt - cut_off_dt) / (max_dt - cut_off_dt) * bonus
    return np.where(recent > 0, recent, 0)


class Solver(ABC):
    @abstractmethod
    def df(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def teams(self) -> List[int]:
        pass

    @abstractmethod
    def factors(self) -> List[str]:
        """second argument is the corresponding strings forarray values."""
        pass

    @abstractmethod
    def initial(self) -> List[float]:
        """
        first argument required by optimize is a 1d array with some number of values
        and set a reasonable initial value for the solver.
        """
        pass

    @abstractmethod
    def cons(self) -> List[dict]:
        pass

    @abstractmethod
    def bnds(self) -> List[Tuple[float, float]]:
        pass

    @abstractmethod
    def obj(self, values: List[float], factors: List[str], df: pd.DataFrame) -> float:
        """turn df strings into values that can be calculated."""
        pass

    @abstractmethod
    def solve(self):
        pass

    @abstractmethod
    def result(self):
        pass


class SolverSeason(Solver):
    def __init__(self, df: pd.DataFrame, teams: Optional[list] = None):
        self._df = df
        self._teams = teams
        self.YEARS = 1

    @property
    def df(self) -> pd.DataFrame:
        self._df["recent"] = calculate_recentness(self._df["date_unix"], self.YEARS)
        self._df["avg_goal"] = "avg_goal"
        self._df["home_adv"] = "home_adv"
        for team in ["home", "away"]:
            for factor in ["off", "def"]:
                self._df[f"{team}_{factor}"] = (
                    self._df[f"{team}_id"].astype(str) + f"_{factor}"
                )
        return self._df

    @property
    def teams(self) -> List[int]:
        return self._teams or np.unique(self.df[["home_id", "away_id"]].values)

    @property
    def factors(self) -> List[str]:
        return (
            ["avg_goal", "home_adv"]
            + [f"{team}_off" for team in self.teams]
            + [f"{team}_def" for team in self.teams]
        )

    @property
    def initial(self) -> List[float]:
        return [1.35, 1] + [1] * len(self.teams) * 2

    @property
    def cons(self) -> List[dict]:
        cons_avg_off = {"type": "eq", "fun": avg_off}
        cons_avg_def = {"type": "eq", "fun": avg_def}
        cons_home_adv = {"type": "ineq", "fun": min_home_adv}
        return [cons_avg_off, cons_avg_def, cons_home_adv]

    @property
    def bnds(self) -> List[Tuple[float, float]]:
        return ((0.2, 5),) * len(self.factors)

    @staticmethod
    def obj(values: List[float], factors: List[str], df: pd.DataFrame) -> float:
        lookup = dict(zip(factors, values))
        df = df.replace(lookup)
        obj = (
            (
                df["avg_goal"]
                * df["home_adv"] ** (1 - df["no_home_away"])
                * df["home_off"]
                * df["away_def"]
                + df["home_league"]
                - df["away_league"]
                - df["home_avg"]
            )
            ** 2
            + (
                df["avg_goal"]
                / df["home_adv"] ** (1 - df["no_home_away"])
                * df["away_off"]
                * df["home_def"]
                + df["away_league"]
                - df["home_league"]
                - df["away_avg"]
            )
            ** 2
        ) * df["recent"]
        return np.sum(obj)

    def solve(self) -> optimize.OptimizeResult:
        return optimize.minimize(
            self.obj,
            args=(self.factors, self.df),
            x0=self.initial,
            method="SLSQP",
            constraints=self.cons,
            bounds=self.bnds,
            options={"maxiter": 10000},
        )

    @property
    def result(self) -> Tuple[Tuple[float, float], Tuple[float]]:
        result = self.solve()
        result_season = (result.x[0], result.x[1])
        result_team = list(
            zip(
                self.teams,
                result.x[2 : -len(self.teams)],
                result.x[-len(self.teams) :],
            )
        )
        return result_season, result_team


class SolverInterLeague(Solver):
    def __init__(self, df: pd.DataFrame, teams: Optional[list] = None):
        self._df = df
        self._teams = teams
        self.YEARS = 4

    @property
    def df(self) -> pd.DataFrame:
        self._df["recent"] = calculate_recentness(self._df["date_unix"], self.YEARS)
        self._df["avg_goal"] = "avg_goal"
        self._df["home_adv"] = "home_adv"
        return self._df

    @property
    def teams(self) -> List[int]:
        return np.unique(self.df[["home_league", "away_league"]].values)

    @property
    def factors(self) -> List[str]:
        return ["avg_goal", "home_adv"] + [self.teams]

    @property
    def initial(self) -> List[float]:
        return [1.35, 1] + [0] * len(self.teams)

    @property
    def cons(self) -> List[dict]:
        cons_sum_strength = {"type": "eq", "fun": sum_strength}
        cons_home_adv = {"type": "ineq", "fun": min_home_adv}
        return [cons_sum_strength, cons_home_adv]

    @staticmethod
    def obj(values: List[float], factors: List[str], df: pd.DataFrame) -> float:
        lookup = dict(zip(factors, values))
        df = df.replace(lookup)
        obj = (
            (
                df["avg_goal"]
                * df["home_adv"] ** (1 - df["no_home_away"])
                * df["home_off"]
                * df["away_def"]
                + df["home_league"]
                - df["away_league"]
                - df["home_avg"]
            )
            ** 2
            + (
                df["avg_goal"]
                / df["home_adv"] ** (1 - df["no_home_away"])
                * df["away_off"]
                * df["home_def"]
                + df["away_league"]
                - df["home_league"]
                - df["away_avg"]
            )
            ** 2
        ) * df["recent"]
        return np.sum(obj)

    def solve(self) -> optimize.OptimizeResult:
        return optimize.minimize(
            self.obj,
            args=(self.factors, self.df),
            x0=self.initial,
            method="SLSQP",
            constraints=self.cons,
            options={"maxiter": 10000},
        )

    def result(self) -> Tuple[Tuple[float, float], Tuple[float]]:
        result = self.solve()
        result_season = (result.x[0], result.x[1])
        result_team = list(
            zip(
                self.factors,
                result.x[2:],
            )
        )
        return result_season, result_team
