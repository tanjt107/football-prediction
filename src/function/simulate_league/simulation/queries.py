from gcp import bigquery
from simulation.models import Team


def get_last_run(league: str) -> int:
    return bigquery.query_dict(
        query="SELECT * FROM `simulation.get_last_run`(@league);",
        params={"league": league},
    )[0]["last_run"]


def get_latest_match_date(league: str) -> int:
    return bigquery.query_dict(
        query="SELECT * FROM `simulation.get_latest_match_date`(@league);",
        params={"league": league},
    )[0]["max_date_unix"]


def get_avg_goal_home_adv(league: str) -> tuple[float]:
    return bigquery.query_dict(
        query="SELECT * FROM `simulation.get_avg_goal_home_adv`(@league);",
        params={"league": league},
    )[0]


def get_teams(league: str) -> dict[str, Team]:
    return {
        team["name"]: Team(**team)
        for team in bigquery.query_dict(
            query="SELECT * FROM `simulation.get_teams`(@league);",
            params={"league": league},
        )
    }


def get_completed_matches(league: str) -> dict[tuple[int], tuple[int]]:
    return {
        (row["homeId"], row["awayId"]): (row["homeGoalCount"], row["awayGoalCount"])
        for row in bigquery.query_dict(
            query="SELECT * FROM `simulation.get_matches`(@league);",
            params={"league": league},
        )
    }
