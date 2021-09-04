import json
import numpy as np
import os
import pandas as pd
import requests
from param import API_KEY, SEASON_DATA_FOLDER_PATH, CURRENT_YEAR

class Season:
    def __init__(self, season_id: int):
        self.id = season_id
        response = requests.get(
            f'https://api.football-data-api.com/league-season?key={API_KEY}&season_id={self.id}'
            ).json()
        self.success = response['success']
        if self.success == True:
            data = response['data']
            self.name = data['name']
            self.season = data['season']
            self.country = data['country']
            self.iso = data['iso']
            self.status = data['status']
            self.matches = Matches(self.id)
            self.matchesCompleted = data['matchesCompleted']
            self.json_name = f'{self.id}-{self.iso}-{data["shortHand"]}-{self.season.replace("/", "")}.json'
            if os.path.exists(json_path:= os.path.join(SEASON_DATA_FOLDER_PATH, self.json_name)):
                with open(json_path) as f:
                    if json.load(f)['status'] == 'In Progress':
                        self.need_update =  True
                    else:
                        self.need_update =  False
            else:
                self.need_update =  True
        else:
            print(f'League {self.id} is not chosen by the user or is not available to this user')
            self.need_update = False
    
    def team_ids(self, status: str = None) -> list:
        df = self.matches.df(status)
        return [team for team in np.unique(df[['homeID', 'awayID']].values)]

    def __str__(self):
        return f"Season {self.id}: {self.season} {self.country} {self.name}"

class Matches:
    def __init__(self, season_id: int):
        self.id = season_id

    def df(self, status: str = None) -> pd.DataFrame:
        response = requests.get(
            f'https://api.football-data-api.com/league-matches?key={API_KEY}&season_id={self.id}'
            ).json()
        df = pd.DataFrame.from_dict(response['data'])
        if status == 'complete':
            return df[df['status'] == 'complete']
        elif status == 'not canceled':
            return df[df['status'] != 'canceled']
        elif status == None:
            return df

class Team:
    def __init__(self, team_id: int):
        self.id = team_id
        data = requests.get(
            f'https://api.football-data-api.com/team?key={API_KEY}&team_id={self.id}'
            ).json()['data']
        self.country = data[0]['country']
        self.name = data[0]['name']
        domestic_league_ids_sorted = sorted(
            [season for season in data if season['season_format'] == 'Domestic League'],
            key=lambda season: str(season['season']),
            reverse=True
            )
        self.domestic_league_ids = [
            season['competition_id'] for season in domestic_league_ids_sorted
            ]

    def __str__(self):
         return f'Team {self.id}: {self.country} {self.name}'

def get_all_leagues(chosen_leagues_only: bool) -> pd.DataFrame:
    response = requests.get(
        f'https://api.football-data-api.com/league-list?key={API_KEY}&chosen_leagues_only={str(chosen_leagues_only).lower()}'
        ).json()
    return pd.DataFrame(response['data'])

def get_season_ids(season_ids: list, number_of_years: int) -> list:
    seasons = []
    df = get_all_leagues(True)
    leagues = df.loc[df['name'].isin(season_ids)]['season'].values
    for league in leagues:
        for season in league:
            if int(str(season['year'])[-4:]) >= CURRENT_YEAR - number_of_years:
                seasons.append(season['id'])
    return seasons