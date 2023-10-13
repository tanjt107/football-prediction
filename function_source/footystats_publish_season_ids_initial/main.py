import os
import time

import functions_framework

from gcp import bigquery, pubsub


@functions_framework.cloud_event
def main(_):
    season_ids = bigquery.query_dict(
        query="SELECT * FROM footystats.get_season_id_initial();"
    )
    for season_id in season_ids:
        for endpoint in ["matches", "season", "teams"]:
            pubsub.publish_json_message(
                topic=os.environ["TOPIC_NAME"],
                data={"endpoint": endpoint, **season_id},
            )
            time.sleep(0.05)
