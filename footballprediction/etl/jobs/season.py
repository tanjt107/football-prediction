import json
import mysql.connector
from tqdm import tqdm
from typing import Optional
from footballprediction.etl import pipeline
from footballprediction.etl.source.footystats import FootyStats


def transform(season):
    season["league_name"] = f"{season['country']} {season['name']}"
    return season


def main(years: Optional[int] = None):
    keys = [
        "id",
        "name",
        "country",
        "status",
        "format",
        "division",
        "starting_year",
        "ending_year",
        "clubNum",
        "season",
        "totalMatches",
        "matchesCompleted",
        "canceledMatchesNum",
        "game_week",
        "total_game_week",
        "league_name",
    ]

    with open("credentials/footystats.json") as f:
        key = json.load(f)["key"]
    fs = FootyStats(key)
    season_ids = fs.chosen_season_id(years)

    sql_create = open("sql/footystats/tables/season/create.sql").read()
    sql_insert = open("sql/footystats/tables/season/insert.sql").read()

    conn = mysql.connector.connect(
        user="root", password="password", host="127.0.0.1", database="footystats"
    )
    conn.cursor().execute(sql_create)

    pbar = tqdm(season_ids)
    pbar.set_description("Ingesting season data")

    for season_id in pbar:
        data = pipeline.extract(fs.season, season_id)
        data = pipeline.transform(data, transform, keys)
        pipeline.load(data, sql_insert, conn)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
