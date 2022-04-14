import json
import random
from footballprediction.etl.pipeline import is_updated, Pipeline

N = random.random()


class MockAPI:
    def call(self):
        return {"status": 200, "number": N, "transformed": False}


def transform_mock(dict):
    dict["transformed"] = True
    return dict


def test_compare_equal():
    data = {
        "brand": "Ford",
        "model": "Mustang",
        "year": 1964,
        "modified_on": "2022-02-01 00:00:00",
    }
    return is_updated(data, "tests/data/test.json")


def test_compare_not_equal():
    data = {
        "brand": "Ford",
        "model": "Mustang",
        "year": 2020,
        "modified_on": "2022-01-01 00:00:00",
    }
    return is_updated(data, "tests/data/test.json")


def test_pipeline_no_update():
    p = Pipeline("mockapi", "mockapi", "tests/data/incoming", "tests/data/completed")
    p.extract(MockAPI().call)
    with open("tests/data/incoming/mockapi/mockapi.json") as f:
        data = json.load(f)
    assert data == {"status": 200, "number": N, "transformed": False}
    p.transform(transform_mock)
    with open("tests/data/completed/mockapi/mockapi.json") as f:
        data = json.load(f)
    assert data == {"status": 200, "number": N, "transformed": True}
