import base64
import json
import os
import functions_framework
from google.cloud import bigquery, storage
from pulp import LpMinimize, LpProblem, lpSum, LpVariable

BOUND = os.environ.get("BOUND")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
BQ_CLIENT = bigquery.Client()
GS_CLIENT = storage.Client()


@functions_framework.cloud_event
def main(cloud_event):
    type = get_message(cloud_event)
    last_run = get_last_run(type) or -1
    latest_match_date = get_latest_match_date(type)
    if last_run >= latest_match_date:
        return

    matches = get_matches(type, latest_match_date)
    leagues, teams = solver(matches)
    leagues = convert_to_newline_delimited_json(leagues)
    teams = convert_to_newline_delimited_json(teams)

    upload_to_gcs(BUCKET_NAME, leagues, f"leagues/{type}.json")
    upload_to_gcs(BUCKET_NAME, teams, f"teams/{type}.json")

    insert_run_log(type, latest_match_date)


def get_message(cloud_event) -> str:
    return base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")


def get_last_run(type):
    sql = f"SELECT date_unix AS last_run FROM `solver.run_log` WHERE type = '{type}'"
    return bq_fetch_one(sql)


def bq_fetch_one(sql: str):
    query_job = BQ_CLIENT.query(sql)
    rows = query_job.result()
    return next(iter(rows), [None])[0]


def get_latest_match_date(type):
    sql = f"""
    SELECT
        MAX(date_unix)
    FROM `footystats.matches` matches
    JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
    JOIN `master.leagues` leagues ON seasons.country = leagues.country
        AND seasons.name = leagues.footystats_name
    WHERE matches.status = 'complete'
        AND leagues.type = '{type}'
    """
    return bq_fetch_one(sql)


def get_matches(type, max_time: int):
    sql = f"SELECT * FROM `functions.get_solver_matches`('{type}', {max_time}, 1, 5);"
    query_job = BQ_CLIENT.query(sql)
    rows = query_job.result()
    return [dict(row) for row in rows]


def solver(matches: list[dict]) -> dict[str, list[dict[str, float]]]:
    prob = LpProblem(sense=LpMinimize)

    # Lists to contain all leagues, teams and match ids
    leagues = list({match["league_name"] for match in matches})
    teams = list(
        {match["home_id"] for match in matches}
        | {match["away_id"] for match in matches}
    )
    ids = [match["id"] for match in matches]

    # Dictionaries to contain all variables
    avg_goals = LpVariable.dicts("avg_goal", leagues, lowBound=0)
    home_advs = LpVariable.dict("home_adv", leagues, lowBound=0)
    up_bound = int(BOUND) if BOUND else None
    low_bound = -int(BOUND) if BOUND else None
    offences = LpVariable.dicts("offence", teams, lowBound=low_bound, upBound=up_bound)
    defences = LpVariable.dicts("defence", teams, lowBound=low_bound, upBound=up_bound)
    home_errors = LpVariable.dicts("home_error", ids)
    away_errors = LpVariable.dicts("away_error", ids)

    for match in matches:
        home_error = (
            avg_goals[match["league_name"]]
            + home_advs[match["league_name"]]
            + offences[match["home_id"]]
            + defences[match["away_id"]]
            - float(match["home_avg"])
        ) * float(match["recent"])
        away_error = (
            avg_goals[match["league_name"]]
            - home_advs[match["league_name"]]
            + offences[match["away_id"]]
            + defences[match["home_id"]]
            - float(match["away_avg"])
        ) * float(match["recent"])

        # Constraints for absolute values
        prob += home_errors[match["id"]] >= home_error
        prob += home_errors[match["id"]] >= -home_error
        prob += away_errors[match["id"]] >= away_error
        prob += away_errors[match["id"]] >= -away_error

    # Objective function
    prob += lpSum(home_errors) + lpSum(away_errors)

    # Other constraints
    prob += lpSum(offences) == 0
    prob += lpSum(defences) == 0

    prob.solve()

    return (
        [
            {
                "division": league,
                "avg_goal": avg_goals[league].varValue,
                "home_adv": home_advs[league].varValue,
            }
            for league in leagues
        ],
        [
            {
                "id": team,
                "offence": offences[team].varValue,
                "defence": defences[team].varValue,
            }
            for team in teams
        ],
    )


def convert_to_newline_delimited_json(data: list) -> str:
    return "\n".join([json.dumps(d) for d in data])


def upload_to_gcs(bucket_name: str, content: str, destination: str):
    GS_CLIENT.bucket(bucket_name).blob(destination).upload_from_string(content)


def insert_run_log(type, match_date):
    sql = f"INSERT INTO solver.run_log VALUES ('{type}', {match_date})"
    query_job = BQ_CLIENT.query(sql)
    query_job.result()
