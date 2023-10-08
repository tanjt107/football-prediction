import os
import time

import functions_framework

from gcp import bigquery, pubsub


@functions_framework.cloud_event
def main(_):
    for season_id in get_latest_season_ids():
        for endpoint in ["matches", "season", "teams"]:
            pubsub.publish_json_message(
                topic=os.environ["TOPIC_NAME"],
                data={"endpoint": endpoint, "season_id": season_id},
            )
            time.sleep(0.1)


def get_latest_season_ids() -> list[int]:
    query = """
    SELECT
      season.id
    FROM
      `footystats.league_list`,
      UNNEST(season) AS season
    """
    return [row["id"] for row in bigquery.query_dict(query)]
