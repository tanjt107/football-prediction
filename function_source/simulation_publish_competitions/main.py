import json
import os
import re

import functions_framework
from google.cloud import bigquery, pubsub_v1, storage

GCP_PROJECT = os.getenv("GCP_PROJECT")
BQ_CLIENT = bigquery.Client()
GS_CLIENT = storage.Client()
PUBLISHER = pubsub_v1.PublisherClient()


@functions_framework.cloud_event
def main(cloud_event):
    data = cloud_event.data
    blob_name = data["name"]
    _type, table = re.match(r"type=(\w+)/(\w+)\.json", blob_name).groups()
    if table != "teams":
        return
    params = get_params(_type)
    for param in params:
        topic, league, country, h2h = param
        message = {"league": league, "country": country, "h2h": h2h}
        publish_json(get_topic_path(topic), message)


def fetch_bq(query: str, job_config: bigquery.QueryJobConfig = None):
    query_job = BQ_CLIENT.query(query, job_config)
    return list(query_job.result())


def get_params(_type: str):
    query = """
    SELECT
        topic,
        league,
        country,
        h2h
    FROM `simulation.params`
    WHERE type = @type
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("type", "STRING", _type)]
    )
    if result := fetch_bq(query, job_config):
        return result
    return []


def get_topic_path(topic_id):
    return PUBLISHER.topic_path(GCP_PROJECT, topic_id)


def publish_json(topic_path: str, message: str):
    return PUBLISHER.publish(topic_path, json.dumps(message).encode())
