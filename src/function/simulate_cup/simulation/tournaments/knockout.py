import random
from collections import defaultdict
from dataclasses import dataclass

from simulation.models import Match, Team


@dataclass
class Knockout:
    name: str
    teams: set[Team]
    avg_goal: float
    home_adv: float
    leg: int = 2
    matches: list[Match] | None = None
    winning_teams: set[Team] | None = None

    def __post_init__(self):
        if not self.leg in (1, 2):
            raise ValueError

        self.matches = self.matches or []
        self.winning_teams = self.winning_teams or set()
        self._teams = self.teams
        self._matches = self.matches
        self._winning_teams = self.winning_teams

        for team in self.teams:
            team.update_sim_rounds(self.name)

    @property
    def _home_adv(self):
        if self.leg == 1:
            return 0
        return self.home_adv

    @staticmethod
    def draw_series(
        teams: set[Team], scheduled_matches: list[Match], leg: int = 2
    ) -> dict[tuple[Team], list[Match]]:
        if len(teams) == 1:
            return {}

        series = defaultdict(list)
        drawn = {team for match in scheduled_matches for team in match.teams}
        undrawn = [team for team in teams if team not in drawn]
        random.shuffle(undrawn)

        for match in scheduled_matches:
            series_id = f"{match.home_team.name}_{match.away_team.name}"  # TODO Review this logic
            series[series_id].append(match)

        for i in range(0, len(undrawn), 2):
            home_team = undrawn[i]
            away_team = undrawn[i + 1]
            series_id = f"{home_team.name}_{away_team.name}"
            series[series_id].append(Match(home_team, away_team))
            if leg == 2:
                series[series_id].append(Match(away_team, home_team))

        return series

    def simulate(self):
        series = self.draw_series(self.teams, self.matches, self.leg)
        for matches in series.values():
            if self.leg == 2:
                leg1 = matches[0]
                if not leg1.is_complete:
                    leg1.simulate()
                leg2 += matches[1]
            else:
                leg2 = matches[0]

            if not leg2.is_complete:
                leg2.simulate(is_cup=True)

            if leg2.winning_team:
                self.winning_teams.add(leg2.winning_team)

    def reset(self):
        self.teams = self._teams
        self.matches = self._matches
        self.winning_teams = self._winning_teams
