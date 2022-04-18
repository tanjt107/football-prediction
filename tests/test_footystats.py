import json
from footballprediction.etl.source.footystats import FootyStats


def test_league_list():
    fs = FootyStats()
    league_list = fs.league_list()
    assert len(league_list) > 0


def test_league_list_chosen_leagues_only():
    with open("credentials/footystats.json") as f:
        key = json.load(f)["key"]
    fs = FootyStats(key)
    league_list = fs.league_list(chosen_leagues_only=True)
    assert "country" not in league_list[0]


def test_chosen_season_id():
    with open("credentials/footystats.json") as f:
        key = json.load(f)["key"]
    fs = FootyStats(key)
    season_ids = fs.chosen_season_id()
    assert 6639 in season_ids


def test_season():
    fs = FootyStats()
    season_id = 2012
    season = fs.season(season_id)
    assert season["id"] == season_id


def test_matches():
    fs = FootyStats()
    season_id = 2012
    matches = fs.matches(season_id)
    assert matches[0]["competition_id"] == season_id


def test_teams():
    fs = FootyStats()
    season_id = 2012
    teams = fs.teams(season_id)
    assert teams[0]["competition_id"] == season_id


def test_teams_pl_1920():
    fs = FootyStats()
    teams = fs.teams(2012)
    assert teams[0]["cleanName"] == "Arsenal"
