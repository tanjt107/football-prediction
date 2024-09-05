from .team import Team


class TieBreaker:
    @staticmethod
    def h2h(team: Team) -> tuple:
        return (
            team.table.points,
            team.h2h_table.points,
            team.h2h_table.goal_diff,
            team.h2h_table.scored,
            team.table.goal_diff,
            team.table.scored,
        )

    @staticmethod
    def goal_diff(team: Team) -> tuple:
        return (team.table.points, team.table.goal_diff, team.table.scored)
