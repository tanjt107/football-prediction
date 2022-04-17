import mysql.connector
import pandas as pd
import pathlib
from datetime import datetime
from footballprediction.solver.solver import SolverInterLeague

MODIFIED_ON = datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def main():
    conn = mysql.connector.connect(user="root", password="password", host="127.0.0.1")
    cursor = conn.cursor()

    sql_create_inter_league = pathlib.Path(
        "sql/solver/tables/inter_league/create.sql"
    ).read_text()
    sql_insert_inter_league = pathlib.Path(
        "sql/solver/tables/inter_league/insert.sql"
    ).read_text()
    sql_create_factors = pathlib.Path(
        "sql/solver/tables/factors/create.sql"
    ).read_text()
    sql_insert_factors = pathlib.Path(
        "sql/solver/tables/factors/insert.sql"
    ).read_text()
    cursor.execute(sql_create_factors)
    cursor.execute(sql_create_inter_league)

    sql = pathlib.Path("sql/matches/inter_league.sql").read_text()
    df = pd.read_sql(sql, conn)
    print("Solving inter-league season")
    (avg_goal, home_adv), league_strengths = SolverInterLeague(df).results

    vals = (-1, float(avg_goal), float(home_adv), MODIFIED_ON)
    cursor.execute(sql_insert_factors, vals)

    cursor.execute("TRUNCATE solver.inter_league")
    for league, strength in league_strengths:
        vals = (
            league,
            float(strength),
            MODIFIED_ON,
        )
        cursor.execute(sql_insert_inter_league, vals)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
