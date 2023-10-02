import base64
import functions_framework
import json
import os
import numpy as np
from google.cloud import bigquery, storage
from collections import defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations, permutations

BUCKET_NAME = os.getenv("BUCKET_NAME")
NO_OF_SIMULATIONS = 10000
BQ_CLIENT = bigquery.Client()
GS_CLIENT = storage.Client()


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


@dataclass
class Team:
    name: str
    offence: float
    defence: float

    def __post_init__(self):
        self.table = Table()
        self.h2h_table = Table()
        self.sim_table = Table()
        self.sim_positions = defaultdict(int)
        self.sim_rounds = defaultdict(int)

    def reset(self):
        self.table.reset()
        self.h2h_table.reset()


@dataclass
class Match:
    home_team: Team
    away_team: Team
    home_score: int = 0
    away_score: int = 0

    def simulate(self, avg_goal: float, home_adv: float):
        home_exp = avg_goal + home_adv + self.home_team.offence + self.away_team.defence
        away_exp = avg_goal - home_adv + self.away_team.offence + self.home_team.defence
        home_exp = max(home_exp, 0.2)
        away_exp = max(away_exp, 0.2)
        self.home_score = np.random.poisson(home_exp)
        self.away_score = np.random.poisson(away_exp)

    def update_teams(self, h2h=False):
        table = "table" if h2h else "h2h_table"
        home_table: Table = getattr(self.home_team, table)
        away_table: Table = getattr(self.away_team, table)

        if self.home_score > self.away_score:
            home_table.wins += 1
            away_table.losses += 1
        elif self.home_score < self.away_score:
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
class Season:
    teams: list[Team]
    completed: dict[
        tuple[str],
        tuple[int],
    ] | None = None
    round: int = 2

    def __post_init__(self):
        self._completed = self.completed.copy() if self.completed else {}

    @property
    def scheduling(self):
        return combinations if self.round == 1 else permutations

    def simulate(self, avg_goal, home_adv):
        for home_team, away_team in self.scheduling(self.teams, 2):
            key = (home_team.name, away_team.name)
            if key in self._completed:
                home_score, away_score = self._completed[key]
                game = Match(home_team, away_team, home_score, away_score)
            elif self.round == 1 and key[::-1] in self._completed:
                away_score, home_score = self._completed[key[::-1]]
                game = Match(away_team, home_team, away_score, home_score)
            else:
                game = Match(home_team, away_team)
                game.simulate(avg_goal, home_adv)
                self._completed[key] = (
                    game.home_score,
                    game.away_score,
                )
            game.update_teams()

    def rank_teams(self, h2h: bool) -> list[Team]:
        tiebreaker = head_to_head_criterias if h2h else goal_diff_criterias
        points: dict[int, list[Team]] = defaultdict(list)
        for team in self.teams:
            points[team.table.points].append(team)

        for _teams in points.values():
            for home_team, away_team in self.scheduling(_teams, 2):
                key = (home_team.name, away_team.name)
                if key in self._completed:
                    home_score, away_score = self._completed[key]
                    game = Match(home_team, away_team, home_score, away_score)
                else:
                    away_score, home_score = self._completed[key[::-1]]
                    game = Match(away_team, home_team, away_score, home_score)
                game.update_teams(h2h=True)

        return sorted(
            self.teams,
            key=tiebreaker,
            reverse=True,
        )

    def reset(self):
        for team in self.teams:
            team.reset()


def head_to_head_criterias(team: Team) -> tuple:
    return (
        team.table.points,
        team.h2h_table.points,
        team.h2h_table.goal_diff,
        team.h2h_table.scored,
        team.table.goal_diff,
        team.table.scored,
    )


def goal_diff_criterias(team: Team) -> tuple:
    return (
        team.table.points,
        team.table.goal_diff,
        team.table.scored,
        team.h2h_table.points,
        team.h2h_table.goal_diff,
        team.h2h_table.scored,
    )


@functions_framework.cloud_event
def main(cloud_event):
    data = get_message(cloud_event)
    message = json.loads(data)
    league, country, h2h = message["league"], message["country"], message["h2h"]
    last_run = get_last_run(league, country) or -1
    latest_match_date = get_latest_match_date(league, country)
    if last_run >= latest_match_date:
        return
    avg_goal, home_adv = get_avg_goal_home_adv(league, country)
    teams = get_teams(league, country)
    completed = get_completed_matches(league, country)

    results = simulate_season(
        teams, avg_goal, home_adv, completed, h2h, NO_OF_SIMULATIONS
    )
    results = [
        {
            "team": team.name,
            "positions": dict(team.sim_positions),
            "table": asdict(team.sim_table),
        }
        for team in results
    ]
    formatted_data = format_data(results)
    destination = f"{league}.json"
    upload_to_gcs(BUCKET_NAME, formatted_data, destination)

    insert_run_log(league, country, latest_match_date)


