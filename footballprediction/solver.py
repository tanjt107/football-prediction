from pulp import LpMinimize, LpProblem, lpSum, LpVariable
from typing import Any


def solver(matches: list[dict[str, Any]]) -> dict[str, list[dict[str, float]]]:
    """
    Solver for expected goals.

    Parameters:
        matches: A list of match detail dictionaries, with keys of match id (`id`),
        league name (`league_name`), home team id (`home_id`), away team id (`away_id`),
        home score (`home_avg`), away score (`away_avg`), recentness factor (`recent`).

    Returns:
        A dictionary containing average goals (`avg_goal`) and home advantage
        factor (`home_adv`) of leagues and offence (`offence`) and defence (`defence`)
        factors of teams.
    """
    prob = LpProblem(sense=LpMinimize)

    # Lists to contain all leagues, teams and match ids
    leagues = list({match["league_name"] for match in matches})
    teams = list(
        {match["home_id"] for match in matches}
        | {match["away_id"] for match in matches}
    )
    ids = [match["id"] for match in matches]

    # Dictionaries to contain all variables
    avg_goals = LpVariable.dicts("Avg_goal", leagues, lowBound=0)
    home_advs = LpVariable.dict("Home_adv", leagues, lowBound=0)
    offences = LpVariable.dicts("Offence", teams)
    defences = LpVariable.dicts("Defence", teams)
    home_errors = LpVariable.dicts("Home_error", ids)
    away_errors = LpVariable.dicts("Away_error", ids)

    for match in matches:
        home_error = (
            avg_goals[match["league_name"]]
            + home_advs[match["league_name"]] * int(not match["no_home_away"])
            + offences[match["home_id"]]
            + defences[match["away_id"]]
            - float(match["home_adj"])
        ) * float(match["recent"])
        away_error = (
            avg_goals[match["league_name"]]
            - home_advs[match["league_name"]] * int(not match["no_home_away"])
            + offences[match["away_id"]]
            + defences[match["home_id"]]
            - float(match["away_adj"])
        ) * float(match["recent"])

        # Constraints for absolute values
        prob += home_errors[match["id"]] >= home_error
        prob += home_errors[match["id"]] >= -home_error
        prob += away_errors[match["id"]] >= away_error
        prob += away_errors[match["id"]] >= -away_error

    # Objective function
    prob += lpSum(home_errors) + lpSum(away_errors)

    # Other constraints
    prob += lpSum(offences) == 0
    prob += lpSum(defences) == 0

    prob.solve()

    return {
        "league": [
            {
                "league": league,
                "avg_goal": avg_goals[league].varValue,
                "home_adv": home_advs[league].varValue,
            }
            for league in leagues
        ],
        "teams": [
            {
                "team": team,
                "offence": offences[team].varValue,
                "defence": defences[team].varValue,
            }
            for team in teams
        ],
    }
