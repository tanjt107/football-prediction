import base64
import json

from cloudevents.http.event import CloudEvent
from google.cloud import bigquery, storage


class BigQueryClient(bigquery.Client):
    def query_dict(
        self, query: str, job_config: bigquery.QueryJobConfig | None = None
    ) -> list[dict]:
        query_job = self.query(query, job_config)
        return [dict(row) for row in query_job.result()]


class StorageClient(storage.Client):
    def upload(self, bucket_name: str, data: str, blob_name: str):
        self.bucket(bucket_name).blob(blob_name).upload_from_string(data)


def convert_to_newline_delimited_json(obj: dict | list) -> str:
    if isinstance(obj, list):
        return "\n".join([json.dumps(o) for o in obj])
    return json.dumps(obj)


def decode_message(cloud_event: CloudEvent) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
