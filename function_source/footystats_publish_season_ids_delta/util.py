import base64
import json
import os

from cloudevents.http.event import CloudEvent
from google.cloud import bigquery, pubsub_v1

GCP_PROJECT = os.getenv("GCP_PROJECT")


class BigQueryClient(bigquery.Client):
    def query_dict(self, query: str, query_params: dict | None = None) -> list[dict]:
        _query_params = []
        for key, value in query_params.items():
            if isinstance(value, str):
                _type = "STRING"
            if isinstance(value, int):
                _type = "INT64"
            _query_params.append(bigquery.ScalarQueryParameter(key, _type, value))

        job_config = bigquery.QueryJobConfig(query_parameters=_query_params)
        query_job = self.query(query, job_config)
        return [dict(row) for row in query_job.result()]


class PublisherClient(pubsub_v1.PublisherClient):
    def get_topic_path(self, topic_id: str) -> str:
        return self.topic_path(GCP_PROJECT, topic_id)

    def publish_json_message(self, topic_path: str, message: dict):
        return self.publish(topic_path, json.dumps(message).encode())


def convert_to_newline_delimited_json(data: dict | list) -> str:
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def decode_message(cloud_event: CloudEvent) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
