import mysql.connector
import pathlib
from tqdm import tqdm
from common.pipeline import Pipeline, filter_dict_keys
from common.source import FootyStats


def transform(data):
    keys = ["id", "name", "cleanName", "country", "competition_id"]
    return filter_dict_keys(data, keys)


def teams():
    sql_create = pathlib.Path("sql/teams_create.sql").read_text()
    sql_insert = pathlib.Path("sql/teams_insert.sql").read_text()

    pipeline = Pipeline("teams")

    db = mysql.connector.connect(
        host="127.0.0.1", user="root", password="password", database="footystats"
    )
    cursor = db.cursor()

    fs = FootyStats()
    season_ids = fs.league_id_list_filtered()
    cursor.execute(sql_create)
    for season_id in (pbar := tqdm(season_ids)):
        pbar.set_description(pipeline.folder)
        pipeline.extract(fs.teams, season_id)
    pipeline.transform(transform)
    pipeline.load(sql_insert, cursor)

    db.commit()
    db.close()


if __name__ == "__main__":
    teams()
