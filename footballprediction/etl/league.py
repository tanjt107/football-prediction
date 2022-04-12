import mysql.connector
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
    sql_create = """CREATE TABLE IF NOT EXISTS seasons (
	id INT PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    status VARCHAR(255),
    format VARCHAR(255),
    division INT,
    starting_year INT,
    ending_year INT,
    club_num INT,
    season VARCHAR(9),
    total_matches INT,
    matches_completed INT,
    canceled_matches_num INT,
    game_week INT,
    total_game_week INT,
    modified_on TIMESTAMP NOT NULL);"""

    sql_insert = """REPLACE seasons(
    id,
    name,
    country,
    status,
    format,
    division,
    starting_year,
    ending_year,
    club_num,
    season,
    total_matches,
    matches_completed,
    canceled_matches_num,
    game_week,
    total_game_week,
    modified_on)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

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
