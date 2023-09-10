import os
import functions_framework
from google.cloud import bigquery, pubsub_v1

TOPIC_NAME = os.getenv("TOPIC_NAME")
BQ_CLIENT = bigquery.Client()


@functions_framework.cloud_event
def main(cloud_event):
    season_ids = get_latest_season_ids()

    publisher = pubsub_v1.PublisherClient()

    for season_id in season_ids:
        for endpoint in ["matches", "season", "teams"]:
            future = publish_message(publisher, TOPIC_NAME, season_id, endpoint)

    future.result()


def get_latest_season_ids() -> list[int]:
    query = """
    SELECT
      season.id
    FROM
      `footystats.league_list`,
      UNNEST(season) AS season
    """
    query_job = BQ_CLIENT.query(query)
    return [row[0] for row in query_job]


def publish_message(
    publisher: pubsub_v1.PublisherClient,
    topic_path: str,
    season_id: int,
    endpoint: str,
):
    return publisher.publish(
        topic_path, f'{{"endpoint": "{endpoint}", "season_id": {season_id}}}'.encode()
    )
