import os
import time

import functions_framework

from gcp import bigquery, pubsub


@functions_framework.cloud_event
def main(_):
    for season_id in get_latest_season_ids():
        pubsub.publish_json_message(
            topic=os.environ["TOPIC_NAME"],
            data={"endpoint": "matches", "season_id": season_id},
        )
        time.sleep(0.1)


def get_latest_season_ids() -> list[int]:
    query = """
    SELECT
      DISTINCT competition_id
    FROM `footystats.matches`
    WHERE status = 'incomplete'
      AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP())
    """
    return [row["competition_id"] for row in bigquery.query_dict(query)]
