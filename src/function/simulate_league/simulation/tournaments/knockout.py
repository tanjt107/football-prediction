import random
from dataclasses import dataclass

from simulation.models import Match, Round, Team


@dataclass
class Knockout:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    leg: int = 2
    fixtures: dict[Round, list[tuple[Team, Team]]] | None = None
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

        if not self.fixtures:
            self.fixtures = {}
        self.results = {Round(len(self.teams)): self.teams}

    @property
    def _home_adv(self):
        if self.leg == 2:
            return self.home_adv
        return 0

    @staticmethod
    def draw_matchup(
        teams: list[Team], drawn: set[set[Team]]
    ) -> list[tuple[Team, Team]]:
        drawn_teams = [team for teams in drawn for team in teams]
        undrawn = [team for team in teams if team not in drawn_teams]
        random.shuffle(undrawn)
        return [(home, away) for home, away in drawn] + list(
            zip(undrawn[::2], undrawn[1::2])
        )

    def get_winner(
        self, home_team: Team, away_team: Team, advanced: list[Team] | None = None
    ):
        advanced = advanced or []

        if home_team in advanced:
            return home_team
        if away_team in advanced:
            return away_team

        if self.leg == 1:
            return self.get_single_leg_winner(home_team, away_team)
        return self.get_double_leg_winner(home_team, away_team)

    def update_or_simulate_match(self, home_team: Team, away_team: Team) -> Match:
        game = Match(home_team, away_team)
        game.update_score(self.results, self.leg)
        if not game.is_complete:
            game.simulate(self.avg_goal, self._home_adv)
        return game

    def get_single_leg_winner(self, home_team: Team, away_team: Team):
        game = self.update_or_simulate_match(home_team, away_team)
        return game.winner or self.get_extra_time_winner(home_team, away_team)

    def get_double_leg_winner(
        self,
        home_team: Team,
        away_team: Team,
    ):
        leg1 = self.update_or_simulate_match(home_team, away_team)
        leg2 = self.update_or_simulate_match(home_team=away_team, away_team=home_team)

        game = Match(
            home_team,
            away_team,
            home_score=leg1.home_score + leg2.away_score,
            away_score=leg1.away_score + leg2.home_score,
        )

        if game.winner:
            return game.winner

        return game.winner or self.get_extra_time_winner(
            home_team=away_team,
            away_team=home_team,
        )

    def get_extra_time_winner(
        self,
        home_team: Team,
        away_team: Team,
    ):
        game = Match(home_team, away_team)
        game.simulate(self.avg_goal, self._home_adv, extra_time=True)
        return game.winner or random.choice([home_team, away_team])

    def simulate(self):
        advanced = self.teams
        current_round = Round(len(advanced))
        next_round_len = len(advanced) / 2

        while current_round > Round.CHAMPS:
            matchups = self.fixtures.get(current_round, [])
            next_round = Round(next_round_len)
            winners = [
                team for teams in self.fixtures.get(next_round, []) for team in teams
            ]

            matchups = self.draw_matchup(advanced, matchups)

            advanced = [
                self.get_winner(home_team, away_team, winners)
                for home_team, away_team in matchups
            ]

            self.results[next_round] = advanced
            current_round = next_round
            next_round_len /= 2
