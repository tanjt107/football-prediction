from dataclasses import dataclass

from pulp import LpVariable


@dataclass
class League:
    name: str

    def __post_init__(self):
        self.avg_goal = LpVariable(f"avg_goal_{self.name}", lowBound=0)
        self.home_adv = LpVariable(f"home_adv_{self.name}", lowBound=0)


@dataclass
class Team:
    id: str

    def __post_init__(self):
        self.offence = LpVariable(f"offence_{self.id}")
        self.defence = LpVariable(f"defence_{self.id}")


@dataclass
class Match:
    id: int
    league: League
    home_team: Team
    away_team: Team
    home_score: float
    away_score: float
    recent: float

    def __post_init__(self):
        self.home_error = LpVariable(f"offence_{self.id}")
        self.away_error = LpVariable(f"defence_{self.id}")

    @property
    def home_error_val(self):
        return (
            self.league.avg_goal
            + self.league.home_adv
            + self.home_team.offence
            + self.away_team.defence
            - self.home_score
        ) * self.recent

    @property
    def away_error_val(self):
        return (
            self.league.avg_goal
            - self.league.home_adv
            + self.away_team.offence
            + self.home_team.defence
            - self.away_score
        ) * self.recent
