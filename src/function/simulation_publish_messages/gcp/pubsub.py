import json
import os

from google.cloud import pubsub_v1

CLIENT = pubsub_v1.PublisherClient()


def get_topic_path(topic: str) -> str:
    return CLIENT.topic_path(project=os.environ["GCP_PROJECT"], topic=topic)


def publish_json_message(topic: str, data: dict):
    return CLIENT.publish(topic, data=json.dumps(data).encode())
