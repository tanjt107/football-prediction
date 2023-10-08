import json
import os

import functions_framework
import requests

from gcp import storage


@functions_framework.cloud_event
def main(_):
    for pool in json.loads(os.environ["POOLS"]):
        pool = pool.lower()
        data = get_hkjc_odds(pool)
        storage.upload_json_to_bucket(
            data, blob_name=f"odds_{pool}.json", bucket_name=os.environ["BUCKET_NAME"]
        )


def get_hkjc_odds(pool: str) -> dict:
    print(f"Getting HKJC data: {pool=}")
    response = requests.get(
        f"https://bet.hkjc.com/football/getJSON.aspx?jsontype=odds_{pool}.aspx",
        timeout=5,
    )
    response.raise_for_status()
    matches = response.json()["matches"]
    print(f"Got HKJC data: {pool=}")
    return matches
