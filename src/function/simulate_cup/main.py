# import logging
# import math
import os
from dataclasses import asdict

# import functions_framework
# from cloudevents.http.event import CloudEvent

# from gcp import storage
# from gcp.logging import setup_logging
# from gcp.util import decode_message
from simulation import queries
from simulation.models import Match, Team
from simulation.tournaments import Groups, Knockout, Winner


# setup_logging()

BUCKET_NAME = os.getenv("BUCKET_NAME")


# @functions_framework.cloud_event
# def main(cloud_event: CloudEvent):
def main():
    # data = decode_message(cloud_event)
    data = {
        "league": "International AFC Asian Cup",
        "rounds": {
            "Group Stage": {
                "format": "Groups",
                "h2h": False,
                "leg": 1,
                "advance_to": {"Round of 16": {"start": 1, "end": 16}},
            },
            "Round of 16": {
                "format": "Knockout",
                "leg": 1,
                "advance_to": "Quarter-finals",
            },
            "Quarter-finals": {
                "format": "Knockout",
                "leg": 1,
                "advance_to": "Semi-finals",
            },
            "Semi-finals": {
                "format": "Knockout",
                "leg": 1,
                "advance_to": "Final",
            },
            "Final": {
                "format": "Knockout",
                "leg": 1,
                "advance_to": "Winner",
            },
            "Winner": {"format": "Winner"},
        },
    }
    league = data["league"]

    # last_run = queries.get_last_run(league)
    # latest_match_date = queries.get_latest_match_date(league)
    # if last_run >= latest_match_date:
    # logging.info(f"Already updated. Simulation aborted: {league=}")
    # return

    factors = queries.get_avg_goal_home_adv(league)
    avg_goal, home_adv = factors["avg_goal"], factors["home_adv"]
    teams = queries.get_teams(league)

    # logging.info(f"Simulating: {league=}")
    data = simulate_cup(
        data["rounds"],
        avg_goal,
        home_adv,
        teams.values(),
        matches=queries.get_matches(league, teams),
        groups=queries.get_groups(league, teams),
    )
    # logging.info(f"Simulated: {league=}")

    import json

    with open("check.json", "w") as f:
        json.dump(data, f)
    # storage.upload_json_to_bucket(
    #     data,
    #     blob_name="league.json",
    #     bucket_name=BUCKET_NAME,
    #     hive_partitioning={"_LEAGUE": league, "_DATE_UNIX": latest_match_date},
    # )


def simulate_cup(
    rounds: dict,
    avg_goal: float,
    home_adv: float,
    teams: list[Team],
    matches: dict[str, list[Match]] | None = None,
    groups: dict[dict[str, list[Team]]] | None = None,
    no_of_simulations: int = 10000,
):
    round_objs = {}
    _groups = None

    for name, param in rounds.items():
        if param["format"] == "Groups":
            _groups = groups.get(name)
            if not _groups and "groups" in param:
                _groups = {
                    group: [teams[team] for team in _teams]
                    for group, _teams in param["groups"].items()
                }
            round_objs[name] = Groups(
                _groups,
                avg_goal,
                home_adv,
                matches[name],
                param["h2h"],
                param["leg"],
            )
        elif param["format"] == "Knockout":
            round_objs[name] = Knockout(
                name,
                avg_goal,
                home_adv,
                matches[name],
                param["leg"],
                winning_teams={
                    team
                    for match in matches.get(param["advance_to"], [])
                    for team in match.teams
                },
            )
        elif param["format"] == "Winner":
            round_objs[name] = Winner()

    for _ in range(no_of_simulations):
        for name, round_obj in round_objs.items():
            round_obj.simulate()
            if zones := rounds[name].get("advance_to"):
                if isinstance(zones, str):
                    round_objs[zones].add_teams(round_obj.get_advanced())
                else:
                    for name, positions in zones.items():
                        round_objs[name].add_teams(round_obj.get_advanced(**positions))
            round_obj.reset()

    for team in teams:
        team.sim_table /= no_of_simulations
        team.sim_rounds /= no_of_simulations
        team.sim_positions /= no_of_simulations

    if groups:
        return [
            {
                "team": team.name,
                "group": group,
                "positions": dict(team.sim_positions),
                "rounds": dict(team.sim_rounds),
                "table": asdict(team.sim_table),
            }
            for group, teams in _groups.items()
            for team in teams
        ]
    return [
        {
            "team": team.name,
            "positions": dict(team.sim_positions),
            "rounds": dict(team.sim_rounds),
            "table": asdict(team.sim_table),
        }
        for team in teams
    ]


main()
