import os

import functions_framework

from gcp import bigquery, pubsub


@functions_framework.cloud_event
def main(_):
    for message in bigquery.query_dict(query="SELECT * FROM `solver.get_messages`();"):
        pubsub.publish_json_message(
            topic=os.environ["TOPIC_NAME"],
            data=message,
        )
