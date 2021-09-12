from datetime import datetime
import json
import numpy as np
import os
import pandas as pd
import requests
import time
from typing import Dict, List
from param import PARENT_DIRECTORY
from scipy.stats import distributions

class Season:
    def __init__(self, season_id: int):
        self.id = season_id
        response = call_api("league-season", {"season_id": self.id})
        self.success = response["success"]
        if self.success:
            data = response["data"]
            self.name = data["name"]
            self.season = data["season"]
            self.country = data["country"]
            self.iso = data["iso"]
            self.status = data["status"]
            self.matches = Matches(self.id)
            self.matchesCompleted = data["matchesCompleted"]
            self.json_path = f"{self.id}-{self.iso}-{data['shortHand']}-{self.season.replace('/', '')}.json"
            self.market_value_path = f"{self.iso}-{data['shortHand']}.json"
            self.market_value_full_path = os.path.join(PARENT_DIRECTORY, "data/market-value", self.market_value_path)
            self.has_market_value = os.path.exists(self.market_value_full_path)
            self.need_update = self.check_if_needs_update()
        else:
            print(
                f"{self.id}: {response['message']}"
                )

    def check_if_needs_update(self) -> bool:
        if os.path.exists(fp:= os.path.join(PARENT_DIRECTORY, "data/season", self.json_path)):
            with open(fp) as f:
                if json.load(f)["status"] == "Completed":
                    return False
        return True

    def market_value_factors(self) -> pd.Series:
        if self.has_market_value:
            with open("transfermarkt/teams.json", "r") as f:
                lookups = json.load(f)
            df = pd.read_json(self.market_value_full_path, orient="index")
            df.index = df.index.map(lookups)
            market_values = (df[0].str.replace("€", "", regex=False)
                                  .str.replace("m", "e3", regex=False)
                                  .str.replace("Th.", "", regex=False)
                                  .astype(float))
            market_values /= np.prod(market_values) ** (1/len(market_values))
            market_values.name = "market_value"
            market_values = market_values.loc[~market_values.duplicated(keep=False)]
            return market_values

    def team_ids(self, status: str="all") -> list:
        df = self.matches.df(status)
        return [team for team in np.unique(df[["homeID", "awayID"]].values)]

    def __str__(self):
        return f"Season {self.id}: {self.season} {self.country} {self.name}"   

class Matches:
    def __init__(self, season_id: int):
        self.id = season_id
    
    def df(self, status: str="all") -> pd.DataFrame:
        response = call_api("league-matches", {"season_id": self.id})
        df = pd.DataFrame.from_dict(response["data"])
        if status == "all":
            return df
        elif status == "complete":
            return df.loc[df["status"] == "complete"]
        elif status == "not canceled":
            return df.loc[df["status"] != "canceled"]

class Team:
    def __init__(self, team_id: int):
        self.id = team_id
        data = call_api("team", {"team_id": self.id})["data"]
        self.country = data[0]["country"]
        self.name = data[0]["name"]
        domestic_leagues = sorted(
            [season for season in data if season["season_format"] == "Domestic League"],
            key=lambda season: str(season["season"]),
            reverse=True
        )
        self.domestic_league_ids = [
            season["competition_id"] for season in domestic_leagues
        ]

    def __str__(self):
        return f"Team {self.id}: {self.country} {self.name}"

def append_matches_dfs(main_season: Season=None, seasons: List[Season]=[], market_value: bool=False, main_teams_only: bool=True) -> pd.DataFrame:
    if main_season:
        team_ids = main_season.team_ids()
        df = main_season.matches.df("complete")
        df["previous_season"] = 0
    else:
        df = pd.DataFrame()
        assert main_teams_only == False
    for season in seasons:
        df_season = season.matches.df("complete")
        df_season["previous_season"] = int(market_value)
        df = df.append(df_season)
    if main_teams_only:
        df = df[
            df.homeID.isin(team_ids)
            & df.awayID.isin(team_ids)
            ]
    return df

