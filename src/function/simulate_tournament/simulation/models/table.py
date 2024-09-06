from dataclasses import dataclass


@dataclass
class Table:
    wins: int = 0
    draws: int = 0
    losses: int = 0
    scored: int = 0
    conceded: int = 0
    correction: int = 0

    def __add__(self, other: "Table"):
        return Table(
            self.wins + other.wins,
            self.draws + other.draws,
            self.losses + other.losses,
            self.scored + other.scored,
            self.conceded + other.conceded,
            self.correction + other.correction,
        )

    def __truediv__(self, other: "Table"):
        return Table(
            self.wins / other,
            self.draws / other,
            self.losses / other,
            self.scored / other,
            self.conceded / other,
            self.correction / other,
        )

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws + self.correction

    @property
    def goal_diff(self) -> int:
        return self.scored - self.conceded

    def reset(self):
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.scored = 0
        self.conceded = 0
