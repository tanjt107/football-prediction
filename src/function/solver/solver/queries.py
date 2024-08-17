from solver.models import League, Match, Team
from gcp import bigquery


def get_last_run(_type: str) -> int:
    if rows := bigquery.query_dict(
        query="""
            SELECT
                COALESCE(MAX(_DATE_UNIX), 0) AS last_run
            FROM `solver.teams` teams
            WHERE _TYPE = @type
            """,
        params={"type": _type},
    ):
        return rows[0]["last_run"]


def get_latest_match_date(_type: str) -> dict[str, League | Match | Team]:
    return bigquery.query_dict(
        query="SELECT * FROM `solver.get_latest_match_date`(@type);",
        params={"type": _type},
    )[0]["max_date_unix"]


def get_matches_and_teams(_type: str, max_time: int) -> dict:
    data = bigquery.query_dict(
        query="SELECT * FROM `solver.get_matches`(@type, @max_time);",
        params={"type": _type, "max_time": max_time},
    )
    league_names = {match["league_name"] for match in data}
    leagues = {name: League(name) for name in league_names}
    team_ids = {(match["home_id"], match["is_home_team_rating"]) for match in data} | {
        (match["away_id"], match["is_away_team_rating"]) for match in data
    }
    teams = {id: Team(id, is_team_rating) for id, is_team_rating in team_ids}
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
