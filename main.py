import aiohttp
import asyncio
import sqlite3
from dotenv import dotenv_values
from footballprediction import footystats, pipeline, solver, util


async def main(load_years=None):
    key = dotenv_values()["FOOTYSTATS_API_KEY"]
    endpoints = {
        "matches": footystats.transform_matches,
        "season": None,
        "teams": None,
    }

    session = aiohttp.ClientSession()
    con: sqlite3.Connection = sqlite3.connect("footystats.db")

    try:
        league_list = await footystats.get_league_list(key, session)
        season_ids = footystats.filter_season_id(league_list, load_years)
        for endpoint, transform_func in endpoints.items():
            await footystats.etl(
                endpoint,
                season_ids,
                transform_func=transform_func,
                insert_sql=util.read_file(f"sql/footystats/{endpoint}/insert.sql"),
                create_sql=util.read_file(f"sql/footystats/{endpoint}/create.sql"),
                key=key,
                session=session,
                con=con,
            )

        matches = footystats.get_match_details(con)
        factors = solver.solver(matches)

        for table, variables in factors.items():
            pipeline.load(
                variables,
                insert_sql=util.read_file(f"sql/solver/{table}/insert.sql"),
                create_sql=util.read_file(f"sql/solver/{table}/create.sql"),
                truncate_sql=util.read_file(f"sql/solver/{table}/truncate.sql"),
                con=con,
            )
    finally:
        con.close()
        await session.close()


if __name__ == "__main__":
    asyncio.run(main(0))
