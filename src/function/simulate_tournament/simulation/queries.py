from collections import defaultdict

from gcp import bigquery

from simulation.models import Team, Match


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


def get_groups(league: str, teams: dict[str, Team]) -> dict[str, list[Team]]:
    rounds = defaultdict(lambda: defaultdict(list))
    rows = bigquery.query_dict(
        query="SELECT * FROM `simulation.get_groups`(@league);",
        params={"league": league},
    )
    for row in rows:
        rounds[row["round"]][row["name"]].append(teams[row["id"]])
    return rounds
