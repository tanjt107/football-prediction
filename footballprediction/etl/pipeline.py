import copy
import json
import os
from datetime import datetime
from typing import Callable

DATA_DIR = "data"
SOURCE_DIR = os.path.join(DATA_DIR, "source")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NOW = datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def is_updated(data1: dict, path2: str) -> bool:
    """
    Compare data 1 and contents of path2. Return True if they are not equal.

    Parameters
    ----------
    data1 : dict
        First dictionary to be compared.
    path2 : str
        Path of second file to be compared.

    Returns
    -------
    bool
        True if contents of data1 and path2 are not equal.
    """
    _data1 = copy.deepcopy(data1)
    if not os.path.exists(path2):
        return True
    with open(path2) as f:
        data2 = json.load(f)
    if type(_data1) != type(data2):
        return True
    if isinstance(_data1, dict):
        _data1.pop("modified_on", None)
        data2.pop("modified_on", None)
    elif isinstance(_data1, list):
        for data in [_data1, data2]:
            for d in data:
                d.pop("modified_on", None)
    return _data1 != data2


class Pipeline:
    """
    Parameters
    ----------
    basename : str
        Name of file to be created, withou suffix.
    dir : str
        Directory containing data.
    source_root_dir : str
        Root directory containing all source data.
    staging_root_dir : str
        Root directory containing all staging data.
    initial : bool
        Initial load. If True, all data in database will be replaced.
    """

    def __init__(
        self,
        basename: str,
        dir: str,
        source_root_dir: str = SOURCE_DIR,
        staging_root_dir: str = STAGING_DIR,
        initial: bool = False,
    ):
        self.basename = basename
        self.dir = dir
        self.source_dir = os.path.join(source_root_dir, dir, f"{basename}.json")
        self.staging_dir = os.path.join(staging_root_dir, dir, f"{basename}.json")
        if initial:
            self.write_to_source = True
            self.write_to_db = True
        else:
            self.write_to_source = False
            self.write_to_db = False

    def extract(self, endpoint: Callable, *args, **kwargs):
        """
        Copy raw data to source directory.

        Parameters
        ----------
        endpoint : Callable
            API endpoint to be called.
        args
        kwargs
        """
        data = endpoint(*args, **kwargs)
        if is_updated(data, self.source_dir):
            self.write_to_source = True
        if not self.write_to_source:
            return
        with open(self.source_dir, "w") as f:
            json.dump(data, f, indent=4)

    def transform(self, func: Callable[[dict], dict], keys: list):
        """
        Transform data for intended use case.

        Parameters
        ----------
        func : Callable
            Function to apply to each dictionary.
        keys : list
            List of dictionary keys to keep.
        """
        if not self.write_to_source:
            return

        with open(self.source_dir) as f:
            data = json.load(f)

        if isinstance(data, dict):
            transformed_data = func(data)
            transformed_data = {k: v for k, v in transformed_data.items() if k in keys}
            transformed_data["modified_on"] = NOW
        elif isinstance(data, list):
            transformed_data = []
            for d in data:
                d = func(d)
                d = {k: v for k, v in d.items() if k in keys}
                d["modified_on"] = NOW
                transformed_data.append(d)
        else:
            raise TypeError

        if is_updated(transformed_data, self.staging_dir):
            self.write_to_db = True
            with open(self.staging_dir, "w") as f:
                json.dump(transformed_data, f, indent=4)

    def load(self, sql: str, con):
        """
        Move transformed data from staging directory into a database.

        Parameters
        ----------
        sql : str
            SQL INSERT INTO statement.
        con :
            Database connection.
        """
        if not self.write_to_db:
            return
        cursor = con.cursor()
        with open(self.staging_dir) as f:
            data = json.load(f)

        if isinstance(data, dict):
            sql = sql
            val = tuple(data.values())
            cursor.execute(sql, val)
        elif isinstance(data, list):
            for d in data:
                sql = sql
                val = tuple(d.values())
                cursor.execute(sql, val)
        else:
            raise TypeError
