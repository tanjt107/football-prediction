import json
import os
import functions_framework
from google.cloud import bigquery, storage
from pulp import LpMinimize, LpProblem, lpSum, LpVariable

BOUND = os.environ.get("BOUND")
BUCKET_NAME = os.environ.get("BUCKET_NAME")


def get_matches():
    bigquery_client = bigquery.Client()
    sql = "SELECT * FROM `footystats.get_solver_matches`(1, 5);"
    query_job = bigquery_client.query(sql)
    rows = query_job.result()
    return [dict(row) for row in rows]


def save_to_bucket(file_name, data):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    bucket.blob(file_name).upload_from_string(data)


def convert_to_newline_delimited_json(data: list) -> str:
    return "\n".join([json.dumps(d) for d in data])


def solver(matches: list[dict]) -> dict[str, list[dict[str, float]]]:
    prob = LpProblem(sense=LpMinimize)

    # Lists to contain all leagues, teams and match ids
    leagues = list({match["league_name"] for match in matches})
    teams = list(
        {match["homeID"] for match in matches} | {match["awayID"] for match in matches}
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
            + offences[match["homeID"]]
            + defences[match["awayID"]]
            - float(match["home_avg"])
        ) * float(match["recent"])
        away_error = (
            avg_goals[match["league_name"]]
            - home_advs[match["league_name"]]
            + offences[match["awayID"]]
            + defences[match["homeID"]]
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
                "league": league,
                "avg_goal": avg_goals[league].varValue,
                "home_adv": home_advs[league].varValue,
            }
            for league in leagues
        ],
        [
            {
                "team": team,
                "offence": offences[team].varValue,
                "defence": defences[team].varValue,
            }
            for team in teams
        ],
    )


@functions_framework.cloud_event
def main(cloud_event):
    matches = get_matches()
    leagues, teams = solver(matches)
    leagues = convert_to_newline_delimited_json(leagues)
    teams = convert_to_newline_delimited_json(teams)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    bucket.blob("leagues.json").upload_from_string(leagues)
    bucket.blob("teams.json").upload_from_string(teams)
