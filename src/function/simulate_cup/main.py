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
        "rounds": [
            {
                "name": "Group Stage",
                "format": "Groups",
                "h2h": False,
                "leg": 1,
                "advance_to": {"name": "Round of 16", "n": 16},
            },
            {
                "name": "Round of 16",
                "format": "Knockout",
                "leg": 1,
                "advance_to": {"name": "Quarter-finals"},
            },
            {
                "name": "Quarter-finals",
                "format": "Knockout",
                "leg": 1,
                "advance_to": {"name": "Semi-finals"},
            },
            {
                "name": "Semi-finals",
                "format": "Knockout",
                "leg": 1,
                "advance_to": {"name": "Final"},
            },
            {
                "name": "Final",
                "format": "Knockout",
                "leg": 1,
                "advance_to": {"name": "Winner"},
            },
            {"name": "Winner", "format": "Winner"},
        ],
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
        teams,
        league,
        matches=queries.get_matches(league, teams),
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
    rounds: str,
    avg_goal: float,
    home_adv: float,
    teams: dict[str, Team],
    league: str,
    matches: dict[str, list[Match]] | None = None,
    no_of_simulations: int = 10000,
):

    _rounds = {}
    groups = None
    for _round in rounds:
        if _round["format"] == "Groups":
            groups = queries.get_groups(league, teams, _round["name"])
            if not groups:
                groups = {
                    group: [teams[team] for team in _teams]
                    for group, _teams in _round["groups"].items()
                }
            _rounds[_round["name"]] = Groups(
                groups,
                avg_goal,
                home_adv,
                matches[_round["name"]],
                _round["h2h"],
                _round["leg"],
            )
        elif _round["format"] == "Knockout":
            _rounds[_round["name"]] = Knockout(
                _round["name"],
                avg_goal,
                home_adv,
                matches[_round["name"]],
                _round["leg"],
                winning_teams={
                    team
                    for match in matches.get(_round["advance_to"]["name"], [])
                    for team in match.teams
                },
            )
        elif _round["format"] == "Winner":
            _rounds[_round["name"]] = Winner()

    for _ in range(no_of_simulations):
        for _round in rounds:
            __round = _rounds[_round["name"]]
            __round.simulate()
            if "advance_to" in _round:
                if isinstance(__round, Groups):
                    advanced = __round.get_advanced(_round["advance_to"]["n"])
                elif isinstance(__round, Knockout):
                    advanced = __round.winning_teams
                _rounds[_round["advance_to"]["name"]].add_teams(advanced)

            __round.reset()

    for team in teams.values():
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
            for group, teams in groups.items()
            for team in teams
        ]
    return [
        {
            "team": team.name,
            "positions": dict(team.sim_positions),
            "rounds": dict(team.sim_rounds),
            "table": asdict(team.sim_table),
        }
        for team in teams.values()
    ]


main()
