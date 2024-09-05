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

    if data == [
        {
            "team": 8589,
            "group": "Group A",
            "positions": {"_1": 1.0},
            "rounds": {
                "round_of_16": 1.0,
                "quarter_finals": 1.0,
                "semi_finals": 1.0,
                "final": 1.0,
                "winner": 1.0,
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
            "rounds": {"round_of_16": 1.0, "quarter_finals": 1.0},
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
            "rounds": {"round_of_16": 1.0, "quarter_finals": 1.0},
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
            "rounds": {"round_of_16": 1.0, "quarter_finals": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0, "quarter_finals": 1.0, "semi_finals": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0, "quarter_finals": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0, "quarter_finals": 1.0, "semi_finals": 1.0},
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
                "round_of_16": 1.0,
                "quarter_finals": 1.0,
                "semi_finals": 1.0,
                "final": 1.0,
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
            "rounds": {"round_of_16": 1.0},
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
            "rounds": {"round_of_16": 1.0},
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
    rounds: str,
    avg_goal: float,
    home_adv: float,
    teams: list[Team],
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

        # groups.simulate()
        # advanced = groups.get_advanced(team_no_ko)
        # _rounds = [
        #     "Round of 16",
        #     "Quarter-finals",
        #     "Semi-finals",
        #     "Final",
        #     "Winner",
        # ]
        # for i in range(len(_rounds) - 1):
        #     current_round = _rounds[i]
        #     next_round = _rounds[i + 1]
        #     winners = set(
        #         team for match in matches.get(next_round, []) for team in match.teams
        #     )
        #     knockout = Knockout(
        #         name=current_round,
        #         teams=set(advanced),
        #         avg_goal=groups.avg_goal,
        #         home_adv=groups.home_adv,
        #         matches=matches[current_round],
        #         leg=groups.leg,
        #         winning_teams=winners,
        #     )

        #     knockout.simulate()
        #     advanced = knockout.winning_teams

        # knockout = Knockout(
        #     name="Winner",
        #     teams=set(advanced),
        #     avg_goal=groups.avg_goal,
        #     home_adv=groups.home_adv,
        #     leg=groups.leg,
        #     winning_teams=winners,
        # )

        # groups.reset()

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
