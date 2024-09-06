from dataclasses import dataclass

from .results import Results
from .table import Table


@dataclass
class Team:
    name: str
    offence: float
    defence: float

    def __post_init__(self):
        self.table = Table()
        self.h2h_table = Table()
        self.sim_table = Table()
        self.sim_positions = Results()
        self.sim_rounds = Results()

    def __eq__(self, other: "Team") -> bool:
        return other and self.name == other.name

    def __gt__(self, other: "Team") -> bool:
        return self.name > other.name

    def __hash__(self):
        return hash(self.name)

    def set_correction(self, value: int):
        self.table.correction = value

    def log_sim_table(self):
        self.sim_table += self.table

    def log_sim_positions(self, position: int):
        self.sim_positions[f"_{position}"] += 1

    def log_sim_rounds(self, _round: str):
        self.sim_rounds[_round] += 1

    def reset(self):
        self.table.reset()
        self.h2h_table.reset()
