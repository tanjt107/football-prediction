from dataclasses import dataclass
from collections import defaultdict
from enum import Enum

import numpy as np


class Leg(Enum):
    SINGLE = 1
    DOUBLE = 2


class Round(Enum):
    R16 = 16
    QF = 8
    SF = 4
    F = 2
    CHAMP = 1

    def __gt__(self, other: "Round"):
        return self.value > other.value

    def __hash__(self):
        return hash(self.value)


@dataclass
class Rules:
    h2h: bool = False
    leg: int = 2
    leg_final: int = 1
    away_goal: bool = True

    def __post_init__(self):
        self.leg = Leg(self.leg)
        self.leg_final = Leg(self.leg_final)

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff


@dataclass
class Table:
    wins: int = 0
    draws: int = 0
    losses: int = 0
    scored: int = 0
    conceded: int = 0
    correction: int = 0

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws + self.correction

    @property
    def goal_diff(self) -> int:
        return self.scored - self.conceded

    def __add__(self, other: "Table"):
        return Table(
            self.wins + other.wins,
            self.draws + other.draws,
            self.losses + other.losses,
            self.scored + other.scored,
            self.conceded + other.conceded,
            self.correction + other.correction,
        )

    def __truediv__(self, other: "Table"):
        return Table(
            self.wins / other,
            self.draws / other,
            self.losses / other,
            self.scored / other,
            self.conceded / other,
            self.correction / other,
        )

    def reset(self):
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.scored = 0
        self.conceded = 0


class Results(defaultdict):
    def __init__(self):
        super().__init__(int)

    def __truediv__(self, other):
        for key in self:
            self[key] /= other
        return self


@dataclass
class Team:
    name: str
    offence: float
    defence: float

    def __post_init__(self):
        self.table = Table()
        self.h2h_table = Table()
        self.sim_table = Table()
        self.sim_positions = Results()
        self.sim_rounds = Results()

    def __eq__(self, other: "Team") -> bool:
        return other and self.name == other.name

    def set_correction(self, value: int):
        self.correction = value

    def update_sim_table(self):
        self.sim_table += self.table

    def update_sim_positions(self, position: int):
        self.sim_positions[f"_{position}"] += 1

    def update_sim_rounds(self, _round: Round):
        self.sim_rounds[_round.name] += 1

    def reset(self):
        self.table.reset()
        self.h2h_table.reset()


class TieBreaker:
    @staticmethod
    def h2h(team: Team) -> tuple:
        return (
            team.table.points,
            team.h2h_table.points,
            team.h2h_table.goal_diff,
            team.h2h_table.scored,
            team.table.goal_diff,
            team.table.scored,
        )

    @staticmethod
    def goal_diff(team: Team) -> tuple:
        return (team.table.points, team.table.goal_diff, team.table.scored)


@dataclass
class Match:
    home_team: Team
    away_team: Team
    home_score: int | None = None
    away_score: int | None = None

    @property
    def teams(self):
        return (self.home_team.name, self.away_team.name)

    @property
    def teams_reversed(self):
        return (self.away_team.name, self.home_team.name)

    @property
    def score(self):
        return (self.home_score, self.away_score)

    @property
    def completed(self) -> bool:
        return self.home_score is not None and self.away_score is not None

    @property
    def winner(self):
        if not self.completed:
            return
        if self.home_score > self.away_score:
            return self.home_team
        if self.away_score > self.home_score:
            return self.away_team

    def update_score(
        self,
        completed: dict[
            tuple[str],
            tuple[int],
        ]
        | None = None,
        round: int = Leg.DOUBLE,
    ) -> tuple[int] | None:
        if not completed:
            return
        if self.teams in completed:
            self.home_score, self.away_score = completed[self.teams]
        if round == Leg.SINGLE and self.teams_reversed in completed:
            self.away_score, self.home_score = completed[self.teams_reversed]

    def simulate(self, avg_goal: float, home_adv: float, extra_time: bool = False):
        home_exp = avg_goal + home_adv + self.home_team.offence + self.away_team.defence
        away_exp = avg_goal - home_adv + self.away_team.offence + self.home_team.defence
        if extra_time:
            home_exp /= 3
            away_exp /= 3
        home_exp = max(home_exp, 0.2)
        away_exp = max(away_exp, 0.2)
        self.home_score = np.random.poisson(home_exp)
        self.away_score = np.random.poisson(away_exp)

    def update_teams(self, h2h=False):
        if h2h:
            home_table = self.home_team.h2h_table
            away_table = self.away_team.h2h_table
        else:
            home_table = self.home_team.table
            away_table = self.away_team.table

        if self.winner == self.home_team:
            home_table.wins += 1
            away_table.losses += 1
        elif self.winner == self.away_team:
            away_table.wins += 1
            home_table.losses += 1
        else:
            home_table.draws += 1
            away_table.draws += 1

        home_table.scored += self.home_score
        away_table.scored += self.away_score
        home_table.conceded += self.away_score
        away_table.conceded += self.home_score
