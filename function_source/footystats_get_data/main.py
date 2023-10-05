import json
import os

import functions_framework
import requests
from cloudevents.http.event import CloudEvent

import util

BUCKET_NAMES = {
    "matches": os.getenv("MATCHES_BUCKET_NAME"),
    "season": os.getenv("SEASONS_BUCKET_NAME"),
    "teams": os.getenv("TEAMS_BUCKET_NAME"),
}
API_KEY = os.getenv("FOOTYSTATS_API_KEY")


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    gs_client = util.StorageClient()
    data = util.decode_message(cloud_event)
    message = json.loads(data)
    endpoint, season_id = message["endpoint"], message["season_id"]
    print(f"Getting data for endpoint: {endpoint}, season_id: {season_id}")
    fetched_data = fetch_footystats(endpoint, API_KEY, season_id=season_id)
    formatted_data = util.convert_to_newline_delimited_json(fetched_data)
    destination = f"{season_id}.json"
    gs_client.upload(BUCKET_NAMES[endpoint], formatted_data, destination)
    print(f"Got data for endpoint: {endpoint}, season_id: {season_id}")


def fetch_footystats(endpoint: str, key: str, **kwargs) -> dict:
    response = requests.get(
        f"https://api.football-data-api.com/league-{endpoint}",
        params={"key": key, **kwargs},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["data"]
