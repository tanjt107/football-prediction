import json
import os
import re
import functions_framework
from google.cloud import storage


BUCKET_NAME = os.environ.get("BUCKET_NAME")
REDUCE_FROM_MINUTE = 70
REDUCE_GOAL_VALUE = 0.5
ADJ_FACTOR = 1.05
XG_WEIGHT = 0.67


@functions_framework.cloud_event
def main(cloud_event):
    data = cloud_event.data
    storage_client = storage.Client()
    blob = storage_client.bucket(data["bucket"]).blob(data["name"])
    raw_data = blob.download_as_text()

    transformed_data = [
        transform_matches(json.loads(line)) for line in raw_data.splitlines()
    ]
    formatted_data = format_data(transformed_data)
    upload_to_gcs(BUCKET_NAME, formatted_data, blob.name)


def transform_matches(
    _match: dict,
) -> dict:
    if (
        _match["goal_timings_recorded"] == 1
        and "None" not in _match["homeGoals"]
        and "None" not in _match["awayGoals"]
    ):
        goal_timings = get_goal_timings_dict(_match["homeGoals"], _match["awayGoals"])
        home_adj, away_adj = reduce_goal_value(goal_timings)
        home_adj *= ADJ_FACTOR
        away_adj *= ADJ_FACTOR
    else:
        home_adj, away_adj = (
            _match["homeGoalCount"],
            _match["awayGoalCount"],
        )

    if _match["total_xg"] > 0:
        home_avg = home_adj * (1 - XG_WEIGHT) + _match["team_a_xg"] * XG_WEIGHT
        away_avg = away_adj * (1 - XG_WEIGHT) + _match["team_b_xg"] * XG_WEIGHT
    else:
        home_avg, away_avg = home_adj, away_adj

    return {
        "id": _match["id"],
        "home_adj": home_adj,
        "away_adj": away_adj,
        "home_avg": home_avg,
        "away_avg": away_avg,
    }


def get_goal_timings_dict(home: list[str], away: list[str]) -> list[tuple]:
    timings = [
        (int(re.search(r"(^1?\d{1,2})", minute).group()), "home") for minute in home
    ]
    timings.extend(
        (int(re.search(r"(^1?\d{1,2})", minute).group()), "away") for minute in away
    )
    return sorted(timings)


def reduce_goal_value(goal_timings: list[tuple]) -> tuple[float]:
    if not goal_timings:
        return 0, 0
    home = home_adj = away = away_adj = 0
    for timing, team in goal_timings:
        timing = min(timing, 90)
        if team == "away":
            away += 1
            away_adj += 1
            if timing > REDUCE_FROM_MINUTE and away - home > 1:
                away_adj -= (
                    (timing - REDUCE_FROM_MINUTE)
                    / (90 - REDUCE_FROM_MINUTE)
                    * (1 - REDUCE_GOAL_VALUE)
                )
        elif team == "home":
            home += 1
            home_adj += 1
            if timing > REDUCE_FROM_MINUTE and home - away > 1:
                home_adj -= (
                    (timing - REDUCE_FROM_MINUTE)
                    / (90 - REDUCE_FROM_MINUTE)
                    * (1 - REDUCE_GOAL_VALUE)
                )
    return home_adj, away_adj


def format_data(data):
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    storage.Client().bucket(bucket_name).blob(destination).upload_from_string(content)
