import json
import os
from datetime import datetime
from typing import Callable

DATA_DIR = "data"
EXTRACT_DIR = os.path.join(DATA_DIR, "incoming")
TRANSFORM_DIR = os.path.join(DATA_DIR, "completed")


def is_data_updated(incoming_data: dict, file_dir: str):
    if not os.path.exists(file_dir):
        return True
    with open(file_dir) as f:
        existing_data = json.load(f)
    if type(existing_data) != type(incoming_data):
        return True
    if isinstance(existing_data, dict):
        existing_data.pop("modified_on", None)
        incoming_data.pop("modified_on", None)
    elif isinstance(existing_data, list):
        for data in [existing_data, incoming_data]:
            for d in data:
                d.pop("modified_on", None)
    return incoming_data != existing_data


def write_if_updated(incoming_data: dict, file_dir: str):
    if not is_data_updated(incoming_data, file_dir):
        return
    with open(file_dir, "w") as f:
        json.dump(incoming_data, f, indent=4)


def filter_dict_keys(d: dict, keys: list) -> dict:
    return {k: v for k, v in d.items() if k in keys}


class Pipeline:
    def __init__(
        self,
        folder: str,
        extract_dir: str = EXTRACT_DIR,
        transform_dir: str = TRANSFORM_DIR,
    ):
        self.folder = folder
        self.extract_dir = extract_dir
        self.transform_dir = transform_dir
        self.modified_on = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def extract(self, endpoint: Callable[[], dict], id: int):
        incoming_data = endpoint(id)
        file_dir = os.path.join(self.extract_dir, self.folder, f"{id}.json")
        write_if_updated(incoming_data, file_dir)

    def transform(self, func: Callable[[dict], dict], initial: bool = True):
        if initial:
            last_modified = 0
        else:
            last_modified = max(
                entry.stat().st_mtime
                for entry in os.scandir(os.path.join(self.transform_dir, self.folder))
            )

        for entry in os.scandir(os.path.join(self.extract_dir, self.folder)):
            if not entry.name.endswith(".json"):
                continue
            if entry.stat().st_mtime < last_modified:
                continue
            with open(entry.path) as f:
                extracted_data = json.load(f)

            file_dir = os.path.join(self.transform_dir, self.folder, entry.name)

            if isinstance(extracted_data, dict):
                transformed_data = func(extracted_data)
                transformed_data["modified_on"] = self.modified_on
                write_if_updated(transformed_data, file_dir)
            elif isinstance(extracted_data, list):
                dicts = []
                for d in extracted_data:
                    transformed_data = func(d)
                    transformed_data["modified_on"] = self.modified_on
                    dicts.append(transformed_data)
                write_if_updated(dicts, file_dir)
            else:
                raise TypeError

    def load(self, sql_insert: str, cursor):
        for entry in os.scandir(os.path.join(self.transform_dir, self.folder)):
            if not entry.name.endswith(".json"):
                continue
            with open(entry.path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                val = tuple(list(data.values()))
                cursor.execute(sql_insert, val)
            elif isinstance(data, list):
                for d in data:
                    val = tuple(list(d.values()))
                    cursor.execute(sql_insert, val)
            else:
                raise TypeError