def get_message(cloud_event) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")


def fetch_bq(query: str, job_config: bigquery.QueryJobConfig = None):
    query_job = BQ_CLIENT.query(query, job_config)
    return list(query_job.result())


def get_last_run(league: str, country: str):
    sql = f"SELECT MAX(date_unix) AS last_run FROM `simulation.run_log` WHERE league = @league AND country = @country"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league", "STRING", league),
            bigquery.ScalarQueryParameter("country", "STRING", country),
        ]
    )
    if result := fetch_bq(sql, job_config):
        return result[0][0]


def get_latest_match_date(league: str, country: str):
    sql = f"""
    SELECT
        MAX(date_unix)
    FROM `footystats.matches` matches
    JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
    WHERE matches.status = 'complete'
        AND seasons.name = @league
        AND seasons.country = @country
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league", "STRING", league),
            bigquery.ScalarQueryParameter("country", "STRING", country),
        ]
    )
    return fetch_bq(sql, job_config)[0][0]


def get_avg_goal_home_adv(league: str, country: str) -> tuple[float]:
    query = """
    SELECT
        avg_goal,
        home_adv
    FROM solver.leagues solver
    JOIN master.leagues master ON solver.division = master.division
    WHERE footystats_name = @league
        AND country = @country
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league", "STRING", league),
            bigquery.ScalarQueryParameter("country", "STRING", country),
        ]
    )
    return fetch_bq(query, job_config)[0]


def get_teams(league: str, country: str) -> list[Team]:
    query = """
    SELECT
        CAST(solver.id AS INT64),
        offence,
        defence
    FROM solver.teams solver
    JOIN master.teams master_teams ON solver.id = master_teams.solver_id
    JOIN master.leagues master_leagues ON master_teams.league_id = master_leagues.id
    WHERE master_leagues.footystats_name = @league
        AND master_leagues.country = @country
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league", "STRING", league),
            bigquery.ScalarQueryParameter("country", "STRING", country),
        ]
    )
    return [Team(*team) for team in fetch_bq(query, job_config)]


def simulate_season(
    teams: list[Team],
    avg_goal: float,
    home_adv: float,
    completed: dict[
        tuple[str],
        tuple[int],
    ]
    | None = None,
    h2h: bool = False,
    no_of_simulations: int = 10000,
    round_robin: int = 2,
) -> list[Team]:
    def update_team(team: Team, position: int):
        team.sim_positions[position] += 1
        team.sim_table.wins += team.table.wins
        team.sim_table.draws += team.table.draws
        team.sim_table.losses += team.table.losses
        team.sim_table.scored += team.table.scored
        team.sim_table.conceded += team.table.conceded

    for _ in range(no_of_simulations):
        season = Season(teams, completed, round_robin)
        season.simulate(avg_goal, home_adv)
        result = season.rank_teams(h2h)
        for position, team in enumerate(result, 1):
            update_team(team, position)

        season.reset()

    for team in teams:
        team.sim_table /= no_of_simulations
        for position in team.sim_positions:
            team.sim_positions[position] /= no_of_simulations

    return teams


def get_completed_matches(league: str, country: str) -> dict[tuple[int], tuple[int]]:
    query = """
    SELECT
        homeId,
        awayId,
        homeGoalCount,
        awayGoalCount
    FROM footystats.matches
    JOIN master.leagues ON matches.competition_id = leagues.latest_season_id
    WHERE status = 'complete'
        AND footystats_name = @league
        AND country = @country
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league", "STRING", league),
            bigquery.ScalarQueryParameter("country", "STRING", country),
        ]
    )
    return {
        (home_team, away_team): (home_score, away_score)
        for home_team, away_team, home_score, away_score in fetch_bq(query, job_config)
    }


def format_data(data):
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    GS_CLIENT.bucket(bucket_name).blob(destination).upload_from_string(content)


def insert_run_log(league: str, country: str, date_unix: int):
    sql = (
        f"INSERT INTO simulation.run_log VALUES ('{league}', '{country}', {date_unix})"
    )
    query_job = BQ_CLIENT.query(sql)
    query_job.result()
