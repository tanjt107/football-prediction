import numpy as np
import pandas as pd
from pytest import approx
from src.solver import (
    _calculate_recentness,
    _get_goal_timings_dict,
    _reduce_goal_value,
    _calculate_adjusted_goal,
    _calculate_average_goal,
)


def test_calculate_recentness():
    timestamp = pd.Series([1483315200, 1514851200, 1546387200, 1577923200, 1609459200])
    assert np.array_equal(
        _calculate_recentness(timestamp, 4), np.array([0, 0.25, 0.5, 0.75, 1.25])
    )


def test_get_goal_timings_dict():
    assert _get_goal_timings_dict(
        ["24", "32", "37", "65", "80"], ["45", "56", "73"]
    ) == {
        24: "home",
        32: "home",
        37: "home",
        45: "away",
        56: "away",
        65: "home",
        73: "away",
        80: "home",
    }


def test_get_goal_timings_dict_nil():
    assert _get_goal_timings_dict([], []) == {}


def test_get_goal_timings_dict_plus():
    assert _get_goal_timings_dict(["90+3"], ["60"]) == {60: "away", 90: "home"}


def test_get_goal_timings_dict_zero():
    assert _get_goal_timings_dict(["84"], ["73", "9006"]) == {
        73: "away",
        84: "home",
        90: "away",
    }


def test_get_goal_timings_ot():
    assert _get_goal_timings_dict(["39", "48"], ["13", "45+1", "101"]) == {
        13: "away",
        39: "home",
        45: "away",
        48: "home",
        101: "away",
    }


def test_reduce_goal_value_zero():
    assert _reduce_goal_value({}) == (0, 0)


def test_reduce_goal_value():
    assert _reduce_goal_value(
        {7: "home", 19: "home", 28: "home", 42: "home", 64: "away"}
    ) == (4, 1)


def test_reduce_goal_value_70():
    assert _reduce_goal_value({63: "home", 70: "home"}) == (2, 0)


def test_reduce_goal_value_80():
    assert _reduce_goal_value({28: "away", 65: "away", 80: "away", 90: "home"}) == (
        1,
        2.75,
    )


def test_reduce_goal_value_90():
    assert _reduce_goal_value({18: "home", 65: "home", 67: "home", 90: "home"}) == (
        3.5,
        0,
    )


def test_reduce_goal_value_80_90():
    assert _reduce_goal_value(
        {20: "home", 59: "away", 60: "away", 80: "away", 90: "away"}
    ) == (1, 3.25)


def test_calculate_adjusted_goal_no_change():
    assert _calculate_adjusted_goal(
        pd.Series([3, 0]), pd.Series([3, 0])
    ).to_numpy() == approx([3.0, 0.0])


def test_calculate_adjusted_goal_simple():
    assert _calculate_adjusted_goal(
        pd.Series([1.9, 0]), pd.Series([2, 0])
    ).to_numpy() == approx([2.0, 0.0])


def test_calculate_adjusted_goal_advance():
    assert _calculate_adjusted_goal(
        pd.Series([3.8, 1, 0, 4.6, 1, 1, 2.9, 0, 0, 0, 0, 2.9, 2.8, 0]),
        pd.Series([4, 1, 0, 5, 1, 1, 3, 0, 0, 0, 0, 3, 3, 0]),
    ).to_numpy() == approx(
        [3.99, 1.05, 0, 4.83, 1.05, 1.05, 3.045, 0, 0, 0, 0, 3.045, 2.94, 0]
    )


def test_calculate_average_goal_1():
    assert _calculate_average_goal(3.6, 0.6) == approx(1.6)


def test_calculate_average_goal_2():
    assert _calculate_average_goal(0, 1.8) == approx(1.2)
