from enum import Enum


class Round(Enum):
    ROUND_OF_16 = 16
    QUARTER_FINALS = 8
    SEMI_FINALS = 4
    FINAL = 2
    FINALS = 2
    CHAMPS = 1

    def __gt__(self, other: "Round"):
        return self.value > other.value

    def __hash__(self):
        return hash(self.value)
