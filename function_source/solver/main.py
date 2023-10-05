import os

import functions_framework
from cloudevents.http.event import CloudEvent
from google.cloud import bigquery

import solver
import util

BUCKET_NAME = os.environ.get("BUCKET_NAME")


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    _type = util.decode_message(cloud_event)
    bq_client = util.BigQueryClient()
    last_run = get_last_run(_type, bq_client) or -1
    latest_match_date = get_latest_match_date(_type, bq_client)
    if last_run >= latest_match_date:
        return

    matches = get_matches(_type, latest_match_date, bq_client)
    leagues, teams = solver.solver(matches)
    leagues = util.convert_to_newline_delimited_json(leagues)
    teams = util.convert_to_newline_delimited_json(teams)

    gs_client = util.StorageClient()
    gs_client.upload(BUCKET_NAME, leagues, f"type={_type}/leagues.json")
    gs_client.upload(BUCKET_NAME, teams, f"type={_type}/teams.json")

    insert_run_log(_type, latest_match_date, bq_client)


def get_last_run(_type: str, client: util.BigQueryClient) -> int:
    query = "SELECT MAX(date_unix) AS last_run FROM `solver.run_log` WHERE type = @type"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("type", "STRING", _type)]
    )
    if rows := client.query_dict(query, job_config):
        return rows[0]["last_run"]


def get_latest_match_date(_type: str, client: util.BigQueryClient) -> int:
    query = """
    SELECT
        MAX(date_unix) AS max_date_unix
    FROM `footystats.matches` matches
    JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
    JOIN `master.leagues` leagues ON seasons.country = leagues.country
        AND seasons.name = leagues.footystats_name
    WHERE matches.status = 'complete'
        AND leagues.type = @type
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("type", "STRING", _type)]
    )
    return client.query_dict(query, job_config)[0]["max_date_unix"]


def get_matches(_type: str, max_time: int, client: util.BigQueryClient) -> dict:
    query = "SELECT * FROM `functions.get_solver_matches`(@type, @max_time);"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("type", "STRING", _type),
            bigquery.ScalarQueryParameter("max_time", "INT64", max_time),
        ]
    )
    return client.query_dict(query, job_config)


def insert_run_log(_type: str, date_unix: int, client: util.BigQueryClient):
    query = "INSERT INTO solver.run_log VALUES (@type, @date_unix)"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("type", "STRING", _type),
            bigquery.ScalarQueryParameter("date_unix", "INT64", date_unix),
        ]
    )
    client.query_dict(query, job_config)
