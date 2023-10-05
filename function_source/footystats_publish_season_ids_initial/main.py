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
        for endpoint in ["matches", "season", "teams"]:
            publisher.publish_json_message(
                TOPIC_NAME,
                {"endpoint": endpoint, "season_id": season_id},
            )


def get_latest_season_ids(client: util.BigQueryClient) -> list[int]:
    query = """
    SELECT
      season.id
    FROM
      `footystats.league_list`,
      UNNEST(season) AS season
    """
    return [row["id"] for row in client.query_dict(query)]
