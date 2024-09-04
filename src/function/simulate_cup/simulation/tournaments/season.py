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
    matches: list[Match] | None = None

    def __post_init__(self):
        self.matches = self.matches or self.scheduling(self.teams)

    @property
    def _home_adv(self):
        if self.leg == 1:
            return 0
        return self.home_adv

    @property
    def scheduling(self):
        if self.leg == 1:
            return partial(combinations, r=2)
        if self.leg == 2:
            return partial(permutations, r=2)
        raise ValueError

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff

    def simulate(self):
        for match in self.matches:
            if not match.is_complete:
                match.simulate(self.avg_goal, self.home_adv)
            match.update_teams()

        for position, team in enumerate(self.positions, 1):
            team.update_sim_table()
            team.update_sim_positions(position)

    @property
    def positions(self) -> list[Team]:
        points = defaultdict(list)
        for team in self.teams:
            points[team.table.points].append(team)

        if self.h2h:
            for teams in points.values():
                if len(teams) < 2:
                    continue
                for match in self.matches:
                    if match.home_team in teams and match.away_team in teams:
                        match.update_teams(h2h=True)

        return sorted(
            self.teams,
            key=self.tiebreaker,
            reverse=True,
        )

    def reset(self):
        for match in self.matches:
            match.reset()
        for team in self.teams:
            team.reset()
