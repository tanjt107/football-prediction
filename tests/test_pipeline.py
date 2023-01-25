import aiohttp
import pytest
import sqlite3
from footballprediction.pipeline import extract, load


@pytest.fixture
def data():
    return [
        {"name": "C", "year": 1972},
        {"name": "Fortran", "year": 1957},
        {"name": "Python", "year": 1991},
        {"name": "Go", "year": 2009},
    ]


@pytest.fixture
def insert_sql():
    return "INSERT INTO lang VALUES(:name, :year)"


@pytest.fixture
def create_sql():
    return "CREATE TABLE IF NOT EXISTS lang(name, first_appeared)"


@pytest.mark.asyncio
async def test_extract():
    async with aiohttp.ClientSession() as session:
        response = await extract(
            "https://api.football-data-api.com/league-list", session, {"key": "example"}
        )
        assert response["success"]


def test_load(data, insert_sql, create_sql):
    with sqlite3.connect(":memory:") as con:
        load(data, con, insert_sql, create_sql)
        cur = con.cursor()
        cur.execute("SELECT * FROM lang WHERE first_appeared = ?", (1972,))
        result = cur.fetchall()
        assert result == [("C", 1972)]


def test_load_without_create(data, insert_sql, create_sql):
    with sqlite3.connect(":memory:") as con:
        cur = con.cursor()
        cur.execute(create_sql)
        load(data, con, insert_sql)
        cur.execute("SELECT * FROM lang WHERE first_appeared = ?", (1972,))
        result = cur.fetchall()
        assert result == [("C", 1972)]
