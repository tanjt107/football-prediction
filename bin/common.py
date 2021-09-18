from datetime import datetime
import json
import numpy as np
import os
import pandas as pd
import requests
import time
from typing import Dict, List, Optional
from param import CHROMEDRIVER_PATH, MARKET_VALUE_URL_LIST, PARENT_DIRECTORY
from scipy.stats import distributions
from selenium import webdriver

class Season:
    def __init__(self, season_id: int):
        self.id = season_id
        response = call_api("league-season", {"season_id": self.id})
        self.success = response["success"]
        if self.success:
            data = response["data"]
            self.name = data["name"]
            self.season = data["season"]
            self.starting_year = data["starting_year"]
            self.ending_year = data["ending_year"]
            self.country = data["country"]
            self.iso = data["iso"]
            self.status = data["status"]
            self.matches = Matches(self.id)
            self.matchesCompletedLatest = data["matchesCompleted"]
            self.iso_shortHand = f"{self.iso}-{data['shortHand']}"
            self.json_path = f"{self.id}-{self.iso_shortHand }-{self.season.replace('/', '')}.json"
            self.market_value_path = f"{self.iso_shortHand}.json"
            self.market_value_full_path = os.path.join(PARENT_DIRECTORY, "data/market-value", self.market_value_path)
            self.has_market_value = os.path.exists(self.market_value_full_path)
            self.exists = os.path.exists(os.path.join(PARENT_DIRECTORY, "data/season", self.json_path))
            self.matchesCompletedBefore = self.get_matchesCompletedBefore()
        else:
            print(
                f"Season {self.id}: {response['message']}"
                )

    def get_matchesCompletedBefore(self) -> int:
        if self.exists:
            with open(os.path.join(PARENT_DIRECTORY, "data/season", self.json_path), "r") as f:
                season = json.load(f)
            return season["matchesCompleted"]
        else:
            return 0

    def market_value_factors(self) -> pd.Series:
        with open("mapping/transfermarkt.json", "r") as f:
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

    def update_market_value(self) -> dict:
        driver = webdriver.Chrome(CHROMEDRIVER_PATH)
        driver.get(MARKET_VALUE_URL_LIST[self.iso_shortHand])
        time.sleep(5)
        teams = driver.find_elements_by_class_name("hauptlink.no-border-links")
        values = driver.find_elements_by_class_name("rechts.hauptlink")
        result = {
            team.text.strip(): value.text.strip()
            for team, value in zip(teams, values)
        }

        with open(self.market_value_full_path, 'w') as f:
                json.dump(result, f, indent=4)
        driver.quit()

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
        assert not main_teams_only
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

def get_all_team_ratings(team_dict: dict, inter_league: bool, league_strength: Optional[dict]=None, size: int=5) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(team_dict, orient="index")
    if inter_league:
        df["league"] = df["league"].map(league_strength)
        df[["offence", "defence"]] *= league_strength["average_goal"]
        df["offence"] += df["league"]
        df["defence"] -= df["league"]
        df["offence"].loc[df["offence"] < 0.2] = 0.2
        df["defence"].loc[df["defence"] < 0.2] = 0.2
    else:
        assert league_strength is None
        df[["offence", "defence"]] *= team_dict["average_goal"]
    df["rating"] = df.apply(lambda df: get_team_rating(df.offence, df.defence), axis=1)
    df = df.round(2)
    return df

def get_team_rating(home_expected_goals: float, away_expected_goals: float, size: int=5) -> float:
    goal_matrix = get_goal_matrix(home_expected_goals, away_expected_goals, size)
    home_draw_away_probs = get_home_draw_away_probs(goal_matrix)
    return (home_draw_away_probs[0] * 3 + home_draw_away_probs[1] * 1) / 3 * 100

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