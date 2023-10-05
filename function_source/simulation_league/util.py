import base64
import json
import os

from cloudevents.http.event import CloudEvent
from google.cloud import bigquery, storage

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


class StorageClient(storage.Client):
    def upload(self, bucket_name: str, content: str, destination: str):
        self.bucket(bucket_name).blob(destination).upload_from_string(content)


def convert_to_newline_delimited_json(data: dict | list) -> str:
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def decode_message(cloud_event: CloudEvent) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