def call_api(endpoint: str, params: Dict[str, str]) -> dict:
    def get_api_key() -> str:
        with open(os.path.join(PARENT_DIRECTORY, "credentials", "footystats.json")) as f:
            return json.load(f)["api_key"]
            
    url = f"https://api.football-data-api.com/{endpoint}"
    params["key"] = get_api_key()
    try:
        response = requests.get(
            url, params=params
        )
    except json.decoder.JSONDecodeError:
        time.sleep(1)
        response = requests.get(
            url, params=params
        )
    return response.json()

def get_all_leagues(chosen_leagues_only=bool) -> pd.DataFrame:
    response = call_api(
        "league-list",
        {"chosen_leagues_only": str(chosen_leagues_only).lower()}
        )
    return pd.DataFrame(response["data"])

def get_all_team_ratings(dict: dict, size: int=5) -> pd.DataFrame:
    def get_team_rating(home_expected_goals: float, away_expected_goals: float, size: int=5) -> float:
        goal_matrix = get_goal_matrix(home_expected_goals, away_expected_goals, size)
        home_draw_away_probs = get_home_draw_away_probs(goal_matrix)
        return (home_draw_away_probs[0] * 3 + home_draw_away_probs[1] * 1) / 3 * 100

    average_goal = dict['average_goal']
    df = pd.DataFrame.from_dict(dict['team'], orient='index')
    df *= average_goal
    df['rating'] = df.apply(lambda team: get_team_rating(team.offence, team.defence, size), axis=1)
    df = df.round(2)
    df.index.name = 'team'
    return df

def get_api_key() -> str:
    with open(os.path.join(PARENT_DIRECTORY, "credentials", "footystats.json")) as f:
        return json.load(f)["api_key"]

def get_current_year() -> int:
    return int(datetime.today().strftime("%Y"))

def get_goal_matrix(home_expected_goals: float, away_expected_goals: float, size: int) -> np.array:
    """
    home_expected_goals, away_expected_goals: number of expected goals calculated from solver
    size: increasing this range increases accuracy but takes more computation time
    """
    # assuming poisson distribution 
    home_goals = [distributions.poisson.pmf(i, home_expected_goals) for i in range(size+1)]
    home_goals[-1] = 1 - np.sum(home_goals[:-1])
    away_goals = [distributions.poisson.pmf(i, away_expected_goals) for i in range(size+1)]
    away_goals[-1] = 1 - np.sum(away_goals[:-1])
    matrix = np.outer(home_goals, away_goals)
    di = np.diag_indices(size+1)   
    # increase probability of draw
    # according to fivethirtyeight, the increment is around 9 percent
    matrix[di] *= 1.09
    matrix /= np.sum(matrix)
    return matrix

def get_home_draw_away_probs(goal_matrix: np.array) -> List[float]:
   home_win_percentage = np.tril(goal_matrix, -1).sum()
   draw_percentage = np.trace(goal_matrix)
   away_win_percentage = np.triu(goal_matrix, 1).sum()
   return [home_win_percentage, draw_percentage, away_win_percentage]

def get_season_ids(competitions: List[str], years: int) -> list:
    seasons = []
    df = get_all_leagues(True)
    leagues = df.loc[df["name"].isin(competitions)]["season"].values
    for league in leagues:
        for season in league:
            if int(str(season["year"])[-4:]) >= CURRENT_YEAR - years:
                seasons.append(season["id"])
    return seasons

def update_worksheet(ws: str, df: pd.DataFrame):
    df = df.reset_index()
    gc = gs.service_account(filename=GS_CREDENTIALS_PATH)
    sh = gc.open(GS_WB_NAME)
    if ws in [sheet.title for sheet in sh.worksheets()]:
        sh.worksheet(ws).clear()
    else:
        sh.add_worksheet(title=ws, rows="100", cols="20")
    sh.worksheet(ws).update([df.columns.values.tolist()] + df.values.tolist())

CURRENT_YEAR = get_current_year()