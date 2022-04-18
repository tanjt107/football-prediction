import mysql.connector
import random
from footballprediction.etl import pipeline

a = round(random.random(), 2)
b = round(random.random(), 2)
c = round(random.random(), 2)
keys = ["index", "value", "transformed"]


class MockAPI:
    def dict(self):
        return {"index": 1, "value": a, "transformed": False}

    def list_of_dicts(self):
        return [
            {"index": 2, "value": b, "transformed": False},
            {"index": 3, "value": c, "transformed": False},
        ]


def transform_mock(dict):
    dict["transformed"] = True
    return dict


def test_etl_list():
    data = pipeline.extract(MockAPI().dict)
    assert data == {"index": 1, "value": a, "transformed": False}

    data = pipeline.transform(data, transform_mock, keys)
    assert data == {"index": 1, "value": a, "transformed": True}

    con = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="test"
    )
    cursor = con.cursor()
    sql_create = open("tests/sql/create.sql").read()
    sql_insert = open("tests/sql/insert.sql").read()
    cursor.execute(sql_create)

    pipeline.load(data, sql_insert, con)
    con.commit()

    cursor.execute("SELECT num FROM test WHERE idx = 1")
    assert cursor.fetchone() == (a,)

    con.close()


def test_etl_list_of_dicts():
    data = pipeline.extract(MockAPI().list_of_dicts)
    assert data == [
        {"index": 2, "value": b, "transformed": False},
        {"index": 3, "value": c, "transformed": False},
    ]

    data = pipeline.transform(data, transform_mock, keys)
    assert data == [
        {"index": 2, "value": b, "transformed": True},
        {"index": 3, "value": c, "transformed": True},
    ]

    con = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="test"
    )
    cursor = con.cursor()
    sql_create = open("tests/sql/create.sql").read()
    sql_insert = open("tests/sql/insert.sql").read()
    cursor.execute(sql_create)

    pipeline.load(data, sql_insert, con)
    con.commit()
    cursor.execute("SELECT num FROM test WHERE idx IN (2, 3)")
    assert cursor.fetchall() in [[(b,), (c,)], [(c,), (b,)]]

    con.close()
