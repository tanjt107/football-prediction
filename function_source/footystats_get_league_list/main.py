import functions_framework
import json
import os
import requests
from google.cloud import storage

BUCKET_NAME = os.getenv("BUCKET_NAME")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")


@functions_framework.cloud_event
def main(cloud_event):
    league_data = fetch_data("list", API_KEY, chosen_leagues_only="true")
    formatted_data = format_data(league_data)
    destination = "league_list.json"
    upload_to_gcs(BUCKET_NAME, formatted_data, destination)


def fetch_data(endpoint: str, key: str, **kwargs) -> dict:
    response = requests.get(
        f"https://api.football-data-api.com/league-{endpoint}",
        params={"key": key, **kwargs},
    )
    response.raise_for_status()
    return response.json()["data"]


def format_data(data):
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    storage.Client().bucket(bucket_name).blob(destination).upload_from_string(content)
