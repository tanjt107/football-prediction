import gspread as gs
import json
import numpy as np
import os
import pandas as pd
from common import Season, get_season_ids
from param import GS_CREDENTIALS_PATH, GS_WB_NAME, GS_WS_NATIONAL_NAME, INTERNATIONAL_FOLDER_PATH
from scipy.stats import distributions
from solver import solver

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

def get_home_draw_away_probs(goal_matrix: np.array) -> list:
   home_win_percentage = np.tril(goal_matrix, -1).sum()
   draw_percentage = np.trace(goal_matrix)
   away_win_percentage = np.triu(goal_matrix, 1).sum()
   return [home_win_percentage, draw_percentage, away_win_percentage]

def get_team_rating(home_expected_goals: float, away_expected_goals: float, size: int=5) -> float:
    goal_matrix = get_goal_matrix(home_expected_goals, away_expected_goals, size)
    home_draw_away_probs = get_home_draw_away_probs(goal_matrix)
    return (home_draw_away_probs[0] * 3 + home_draw_away_probs[1] * 1) / 3 * 100

# TODO Make path constant
def update_worksheet(ws: str, df: pd.DataFrame):
    df = df.reset_index()
    gc = gs.service_account(filename=GS_CREDENTIALS_PATH)
    sh = gc.open(GS_WB_NAME)
    sh.worksheet(ws).clear()
    sh.worksheet(ws).update([df.columns.values.tolist()] + df.values.tolist())

if __name__ == '__main__':
    latest_asian_season_id = get_season_ids(['International WC Qualification Asia'], 1)[0]
    latest_asian_season = Season(latest_asian_season_id)
    asian_countries = latest_asian_season.team_ids()

    national_competitions = ['International WC Qualification Asia', 'International International Friendlies']
    seasons = get_season_ids(national_competitions, 4)

    df = pd.DataFrame()

    for season in seasons:
        df_season = Season(season).matches.df('complete')
        df = df.append(df_season)

    df = df[df.homeID.isin(asian_countries) & df.awayID.isin(asian_countries)]

    print(latest_asian_season)

    result = solver(df, cut_off_number_of_year=4, max_boundary=5)
    with open(os.path.join(
        INTERNATIONAL_FOLDER_PATH, latest_asian_season.json_name
        ), 'w') as f:
        json.dump(result, f, indent=4)

    average_goal = result['average_goal']
    df = pd.DataFrame.from_dict(result['team'], orient='index')
    df *= average_goal
    df['rating'] = df.apply(lambda team: get_team_rating(team.offence, team.defence, 5), axis=1)
    df = df.round(2)
    df.index.name = 'team'

    update_worksheet(GS_WS_NATIONAL_NAME, df)