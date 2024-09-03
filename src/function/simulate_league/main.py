# import logging
import os
from dataclasses import asdict

# import functions_framework
# from cloudevents.http.event import CloudEvent

# from gcp import storage
# from gcp.logging import setup_logging
# from gcp.util import decode_message
from simulation import queries
from simulation.tournaments import Season
from simulation.models import Team

# setup_logging()

BUCKET_NAME = os.getenv("BUCKET_NAME")


# @functions_framework.cloud_event
# def main(cloud_event: CloudEvent):
def main():
    # message = decode_message(cloud_event)
    message = {"league": "India Indian Super League", "h2h": True, "leg": 2}
    # message = {"league": "Hong Kong Hong Kong Premier League", "h2h": True, "leg": 3}
    league = message["league"]

    # last_run = queries.get_last_run(league)
    # latest_match_date = queries.get_latest_match_date(league)
    # if last_run >= latest_match_date:
    #     logging.info(f"Already updated. Simulation aborted: {league=}")
    #     return

    factors = queries.get_avg_goal_home_adv(league)
    teams = queries.get_teams(league)

    if corrections := message.get("corrections"):
        for team, correction in corrections.items():
            teams[int(team)].set_correction(correction)

    season = Season(
        teams=teams.values(),
        avg_goal=factors["avg_goal"],
        home_adv=factors["home_adv"],
        h2h=message["h2h"],
        leg=message["leg"],
        matches=queries.get_matches(league, teams)["Regular Season"],
    )

    # logging.info(f"Simulating: {league=}")
    data = simulate_season(season, no_of_simulations=10000)
    # logging.info(f"Simulated: {league=}")

    if data == [
        {
            "team": 5416,
            "positions": {"_2": 1.0},
            "table": {
                "wins": 13.0,
                "draws": 6.0,
                "losses": 3.0,
                "scored": 40.0,
                "conceded": 20.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5417,
            "positions": {"_6": 1.0},
            "table": {
                "wins": 8.0,
                "draws": 3.0,
                "losses": 11.0,
                "scored": 26.0,
                "conceded": 36.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5419,
            "positions": {"_4": 1.0},
            "table": {
                "wins": 11.0,
                "draws": 6.0,
                "losses": 5.0,
                "scored": 35.0,
                "conceded": 23.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5420,
            "positions": {"_7": 1.0},
            "table": {
                "wins": 6.0,
                "draws": 8.0,
                "losses": 8.0,
                "scored": 30.0,
                "conceded": 34.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5421,
            "positions": {"_3": 1.0},
            "table": {
                "wins": 13.0,
                "draws": 6.0,
                "losses": 3.0,
                "scored": 39.0,
                "conceded": 21.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5422,
            "positions": {"_5": 1.0},
            "table": {
                "wins": 10.0,
                "draws": 3.0,
                "losses": 9.0,
                "scored": 32.0,
                "conceded": 31.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5424,
            "positions": {"_11": 1.0},
            "table": {
                "wins": 5.0,
                "draws": 7.0,
                "losses": 10.0,
                "scored": 28.0,
                "conceded": 30.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5425,
            "positions": {"_10": 1.0},
            "table": {
                "wins": 5.0,
                "draws": 7.0,
                "losses": 10.0,
                "scored": 20.0,
                "conceded": 34.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5426,
            "positions": {"_8": 1.0},
            "table": {
                "wins": 6.0,
                "draws": 6.0,
                "losses": 10.0,
                "scored": 28.0,
                "conceded": 35.0,
                "correction": 0.0,
            },
        },
        {
            "team": 5430,
            "positions": {"_9": 1.0},
            "table": {
                "wins": 6.0,
                "draws": 6.0,
                "losses": 10.0,
                "scored": 27.0,
                "conceded": 29.0,
                "correction": 0.0,
            },
        },
        {
            "team": 674110,
            "positions": {"_12": 1.0},
            "table": {
                "wins": 1.0,
                "draws": 5.0,
                "losses": 16.0,
                "scored": 10.0,
                "conceded": 43.0,
                "correction": 0.0,
            },
        },
        {
            "team": 688913,
            "positions": {"_1": 1.0},
            "table": {
                "wins": 15.0,
                "draws": 3.0,
                "losses": 4.0,
                "scored": 47.0,
                "conceded": 26.0,
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


def simulate_season(
    season: Season,
    no_of_simulations: int = 10000,
) -> list[Team]:
    for _ in range(no_of_simulations):
        season.simulate()
        for position, team in enumerate(season.positions, 1):
            team.update_sim_table()
            team.update_sim_positions(position)
        season.reset()

    for team in season.teams:
        team.sim_table /= no_of_simulations
        team.sim_positions /= no_of_simulations

    return [
        {
            "team": team.name,
            "positions": dict(team.sim_positions),
            "table": asdict(team.sim_table),
        }
        for team in season.teams
    ]


main()
