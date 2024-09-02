import logging
import os

import functions_framework
import requests

from gcp import storage
from gcp.logging import setup_logging

setup_logging()


@functions_framework.cloud_event
def main(_):
    storage.upload_json_to_bucket(
        data=get_hkjc_team_list(),
        blob_name="teamList.json",
        bucket_name=os.environ["BUCKET_NAME"],
    )


def get_hkjc_team_list() -> dict:
    logging.info("Getting HKJC team list")
    body = """query teamList {
  teamList {
    id
    code
    name_ch
    name_en
  }
}"""
    response = requests.post(
        url="https://info.cld.hkjc.com/graphql/base/",
        headers={"content-type": "application/json"},
        json={
            "query": body,
            "operationName": "teamList",
        },
        timeout=5,
    )
    response.raise_for_status()
    team_list = response.json()["data"]["teamList"]
    logging.info("Got HKJC team list")
    return team_list
