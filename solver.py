import json
import numpy as np
import pandas as pd
import re
import requests
from scipy import optimize

def get_api_key(credentials_path: str) -> str:
    with open(credentials_path) as f:
        return json.load(f)['key']

def get_matches_df(season_id: int) -> pd.DataFrame:
    response = requests.get(f'https://api.football-data-api.com/league-matches?key={api_key}&season_id={season_id}').json()
    return pd.DataFrame.from_dict(response['data'])

def get_teamID_list(df: pd.DataFrame) -> list:
    return np.unique(df[['homeID', 'awayID']].values)

def remove_cancelled_matches(df: pd.DataFrame) -> pd.DataFrame:
    return df[df['status'] != 'canceled']

def calculate_recentness(df: pd.DataFrame, recent: bool, cut_off_number_of_year: int=1) -> pd.Series:
    '''recentness factor gives less weight to games that were played further back in time.'''
    if recent == True:
        if cut_off_number_of_year is None:
            cut_off_timestamp = df.date_unix.min()
        else:
            cut_off_timestamp = df.date_unix.max() - cut_off_number_of_year * 31536000 # 365 * 24 * 60 * 60
        # a bonus of up to 25 percent is given to games played within past past 25 days to reflect a team's most recent form
        bouns_timestamp = cut_off_number_of_year * 2160000 # 25 * 24 * 60 * 60
        df['recentness'] = np.where(df.date_unix.max() - df.date_unix <= bouns_timestamp,
                              (df.date_unix - cut_off_timestamp) / (df.date_unix.max() - cut_off_timestamp)
                              * (1 + (bouns_timestamp - df.date_unix.max() + df.date_unix) / bouns_timestamp * 0.25),
                              (df.date_unix - cut_off_timestamp)/ (df.date_unix.max() - cut_off_timestamp))
        df.recentness = np.where(df.recentness > 0, df.recentness, 1 / cut_off_number_of_year / 365)
    else:
        df.recentness = 1
    return df.recentness

def get_goal_timings_dict(df: pd.DataFrame) -> dict:
    if df.goal_timings_recorded == 1:
        for goal_timings in ['homeGoals', 'awayGoals']:
            if goal_timings:
                team = goal_timings[:4]
                for minute in ['45', '90', '105', '120']:
                    df[goal_timings] = [re.sub(fr"{minute}('|\+)?\d+", minute, goal_minute) for goal_minute in df[goal_timings]]
                df[goal_timings] = {int(goal_minute): team for goal_minute in df[goal_timings]}
            else:
                df[goal_timings] = {}
        goal_timings_dict = df.homeGoals.copy()
        goal_timings_dict.update(df.awayGoals)
        goal_timings_dict = {int(key): goal_timings_dict[key] for key in sorted(goal_timings_dict.keys())}
        return goal_timings_dict
    else:
        return {}

def reduce_goal_value(df: pd.DataFrame) -> pd.DataFrame:
    '''reduce the value of goals scored late in a match when a team is already leading.'''
    if df.goal_timings:
        if list(df.goal_timings)[-1] > 90:
            playing_time = 120
        else:
            playing_time = 90
        (home_team_goal, home_team_adjusted_goal, away_team_goal, away_team_adjusted_goal) = (0, 0, 0, 0)
        for timing in df.goal_timings:
            if df.goal_timings[timing] == 'home':
                home_team_goal += 1
                if (playing_time - timing < 20) and (home_team_goal - away_team_goal > 1):
                    home_team_adjusted_goal += 0.5 + (playing_time - timing)/20 * 0.5
                else:
                    home_team_adjusted_goal += 1
            elif df.goal_timings[timing] == 'away':
                away_team_goal +=1
                if (playing_time - timing < 20) and (away_team_goal - home_team_goal > 1):
                    away_team_adjusted_goal += 0.5 + (playing_time - timing)/20 * 0.5
                else:
                    away_team_adjusted_goal += 1
        df['home_team_adjusted_goal'] = home_team_adjusted_goal
        df['away_team_adjusted_goal'] = away_team_adjusted_goal
    else:
        df['home_team_adjusted_goal'] = df.homeGoalCount
        df['away_team_adjusted_goal'] = df.awayGoalCount
    return df

def calculate_adjusted_goal(df: pd.DataFrame) -> pd.DataFrame:
    '''increased value of all other goals to make total number of adjusted goals equal to total number of actual goals.'''
    adjusted_goal_ratio = ((df['homeGoalCount'].sum() + df['awayGoalCount'].sum())
                           / (df['home_team_adjusted_goal'].sum() + df['away_team_adjusted_goal'].sum()))
    df['home_team_adjusted_goal'] = df['home_team_adjusted_goal'] * adjusted_goal_ratio
    df['away_team_adjusted_goal'] = df['away_team_adjusted_goal'] * adjusted_goal_ratio
    return df

