import json
import os

import functions_framework
import requests

import util

BUCKET_NAME = os.getenv("BUCKET_NAME")
CONTENTS = ["leaguelist.json", "teamlist.json"]


@functions_framework.cloud_event
def main(_):
    gs_client = util.StorageClient()
    for content in CONTENTS:
        fetched_data = fetch_hkjc(content)
        formatted_data = util.convert_to_newline_delimited_json(fetched_data)
        gs_client.upload(BUCKET_NAME, formatted_data, content)


def fetch_hkjc(content: str) -> dict:
    response = requests.get(
        f"https://bet.hkjc.com/contentserver/jcbw/cmc/fb/{content}", timeout=5
    )
    response.raise_for_status()
    data = response.content.decode("utf-8-sig")
    return json.loads(data)
