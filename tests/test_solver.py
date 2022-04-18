import numpy as np
import pandas as pd
from footballprediction.solver.solver import calculate_recentness


def test_calculate_recentness():
    timestamp = pd.Series([1483315200, 1514851200, 1546387200, 1577923200, 1609459200])
    assert np.array_equal(
        calculate_recentness(timestamp, 4), np.array([0, 0.25, 0.5, 0.75, 1.25])
    )
