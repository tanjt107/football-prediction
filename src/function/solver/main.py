import os

import functions_framework
from cloudevents.http.event import CloudEvent


from gcp import storage
from gcp.logging import setup_logging
from gcp.util import decode_message
from solver import queries
from solver.solver import solver

setup_logging()


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    message = decode_message(cloud_event)
    _type, latest_match_date = message["_TYPE"], message["latest_match_date"]

    data = queries.get_matches_and_teams(_type, latest_match_date)

    for name, data in solver(data["matches"], data["teams"], data["leagues"]).items():
        storage.upload_json_to_bucket(
            data,
            blob_name=f"{name}.json",
            bucket_name=os.environ["BUCKET_NAME"],
            hive_partitioning={"_TYPE": _type, "_DATE_UNIX": latest_match_date},
        )
