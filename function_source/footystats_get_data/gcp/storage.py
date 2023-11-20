import json

from google.cloud import storage

CLIENT = storage.Client()


def convert_to_newline_delimited_json(data: dict | list) -> str:
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def download_blob(blob_name: str, bucket_name: str) -> str:
    return CLIENT.bucket(bucket_name).blob(blob_name).download_as_text()


def upload_json_to_bucket(
    data: list[dict],
    blob_name: str,
    bucket_name: str,
    hive_partitioning: dict | None = None,
):
    CLIENT.bucket(bucket_name).blob(
        blob_name=get_directory(blob_name, hive_partitioning)
    ).upload_from_string(data=convert_to_newline_delimited_json(data))


def get_directory(blob_name: str, hive_partitioning: dict | None = None):
    if hive_partitioning:
        hive_dir = "/".join(
            f"{k}={str(v).replace('/', ' ')}" for k, v in hive_partitioning.items()
        )
        return "/".join([hive_dir, blob_name])
    return blob_name
