from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from itertools import combinations, permutations

from simulation.models import Team, TieBreaker, Match


@dataclass
class Season:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    h2h: bool = False
    leg: int = 2
    fixtures: list[tuple[Team, Team]] | None = None
    results: (
        dict[
            tuple[str],
            tuple[int],
        ]
        | None
    ) = None

    def __post_init__(self):
        if not self.leg in (1, 2):
            raise ValueError

        self.fixtures = self.fixtures or list(self.scheduling(self.teams))
        self._results = self.results.copy() if self.results else {}

    @property
    def _home_adv(self):
        if self.leg == 1:
            return 0
        return self.home_adv

    @property
    def scheduling(self):
        if self.leg == 1:
            return partial(combinations, r=2)
        return partial(permutations, r=2)

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff

    def update_or_simulate_match(self, home_team: Team, away_team: Team):
        game = Match(home_team, away_team)
        game.update_score(self._results, self.leg)
        if not game.completed:
            game.simulate(self.avg_goal, self._home_adv)
            self._results[game.teams] = game.score
        game.update_teams()

    def simulate(self):
        for home_team, away_team in self.fixtures:
            self.update_or_simulate_match(home_team, away_team)

    @property
    def positions(self) -> list[Team]:
        points = defaultdict(list)
        for team in self.teams:
            points[team.table.points].append(team)

        for teams in points.values():
            for home_team, away_team in self.scheduling(teams):
                game = Match(home_team, away_team)
                game.update_score(self._results, self.leg)
                game.update_teams(h2h=True)

        return sorted(
            self.teams,
            key=self.tiebreaker,
            reverse=True,
        )

    def reset(self):
        self._results = self.results.copy() if self.results else {}
        for team in self.teams:
            team.reset()
