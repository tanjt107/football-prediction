from collections import defaultdict


class Results(defaultdict):
    def __init__(self):
        super().__init__(int)

    def __truediv__(self, other):
        for key in self:
            self[key] /= other
        return self
