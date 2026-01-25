from typing import Protocol

from simulation.models import Team


class Round(Protocol):
    def add_teams(self, teams: list[Team]): ...

    def simulate(self): ...

    def reset(self): ...
