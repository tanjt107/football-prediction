import aiohttp
import asyncio
import sqlite3
from dotenv import dotenv_values
from footballprediction import footystats, solver, util


async def main(load_years=None):
    key = dotenv_values()["FOOTYSTATS_API_KEY"]
    params: list[dict] = [
        {
            "endpoint": "matches",
            "transform_func": footystats.transform_matches,
        },
        {"endpoint": "season"},
        {"endpoint": "teams"},
    ]

    session = aiohttp.ClientSession()
    con: sqlite3.Connection = sqlite3.connect("footystats.db")

    try:
        league_list = await footystats.get_league_list(key, session)
        season_ids = footystats.filter_season_id(league_list, load_years)
        for param in params:
            await footystats.etl(
                param["endpoint"],
                season_ids,
                transform_func=param.get("transform_func"),
                insert_sql=util.read_file(f"sql/insert_{param['endpoint']}.sql"),
                create_sql=util.read_file(f"sql/create_{param['endpoint']}.sql"),
                key=key,
                session=session,
                con=con,
            )
        matches = footystats.get_match_details(con)
        factors = solver.solver(matches)
        print(factors)
    finally:
        con.close()
        await session.close()


if __name__ == "__main__":
    asyncio.run(main(load_years=None))
