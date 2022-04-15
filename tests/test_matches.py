from pytest import approx
from footballprediction.etl.jobs.matches import (
    get_goal_timings_dict,
    reduce_goal_value,
    calculate_adjusted_goal,
    calculate_average_goal,
)


def test_get_goal_timings_dict():
    assert get_goal_timings_dict(
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
    assert get_goal_timings_dict([], []) == {}


def test_get_goal_timings_dict_plus():
    assert get_goal_timings_dict(["90+3"], ["60"]) == {60: "away", 90: "home"}


def test_get_goal_timings_dict_zero():
    assert get_goal_timings_dict(["84"], ["73", "9006"]) == {
        73: "away",
        84: "home",
        90: "away",
    }


def test_get_goal_timings_ot():
    assert get_goal_timings_dict(["39", "48"], ["13", "45+1", "101"]) == {
        13: "away",
        39: "home",
        45: "away",
        48: "home",
        101: "away",
    }


def test_reduce_goal_value_zero():
    assert reduce_goal_value({}) == (0, 0)


def test_reduce_goal_value():
    assert reduce_goal_value(
        {7: "home", 19: "home", 28: "home", 42: "home", 64: "away"}
    ) == (4, 1)


def test_reduce_goal_value_70():
    assert reduce_goal_value({63: "home", 70: "home"}) == (2, 0)


def test_reduce_goal_value_80():
    assert reduce_goal_value({28: "away", 65: "away", 80: "away", 90: "home"}) == (
        1,
        2.75,
    )


def test_reduce_goal_value_90():
    assert reduce_goal_value({18: "home", 65: "home", 67: "home", 90: "home"}) == (
        3.5,
        0,
    )


def test_reduce_goal_value_80_90():
    assert reduce_goal_value(
        {20: "home", 59: "away", 60: "away", 80: "away", 90: "away"}
    ) == (1, 3.25)


def test_calculate_adjusted_goal():
    assert calculate_adjusted_goal(1) == 1.05


def test_calculate_average_goal_1():
    assert calculate_average_goal(3.6, 0.6) == approx(1.6)


def test_calculate_average_goal_2():
    assert calculate_average_goal(0, 1.8) == approx(1.2)
