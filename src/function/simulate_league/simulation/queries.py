from collections import defaultdict

from gcp import bigquery
from simulation.models import Round, Team, Match


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


def get_groups(
    league: str, teams: dict[str, Team], gs_name: str = "Group Stage"
) -> dict[str, list[Team]]:
    groups = defaultdict(list)
    group_teams = bigquery.query_dict(
        query="SELECT * FROM `simulation.get_groups`(@league, @stage);",
        params={"league": league, "stage": gs_name},
    )
    for group_team in group_teams:
        groups[group_team["name"]].append(teams[group_team["id"]])
    return groups


def get_matchup(league: str, teams: dict[str, Team]) -> dict[Round, set[set[Team]]]:
    rounds = defaultdict(set)
    round_matchups = bigquery.query_dict(
        query="SELECT * FROM `simulation.get_matchups`(@league);",
        params={"league": league},
    )
    for round_matchup in round_matchups:
        _round = round_matchup["round"].upper().replace("-", "_").replace(" ", "_")
        if _round in Round.__members__:
            rounds[Round[_round]].add(
                frozenset(
                    {teams[round_matchup["homeID"]], teams[round_matchup["awayID"]]}
                )
            )
    return rounds


def get_matches(league: str, teams: dict[str, Team]) -> dict[str, Match]:
    rounds = defaultdict(list)
    query = """
SELECT
    specific_tables.round,
    homeId,
    awayId,
    status,
    homeGoalCount,
    awayGoalCount
FROM footystats.matches
JOIN master.leagues ON matches._SEASON_ID = leagues.latest_season_id
JOIN footystats.tables USING (_SEASON_ID)
JOIN tables.specific_tables ON matches.roundID = specific_tables.round_id
WHERE matches._NAME = @league;
"""
    for row in bigquery.query_dict(
        query,
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
