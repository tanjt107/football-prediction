import json
import os
import re
from enum import Enum

from cloudevents.http.event import CloudEvent
import functions_framework

from gcp import storage
from gcp.logging import setup_logging

setup_logging()

REDUCE_FROM_MINUTE = 70
REDUCE_LEADING_GOAL_VALUE = 0.5
REDUCE_RED_CARD_GOAL_VALUE = 0.2
XG_WEIGHT = 0.67
ADJ_FACTORS = {
    (False, False): 1,
    (True, False): 1.01,
    (False, True): 1.04,
    (True, True): 1.05,
}


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


class Team(Enum):
    HOME = 1
    AWAY = 2

    def __lt__(self, other):
        return self.value > other.value


def transform_matches(
    _match: dict,
) -> dict:
    home_adj, away_adj = (
        _match["homeGoalCount"],
        _match["awayGoalCount"],
    )
    more_player_team = None

    goal_timings_recorded = (
        _match["goal_timings_recorded"] == 1
        and "None" not in _match["homeGoals"]
        and "None" not in _match["awayGoals"]
    )
    card_timings_recorded = _match["card_timings_recorded"] == 1

    if card_timings_recorded == 1:
        more_player_team = get_more_players_team(
            _match["team_a_red_cards"], _match["team_b_red_cards"]
        )

    if goal_timings_recorded:
        goal_timings = get_goal_timings_dict(_match["homeGoals"], _match["awayGoals"])
        home_adj, away_adj = reduce_goal_value(goal_timings, more_player_team)
    elif more_player_team == Team.HOME:
        home_adj *= 1 - (REDUCE_RED_CARD_GOAL_VALUE / 2)
    elif more_player_team == Team.AWAY:
        away_adj *= 1 - (REDUCE_RED_CARD_GOAL_VALUE / 2)

    adj_factor = ADJ_FACTORS[(card_timings_recorded, goal_timings_recorded)]
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


def get_more_players_team(home_red_cards: int, away_red_cards: int) -> Team | None:
    if home_red_cards > away_red_cards:
        return Team.AWAY
    if away_red_cards > home_red_cards:
        return Team.HOME


def get_goal_timings_dict(home: list[str], away: list[str]) -> list[tuple]:
    timings = [
        (int(re.search(r"(^1?\d{1,2})", minute).group()), minute, Team.HOME)
        for minute in home
    ]
    timings.extend(
        (int(re.search(r"(^1?\d{1,2})", minute).group()), minute, Team.AWAY)
        for minute in away
    )
    return sorted(timings)


def reduce_goal_value(
    goal_timings: list[tuple[int, Team]], more_player_team: Team
) -> tuple[float]:
    if not goal_timings:
        return 0, 0
    home = home_adj = away = away_adj = 0
    for timing, _, team in goal_timings:
        timing = min(timing, 90)
        late_leading_adj_val = (
            max(timing - REDUCE_FROM_MINUTE, 0)
            / (90 - REDUCE_FROM_MINUTE)
            * REDUCE_LEADING_GOAL_VALUE
        )
        more_player_adj_val = (timing / 90) * REDUCE_RED_CARD_GOAL_VALUE

        goal_val = 1
        if team == more_player_team:
            goal_val *= 1 - more_player_adj_val
        if team == Team.AWAY:
            away += 1
            if away - home > 1:
                goal_val *= 1 - late_leading_adj_val
            away_adj += goal_val
        elif team == Team.HOME:
            home += 1
            if home - away > 1:
                goal_val *= 1 - late_leading_adj_val
            home_adj += goal_val
    return home_adj, away_adj
