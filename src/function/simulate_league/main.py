import logging
import os
from dataclasses import asdict

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import storage
from gcp.logging import setup_logging
from gcp.util import decode_message
from simulation import queries
from simulation.league import Season
from simulation.models import Team, Rules

setup_logging()

BUCKET_NAME = os.getenv("BUCKET_NAME")


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = decode_message(cloud_event)
    league = message["league"]

    last_run = queries.get_last_run(league)
    latest_match_date = queries.get_latest_match_date(league)
    if last_run >= latest_match_date:
        logging.info(f"Already updated. Simulation aborted: {league=}")
        return

    factors = queries.get_avg_goal_home_adv(league)
    teams = queries.get_teams(league)
    rule = Rules(**message["rule"]) if message.get("rule") else Rules()

    if corrections := message.get("corrections"):
        for team, correction in corrections.items():
            teams[int(team)].set_correction(correction)

    season = Season(
        teams=teams.values(),
        avg_goal=factors["avg_goal"],
        home_adv=factors["home_adv"],
        rule=rule,
        completed=queries.get_completed_matches(league),
    )

    logging.info(f"Simulating: {league=}")
    data = simulate_season(season)
    logging.info(f"Simulated: {league=}")

    storage.upload_json_to_bucket(
        data,
        blob_name="league.json",
        bucket_name=BUCKET_NAME,
        hive_partitioning={"_LEAGUE": league, "_DATE_UNIX": latest_match_date},
    )


def simulate_season(
    season: Season,
    no_of_simulations: int = 10000,
) -> list[Team]:
    for _ in range(no_of_simulations):
        season.simulate()
        for position, team in enumerate(season.positions, 1):
            team.update_sim_table()
            team.update_sim_positions(position)

    for team in season.teams:
        team.sim_table /= no_of_simulations
        team.sim_positions /= no_of_simulations

    return [
        {
            "team": team.name,
            "positions": dict(team.sim_positions),
            "table": asdict(team.sim_table),
        }
        for team in season.teams
    ]
