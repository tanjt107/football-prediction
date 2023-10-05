import re

import functions_framework
from cloudevents.http.event import CloudEvent

import util


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    data = cloud_event.data
    blob_name = data["name"]
    _type, table = re.match(r"type=(\w+)/(\w+)\.json", blob_name).groups()
    if table != "teams":
        return
    bq_client = util.BigQueryClient()
    params = get_params(_type, bq_client)

    publisher = util.PublisherClient()
    for param in params:
        topic = publisher.get_topic_path(param["topic"])
        message = {
            "league": param["league"],
            "country": param["country"],
            "h2h": param["h2h"],
        }
        publisher.publish_json_message(topic, message)


def get_params(_type: str, client: util.BigQueryClient):
    query = """
    SELECT
        topic,
        league,
        country,
        h2h
    FROM `simulation.params`
    WHERE type = @type
    """
    params = {"type": _type}
    return client.query_dict(query, params)
