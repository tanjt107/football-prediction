from google.cloud import bigquery

from gcp.util import safe_load_json

CLIENT = bigquery.Client()
SQL_TYPES = {str: "STRING", int: "INT64"}


def query_dict(query: str, params: dict | None = None) -> list[dict]:
    if params:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(key, SQL_TYPES[type(value)], value)
                for key, value in params.items()
            ]
        )
    else:
        job_config = None
    query_job = CLIENT.query(query, job_config)
    return [safe_load_json(dict(row)) for row in query_job.result()]
