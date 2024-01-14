import base64
import json

from cloudevents.http.event import CloudEvent


def convert_to_newline_delimited_json(data: dict | list) -> str:
    if isinstance(data, list):
        return "\n".join([json.dumps(d) for d in data])
    return json.dumps(data)


def safe_load_json(s: str) -> dict | str:
    try:
        return json.loads(s)
    except (json.decoder.JSONDecodeError, TypeError):
        return s


def decode_message(cloud_event: CloudEvent) -> dict | str:
    data = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    return safe_load_json(data)
