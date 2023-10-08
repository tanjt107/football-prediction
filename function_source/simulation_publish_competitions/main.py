import re

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import bigquery, pubsub
from gcp.util import safe_load_json


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    _type, table = re.match(
        r"type=(\w+)/(\w+)\.json", cloud_event.data["name"]
    ).groups()

    if table != "teams":
        return

    for param in get_params(_type):
        pubsub.publish_json_message(
            topic=pubsub.get_topic_path(param["topic"]),
            data={k: safe_load_json(v) for k, v in param.items() if k != "topic" and v},
        )


def get_params(_type: str) -> list[dict]:
    query = """
    SELECT
        topic,
        league,
        country,
        rule,
        team_no_ko,
        params.groups,
        ko_matchups
    FROM `simulation.params` params
    WHERE type = @type
    """
    return bigquery.query_dict(query, params={"type": _type})
