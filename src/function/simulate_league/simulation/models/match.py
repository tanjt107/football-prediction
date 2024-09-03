from dataclasses import dataclass

import numpy as np

from .team import Team


@dataclass
class Match:
    home_team: Team
    away_team: Team
    status: str = "incomplete"
    home_score: int | None = None
    away_score: int | None = None

    def __post_init__(self):
        self._status = self.status
        self._home_score = self.home_score
        self._away_score = self.away_score

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
        return None

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
        self.status = "complete"

    def update_teams(self, h2h=False):
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
