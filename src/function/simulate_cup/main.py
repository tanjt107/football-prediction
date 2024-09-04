# import logging
# import math
import os
from collections import defaultdict
from dataclasses import asdict

# import functions_framework
# from cloudevents.http.event import CloudEvent

# from gcp import storage
# from gcp.logging import setup_logging
# from gcp.util import decode_message
from simulation import queries
from simulation.models import TieBreaker, Match
from simulation.tournaments import Groups, Knockout


# setup_logging()

BUCKET_NAME = os.getenv("BUCKET_NAME")


# @functions_framework.cloud_event
# def main(cloud_event: CloudEvent):
def main():
    # data = decode_message(cloud_event)
    data = {
        "league": "International AFC Asian Cup",
        "h2h": True,
        "leg": 1,
        "team_no_ko": 16,
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
    matches = queries.get_matches(league, teams)

    gs_name = data.get("gs_name")
    groups = (
        queries.get_groups(league, teams, gs_name)
        if gs_name
        else queries.get_groups(league, teams)
    )
    if not groups:
        groups = {
            group: [teams[team] for team in _teams]
            for group, _teams in data["groups"].items()
        }

    groups = Groups(
        groups, avg_goal, home_adv, data["h2h"], data["leg"], matches["Group Stage"]
    )

    # logging.info(f"Simulating: {league=}")
    data = simulate_cup(groups, data["team_no_ko"], matches)
    # logging.info(f"Simulated: {league=}")

    if data == [
        {
            "team": 8589,
            "group": "Group A",
            "positions": {"_1": 1.0},
            "rounds": {
                "Round of 16": 1.0,
                "Quarter-finals": 1.0,
                "Semi-finals": 1.0,
                "Final": 1.0,
            },
            "table": {
                "wins": 3.0,
                "draws": 0.0,
                "losses": 0.0,
                "scored": 5.0,
                "conceded": 0.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8591,
            "group": "Group A",
            "positions": {"_2": 1.0},
            "rounds": {"Round of 16": 1.0, "Quarter-finals": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 1.0,
                "losses": 1.0,
                "scored": 2.0,
                "conceded": 2.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8585,
            "group": "Group A",
            "positions": {"_3": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 2.0,
                "losses": 1.0,
                "scored": 0.0,
                "conceded": 1.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8600,
            "group": "Group A",
            "positions": {"_4": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 1.0,
                "losses": 2.0,
                "scored": 1.0,
                "conceded": 5.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8582,
            "group": "Group B",
            "positions": {"_1": 1.0},
            "rounds": {"Round of 16": 1.0, "Quarter-finals": 1.0},
            "table": {
                "wins": 2.0,
                "draws": 1.0,
                "losses": 0.0,
                "scored": 4.0,
                "conceded": 1.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8615,
            "group": "Group B",
            "positions": {"_2": 1.0},
            "rounds": {"Round of 16": 1.0, "Quarter-finals": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 2.0,
                "losses": 0.0,
                "scored": 4.0,
                "conceded": 1.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8590,
            "group": "Group B",
            "positions": {"_3": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 1.0,
                "losses": 1.0,
                "scored": 1.0,
                "conceded": 1.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8581,
            "group": "Group B",
            "positions": {"_4": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 0.0,
                "losses": 3.0,
                "scored": 0.0,
                "conceded": 6.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8607,
            "group": "Group C",
            "positions": {"_1": 1.0},
            "rounds": {"Round of 16": 1.0, "Quarter-finals": 1.0, "Semi-finals": 1.0},
            "table": {
                "wins": 3.0,
                "draws": 0.0,
                "losses": 0.0,
                "scored": 7.0,
                "conceded": 2.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8611,
            "group": "Group C",
            "positions": {"_2": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 1.0,
                "losses": 1.0,
                "scored": 5.0,
                "conceded": 4.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8594,
            "group": "Group C",
            "positions": {"_3": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 1.0,
                "losses": 1.0,
                "scored": 5.0,
                "conceded": 5.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8618,
            "group": "Group C",
            "positions": {"_4": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 0.0,
                "losses": 3.0,
                "scored": 1.0,
                "conceded": 7.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8606,
            "group": "Group D",
            "positions": {"_1": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 3.0,
                "draws": 0.0,
                "losses": 0.0,
                "scored": 8.0,
                "conceded": 4.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8579,
            "group": "Group D",
            "positions": {"_2": 1.0},
            "rounds": {"Round of 16": 1.0, "Quarter-finals": 1.0},
            "table": {
                "wins": 2.0,
                "draws": 0.0,
                "losses": 1.0,
                "scored": 8.0,
                "conceded": 5.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8737,
            "group": "Group D",
            "positions": {"_3": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 0.0,
                "losses": 2.0,
                "scored": 3.0,
                "conceded": 6.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8612,
            "group": "Group D",
            "positions": {"_4": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 0.0,
                "losses": 3.0,
                "scored": 4.0,
                "conceded": 8.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8584,
            "group": "Group E",
            "positions": {"_1": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 2.0,
                "draws": 0.0,
                "losses": 1.0,
                "scored": 3.0,
                "conceded": 3.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8619,
            "group": "Group E",
            "positions": {"_2": 1.0},
            "rounds": {"Round of 16": 1.0, "Quarter-finals": 1.0, "Semi-finals": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 2.0,
                "losses": 0.0,
                "scored": 8.0,
                "conceded": 6.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8580,
            "group": "Group E",
            "positions": {"_3": 1.0},
            "rounds": {
                "Round of 16": 1.0,
                "Quarter-finals": 1.0,
                "Semi-finals": 1.0,
                "Final": 1.0,
            },
            "table": {
                "wins": 1.0,
                "draws": 1.0,
                "losses": 1.0,
                "scored": 6.0,
                "conceded": 3.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8601,
            "group": "Group E",
            "positions": {"_4": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 1.0,
                "losses": 2.0,
                "scored": 3.0,
                "conceded": 8.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8588,
            "group": "Group F",
            "positions": {"_1": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 2.0,
                "draws": 1.0,
                "losses": 0.0,
                "scored": 4.0,
                "conceded": 1.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8613,
            "group": "Group F",
            "positions": {"_2": 1.0},
            "rounds": {"Round of 16": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 2.0,
                "losses": 0.0,
                "scored": 2.0,
                "conceded": 0.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8595,
            "group": "Group F",
            "positions": {"_3": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 2.0,
                "losses": 1.0,
                "scored": 2.0,
                "conceded": 3.0,
                "correction": 0.0,
            },
        },
        {
            "team": 8621,
            "group": "Group F",
            "positions": {"_4": 1.0},
            "rounds": {},
            "table": {
                "wins": 0.0,
                "draws": 1.0,
                "losses": 2.0,
                "scored": 1.0,
                "conceded": 5.0,
                "correction": 0.0,
            },
        },
    ]:
        print(True)
    else:
        print(data)
    # storage.upload_json_to_bucket(
    #     data,
    #     blob_name="league.json",
    #     bucket_name=BUCKET_NAME,
    #     hive_partitioning={"_LEAGUE": league, "_DATE_UNIX": latest_match_date},
    # )


def simulate_cup(
    groups: Groups,
    team_no_ko: int,
    matches: dict[str, list[Match]] | None = None,
    no_of_simulations: int = 10000,
):

    for _ in range(no_of_simulations):
        groups.simulate()
        advanced = groups.get_advanced(team_no_ko)
        rounds = [
            "Round of 16",
            "Quarter-finals",
            "Semi-finals",
            "Final",
            "Winner",
        ]  # TODO Currently hard coded. Should be from json.
        for i in range(len(rounds) - 1):
            current_round = rounds[i]
            next_round = rounds[i + 1]
            winners = set(
                team for match in matches.get(next_round, []) for team in match.teams
            )
            knockout = Knockout(
                name=current_round,
                teams=set(advanced),  # TODO review all data type set/tuple/list
                avg_goal=groups.avg_goal,
                home_adv=groups.home_adv,
                leg=groups.leg,
                matches=matches[current_round],
                winning_teams=winners,
            )

            knockout.simulate()
            advanced = knockout.winning_teams

        groups.reset()

    for team in groups.teams:
        team.sim_table /= no_of_simulations
        team.sim_rounds /= no_of_simulations
        team.sim_positions /= no_of_simulations

    return [
        {
            "team": team.name,
            "group": group,
            "positions": dict(team.sim_positions),
            "rounds": dict(team.sim_rounds),
            "table": asdict(team.sim_table),
        }
        for group, teams in groups.groups.items()
        for team in teams
    ]


main()
