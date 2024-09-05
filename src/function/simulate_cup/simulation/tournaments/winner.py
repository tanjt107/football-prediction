from dataclasses import dataclass

from simulation.models import Team


@dataclass
class Winner:
    def __post_init__(self):
        self.teams: set[Team] = set()

    def add_teams(self, teams: list[Team]):
        for team in teams:
            self.teams.add(team)
            team.log_sim_rounds("winner")

    def simulate(self):
        pass

    def reset(self):
        self.teams = set()
