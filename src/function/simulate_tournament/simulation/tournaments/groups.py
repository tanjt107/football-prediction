from collections import defaultdict
from dataclasses import dataclass

from simulation.models import Match, TieBreaker, Team
from .season import Season


@dataclass
class Groups:
    groups: dict[str, list[Team]]
    avg_goal: float
    home_adv: float
    matches: list[Match]
    h2h: bool = False
    leg: int = 2

    def __post_init__(self):
        self.matches = self.matches or []
        self._matches = self.matches.copy()
        self._positions = defaultdict(list)

        group_matches = self.get_matches_by_groups(self.matches, self.groups)
        self._groups = [
            Season(
                teams,
                self.avg_goal,
                self.home_adv,
                group_matches[name],
                self.h2h,
                self.leg,
            )
            for name, teams in self.groups.items()
        ]

    @property
    def teams(self) -> list[Team]:
        return [team for group in self._groups for team in group.teams]

    @property
    def positions(self) -> list[Team]:
        positions = []
        for _, teams in sorted(self._positions.items()):
            positions.extend(sorted(teams, key=TieBreaker.goal_diff, reverse=True))
        return positions

    @staticmethod
    def get_matches_by_groups(
        matches: list[Match], groups: dict[str, list[Team]]
    ) -> dict[str, list[Match]]:
        team_group = {team: group for group, teams in groups.items() for team in teams}
        group_matches = defaultdict(list)
        for match in matches:
            group_matches[team_group[match.home_team]].append(match)
        return group_matches

    def simulate(self):
        for group in self._groups:
            group.simulate()
            for position, team in enumerate(group.positions, 1):
                self._positions[position].append(team)

    def get_advanced(self, end: int, start: int = 1) -> list[Team]:
        return self.positions[start - 1 : end]

    def reset(self):
        self.matches = self._matches.copy()
        self._positions = defaultdict(list)

        for group in self._groups:
            group.reset()
