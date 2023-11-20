import json
import os
import re

from cloudevents.http.event import CloudEvent
import functions_framework

from gcp import storage


REDUCE_FROM_MINUTE = 70
REDUCE_LEADING_GOAL_VALUE = 0.5
REDUCE_RED_CARD_GOAL_VALUE = 0.9
ADJ_FACTOR = 0.025
XG_WEIGHT = 0.67


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = cloud_event.data
    blob_name = message["name"]
    blob = storage.download_blob(
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
        home_adj, away_adj = reduce_leading_goal_value(goal_timings)
    else:
        home_adj, away_adj = (
            _match["homeGoalCount"],
            _match["awayGoalCount"],
        )

    if _match["card_timings_recorded"] == 1:
        if _match["team_a_red_cards"] > _match["team_b_red_cards"]:
            away_adj *= REDUCE_RED_CARD_GOAL_VALUE
        elif _match["team_b_red_cards"] > _match["team_a_red_cards"]:
            home_adj *= REDUCE_RED_CARD_GOAL_VALUE

    adj_factor = (
        1
        + (
            (_match["goal_timings_recorded"] == 1)
            + (_match["card_timings_recorded"] == 1)
        )
        * ADJ_FACTOR
    )
    home_adj *= adj_factor
    away_adj *= adj_factor

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


def reduce_leading_goal_value(goal_timings: list[tuple]) -> tuple[float]:
    if not goal_timings:
        return 0, 0
    home = home_adj = away = away_adj = 0
    for timing, team in goal_timings:
        timing = min(timing, 90)
        adj_val = (
            max(timing - REDUCE_FROM_MINUTE, 0)
            / (90 - REDUCE_FROM_MINUTE)
            * REDUCE_LEADING_GOAL_VALUE
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
