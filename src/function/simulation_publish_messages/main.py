import os
import re

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import bigquery, pubsub


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    _type, table = re.match(
        r"_TYPE=(\w+)\/_DATE_UNIX=\d+\/(\w+)\.json", cloud_event.data["name"]
    ).groups()

    if table != "teams":
        return

    leagues = bigquery.query_dict(
        query="SELECT * FROM `simulation.get_messages`(@type);", params={"type": _type}
    )
    for league in leagues:
        pubsub.publish_json_message(
            topic=os.environ["TOPIC_NAME"],
            data=league,
        )
