from pulp import LpMinimize, LpProblem, lpSum

from solver.models import League, Match, Team


def solver(
    matches: list[Match], teams: list[Team], leagues: list[League]
) -> dict[str, list[dict[str, float]]]:
    prob = LpProblem(sense=LpMinimize)

    for match in matches:
        # Constraints for absolute values
        prob += match.home_error >= match.home_error_val
        prob += match.home_error >= -match.home_error_val
        prob += match.away_error >= match.away_error_val
        prob += match.away_error >= -match.away_error_val

    # Objective function
    prob += lpSum(match.home_error for match in matches) + lpSum(
        match.away_error for match in matches
    )

    # Other constraints
    prob += lpSum(team.offence for team in teams if team.is_team_rating) == 0
    prob += lpSum(team.defence for team in teams if team.is_team_rating) == 0

    prob.solve()

    return {
        "leagues": [
            {
                "division": league.name,
                "avg_goal": league.avg_goal.varValue,
                "home_adv": league.home_adv.varValue,
            }
            for league in leagues
        ],
        "teams": [
            {
                "id": team.id,
                "offence": team.offence.varValue,
                "defence": team.defence.varValue,
            }
            for team in teams
        ],
    }
