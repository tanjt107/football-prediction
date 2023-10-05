from pulp import LpMinimize, LpProblem, lpSum, LpVariable


def solver(matches: list[dict]) -> dict[str, list[dict[str, float]]]:
    prob = LpProblem(sense=LpMinimize)

    # Lists to contain all leagues, teams and match ids
    leagues = list({match["league_name"] for match in matches})
    teams = list(
        {match["home_id"] for match in matches}
        | {match["away_id"] for match in matches}
    )
    ids = [match["id"] for match in matches]

    # Dictionaries to contain all variables
    avg_goals = LpVariable.dicts("avg_goal", leagues, lowBound=0)
    home_advs = LpVariable.dict("home_adv", leagues, lowBound=0)
    offences = LpVariable.dicts("offence", teams)
    defences = LpVariable.dicts("defence", teams)
    home_errors = LpVariable.dicts("home_error", ids)
    away_errors = LpVariable.dicts("away_error", ids)

    for match in matches:
        home_error = (
            avg_goals[match["league_name"]]
            + home_advs[match["league_name"]]
            + offences[match["home_id"]]
            + defences[match["away_id"]]
            - float(match["home_avg"])
        ) * float(match["recent"])
        away_error = (
            avg_goals[match["league_name"]]
            - home_advs[match["league_name"]]
            + offences[match["away_id"]]
            + defences[match["home_id"]]
            - float(match["away_avg"])
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

    return (
        [
            {
                "division": league,
                "avg_goal": avg_goals[league].varValue,
                "home_adv": home_advs[league].varValue,
            }
            for league in leagues
        ],
        [
            {
                "id": team,
                "offence": offences[team].varValue,
                "defence": defences[team].varValue,
            }
            for team in teams
        ],
    )
