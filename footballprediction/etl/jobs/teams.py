import json
import mysql.connector
from tqdm import tqdm
from typing import Optional
from footballprediction.etl.pipeline import Pipeline
from footballprediction.etl.source.footystats import FootyStats


def transform(team):
    return team


def main(years: Optional[int] = 0):
    keys = ["id", "name", "cleanName", "country", "competition_id"]

    with open("credentials/footystats.json") as f:
        key = json.load(f)["key"]
    fs = FootyStats(key)
    season_ids = fs.chosen_season_id(years)

    sql_create = open("sql/footystats/tables/teams/create.sql").read()
    sql_insert = open("sql/footystats/tables/teams/insert.sql").read()

    conn = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="footystats"
    )
    conn.cursor().execute(sql_create)

    pbar = tqdm(season_ids)
    pbar.set_description("Ingesting team data")

    for season_id in pbar:
        p = Pipeline(season_id, "teams", initial=years is None)
        p.extract(fs.teams, season_id)
        p.transform(transform, keys)
        p.load(sql_insert, conn)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
