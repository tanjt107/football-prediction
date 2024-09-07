from solver.models import League, Match, Team
from gcp import bigquery


def get_matches_and_teams(_type: str, max_time: int) -> dict:
    data = bigquery.query_dict(
        query="SELECT * FROM `solver.get_matches`(@type, @max_time);",
        params={"type": _type, "max_time": max_time},
    )
    league_names = {match["league_name"] for match in data}
    leagues = {name: League(name) for name in league_names}
    team_ids = {(match["home_id"], match["home_team_in_rating"]) for match in data} | {
        (match["away_id"], match["away_team_in_rating"]) for match in data
    }
    teams = {
        id: Team(id, in_solver_constraints=in_team_rating)
        for id, in_team_rating in team_ids
    }
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
