from solver.models import League, Match, Team
from gcp import bigquery


def get_last_run(_type: str) -> int:
    query = "SELECT MAX(date_unix) AS last_run FROM `solver.run_log` WHERE type = @type"
    if rows := bigquery.query_dict(
        query=query,
        params={"type": _type},
    ):
        return rows[0]["last_run"]


def get_latest_match_date(_type: str) -> dict[str, League | Match | Team]:
    query = """
    SELECT
        MAX(date_unix) AS max_date_unix
    FROM `footystats.matches` matches
    JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
    JOIN `master.leagues` leagues ON seasons.country = leagues.country
        AND seasons.name = leagues.footystats_name
    WHERE matches.status = 'complete'
        AND leagues.type = @type
    """
    return bigquery.query_dict(query, params={"type": _type})[0]["max_date_unix"]


def get_matches(_type: str, max_time: int) -> dict:
    query = "SELECT * FROM `functions.get_solver_matches`(@type, @max_time);"
    data = bigquery.query_dict(query, params={"type": _type, "max_time": max_time})
    league_names = {match["league_name"] for match in data}
    leagues = {name: League(name) for name in league_names}
    team_ids = {match["home_id"] for match in data} | {
        match["away_id"] for match in data
    }
    teams = {id: Team(id) for id in team_ids}
    return {
        "leagues": leagues.values(),
        "teams": teams.values(),
        "matches": [
            Match(
                id=match["id"],
                league=leagues[match["league_name"]],
                home_team=teams[match["home_id"]],
                away_team=teams[match["away_id"]],
                home_score=match["home_avg"],
                away_score=match["away_avg"],
                recent=match["recent"],
            )
            for match in data
        ],
    }


def insert_run_log(_type: str, date_unix: int):
    query = "INSERT INTO solver.run_log VALUES (@type, @date_unix)"
    bigquery.query_dict(query, params={"type": _type, "date_unix": date_unix})
