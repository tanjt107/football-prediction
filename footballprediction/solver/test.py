import mysql.connector
import pandas as pd
import pathlib
from datetime import datetime
from solver import SolverSeason
from tqdm import tqdm

MODIFIED_ON = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

db = mysql.connector.connect(host="127.0.0.1", user="root", password="password")
cursor = db.cursor()

sql_create = pathlib.Path("sql/solver_domestic_create.sql").read_text()
sql_insert = pathlib.Path("sql/solver_domestic_insert.sql").read_text()
cursor.execute(sql_create)

sql = "SELECT * FROM footystats.solver_param"
cursor.execute(sql)

for season_id, last_date_unix in tqdm(cursor.fetchall()):
    sql = (
        pathlib.Path("sql/get_hist_matches.sql")
        .read_text()
        .format(season_id=season_id, last_date_unix=last_date_unix)
    )
    df = pd.read_sql(sql, db)
    for team, offence, defence in SolverSeason(df).result[1]:
        val = (
            int(season_id),
            int(last_date_unix),
            int(team),
            float(offence),
            float(defence),
            MODIFIED_ON,
        )
        cursor.execute(sql_insert, val)
    db.commit()

db.close()
