import os

import functions_framework

import util

TOPIC_NAME = os.getenv("TOPIC_NAME")


@functions_framework.cloud_event
def main(_):
    bq_client = util.BigQueryClient()
    season_ids = get_latest_season_ids(bq_client)

    publisher = util.PublisherClient()
    for season_id in season_ids:
        publisher.publish_json_message(
            TOPIC_NAME,
            {"endpoint": "matches", "season_id": season_id},
        )


def get_latest_season_ids(client: util.BigQueryClient) -> list[int]:
    query = """
    SELECT
      DISTINCT competition_id
    FROM `footystats.matches`
    WHERE status = 'incomplete'
      AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP())
    """
    return [row["competition_id"] for row in client.query_dict(query)]
