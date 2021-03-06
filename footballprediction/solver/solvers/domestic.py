import mysql.connector
import pandas as pd
import pathlib
from tqdm import tqdm
from footballprediction.solver.solver import SolverSeason


def main():
    conn = mysql.connector.connect(user="root", password="password", host="127.0.0.1")
    cursor = conn.cursor()

    sql_create = pathlib.Path("sql/solver/tables/domestic/create.sql").read_text()
    sql_insert = pathlib.Path("sql/solver/tables/domestic/insert.sql").read_text()
    cursor.execute(sql_create)

    sql = "SELECT DISTINCT season_id, last_date_unix FROM footystats.inter_league_map WHERE modified_date >= (SELECT MIN(modified_date) FROM solver.inter_league)"
    cursor.execute(sql)

    sql = pathlib.Path("sql/matches/domestic.sql").read_text()
    pbar = tqdm(cursor.fetchall())
    pbar.set_description("Solving domestic season")
    for season_id, last_date_unix in pbar:
        df = pd.read_sql(
            sql, conn, params={"season_id": season_id, "last_date_unix": last_date_unix}
        )
        for team, offence, defence in SolverSeason(df, max=3).results[1]:
            val = (
                int(season_id),
                int(last_date_unix),
                int(team),
                float(offence),
                float(defence),
            )
            cursor.execute(sql_insert, val)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