def calculate_average_goal(df: pd.DataFrame) -> pd.DataFrame:
    '''average of the two metrics'''
    df['home_team_average_goal'] = np.where((df.team_a_xg == 0) | (df.team_b_xg == 0),
                                             df.home_team_adjusted_goal, (df.home_team_adjusted_goal + df.team_a_xg * 2) / 3)
    df['away_team_average_goal'] = np.where((df.team_a_xg == 0) | (df.team_b_xg == 0),
                                             df.away_team_adjusted_goal, (df.away_team_adjusted_goal + df.team_b_xg * 2) / 3)
    return df

def set_calculable_string_in_df(df: pd.DataFrame) -> pd.DataFrame:
    df['average_goal'] = 'average_goal'
    df['home_advantage'] = 'home_advantage'
    for team in ['home', 'away']:
        for factor in ['offence', 'defence']:
            df[f'{team}_team_{factor}'] = f"{df[f'{team}ID']}_{factor}"
    return df

def initialise_factors(factors: np.array) -> np.array:
    '''first argument required by optimize is a 1d array with some number of values and set a reasonable initial value for the solver.'''
    return np.concatenate(([1.35], np.repeat(1, factors.size - 1)))

def get_factors_array(teams: list) -> np.array:
    '''second argument is the corresponding strings forarray values.'''
    return np.concatenate((['average_goal', 'home_advantage'], [f'{team}_offence' for team in teams], [f'{team}_defence' for team in teams]))

def set_constraints(factors: np.array) -> list:
    number_of_teams = int((len(factors) - 2) / 2)
    def average_offence(factors):
        return np.product(factors[2:-number_of_teams]) - 1
    def average_defence(factors):
        return np.product(factors[-number_of_teams:]) - 1
    def minimum_home_advantage(factors):
        return factors[1] - 1
    con_avg_offence = {'type': 'eq', 'fun': average_offence}
    con_avg_defence = {'type': 'eq', 'fun': average_defence}
    con_home_advantage = {'type': 'ineq', 'fun': minimum_home_advantage}
    return [con_avg_offence, con_avg_defence, con_home_advantage]

def set_boundaries(factors: np.array) -> tuple:
    n = len(factors)
    return ((0,3),) * n

def objective(values: np.array, factors: np.array, df: pd.DataFrame) -> float:
    '''turn df strings into values that can be calculated.'''
    assert len(values) == len(factors)
    lookup = {factor: value for factor, value in zip (factors, values)}
    df = df.replace(lookup)
    obj = (
          (
              (df.average_goal * df.home_advantage ** df.no_home_away * df.home_team_offence * df.away_team_defence - df.home_team_average_goal) ** 2 +
              (df.average_goal / df.home_advantage ** df.no_home_away * df.away_team_offence * df.home_team_defence - df.away_team_average_goal) ** 2
          ) * df.recentness
    )
    return np.sum(obj)

def parse_result_to_json(solver: str, factors: np.array) -> json:
    number_of_teams = int((len(factors) - 2) / 2)
    result = {factors[0]: solver.x[0], factors[1]: solver.x[1]}
    result_team = {}
    for factor, offence, defence in zip(factors[2:-number_of_teams], solver.x[2:-number_of_teams], solver.x[-number_of_teams:]):
        team = factor.split('_')[0]
        result_team[str(team)] = {'offence': offence, 'defence': defence}
    result['teams'] = result_team
    return result


def solver(df: pd.DataFrame, recent: bool=True) -> json:
    df = df[['date_unix', 'homeID', 'awayID', 'homeGoalCount', 'awayGoalCount', 'goal_timings_recorded', 'homeGoals', 'awayGoals', 'team_a_xg', 'team_b_xg', 'no_home_away']]
    df['recentness'] = calculate_recentness(df, recent)
    df['goal_timings'] = df.apply(get_goal_timings_dict, axis=1)
    df = df.apply(reduce_goal_value, axis=1)
    df = calculate_adjusted_goal(df)
    df = calculate_average_goal(df)
    df = df.apply(set_calculable_string_in_df, axis=1)
    teams = get_teamID_list(df)
    factors = get_factors_array(teams)
    initial = initialise_factors(factors)
    cons = set_constraints(factors)
    bnds = set_boundaries(factors)
    solver = optimize.minimize(objective, args=(factors, df), x0=initial, method = 'SLSQP', constraints=cons, bounds=bnds, options={'maxiter':10000})
    result = parse_result_to_json(solver, factors)
    return result

if __name__ == '__main__':
    # api_key = get_api_key('credentials.json')
    api_key = 'example'
    df = get_matches_df(2012)
    df = remove_cancelled_matches(df)
    result = solver(df)