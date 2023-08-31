import functions_framework
import json
import os
import requests
from google.cloud import storage

BUCKET_NAME = os.getenv("BUCKET_NAME")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")


@functions_framework.cloud_event
def main(cloud_event):
    league_data = fetch_league_list(API_KEY)
    formatted_data = convert_to_newline_delimited_json(league_data)
    destination = "league_list.json"
    upload_to_gcs(BUCKET_NAME, formatted_data, destination)


def fetch_league_list(key: str) -> dict:
    response = requests.get(
        "https://api.football-data-api.com/league-list",
        params={"key": key, "chosen_leagues_only": "true"},
    )
    response.raise_for_status()
    return response.json()["data"]


def convert_to_newline_delimited_json(data: list) -> str:
    return "\n".join([json.dumps(d) for d in data])


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    storage.Client().bucket(bucket_name).blob(destination).upload_from_string(content)
