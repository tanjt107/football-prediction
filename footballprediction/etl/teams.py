import mysql.connector
from tqdm import tqdm
from common.pipeline import Pipeline, filter_dict_keys
from common.source import FootyStats


def transform(data):
    keys = ["id", "name", "cleanName", "country", "competition_id"]
    return filter_dict_keys(data, keys)


def teams():
    sql_create = """CREATE TABLE IF NOT EXISTS teams(
	team_id INT NOT NULL,
    team_name VARCHAR(255),
    team_clean_name VARCHAR(255),
    country VARCHAR(255),
    competition_id INT NOT NULL,
    modified_on TIMESTAMP NOT NULL,
    UNIQUE INDEX (team_id, competition_id));"""

    sql_insert = """REPLACE INTO teams(
    team_id,
    team_name,
    team_clean_name,
    country,
    competition_id,
    modified_on)
    VALUES (%s, %s, %s, %s, %s, %s);"""

    pipeline = Pipeline("teams")

    db = mysql.connector.connect(
        host="127.0.0.1", user="root", password="password", database="footystats"
    )
    cursor = db.cursor()

    fs = FootyStats()
    season_ids = fs.league_id_list_filtered()
    cursor.execute(sql_create)
    # for season_id in (pbar := tqdm(season_ids)):
    #     pbar.set_description(pipeline.folder)
    #     pipeline.extract(fs.teams, season_id)
    pipeline.transform(transform)
    pipeline.load(sql_insert, cursor)

    db.commit()
    db.close()


if __name__ == "__main__":
    teams()
