import json
import logging
import os

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import storage

from gcp.logging import setup_logging

from gcp.util import decode_message
from simulation import queries
from simulation.tournaments import Tournament


setup_logging()


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = decode_message(cloud_event)
    league = message["footystats_name"]
    blob = storage.download_blob(
        blob_name=f"{league}.json", bucket_name="manual-340977255134-asia-east2"
    )
    rounds = json.loads(blob)

    factors = queries.get_avg_goal_home_adv(league)
    avg_goal, home_adv = factors["avg_goal"], factors["home_adv"]
    teams = queries.get_teams(league)
    matches = queries.get_matches(league, teams)
    groups = queries.get_groups(league, teams)

    logging.info("Simulating: %s", league)
    tournament = Tournament(
        avg_goal,
        home_adv,
        teams,
        matches,
        groups,
    )
    tournament.set_rounds(rounds)
    tournament.simulate()
    logging.info("Simulated: %s", league)

    storage.upload_json_to_bucket(
        tournament.result,
        blob_name="league.json",
        bucket_name=os.environ["RESULT_BUCKET_NAME"],
        hive_partitioning={
            "_LEAGUE": league,
            "_DATE_UNIX": message["latest_match_date"],
        },
    )
