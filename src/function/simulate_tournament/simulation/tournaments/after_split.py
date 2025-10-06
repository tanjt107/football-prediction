from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from itertools import combinations, permutations

from simulation.models import Team, TieBreaker, Match


@dataclass
class AfterSplit:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    matches: list[Match] | None = None
    h2h: bool = False
    leg: int = 2
    start: int = 1

    def __post_init__(self):
        self.teams: list[Team] = []
        self.matches = self.matches or []

    @property
    def scheduling(self):
        if self.leg == 1:
            return partial(combinations, r=2)
        if self.leg == 2:
            return partial(permutations, r=2)
        raise ValueError

    def schedule_matches(self):
        return [
            Match(home_team, away_team)
            for home_team, away_team in self.scheduling(self.teams)
        ]

    @property
    def _home_adv(self):
        if self.leg == 1:
            return 0
        return self.home_adv

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff

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
                        match.log_teams_table(h2h=True)

        return sorted(
            self.teams,
            key=self.tiebreaker,
            reverse=True,
        )

    def add_teams(self, teams: list[Team]):
        self.teams.extend(teams)

    def simulate(self):
        self.matches = self.matches or self.schedule_matches()
        for match in self.matches:
            if not match.is_complete:
                match.simulate(self.avg_goal, self._home_adv)
            match.log_teams_table()

        for position, team in enumerate(self.positions, 1):
            team.log_sim_table()
            team.log_sim_positions(position + self.start - 1)

    @property
    def advanced_teams(self):
        return None

    def reset(self):
        for match in self.matches:
            match.reset()
        for team in self.teams:
            team.reset()
        self.teams = []
        self.matches = []
