from dataclasses import dataclass

import random
import numpy as np

from .team import Team


@dataclass
class Match:
    home_team: Team
    away_team: Team
    status: str = "incomplete"
    home_score: int = 0
    away_score: int = 0

    def __post_init__(self):
        self._status = self.status
        self._home_score = self.home_score
        self._away_score = self.away_score
        self._winning_team = None

    def __add__(self, other: "Match") -> "Match":
        if (self.home_team, self.away_team) != (other.away_team, other.home_team):
            raise ValueError
        if self.is_complete and other.is_complete:
            status = "complete"
        else:
            status = "incomplete"
        return Match(
            home_team=self.away_team,
            away_team=self.home_team,
            status=status,
            home_score=self.away_score + other.home_score,
            away_score=self.home_score + other.away_score,
        )

    @property
    def teams(self) -> tuple[Team]:
        return (self.home_team, self.away_team)

    @property
    def is_complete(self) -> bool:
        return self.status == "complete"

    @property
    def winning_team(self) -> Team | None:
        if not self.is_complete:
            return None
        if self.home_score > self.away_score:
            return self.home_team
        if self.away_score > self.home_score:
            return self.away_team
        return self._winning_team

    def _simulate(self, avg_goal: float, home_adv: float, extra_time: bool = False):
        home_exp = avg_goal + home_adv + self.home_team.offence + self.away_team.defence
        away_exp = avg_goal - home_adv + self.away_team.offence + self.home_team.defence
        if extra_time:
            home_exp /= 3
            away_exp /= 3
        home_exp = max(home_exp, 0.2)
        away_exp = max(away_exp, 0.2)
        self.home_score += np.random.poisson(home_exp)
        self.away_score += np.random.poisson(away_exp)

    def set_status_complete(self):
        self.status = "complete"

    def simulate(self, avg_goal: float, home_adv: float, is_cup: bool = False):
        self._simulate(avg_goal, home_adv)
        if self.winning_team or not is_cup:
            self.set_status_complete()
            return

        self._simulate(avg_goal, home_adv, extra_time=True)
        if self.winning_team:
            self.set_status_complete()
            return

        self._winning_team = random.choice([self.home_team, self.away_team])
        self.set_status_complete()

    def log_teams_table(self, h2h=False):
        if h2h:
            home_table = self.home_team.h2h_table
            away_table = self.away_team.h2h_table
        else:
            home_table = self.home_team.table
            away_table = self.away_team.table

        if self.winning_team == self.home_team:
            home_table.wins += 1
            away_table.losses += 1
        elif self.winning_team == self.away_team:
            away_table.wins += 1
            home_table.losses += 1
        else:
            home_table.draws += 1
            away_table.draws += 1

        home_table.scored += self.home_score
        away_table.scored += self.away_score
        home_table.conceded += self.away_score
        away_table.conceded += self.home_score

    def reset(self):
        self.status = self._status
        self.home_score = self._home_score
        self.away_score = self._away_score
        self._winning_team = None
