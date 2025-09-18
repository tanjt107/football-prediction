import json
import logging
import os
from dataclasses import asdict

import functions_framework
from cloudevents.http.event import CloudEvent

from gcp import storage
from gcp.logging import setup_logging

from gcp.util import decode_message
from simulation import queries
from simulation.models import Match, Team
from simulation.tournaments import Groups, Knockout, Season, Winner


setup_logging()

Round = Groups | Knockout | Season | Winner


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = decode_message(cloud_event)
    league = message["footystats_name"]
    rounds = json.loads(
        storage.download_blob(
            blob_name=f"{league}.json", bucket_name="manual-340977255134-asia-east2"
        )
    )

    factors = queries.get_avg_goal_home_adv(league)
    avg_goal, home_adv = factors["avg_goal"], factors["home_adv"]
    teams = queries.get_teams(league)

    logging.info(f"Simulating: {league=}")
    data = simulate_tournament(
        rounds,
        avg_goal,
        home_adv,
        teams,
        matches=queries.get_matches(league, teams),
        groups=queries.get_groups(league, teams),
    )
    logging.info(f"Simulated: {league=}")

    storage.upload_json_to_bucket(
        data,
        blob_name="league.json",
        bucket_name=os.environ["RESULT_BUCKET_NAME"],
        hive_partitioning={
            "_LEAGUE": league,
            "_DATE_UNIX": message["latest_match_date"],
        },
    )


def simulate_tournament(
    rounds: dict[str, dict],
    avg_goal: float,
    home_adv: float,
    teams: dict[str, Team],
    matches: dict[str, list[Match]] | None = None,
    groups: dict[dict[str, list[Team]]] | None = None,
    no_of_simulations: int = 10000,
):
    round_objs: dict[str, Round] = {}
    _groups = None

    for name, param in rounds.items():
        _format = param["format"]

        if _format == "Groups":
            _groups: dict[str, list[Team]] = groups.get(name) or {
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

        elif _format == "Knockout":
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

        elif _format == "Season":
            round_objs[name] = Season(
                teams.values(),
                avg_goal,
                home_adv,
                matches[name],
                param["h2h"],
                param["leg"],
            )

        elif _format == "Winner":
            round_objs[name] = Winner()

    for _ in range(no_of_simulations):
        for name, round_obj in round_objs.items():
            round_obj.simulate()

            if advance_to := rounds[name].get("advance_to"):
                if isinstance(advance_to, str):
                    round_objs[advance_to].add_teams(round_obj.get_advanced())
                else:
                    for name, positions in advance_to.items():
                        round_objs[name].add_teams(round_obj.get_advanced(**positions))
            round_obj.reset()

    for team in teams.values():
        team.sim_table /= no_of_simulations
        team.sim_rounds /= no_of_simulations
        team.sim_positions /= no_of_simulations

    if _groups:
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
        for team in teams.values()
    ]
