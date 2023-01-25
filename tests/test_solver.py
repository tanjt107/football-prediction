import csv
import pytest
from footballprediction.solver import solver


@pytest.fixture
def matches():
    with open("tests/test.csv", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def test_solver_single_league(matches):
    matches = [
        match for match in matches if match["league_name"] == matches[0]["league_name"]
    ]
    s = solver(matches)
    assert s["league"].keys() == {match["league_name"] for match in matches}
    assert s["teams"].keys() == {match["home_id"] for match in matches} | {
        match["away_id"] for match in matches
    }


def test_solver_multiple_leagues(matches):
    s = solver(matches)
    assert s["league"].keys() == {match["league_name"] for match in matches}
    assert s["teams"].keys() == {match["home_id"] for match in matches} | {
        match["away_id"] for match in matches
    }
