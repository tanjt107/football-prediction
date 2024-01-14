import re

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import bigquery, pubsub
from gcp.util import safe_load_json


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    _type, table = re.match(
        r"_TYPE=(\w+)\/_DATE_UNIX=\d+\/(\w+)\.json", cloud_event.data["name"]
    ).groups()

    if table != "teams":
        return

    params = bigquery.query_dict(
        query="SELECT * FROM `simulation.get_params`(@type);", params={"type": _type}
    )
    for param in params:
        pubsub.publish_json_message(
            topic=pubsub.get_topic_path(param["topic"]),
            data={k: safe_load_json(v) for k, v in param.items() if k != "topic" and v},
        )
