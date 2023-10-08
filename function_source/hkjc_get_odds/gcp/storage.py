import json

from google.cloud import storage

CLIENT = storage.Client()


def convert_to_newline_delimited_json(data: dict | list) -> str:
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def download_bolb(blob_name: str, bucket_name: str) -> str:
    return CLIENT.bucket(bucket_name).blob(blob_name).download_as_text()


def upload_json_to_bucket(data: list[dict], blob_name: str, bucket_name: str):
    CLIENT.bucket(bucket_name).blob(blob_name).upload_from_string(
        data=convert_to_newline_delimited_json(data)
    )
