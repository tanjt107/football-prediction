from dataclasses import dataclass

from .tiebreaker import TieBreaker


@dataclass
class Rules:
    h2h: bool = False
    leg: int = 2

    @property
    def tiebreaker(self):
        return TieBreaker.h2h if self.h2h else TieBreaker.goal_diff
