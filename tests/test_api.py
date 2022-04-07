from src.api import FootyStats

def test_footystats_league():
    api = FootyStats('example')
    response = api.leagues()
    assert response['success']

def test_footystats_league_chosen_league_only():
    api = FootyStats('example')
    response = api.leagues(True)
    assert response['success']

def test_footystats_league_stats():
    api = FootyStats('example')
    response = api.league_stats(2012)
    assert response['success']

def test_footystats_matches():
    api = FootyStats('example')
    response = api.matches(2012)
    assert response['success']

def test_footystats_league_teams():
    api = FootyStats('example')
    response = api.league_teams(2012)
    assert response['success']

def test_footystats_team():
    api = FootyStats('example')
    response = api.team(93)
    assert response['success']