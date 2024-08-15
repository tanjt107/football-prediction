import os

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import bigquery, pubsub
from gcp.util import decode_message


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    endpoint = decode_message(cloud_event)

    seasons = bigquery.query_dict(
        query="SELECT * FROM footystats.get_season_id_initial();"
    )
    for season in seasons:
        pubsub.publish_json_message(
            topic=os.environ["TOPIC_NAME"],
            data={"endpoint": endpoint, **season},
        )
