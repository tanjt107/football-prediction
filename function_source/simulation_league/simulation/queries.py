from gcp import bigquery
from simulation.models import Team


def get_last_run(league: str, country: str) -> int:
    query = """
    SELECT MAX(date_unix) AS last_run
    FROM `simulation.run_log`
    WHERE league = @league
        AND country = @country"""
    params = {"league": league, "country": country}
    return bigquery.query_dict(query, params)[0]["last_run"]


def get_latest_match_date(league: str, country: str) -> int:
    sql = """
    SELECT
        MAX(date_unix) AS max_date_unix
    FROM `footystats.matches` matches
    JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
    WHERE matches.status = 'complete'
        AND seasons.name = @league
        AND seasons.country = @country
    """
    params = {"league": league, "country": country}
    return bigquery.query_dict(sql, params)[0]["max_date_unix"]


def get_avg_goal_home_adv(league: str, country: str) -> tuple[float]:
    query = """
    SELECT
        avg_goal,
        home_adv
    FROM solver.leagues solver
    JOIN master.leagues master ON solver.division = master.division
    WHERE footystats_name = @league
        AND country = @country
    """
    return bigquery.query_dict(query, params={"league": league, "country": country})[0]


def get_teams(league: str, country: str) -> dict[str, Team]:
    query = """
    SELECT
        footystats.id AS name,
        offence,
        defence
    FROM master.leagues master_leagues
    JOIN footystats.teams footystats ON master_leagues.latest_season_id = footystats.competition_id
    JOIN master.teams master_teams ON footystats.id = master_teams.footystats_id
    JOIN solver.teams solver ON master_teams.solver_id = solver.id
    WHERE master_leagues.footystats_name = @league
        AND master_leagues.country = @country
    """
    return {
        team["name"]: Team(**team)
        for team in bigquery.query_dict(
            query, params={"league": league, "country": country}
        )
    }


def get_completed_matches(league: str, country: str) -> dict[tuple[int], tuple[int]]:
    query = """
    SELECT
        homeId,
        awayId,
        homeGoalCount,
        awayGoalCount
    FROM footystats.matches
    JOIN master.leagues ON matches.competition_id = leagues.latest_season_id
    WHERE status = 'complete'
        AND footystats_name = @league
        AND country = @country
    """
    return {
        (row["homeId"], row["awayId"]): (row["homeGoalCount"], row["awayGoalCount"])
        for row in bigquery.query_dict(
            query, params={"league": league, "country": country}
        )
    }


def insert_run_log(league: str, country: str, date_unix: int):
    query = "INSERT INTO simulation.run_log VALUES (@league, @country, @date_unix)"
    bigquery.query_dict(
        query, params={"league": league, "country": country, "date_unix": date_unix}
    )
