import mysql.connector
import pathlib
from tqdm import tqdm
from common.pipeline import Pipeline, filter_dict_keys
from common.source import FootyStats


def transform(data):
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
    ]
    return filter_dict_keys(data, keys)


def league():
    sql_create = pathlib.Path("sql/league_create.sql").read_text()
    sql_insert = pathlib.Path("sql/league_insert.sql").read_text()

    pipeline = Pipeline("league")

    db = mysql.connector.connect(
        host="127.0.0.1", user="root", password="password", database="footystats"
    )
    cursor = db.cursor()

    fs = FootyStats()
    season_ids = fs.league_id_list_filtered()
    cursor.execute(sql_create)
    for season_id in (pbar := tqdm(season_ids)):
        pbar.set_description(pipeline.folder)
        pipeline.extract(fs.season, season_id)
    pipeline.transform(transform)
    pipeline.load(sql_insert, cursor)

    db.commit()
    db.close()


if __name__ == "__main__":
    league()
