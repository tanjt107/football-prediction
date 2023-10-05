import os

import functions_framework
import requests

import util

BUCKET_NAME = os.getenv("BUCKET_NAME")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")


@functions_framework.cloud_event
def main(_):
    gs_client = util.StorageClient()
    league_data = fetch_footystats("list", API_KEY, chosen_leagues_only="true")
    formatted_data = util.convert_to_newline_delimited_json(league_data)
    destination = "league_list.json"
    gs_client.upload(BUCKET_NAME, formatted_data, destination)


def fetch_footystats(endpoint: str, key: str, **kwargs) -> dict:
    response = requests.get(
        f"https://api.football-data-api.com/league-{endpoint}",
        params={"key": key, **kwargs},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["data"]
