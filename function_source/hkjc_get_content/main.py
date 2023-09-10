import base64
import functions_framework
import json
import os
import requests
from google.cloud import storage

BUCKET_NAME = os.getenv("BUCKET_NAME")
CONTENTS = ["leaguelist.json", "teamlist.json"]
GS_CLIENT = storage.Client()


@functions_framework.cloud_event
def main(cloud_event):
    for content in CONTENTS:
        fetched_data = fetch_hkjc(content)
        formatted_data = format_data(fetched_data)
        upload_to_gcs(BUCKET_NAME, formatted_data, content)


def fetch_hkjc(content: str) -> dict:
    response = requests.get(
        f"https://bet.hkjc.com/contentserver/jcbw/cmc/fb/{content}",
    )
    response.raise_for_status()
    data = response.content.decode("utf-8-sig")
    return json.loads(data)


def format_data(data):
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    GS_CLIENT.bucket(bucket_name).blob(destination).upload_from_string(content)
