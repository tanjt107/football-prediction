import random
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import combinations, permutations

import numpy as np


class RoundRobin(Enum):
    SINGLE = 1
    DOUBLE = 2


@dataclass
class Table:
    wins: int = 0
    draws: int = 0
    losses: int = 0
    scored: int = 0
    conceded: int = 0

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def goal_diff(self) -> int:
        return self.scored - self.conceded

    def reset(self):
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.scored = 0
        self.conceded = 0

    def __add__(self, other):
        self.wins += other.wins
        self.draws += other.draws
        self.losses += other.losses
        self.scored += other.scored
        self.conceded += other.conceded
        return self

    def __truediv__(self, other):
        self.wins /= other
        self.draws /= other
        self.losses /= other
        self.scored /= other
        self.conceded /= other
        return self


class Outcome(defaultdict):
    def __init__(self):
        super().__init__(int)

    def __truediv__(self, other):
        for key in self:
            self[key] /= other
        return self


@dataclass
class Team:
    name: str
    offence: float
    defence: float

    def __post_init__(self):
        self.table = Table()
        self.h2h_table = Table()
        self.sim_table = Table()
        self.sim_positions = Outcome()
        self.sim_rounds = Outcome()

    def update_sim_table(self):
        self.sim_table += self.table

    def update_sim_positions(self, position: int):
        self.sim_positions[position] += 1

    def update_sim_rounds(self, round: str):
        self.sim_rounds[round] += 1

    def __eq__(self, other) -> bool:
        return other and self.name == other.name

    def reset(self):
        self.table.reset()
        self.h2h_table.reset()


@dataclass
class Match:
    home_team: Team
    away_team: Team
    home_score: int | None = None
    away_score: int | None = None

    @property
    def completed(self) -> bool:
        return self.home_score is not None and self.away_score is not None

    @property
    def winner(self):
        if not self.completed:
            return
        if self.home_score > self.away_score:
            return self.home_team
        if self.away_score > self.home_score:
            return self.away_team

    def update_score(
        self,
        completed: dict[
            tuple[str],
            tuple[int],
        ]
        | None = None,
        round: int = RoundRobin.DOUBLE,
    ) -> tuple[int] | None:
        if not completed:
            return
        key = (self.home_team.name, self.away_team.name)
        key_reversed = (self.away_team.name, self.home_team.name)
        if key in completed:
            self.home_score, self.away_score = completed[key]
        if round == RoundRobin.SINGLE and key_reversed in completed:
            self.away_score, self.home_score = completed[key_reversed]

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

    def update_teams(self, h2h=False):
        if h2h:
            home_table = self.home_team.h2h_table
            away_table = self.away_team.h2h_table
        else:
            home_table = self.home_team.table
            away_table = self.away_team.table

        if self.winner == self.home_team:
            home_table.wins += 1
            away_table.losses += 1
        elif self.winner == self.away_team:
            away_table.wins += 1
            home_table.losses += 1
        else:
            home_table.draws += 1
            away_table.draws += 1

        home_table.scored += self.home_score
        away_table.scored += self.away_score
        home_table.conceded += self.away_score
        away_table.conceded += self.home_score


@dataclass
class TournamentRules:
    h2h: bool = False
    round_robin: RoundRobin = RoundRobin.DOUBLE
    round_robin_final: RoundRobin = RoundRobin.SINGLE
    away_goal: bool = True

    def __post_init__(self):
        self.tiebreaker = (
            self.head_to_head_criterias if self.h2h else self.goal_diff_criterias
        )

    @staticmethod
    def head_to_head_criterias(team: Team) -> tuple:
        return (
            team.table.points,
            team.h2h_table.points,
            team.h2h_table.goal_diff,
            team.h2h_table.scored,
            team.table.goal_diff,
            team.table.scored,
        )

    @staticmethod
    def goal_diff_criterias(team: Team) -> tuple:
        return (team.table.points, team.table.goal_diff, team.table.scored)


@dataclass
class RoundRobinTournament:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    rule: TournamentRules
    completed: dict[
        tuple[str],
        tuple[int],
    ] | None = None

    def __post_init__(self):
        self._completed = self.completed.copy() if self.completed else {}
        self.scheduling = (
            combinations if self.rule.round_robin == RoundRobin.SINGLE else permutations
        )

    def simulate(self):
        for home_team, away_team in self.scheduling(self.teams, 2):
            game = Match(home_team, away_team)
            game.update_score(self._completed, self.rule.round_robin)
            if not game.completed:
                game.simulate(self.avg_goal, self.home_adv)
                self._completed[(home_team.name, away_team.name)] = (
                    game.home_score,
                    game.away_score,
                )
            game.update_teams()

    def rank_teams(self) -> list[Team]:
        points = defaultdict(list)
        for team in self.teams:
            points[team.table.points].append(team)

        for teams in points.values():
            for home_team, away_team in self.scheduling(teams, 2):
                game = Match(home_team, away_team)
                game.update_score(self._completed, self.rule.round_robin)
                game.update_teams(self.rule.h2h)

        return sorted(
            self.teams,
            key=self.rule.tiebreaker,
            reverse=True,
        )

    def reset(self):
        self._completed = self.completed.copy() if self.completed else {}
        for team in self.teams:
            team.reset()


@dataclass
class EliminationTournament:
    teams: list[Team]
    avg_goal: float
    home_adv: float
    rule: TournamentRules
    completed: dict[
        tuple[str],
        tuple[int],
    ] | None = None
    drawing_results: dict[int, list[tuple[str]]] | None = None

    def __post_init__(self):
        self.drawing_results = self.drawing_results or {}

        team_mapping = {team.name: team for team in self.teams}
        self._drawing_results = {
            _round: [
                (team_mapping[home_team], team_mapping[away_team])
                for (home_team, away_team) in matchups
            ]
            for _round, matchups in self.drawing_results.items()
        }

    def get_winner(self, home_team: Team, away_team: Team, round_robin: RoundRobin):
        return (
            self.get_single_legged_winner(home_team, away_team)
            if round_robin == RoundRobin.SINGLE
            else self.get_double_legged_winner(home_team, away_team)
        )

    def simulate(self):
        for team in self.teams:
            team.update_sim_rounds(len(self.teams))

        qualified = self.teams
        while len(qualified) > 1:
            if len(qualified) == 2:
                qualified = self.simulate_final(qualified)
            else:
                qualified = self.simulate_round(qualified)

            for team in qualified:
                team.update_sim_rounds(len(qualified))

    def simulate_round(self, teams: list[Team]):
        _round = len(teams)
        matchups = self._drawing_results.get(_round) or self.draw_matchup(teams)
        return [
            self.get_winner(home_team, away_team, self.rule.round_robin)
            for home_team, away_team in matchups
        ]

    def simulate_final(self, teams: list[Team]):
        if self.rule.round_robin_final == RoundRobin.SINGLE:
            self.home_adv = 0
        home_team, away_team = teams
        return [self.get_winner(home_team, away_team, self.rule.round_robin_final)]

    @staticmethod
    def draw_matchup(teams: list[Team]) -> list[tuple[Team]]:
        random.shuffle(teams)
        return list(zip(teams[::2], teams[1::2]))

    def get_single_legged_winner(self, home_team: Team, away_team: Team):
        game = Match(home_team, away_team)
        game.update_score(self.completed, self.rule.round_robin)
        if not game.completed:
            game.simulate(self.avg_goal, self.home_adv)

        return game.winner or self.get_extra_time_winner(home_team, away_team)

    def get_double_legged_winner(
        self,
        home_team: Team,
        away_team: Team,
    ):
        first_leg = Match(home_team, away_team)
        second_leg = Match(home_team=away_team, away_team=home_team)

        for game in [first_leg, second_leg]:
            game.update_score(self.completed, self.rule.round_robin)
            if not game.completed:
                game.simulate(self.avg_goal, self.home_adv)

        game = Match(
            home_team,
            away_team,
            home_score=first_leg.home_score + second_leg.away_score,
            away_score=first_leg.away_score + second_leg.home_score,
        )

        if game.winner:
            return game.winner

        if self.rule.away_goal:
            game = Match(
                home_team,
                away_team,
                home_score=second_leg.away_score,
                away_score=first_leg.away_score,
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
        game.simulate(self.avg_goal, self.home_adv, extra_time=True)
        return game.winner or random.choice([home_team, away_team])
