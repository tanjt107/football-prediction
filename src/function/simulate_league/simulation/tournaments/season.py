from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations

from simulation.models import Team, TieBreaker, Match


@dataclass
class Season:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    h2h: bool = False
    leg: int = 2
    completed: (
        dict[
            tuple[str],
            tuple[int],
        ]
        | None
    ) = None

    def __post_init__(self):
        if not self.leg in (1, 2):
            raise ValueError

        self._completed = self.completed.copy() if self.completed else {}

    @property
    def _home_adv(self):
        if self.leg == 1:
            return 0
        return self.home_adv

    @property
    def scheduling(self):
        if self.leg == 1:
            return combinations
        return permutations

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff

    def update_or_simulate_match(self, home_team: Team, away_team: Team):
        game = Match(home_team, away_team)
        game.update_score(self._completed, self.leg)
        if not game.completed:
            game.simulate(self.avg_goal, self._home_adv)
            self._completed[game.teams] = game.score
        game.update_teams()

    def simulate(self):
        self.reset()
        for home_team, away_team in self.scheduling(self.teams, 2):
            self.update_or_simulate_match(home_team, away_team)

    @property
    def positions(self) -> list[Team]:
        points = defaultdict(list)
        for team in self.teams:
            points[team.table.points].append(team)

        for teams in points.values():
            for home_team, away_team in self.scheduling(teams, 2):
                game = Match(home_team, away_team)
                game.update_score(self._completed, self.leg)
                game.update_teams(h2h=True)

        return sorted(
            self.teams,
            key=self.tiebreaker,
            reverse=True,
        )

    def reset(self):
        self._completed = self.completed.copy() if self.completed else {}
        for team in self.teams:
            team.reset()
