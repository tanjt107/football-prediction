import json
import logging
import os
from datetime import datetime

import functions_framework
import requests

from gcp import storage
from gcp.logging import setup_logging

setup_logging()


@functions_framework.cloud_event
def main(_):
    timestamp = get_current_timestamp()
    for pool in json.loads(os.environ["POOLS"]):
        pool = pool.lower()
        storage.upload_json_to_bucket(
            data=get_hkjc_odds(pool),
            blob_name=f"odds_{pool}.json",
            bucket_name=os.environ["BUCKET_NAME"],
            hive_partitioning={"_TIMESTAMP": timestamp},
        )


def get_hkjc_odds(pool: str) -> dict:
    logging.info(f"Getting HKJC data: {pool=}")
    response = requests.get(
        f"https://bet.hkjc.com/football/getJSON.aspx?jsontype=odds_{pool}.aspx",
        timeout=5,
    )
    response.raise_for_status()
    matches = response.json()["matches"]
    logging.info(f"Got HKJC data: {pool=}")
    return matches


def get_current_timestamp():
    return datetime.now().isoformat()
