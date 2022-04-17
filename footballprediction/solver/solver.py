import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from scipy import optimize
from typing import List, Optional, Tuple
from .constraints import avg_off, avg_def, sum_strength


def calculate_recentness(dt: pd.Series, years: float) -> pd.Series:
    """
    Recentness factor gives less weight to games that were played further back in time.
    A bouns of up to 25 percent is also given to games played within past past 25 days to reflect a team's most recent form.

    Parameters:
    ------------
    ts: pandas.Series
        Series of epoch timestamps.
    year: float
        Cut off number of year.

    Return:
    ------------
    recent: pandas.Series
        Series of recentness factor.
    """
    max_dt = dt.max()
    cut_off_dt = max_dt - years * 31536000  # 365 * 24 * 60 * 60
    bonus_dt = years * 2160000  # 25 * 24 * 60 * 60
    bonus = np.where(
        max_dt - dt < bonus_dt, 1 + (bonus_dt - max_dt + dt) / bonus_dt * 0.25, 1
    )
    recent = (dt - cut_off_dt) / (max_dt - cut_off_dt) * bonus
    return np.where(recent > 0, recent, 0)


class Solver(ABC):
    @abstractmethod
    def df(self) -> pd.DataFrame:
        """
        Dataframe to be passed to the opbjective function.
        """
        pass

    @abstractmethod
    def func(self, values: List[float], factors: List[str], df: pd.DataFrame) -> float:
        """
        The objective function to be minimized.
        turn df strings into values that can be calculated.
        """
        pass

    @abstractmethod
    def x0(self) -> List[float]:
        """
        Initial guess.
        A 1d array with some number of values
        and set a reasonable initial value for the solver.
        """
        pass

    @abstractmethod
    def factors(self) -> List[str]:
        """
        Corresponding strings for array values.
        """
        pass

    @abstractmethod
    def bounds(self) -> List[Tuple[float, float]]:
        """
        Sequence of (min, max) pairs for each element in x.
        """
        pass

    @abstractmethod
    def constraints(self) -> List[dict]:
        """
        List of dictionaries of constraints.

        Each dictionary has the following keys:
        type: str
            Constraint type: 'eq' for equality, 'ineq' for inequality.
        fun: Callable
            Constraint function.
        """
        pass

    @abstractmethod
    def solve(self) -> optimize.OptimizeResult:
        pass

    @abstractmethod
    def results(self) -> Tuple[Tuple[float], Tuple[float]]:
        pass


class SolverSeason(Solver):
    def __init__(
        self,
        df: pd.DataFrame,
        teams: Optional[list] = None,
        max: Optional[float] = None,
    ):
        self._df = df
        self._teams = teams
        self.max = max
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

    @staticmethod
    def func(values: List[float], factors: List[str], df: pd.DataFrame) -> float:
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

    @property
    def teams(self) -> List[int]:
        return self._teams or np.unique(self.df[["home_id", "away_id"]].values)

    @property
    def x0(self) -> List[float]:
        return [1.35, 1] + [1] * len(self.teams) * 2

    @property
    def factors(self) -> List[str]:
        return (
            ["avg_goal", "home_adv"]
            + [f"{team}_off" for team in self.teams]
            + [f"{team}_def" for team in self.teams]
        )

    @property
    def bounds(self) -> Tuple[Tuple[float, float]]:
        return ((0, None), (1, None)) + ((0.2, self.max),) * len(self.teams) * 2

    @property
    def constraints(self) -> List[dict]:
        return [{"type": "eq", "fun": avg_off}, {"type": "eq", "fun": avg_def}]

    def solve(self) -> optimize.OptimizeResult:
        return optimize.minimize(
            self.func,
            self.x0,
            args=(self.factors, self.df),
            method="SLSQP",
            bounds=self.bounds,
            constraints=self.constraints,
        )

    @property
    def results(self) -> Tuple[Tuple[float], Tuple[float]]:
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
    def __init__(
        self,
        df: pd.DataFrame,
    ):
        self._df = df
        self.YEARS = 5

    @property
    def df(self) -> pd.DataFrame:
        self._df["recent"] = calculate_recentness(self._df["date_unix"], self.YEARS)
        self._df["avg_goal"] = "avg_goal"
        self._df["home_adv"] = "home_adv"
        return self._df

    @staticmethod
    def func(values: List[float], factors: List[str], df: pd.DataFrame) -> float:
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

    @property
    def leagues(self) -> List[str]:
        return np.unique(self.df[["home_league", "away_league"]].values).tolist()

    @property
    def x0(self) -> List[float]:
        return [1.35, 1] + [0] * len(self.leagues)

    @property
    def factors(self) -> List[str]:
        return ["avg_goal", "home_adv"] + self.leagues

    @property
    def bounds(self) -> Tuple[Tuple[float, float]]:
        return ((0, None), (1, None)) + ((None, None),) * len(self.leagues)

    @property
    def constraints(self) -> List[dict]:
        return [{"type": "eq", "fun": sum_strength}]

    def solve(self) -> optimize.OptimizeResult:
        return optimize.minimize(
            self.func,
            self.x0,
            args=(self.factors, self.df),
            method="SLSQP",
            bounds=self.bounds,
            constraints=self.constraints,
        )

    @property
    def results(self) -> Tuple[Tuple[float], Tuple[float]]:
        result = self.solve()
        result_season = (result.x[0], result.x[1])
        result_league = list(
            zip(
                self.leagues,
                result.x[2:],
            )
        )
        return result_season, result_league
