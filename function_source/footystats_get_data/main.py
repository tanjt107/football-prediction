import os

import functions_framework
import requests
from cloudevents.http.event import CloudEvent

from gcp import storage
from gcp.util import decode_message


BUCKET_NAMES = {
    "matches": os.environ["MATCHES_BUCKET_NAME"],
    "season": os.environ["SEASONS_BUCKET_NAME"],
    "teams": os.environ["TEAMS_BUCKET_NAME"],
}


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = decode_message(cloud_event)
    endpoint, season_id = message["endpoint"], message["season_id"]
    data = get_footystats(
        endpoint, key=os.environ["FOOTYSTATS_API_KEY"], season_id=season_id
    )
    storage.upload_json_to_bucket(
        data,
        blob_name=f"{endpoint}.json",
        bucket_name=BUCKET_NAMES[endpoint],
        hive_partitioning={
            "_COUNTRY": message["country"],
            "_NAME": message["name"],
            "_YEAR": message["year"],
            "_SEASON_ID": season_id,
        },
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
