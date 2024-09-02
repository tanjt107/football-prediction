# import logging
import math
import os
from collections import defaultdict
from dataclasses import asdict

# import functions_framework
# from cloudevents.http.event import CloudEvent

# from gcp import storage
# from gcp.logging import setup_logging
# from gcp.util import decode_message
from simulation import queries
from simulation.models import Team, TieBreaker, Round
from simulation.tournaments import Season, Knockout


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
    completed_gs = queries.get_completed_matches(
        league, stage="gs", gs_name=data.get("gs_name", "Group Stage")
    )
    completed_ko = queries.get_completed_matches(league, stage="ko")

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

    group_seasons = {
        name: Season(teams, avg_goal, home_adv, data["h2h"], data["leg"], completed_gs)
        for name, teams in groups.items()
    }

    matchups = queries.get_matchup(league, teams)

    # logging.info(f"Simulating: {league=}")
    data = simulate_cup(
        group_seasons, data["team_no_ko"], matchups, completed_ko=completed_ko
    )
    # logging.info(f"Simulated: {league=}")

    print(
        data
        == [
            {
                "team": 8589,
                "group": "Group A",
                "positions": {"_1": 1.0},
                "rounds": {
                    "ROUND_OF_16": 1.0,
                    "QUARTER_FINALS": 1.0,
                    "SEMI_FINALS": 1.0,
                    "FINAL": 1.0,
                    "CHAMPS": 1.0,
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
                "rounds": {"ROUND_OF_16": 1.0, "QUARTER_FINALS": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0, "QUARTER_FINALS": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0, "QUARTER_FINALS": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {
                    "ROUND_OF_16": 1.0,
                    "QUARTER_FINALS": 1.0,
                    "SEMI_FINALS": 1.0,
                },
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0, "QUARTER_FINALS": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {
                    "ROUND_OF_16": 1.0,
                    "QUARTER_FINALS": 1.0,
                    "SEMI_FINALS": 1.0,
                },
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
                    "ROUND_OF_16": 1.0,
                    "QUARTER_FINALS": 1.0,
                    "SEMI_FINALS": 1.0,
                    "FINAL": 1.0,
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
                "rounds": {"ROUND_OF_16": 1.0},
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
                "rounds": {"ROUND_OF_16": 1.0},
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
        ]
    )
    # storage.upload_json_to_bucket(
    #     data,
    #     blob_name="league.json",
    #     bucket_name=BUCKET_NAME,
    #     hive_partitioning={"_LEAGUE": league, "_DATE_UNIX": latest_match_date},
    # )


def simulate_cup(
    groups: dict[str, Season],
    team_no_ko: int,
    matchups: dict[Round, list[tuple[Team, Team]]] | None = None,
    completed_ko: dict[tuple[str], tuple[int]] | None = None,
    no_of_simulations: int = 10000,
):
    direct, wildcard = divmod(team_no_ko, len(groups))

    for _ in range(no_of_simulations):
        positions = defaultdict(list)
        for group in groups.values():
            group.simulate()
            for position, team in enumerate(group.positions, 1):
                team.update_sim_table()
                team.update_sim_positions(position)
                positions[position].append(team)

        if not math.log2(team_no_ko).is_integer():
            continue

        advanced = []
        for position, teams in positions.items():
            if position <= direct:
                advanced.extend(teams)
            if position == direct + 1:
                advanced.extend(
                    sorted(
                        positions[direct + 1],
                        key=TieBreaker.goal_diff,
                        reverse=True,
                    )[:wildcard]
                )

        group = list(groups.values())[0]
        knockout = Knockout(
            teams=advanced,
            avg_goal=group.avg_goal,
            home_adv=group.home_adv,
            leg=group.leg,
            matchups=matchups,
            completed=completed_ko,
        )
        knockout.simulate()
        for _round, teams in knockout.results.items():
            for team in teams:
                team.update_sim_rounds(_round)

    for season in groups.values():
        for team in season.teams:
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
        for group, season in groups.items()
        for team in season.teams
    ]


main()
