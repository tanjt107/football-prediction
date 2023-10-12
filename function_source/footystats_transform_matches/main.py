import json
import os
import re

from cloudevents.http.event import CloudEvent
import functions_framework

from gcp import storage


REDUCE_FROM_MINUTE = 70
REDUCE_GOAL_VALUE = 0.5
ADJ_FACTOR = 1.05
XG_WEIGHT = 0.67


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = cloud_event.data
    blob_name = message["name"]
    blob = storage.download_bolb(
        blob_name,
        bucket_name=message["bucket"],
    )
    data = [transform_matches(json.loads(line)) for line in blob.splitlines()]
    storage.upload_json_to_bucket(
        data, blob_name, bucket_name=os.environ["BUCKET_NAME"]
    )


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
        adj_val = (
            max(timing - REDUCE_FROM_MINUTE, 0)
            / (90 - REDUCE_FROM_MINUTE)
            * REDUCE_GOAL_VALUE
        )
        if team == "away":
            away += 1
            away_adj += 1
            if timing > REDUCE_FROM_MINUTE and away - home > 1:
                away_adj -= adj_val
        elif team == "home":
            home += 1
            home_adj += 1
            if timing > REDUCE_FROM_MINUTE and home - away > 1:
                home_adj -= adj_val
    return home_adj, away_adj
