from dataclasses import dataclass

from .leg import Leg
from .tiebreaker import TieBreaker


@dataclass
class Rules:
    h2h: bool = False
    leg: int = 2
    leg_final: int = 1

    def __post_init__(self):
        self.leg = Leg(self.leg)
        self.leg_final = Leg(self.leg_final)

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff
