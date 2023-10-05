import random
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import combinations, permutations

import numpy as np

NO_OF_SIMULATIONS = 10000


class Round(Enum):
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

    def __truediv__(self, other):
        self.wins /= other
        self.draws /= other
        self.losses /= other
        self.scored /= other
        self.conceded /= other
        return self


class Occurance(defaultdict):
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
        self.sim_positions = Occurance()
        self.sim_rounds = Occurance()

    def __eq__(self, other) -> bool:
        return other and self.name == other.name

    def reset(self):
        self.table.reset()
        self.h2h_table.reset()


@dataclass
class Match:
    home_team: Team
    away_team: Team
    home_score: int = 0
    away_score: int = 0

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

    @property
    def winner(self):
        if self.home_score > self.away_score:
            return self.home_team
        if self.away_score > self.home_score:
            return self.away_team

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
class RoundRobinTournament:
    teams: list[Team]
    completed: dict[
        tuple[str],
        tuple[int],
    ] | None = None
    round: int = Round.DOUBLE

    def __post_init__(self):
        self._completed = self.completed.copy() if self.completed else {}

    @property
    def scheduling(self):
        return combinations if self.round == Round.SINGLE else permutations

    def simulate(self, avg_goal, home_adv):
        for home_team, away_team in self.scheduling(self.teams, 2):
            if _game := get_match_if_completed(
                home_team, away_team, self._completed, self.round
            ):
                game = _game
            else:
                game = Match(home_team, away_team)
                game.simulate(avg_goal, home_adv)
                self._completed[(home_team.name, away_team.name)] = (
                    game.home_score,
                    game.away_score,
                )
            game.update_teams()

    def rank_teams(self, h2h: bool) -> list[Team]:
        tiebreaker = self.head_to_head_criterias if h2h else self.goal_diff_criterias
        points = defaultdict(list)
        for team in self.teams:
            points[team.table.points].append(team)

        for teams in points.values():
            for home_team, away_team in self.scheduling(teams, 2):
                game = get_match_if_completed(home_team, away_team, self._completed)
                game.update_teams(h2h=True)

        return sorted(
            self.teams,
            key=tiebreaker,
            reverse=True,
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
        return (
            team.table.points,
            team.table.goal_diff,
            team.table.scored,
            team.h2h_table.points,
            team.h2h_table.goal_diff,
            team.h2h_table.scored,
        )

    def reset(self):
        for team in self.teams:
            team.reset()


@dataclass
class EliminationTournament:
    teams: list[Team]
    completed: dict[
        tuple[str],
        tuple[int],
    ] | None = None
    round: int = Round.DOUBLE

    @property
    def scheduling(self):
        return (
            self.get_single_legged_winner
            if self.round == Round.SINGLE
            else self.get_double_legged_winner
        )

    def simulate(self, avg_goal: float, home_adv: float):
        for team in self.teams:
            team.sim_rounds[len(self.teams)] += 1

        qualified = self.teams
        while len(qualified) > 1:
            matchups = self.draw_matchup(qualified)
            qualified = [
                self.scheduling(home_team, away_team, avg_goal, home_adv)
                for home_team, away_team in matchups
            ]

            for team in qualified:
                team.sim_rounds[len(qualified)] += 1

    @staticmethod
    def draw_matchup(teams: list[Team]) -> list[tuple[Team]]:
        random.shuffle(teams)
        return list(zip(teams[::2], teams[1::2]))

    def get_single_legged_winner(
        self,
        home_team: Team,
        away_team: Team,
        avg_goal: float,
        home_adv: float,
    ):
        if _game := get_match_if_completed(
            home_team, away_team, self.completed, round=Round.SINGLE
        ):
            game = _game
        else:
            game = Match(home_team, away_team)
            game.simulate(avg_goal, home_adv)

        return game.winner or self.get_extra_time_winner(
            home_team, away_team, avg_goal, home_adv
        )

    def get_double_legged_winner(
        self, home_team: Team, away_team: Team, avg_goal: float, home_adv: float
    ):
        if game := get_match_if_completed(home_team, away_team, self.completed):
            first_leg = game
        else:
            first_leg = Match(home_team, away_team)
            first_leg.simulate(avg_goal, home_adv)

        if game := get_match_if_completed(away_team, home_team, self.completed):
            second_leg = game
        else:
            second_leg = Match(home_team=away_team, away_team=home_team)
            second_leg.simulate(avg_goal, home_adv)

        game = Match(
            home_team=away_team,
            away_team=home_team,
            home_score=first_leg.home_score + second_leg.away_score,
            away_score=first_leg.away_score + second_leg.home_score,
        )

        return game.winner or self.get_extra_time_winner(
            home_team=away_team,
            away_team=home_team,
            avg_goal=avg_goal,
            home_adv=home_adv,
        )

    @staticmethod
    def get_extra_time_winner(
        home_team: Team,
        away_team: Team,
        avg_goal: float,
        home_adv: float,
    ):
        game = Match(home_team, away_team)
        game.simulate(avg_goal, home_adv, extra_time=True)
        return game.winner or random.choice([home_team, away_team])


def get_match_if_completed(
    home_team: Team,
    away_team: Team,
    completed: dict[
        tuple[str],
        tuple[int],
    ]
    | None = None,
    round: int = Round.DOUBLE,
) -> Match | None:
    if not completed:
        return
    key = (home_team.name, away_team.name)
    key_reversed = (away_team.name, home_team.name)
    if key in completed:
        home_score, away_score = completed[key]
        return Match(home_team, away_team, home_score, away_score)
    if round == Round.SINGLE and key_reversed in completed:
        away_score, home_score = completed[key_reversed]
        return Match(
            home_team=away_team,
            away_team=home_team,
            home_score=away_score,
            away_score=home_score,
        )


def update_sim_table(team: Team, position: int):
    team.sim_positions[position] += 1
    team.sim_table.wins += team.table.wins
    team.sim_table.draws += team.table.draws
    team.sim_table.losses += team.table.losses
    team.sim_table.scored += team.table.scored
    team.sim_table.conceded += team.table.conceded
