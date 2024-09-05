from collections import defaultdict

from gcp import bigquery
from simulation.models import Team, Match


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


def get_completed_matches(
    league: str, stage: str = "ko", gs_name: str = "Group Stage"
) -> dict[tuple[int], tuple[int]]:
    return {
        (row["homeId"], row["awayId"]): (row["homeGoalCount"], row["awayGoalCount"])
        for row in bigquery.query_dict(
            query=f"SELECT * FROM `simulation.get_{stage}_matches`(@league, @stage);",
            params={"league": league, "stage": gs_name},
        )
    }


def get_groups(league: str, teams: dict[str, Team]) -> dict[str, list[Team]]:
    rounds = defaultdict(lambda: defaultdict(list))
    rows = bigquery.query_dict(
        query="SELECT * FROM `simulation.get_groups`(@league);",
        params={"league": league},
    )
    for row in rows:
        rounds[row["round"]][row["name"]].append(teams[row["id"]])
    return rounds


def get_matches(league: str, teams: dict[str, Team]) -> dict[str, Match]:
    rounds = defaultdict(list)
    for row in bigquery.query_dict(
        query="SELECT * FROM `simulation.get_matches`(@league);",
        params={"league": league},
    ):
        rounds[row["round"]].append(
            Match(
                home_team=teams[row["homeId"]],
                away_team=teams[row["awayId"]],
                status=row["status"],
                home_score=row["homeGoalCount"],
                away_score=row["awayGoalCount"],
            )
        )
    return rounds
