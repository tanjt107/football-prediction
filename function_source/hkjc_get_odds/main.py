import base64
import functions_framework
import json
import os
import requests
from google.cloud import storage

BUCKET_NAME = os.getenv("BUCKET_NAME")
POOLS = os.getenv("POOLS")


@functions_framework.cloud_event
def main(cloud_event):
    pools = json.loads(POOLS)
    for pool in pools:
        pool = pool.lower()
        fetched_data = fetch_hkjc(pool)
        formatted_data = format_data(fetched_data)
        destination = f"odds_{pool}.json"
        upload_to_gcs(BUCKET_NAME, formatted_data, destination)


def get_message(cloud_event) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")


def fetch_hkjc(pool: str) -> dict:
    response = requests.get(
        f"https://bet.hkjc.com/football/getJSON.aspx?jsontype=odds_{pool}.aspx",
    )
    response.raise_for_status()
    return response.json()["matches"]


def format_data(data):
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    storage.Client().bucket(bucket_name).blob(destination).upload_from_string(content)
