import json
import logging
import os

import functions_framework
import requests

from gcp import storage
from gcp.logging import setup_logging

setup_logging()


@functions_framework.cloud_event
def main(_):
    for content in ["leaguelist.json", "teamlist.json"]:
        storage.upload_json_to_bucket(
            data=get_hkjc_content(content),
            blob_name=content,
            bucket_name=os.environ["BUCKET_NAME"],
        )


def get_hkjc_content(content: str) -> dict:
    logging.info(f"Getting HKJC data: {content=}")
    response = requests.get(
        f"https://bet.hkjc.com/contentserver/jcbw/cmc/fb/{content}", timeout=5
    )
    response.raise_for_status()
    data = response.content.decode("utf-8-sig")
    data = json.loads(data)
    logging.info(f"Got HKJC data: {content=}")
    return data
