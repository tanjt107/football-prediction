import mysql.connector
import pandas as pd
import pathlib
from tqdm import tqdm
from footballprediction.solver.solver import SolverSeason


def main():
    conn = mysql.connector.connect(user="root", password="password", host="127.0.0.1")
    cursor = conn.cursor()
    sql_create_factors = pathlib.Path(
        "sql/solver/tables/factors/create.sql"
    ).read_text()
    sql_insert_factors = pathlib.Path(
        "sql/solver/tables/factors/insert.sql"
    ).read_text()
    sql_create_final = pathlib.Path("sql/solver/tables/final/create.sql").read_text()
    sql_insert_final = pathlib.Path("sql/solver/tables/final/insert.sql").read_text()
    cursor.execute(sql_create_factors)
    cursor.execute(sql_create_final)

    sql = "SELECT id FROM footystats.latest_season"
    cursor.execute(sql)

    pbar = tqdm(cursor.fetchall())
    pbar.set_description("Solving full season")
    for season_id in pbar:
        season_id = season_id[0]
        sql = pathlib.Path("sql/matches/final.sql").read_text()
        df = pd.read_sql(sql, conn, params={"season_id": season_id})
        sql = f"SELECT team_id FROM footystats.teams WHERE competition_id = {season_id}"
        cursor.execute(sql)
        teams = [t[0] for t in cursor.fetchall()]
        (avg_goal, home_adv), team_factors = SolverSeason(df, teams, max=3).results
        vals = (season_id, float(avg_goal), float(home_adv))
        cursor.execute(sql_insert_factors, vals)
        for team, offence, defence in team_factors:
            val = (season_id, team, float(offence), float(defence))
            cursor.execute(sql_insert_final, val)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
