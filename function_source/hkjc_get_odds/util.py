import base64
import json
import os

from cloudevents.http.event import CloudEvent
from google.cloud import storage

GCP_PROJECT = os.getenv("GCP_PROJECT")


class StorageClient(storage.Client):
    def upload(self, bucket_name: str, content: str, destination: str):
        self.bucket(bucket_name).blob(destination).upload_from_string(content)


def convert_to_newline_delimited_json(data: dict | list) -> str:
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def decode_message(cloud_event: CloudEvent) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
