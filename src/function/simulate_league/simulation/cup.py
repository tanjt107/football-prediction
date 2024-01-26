import random
from dataclasses import dataclass

from simulation.models import Leg, Match, Round, Rules, Team


@dataclass
class Knockout:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    rule: Rules
    matchups: dict[Round, list[tuple[Team, Team]]] | None = None
    completed: dict[
        tuple[str],
        tuple[int],
    ] | None = None

    def __post_init__(self):
        if not self.matchups:
            self.matchups = {}
        self._leg = self.rule.leg
        self.results = {Round(len(self.teams)): self.teams}

    @property
    def _home_adv(self):
        return {Leg.SINGLE: 0, Leg.DOUBLE: self.home_adv}[self._leg]

    @staticmethod
    def draw_matchup(teams: list[Team]) -> list[tuple[Team, Team]]:
        random.shuffle(teams)
        return list(zip(teams[::2], teams[1::2]))

    def get_winner(self, home_team: Team, away_team: Team):
        return {
            Leg.SINGLE: self.get_single_leg_winner(home_team, away_team),
            Leg.DOUBLE: self.get_double_leg_winner(home_team, away_team),
        }[self._leg]

    def update_or_simulate_match(self, home_team: Team, away_team: Team) -> Match:
        game = Match(home_team, away_team)
        game.update_score(self.completed, self._leg)
        if not game.completed:
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

        if self.rule.away_goal:
            game = Match(
                home_team,
                away_team,
                home_score=leg2.away_score,
                away_score=leg1.away_score,
            )

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
        _round = Round(len(advanced))

        while _round > Round.CHAMPS:
            self._leg = self.rule.leg_final if _round == Round.FINAL else self.rule.leg

            matchups = self.matchups.get(_round) or []
            if len(matchups) != len(advanced) / 2:
                matchups = self.draw_matchup(advanced)

            advanced = [
                self.get_winner(home_team, away_team)
                for home_team, away_team in matchups
            ]

            _round = Round(len(advanced))
            self.results[_round] = advanced
