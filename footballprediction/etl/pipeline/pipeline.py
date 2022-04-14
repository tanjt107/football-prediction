import json
import os
from datetime import datetime
from typing import Callable, Optional

DATA_DIR = "data"
SOURCE_DIR = os.path.join(DATA_DIR, "incoming")
INTEGRATION_DIR = os.path.join(DATA_DIR, "completed")
NOW = datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def is_updated(data1: dict, path2: str) -> bool:
    """
    Compare the contents of data1 and path2. Return True if they are not equal.

    Parameters
    ----------
    data1 : dict
        The first dictionary to be compared.
    path2 : str
        The path of the second file to be compared.

    Returns
    -------
    bool
        #TODO
        True if the contents of data1 and path2 are not equal.
    """
    if not os.path.exists(path2):
        return True
    with open(path2) as f:
        data2 = json.load(f)
    if type(data1) != type(data2):
        return True
    if isinstance(data1, dict):
        data1.pop("modified_on", None)
        data2.pop("modified_on", None)
    elif isinstance(data1, list):
        for data in [data1, data2]:
            for d in data:
                d.pop("modified_on", None)
    return data1 != data2


class Pipeline:
    def __init__(
        self,
        basename: str,
        dir: str,
        source_root_dir: str = SOURCE_DIR,
        integration_root_dir: str = INTEGRATION_DIR,
        write_if_no_update: bool = False,
    ):
        self.basename = basename
        self.dir = dir
        self.source_dir = os.path.join(source_root_dir, dir, f"{basename}.json")
        self.integration_dir = os.path.join(
            integration_root_dir, dir, f"{basename}.json"
        )
        if write_if_no_update:
            self.write_to_source = True
            self.write_to_integration = True
        else:
            self.write_to_source = False
            self.write_to_integration = False

    def extract(self, endpoint: Callable, *args, **kwargs):
        data = endpoint(*args, **kwargs)
        if is_updated(data, self.source_dir):
            self.write_to_source = True
        if not self.write_to_source:
            return
        with open(self.source_dir, "w") as f:
            json.dump(data, f, indent=4)

    def transform(self, func: Optional[Callable] = None):
        if not self.write_to_source:
            return

        with open(self.source_dir) as f:
            data = json.load(f)

        if isinstance(data, dict):
            if func:
                transformed_data = func(data)
            transformed_data["modified_on"] = NOW
        elif isinstance(data, list):
            for d in data:
                if func:
                    d = func(d)
                d["modified_on"] = NOW
        else:
            raise TypeError
        if is_updated(transformed_data, self.integration_dir):
            self.write_to_integration = True
        if not self.write_to_integration:
            return
        with open(self.integration_dir, "w") as f:
            json.dump(transformed_data, f, indent=4)

    def load(self, sql: str, cursor):
        if not self.write_to_integration:
            return
        with open(self.integration_dir) as f:
            data = json.load(f)
        if isinstance(data, dict):
            sql = sql.format(**data)
            cursor.execute(sql)
        elif isinstance(data, list):
            for d in data:
                sql = sql.format(**d)
                cursor.execute(sql)
        else:
            raise TypeError
