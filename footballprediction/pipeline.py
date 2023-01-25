import aiohttp
import sqlite3
from typing import Optional


async def extract(
    url: str, session: aiohttp.ClientSession, params: Optional[dict[str, str]] = None
) -> dict:
    """
    Perform an API get requests and return the response in json asynchronously.

    Parameters:
        url: The request URL.
        session: The aiohttp Client session.
        params: Parameters to send in the request.

    Returns:
        The json-encoded content of a response.
    """
    async with session.get(url, params=params) as response:
        return await response.json()


def load(
    data: list[tuple],
    con: sqlite3.Connection,
    insert_sql: str,
    create_sql: Optional[str] = None,
) -> None:
    """
    Load data into a SQLite database.

    Parameters:
        data: A list of tuple of data.
        con: The SQLite database connection.
        insert_sql_filename: The insert SQL statement.
        create_sql_filename: The create SQL statement.

    Returns:
        None.
    """
    with con as con:
        cur = con.cursor()
        if create_sql:
            cur.execute(create_sql)
        cur.executemany(insert_sql, data)
        con.commit()
