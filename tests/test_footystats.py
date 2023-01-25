import aiohttp
import pytest
import sqlite3
from dotenv import dotenv_values
from footballprediction import footystats
from footballprediction.util import read_file


@pytest.mark.asyncio
async def test_get_league_list():
    async with aiohttp.ClientSession() as session:
        league_list = await footystats.get_league_list(
            dotenv_values()["FOOTYSTATS_API_KEY"], session
        )
        assert 0 < len(league_list) < 150


def test_filter_season_id_fall_to_spring():
    league_list = [
        {
            "name": "England Premier League",
            "season": [
                {"id": 1625, "year": 20172018},
                {"id": 2012, "year": 20182019},
                {"id": 4759, "year": 20192020},
            ],
        }
    ]
    assert footystats.filter_season_id(league_list, 1, 2020) == [2012, 4759]


def test_filter_season_id_spring_to_fall():
    league_list = [
        {
            "name": "England Premier League",
            "season": [
                {"id": 1625, "year": 2018},
                {"id": 2012, "year": 2019},
                {"id": 4759, "year": 2020},
            ],
        }
    ]
    assert footystats.filter_season_id(league_list, 0, 2020) == [4759]


@pytest.mark.asyncio
async def test_get_season_data():
    async with aiohttp.ClientSession() as session:
        data = await footystats.get_season_data("matches", 2012, "example", session)
    assert len(data) == 380


def test_get_goal_timings_dict():
    assert footystats.get_goal_timings_dict(
        ["24", "32", "37", "65", "80"], ["45", "56", "73"]
    ) == [
        (24, "home"),
        (32, "home"),
        (37, "home"),
        (45, "away"),
        (56, "away"),
        (65, "home"),
        (73, "away"),
        (80, "home"),
    ]


def test_get_goal_timings_dict_nil():
    assert footystats.get_goal_timings_dict([], []) == []


def test_get_goal_timings_dict_plus():
    assert footystats.get_goal_timings_dict(["90+3"], ["60"]) == [
        (60, "away"),
        (90, "home"),
    ]


def test_get_goal_timings_dict_zero():
    assert footystats.get_goal_timings_dict(["84"], ["73", "9006"]) == [
        (73, "away"),
        (84, "home"),
        (90, "away"),
    ]


def test_get_goal_timings_ot():
    assert footystats.get_goal_timings_dict(["39", "48"], ["13", "45+1", "101"]) == [
        (13, "away"),
        (39, "home"),
        (45, "away"),
        (48, "home"),
        (101, "away"),
    ]


def test_reduce_goal_value_zero():
    assert footystats.reduce_goal_value([]) == (0, 0)


def test_reduce_goal_value():
    assert footystats.reduce_goal_value(
        [(7, "home"), (19, "home"), (28, "home"), (42, "home"), (64, "away")]
    ) == (4, 1)


def test_reduce_goal_value_70():
    assert footystats.reduce_goal_value([(63, "home"), (70, "home")]) == (2, 0)


def test_reduce_goal_value_80():
    assert footystats.reduce_goal_value(
        [(28, "away"), (65, "away"), (80, "away"), (90, "home")]
    ) == (
        1,
        2.75,
    )


def test_reduce_goal_value_90():
    assert footystats.reduce_goal_value(
        [(18, "home"), (65, "home"), (67, "home"), (90, "home")]
    ) == (
        3.5,
        0,
    )


def test_reduce_goal_value_80_90():
    assert footystats.reduce_goal_value(
        [(20, "home"), (59, "away"), (60, "away"), (80, "away"), (90, "away")]
    ) == (1, 3.25)


def test_reduce_goal_value_ot():
    assert footystats.reduce_goal_value(
        [(78, "home"), (90, "away"), (96, "away"), (105, "away"), (120, "away")]
    ) == (1, 3)


@pytest.mark.asyncio
async def test_pipeline_matches():
    session = aiohttp.ClientSession()
    con = sqlite3.connect(":memory:")
    try:
        await footystats.etl(
            "matches",
            [1625, 2012, 4759],
            transform_func=footystats.transform_matches,
            insert_sql=read_file("sql/insert_matches.sql"),
            create_sql=read_file("sql/create_matches.sql"),
            key="example",
            session=session,
            con=con,
        )
        cur = con.cursor()
        cur.execute("SELECT * FROM matches")
        assert len(cur.fetchall()) == 1140
    finally:
        con.close()
        await session.close()


@pytest.mark.asyncio
async def test_pipeline_seasons():
    session = aiohttp.ClientSession()
    con = sqlite3.connect(":memory:")
    try:
        await footystats.etl(
            "season",
            [1625, 2012, 4759],
            insert_sql=read_file("sql/insert_seasons.sql"),
            create_sql=read_file("sql/create_seasons.sql"),
            key="example",
            session=session,
            con=con,
        )
        cur = con.cursor()
        cur.execute("SELECT * FROM seasons")
        assert len(cur.fetchall()) == 3
    finally:
        con.close()
        await session.close()


@pytest.mark.asyncio
async def test_pipeline_teams():
    session = aiohttp.ClientSession()
    con = sqlite3.connect(":memory:")
    try:
        await footystats.etl(
            "teams",
            [1625, 2012, 4759],
            insert_sql=read_file("sql/insert_teams.sql"),
            create_sql=read_file("sql/create_teams.sql"),
            key="example",
            session=session,
            con=con,
        )
        cur = con.cursor()
        cur.execute("SELECT * FROM teams")
        assert len(cur.fetchall()) == 60
    finally:
        con.close()
        await session.close()
