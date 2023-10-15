import os

import functions_framework
from cloudevents.http.event import CloudEvent


from gcp import storage
from gcp.util import decode_message
from solver import queries
from solver.solver import solver


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    _type = decode_message(cloud_event)

    last_run = queries.get_last_run(_type)
    latest_match_date = queries.get_latest_match_date(_type)
    if last_run >= latest_match_date:
        print(
            f"Already updated. Solver aborted: {_type=}, {last_run=} {latest_match_date=}"
        )
        return

    data = queries.get_matches(_type, latest_match_date)

    for name, data in solver(data["matches"], data["teams"], data["leagues"]).items():
        storage.upload_json_to_bucket(
            data,
            blob_name=f"{name}.json",
            bucket_name=os.environ["BUCKET_NAME"],
            hive_partitioning={"_TYPE": _type, "_DATE_UNIX": latest_match_date},
        )
