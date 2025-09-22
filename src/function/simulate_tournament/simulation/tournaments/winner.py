from dataclasses import dataclass

from simulation.models import Team


@dataclass
class Winner:
    def __post_init__(self):
        self.advance_to = None

    def add_teams(self, teams: list[Team]):
        if len(teams) != 1:
            raise ValueError("Winner round must have exactly one team.")

        teams[0].log_sim_rounds("winner")

    def simulate(self):
        pass

    def reset(self):
        pass
