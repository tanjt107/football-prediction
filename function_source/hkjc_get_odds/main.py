import json
import os

import functions_framework
import requests

import util

BUCKET_NAME = os.getenv("BUCKET_NAME")
POOLS = os.getenv("POOLS")


@functions_framework.cloud_event
def main(_):
    gs_client = util.StorageClient()
    pools = json.loads(POOLS)
    for pool in pools:
        pool = pool.lower()
        fetched_data = fetch_hkjc(pool)
        formatted_data = util.convert_to_newline_delimited_json(fetched_data)
        destination = f"odds_{pool}.json"
        gs_client.upload(BUCKET_NAME, formatted_data, destination)


def fetch_hkjc(pool: str) -> dict:
    response = requests.get(
        f"https://bet.hkjc.com/football/getJSON.aspx?jsontype=odds_{pool}.aspx",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["matches"]
