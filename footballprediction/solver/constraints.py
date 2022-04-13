import numpy as np


def avg_off(factors: list[float]) -> float:
    return np.product(factors[2 : -len(factors - 2) // 2]) - 1


def avg_def(factors: list[float]) -> float:
    return np.product(factors[-len(factors - 2) // 2 :]) - 1


def min_home_adv(factors: list[float]) -> float:
    return factors[1] - 1


def sum_strength(factors: list[float]) -> float:
    return np.sum(factors[2:])
