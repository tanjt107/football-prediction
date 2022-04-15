import json
import mysql.connector
import random
from footballprediction.etl.pipeline import is_updated, Pipeline

a = round(random.random(), 2)
b = round(random.random(), 2)


class MockAPI:
    def dict(self):
        return {"status": 200, "value": a, "transformed": False}

    def list_of_dicts(self):
        return [
            {"status": 200, "value": a, "transformed": False},
            {"status": 200, "value": b, "transformed": False},
        ]


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


def test_pipeline_list():
    p = Pipeline("mockapi", "mockapi", "tests/data/incoming", "tests/data/completed")

    p.extract(MockAPI().dict)
    with open("tests/data/incoming/mockapi/mockapi.json") as f:
        data = json.load(f)
    assert data == {"status": 200, "value": a, "transformed": False}

    p.transform(transform_mock, ["status", "value", "transformed"])
    with open("tests/data/completed/mockapi/mockapi.json") as f:
        data = json.load(f)
    data.pop("modified_on")
    assert data == {"status": 200, "value": a, "transformed": True}

    con = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="test"
    )
    cursor = con.cursor()
    sql_create = open("tests/sql/create.sql").read()
    sql_insert = open("tests/sql/insert.sql").read()
    cursor.execute(sql_create)

    p.load(sql_insert, con)
    con.commit()

    cursor.execute("SELECT num FROM test ORDER BY modified_on DESC LIMIT 1")
    assert cursor.fetchone() == (a,)
    con.close()


def test_pipeline_list_of_dicts():
    p = Pipeline("mockapi", "mockapi", "tests/data/incoming", "tests/data/completed")

    p.extract(MockAPI().list_of_dicts)
    with open("tests/data/incoming/mockapi/mockapi.json") as f:
        data = json.load(f)
    assert data == [
        {"status": 200, "value": a, "transformed": False},
        {"status": 200, "value": b, "transformed": False},
    ]

    p.transform(transform_mock, ["status", "value", "transformed"])
    with open("tests/data/completed/mockapi/mockapi.json") as f:
        data = json.load(f)
    for d in data:
        d.pop("modified_on")
    assert data == [
        {"status": 200, "value": a, "transformed": True},
        {"status": 200, "value": b, "transformed": True},
    ]

    con = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="test"
    )
    cursor = con.cursor()
    sql_create = open("tests/sql/create.sql").read()
    sql_insert = open("tests/sql/insert.sql").read()
    cursor.execute(sql_create)

    p.load(sql_insert, con)
    con.commit()

    cursor.execute("SELECT num FROM test ORDER BY modified_on DESC LIMIT 2")
    assert cursor.fetchall() in [[(a,), (b,)], [(b,), (a,)]]
    con.close()
