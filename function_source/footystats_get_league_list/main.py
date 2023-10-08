import os

import functions_framework
import requests

from gcp import storage


@functions_framework.cloud_event
def main(_):
    data = get_footystats(
        endpoint="list",
        key=os.environ["FOOTYSTATS_API_KEY"],
        chosen_leagues_only="true",
    )
    storage.upload_json_to_bucket(
        data,
        blob_name="league_list.json",
        bucket_name=os.environ["BUCKET_NAME"],
    )


def get_footystats(endpoint: str, key: str, **kwargs) -> dict:
    print(f"Getting footystats data: {endpoint=}, {kwargs=}")
    response = requests.get(
        f"https://api.football-data-api.com/league-{endpoint}",
        params={"key": key, **kwargs},
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()["data"]
    print(f"Got footystats data: {endpoint=}, {kwargs=}")
    return data
