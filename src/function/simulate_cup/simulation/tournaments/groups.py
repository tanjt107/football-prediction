from collections import defaultdict
from dataclasses import dataclass

from simulation.models import Match, TieBreaker, Team
from .season import Season


@dataclass
class Groups:
    groups: dict[str, list[Team]]
    avg_goal: float
    home_adv: float
    h2h: bool = False
    leg: int = 2
    matches: list[Match] | None = None

    def __post_init__(self):
        if not self.leg in (1, 2):
            raise ValueError  # TODO Error Message

        self.matches = self.matches or []
        self._matches = self.matches
        self.positions = defaultdict(list)

        # TODO review this logic
        team_group = {
            team: group for group, teams in self.groups.items() for team in teams
        }
        group_matches = defaultdict(list)
        for match in self.matches:
            group_matches[team_group[match.home_team]].append(match)
        self._groups = [
            Season(
                teams,
                self.avg_goal,
                self.home_adv,
                self.h2h,
                self.leg,
                group_matches[name],
            )
            for name, teams in self.groups.items()
        ]

    @property
    def teams(self) -> list[Team]:
        return [team for group in self._groups for team in group.teams]

    def simulate(self):
        for group in self._groups:
            group.simulate()
            for position, team in enumerate(group.positions, 1):
                self.positions[position].append(team)

    def reset(self):
        self.matches = self._matches
        self.positions = defaultdict(list)

        for group in self._groups:
            group.reset()

    def get_advanced(self, n: int) -> list[Team]:
        direct, wildcard = divmod(n, len(self.groups))
        advanced = []
        for position, teams in self.positions.items():
            if position <= direct:
                advanced.extend(teams)
            if position == direct + 1:
                advanced.extend(
                    sorted(
                        self.positions[direct + 1],
                        key=TieBreaker.goal_diff,
                        reverse=True,
                    )[:wildcard]
                )
        return advanced
