import json
import os
from dataclasses import asdict

import functions_framework
from cloudevents.http.event import CloudEvent

import simulation
import util
from simulation import Team, TournamentRules

BUCKET_NAME = os.getenv("BUCKET_NAME")


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    data = util.decode_message(cloud_event)
    message = json.loads(data)
    league, country = message["league"], message["country"]

    bq_client = util.BigQueryClient()
    last_run = get_last_run(league, country, bq_client) or -1
    latest_match_date = get_latest_match_date(league, country, bq_client)
    if last_run >= latest_match_date:
        return

    avg_goal, home_adv = get_avg_goal_home_adv(league, country, bq_client)
    teams = get_teams(league, country, bq_client)
    completed = get_completed_matches(league, country, bq_client)
    rule = TournamentRules(message["h2h"])

    result = simulate_season(teams, avg_goal, home_adv, rule, completed)
    formatted_data = util.convert_to_newline_delimited_json(result)
    destination = f"{league}.json"
    gs_client = util.StorageClient()
    gs_client.upload(BUCKET_NAME, formatted_data, destination)

    insert_run_log(league, country, latest_match_date, bq_client)


def simulate_season(
    teams: list[Team],
    avg_goal: float,
    home_adv: float,
    rule: TournamentRules,
    completed: dict[
        tuple[str],
        tuple[int],
    ]
    | None = None,
    no_of_simulations: int = 10000,
) -> list[Team]:
    season = simulation.RoundRobinTournament(teams, avg_goal, home_adv, rule, completed)
    for _ in range(no_of_simulations):
        season.simulate()
        result = season.rank_teams()
        for position, team in enumerate(result, 1):
            team.update_sim_table()
            team.update_sim_positions(position)

        season.reset()

    for team in teams:
        team.sim_table /= no_of_simulations
        team.sim_positions /= no_of_simulations

    return [
        {
            "team": team.name,
            "positions": dict(team.sim_positions),
            "table": asdict(team.sim_table),
        }
        for team in teams
    ]


def get_last_run(league: str, country: str, client: util.BigQueryClient) -> int:
    query = """
    SELECT MAX(date_unix) AS last_run
    FROM `simulation.run_log`
    WHERE league = @league
        AND country = @country"""
    params = {"league": league, "country": country}
    client.query_dict(query, params)[0]["last_run"]


def get_latest_match_date(
    league: str, country: str, client: util.BigQueryClient
) -> int:
    sql = """
    SELECT
        MAX(date_unix) AS max_date_unix
    FROM `footystats.matches` matches
    JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
    WHERE matches.status = 'complete'
        AND seasons.name = @league
        AND seasons.country = @country
    """
    params = {"league": league, "country": country}
    return client.query_dict(sql, params)[0]["max_date_unix"]


def get_avg_goal_home_adv(
    league: str, country: str, client: util.BigQueryClient
) -> tuple[float]:
    query = """
    SELECT
        avg_goal,
        home_adv
    FROM solver.leagues solver
    JOIN master.leagues master ON solver.division = master.division
    WHERE footystats_name = @league
        AND country = @country
    """
    params = {"league": league, "country": country}
    factors = client.query_dict(query, params)[0]
    return factors["avg_goal"], factors["home_adv"]


def get_teams(league: str, country: str, client: util.BigQueryClient) -> list[Team]:
    query = """
    SELECT
        CAST(solver.id AS INT64) AS name,
        offence,
        defence
    FROM solver.teams solver
    JOIN master.teams master_teams ON solver.id = master_teams.solver_id
    JOIN master.leagues master_leagues ON master_teams.league_id = master_leagues.id
    WHERE master_leagues.footystats_name = @league
        AND master_leagues.country = @country
    """
    params = {"league": league, "country": country}
    return [Team(**team) for team in client.query_dict(query, params)]


def get_completed_matches(
    league: str, country: str, client: util.BigQueryClient
) -> dict[tuple[int], tuple[int]]:
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
    params = {"league": league, "country": country}
    return {
        (row["homeId"], row["awayId"]): (row["homeGoalCount"], row["awayGoalCount"])
        for row in client.query_dict(query, params)
    }


def insert_run_log(
    league: str, country: str, date_unix: int, client: util.BigQueryClient
):
    query = "INSERT INTO simulation.run_log VALUES (@league, @country, @date_unix)"
    params = {"league": league, "country": country, "date_unix": date_unix}
    client.query_dict(query, params)
