import json
import os
import functions_framework
from google.cloud import bigquery, pubsub_v1

TOPIC_NAME = os.getenv("TOPIC_NAME")
BQ_CLIENT = bigquery.Client()
PUBLISHER = pubsub_v1.PublisherClient()


@functions_framework.cloud_event
def main(cloud_event):
    season_ids = get_latest_season_ids()

    for season_id in season_ids:
        for endpoint in ["matches", "season", "teams"]:
            future = publish_json(
                TOPIC_NAME,
                {"endpoint": endpoint, "season_id": season_id},
            )

    future.result()


def get_latest_season_ids() -> list[int]:
    query = """
    SELECT
      season.id
    FROM
      `footystats.league_list`,
      UNNEST(season) AS season
    WHERE
      MOD(season.year, 10000) >= EXTRACT(YEAR FROM CURRENT_DATE())
    """
    query_job = BQ_CLIENT.query(query)
    return [row[0] for row in query_job]


def publish_json(topic_path: str, message: str):
    return PUBLISHER.publish(topic_path, json.dumps(message).encode())
