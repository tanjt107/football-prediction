import json
import numpy as np
import pandas as pd
import re
import requests
from scipy import optimize

def get_api_key(credentials_path: str):
    with open(credentials_path) as f:
        return json.load(f)['key']

def get_match_df(season_id: int):
    data_dict = requests.get(f'https://api.football-data-api.com/league-matches?key={api_key}&season_id={season_id}') \
                        .json()['data']
    return pd.DataFrame.from_dict(data_dict)

def get_team_id_list(df: pd.DataFrame):
    try:
        df = df[df['status'] == 'complete']
    except KeyError:
        pass
    return np.unique(df[['homeID', 'awayID']].values)

def calculate_recentness(df: pd.DataFrame, recent: bool=True, cut_off_number_of_year: int=1):
    '''recentness factor gives less weight to games that were played further back in time.'''
    if recent == True:
        if cut_off_number_of_year is None:
            cut_off_timestamp = df.date_unix.min()
        else:
            cut_off_timestamp = df.date_unix.max() - cut_off_number_of_year * 31536000 # 365 * 24 * 60 * 60
        # a bonus of up to 25 percent is given to games played within past past 25 days to reflect a team's most recent form
        bouns_timestamp = cut_off_number_of_year * 2160000 # 25 * 24 * 60 * 60
        # TODO Add if timestamp difference smaller than 0
        df['recentness'] = np.where(df.date_unix.max() - df.date_unix <= bouns_timestamp,
                              (df.date_unix - cut_off_timestamp) / (df.date_unix.max() - cut_off_timestamp) * (1 + (bouns_timestamp - df.date_unix.max() + df.date_unix) / bouns_timestamp * 0.25),
                              (df.date_unix - cut_off_timestamp)/ (df.date_unix.max() - cut_off_timestamp))
    else:
        df.recentness = 1
    return df.recentness

def get_goal_timings_dict(df: pd.DataFrame):
    for goal_timings in ['homeGoals', 'awayGoals']:
        if goal_timings:
            team = goal_timings[:4]
            df[goal_timings] = {int(re.sub(r'\+\d+', '', minute)): team for minute in df[goal_timings]}
        else:
            df[goal_timings] = {}
    goal_timings_dict = df.homeGoals.copy()
    goal_timings_dict.update(df.awayGoals)
    goal_timings_dict = {int(key): goal_timings_dict[key] for key in sorted(goal_timings_dict.keys())}
    return goal_timings_dict

def reduce_goal_value(df: pd.DataFrame):
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

def calculate_adjusted_goal(df: pd.DataFrame):
    '''increased value of all other goals to make total number of adjusted goals equal to total number of actual goals.'''
    adjusted_goal_ratio = (df['homeGoalCount'].sum() + df['awayGoalCount'].sum()) / (df['home_team_adjusted_goal'].sum() + df['away_team_adjusted_goal'].sum())
    df['home_team_adjusted_goal'] = df['home_team_adjusted_goal'] * adjusted_goal_ratio
    df['away_team_adjusted_goal'] = df['away_team_adjusted_goal'] * adjusted_goal_ratio
    return df

def calculate_average_goal(df: pd.DataFrame):
    '''average of the two metrics'''
    df['home_team_average_goal'] = np.where((df.team_a_xg == 0) | (df.team_b_xg == 0), df.home_team_adjusted_goal, (df.home_team_adjusted_goal + df.team_a_xg * 2) / 3)
    df['away_team_average_goal'] = np.where((df.team_a_xg == 0) | (df.team_b_xg == 0), df.away_team_adjusted_goal, (df.away_team_adjusted_goal + df.team_b_xg * 2) / 3)
    return df

def set_calculable_string_in_df(df: pd.DataFrame):
    df['average_goal'] = 'average_goal'
    df['home_advantage'] = 'home_advantage'
    for team in ['home', 'away']:
        for factor in ['offence', 'defence']:
            df[f'{team}_team_{factor}'] = f"{df[f'{team}ID']}_{factor}"
    return df

def initialise_factors(factors: np.array):
    '''first argument required by optimize is a 1d array with some number of values and set a reasonable initial value for the solver.'''
    return np.concatenate(([1.35], np.repeat(1, factors.size - 1)))

def get_factors_array(teams: list):
    '''second argument is the corresponding strings forarray values.'''
    return np.concatenate((['average_goal', 'home_advantage'], [f'{team}_offence' for team in teams], [f'{team}_defence' for team in teams]))

def set_constraints(factors: np.array, home_advantage: bool=True):
    number_of_teams = int((len(factors) - 2) / 2)
    def average_offence(factors):
        factor_offence = factors[2:-number_of_teams]
        return np.product(factor_offence) - 1
    def average_defence(factors):
        factor_defence = factors[-number_of_teams:]
        return np.product(factor_defence) - 1
    def minimum_home_advantage(factors):
        return factors[1] - 1
    con_avg_offence = {'type': 'eq', 'fun': average_offence}
    con_avg_defence = {'type': 'eq', 'fun': average_defence}
    if home_advantage == True:
        con_home_advantage = {'type': 'ineq', 'fun': minimum_home_advantage}
    else:
        con_home_advantage = {'type': 'eq', 'fun': minimum_home_advantage}
    return [con_avg_offence, con_avg_defence, con_home_advantage]

def objective(value: np.array, factor: np.array, df: pd.DataFrame):
    '''turn df strings into values that can be calculated.'''
    assert len(value) == len(factor)
    lookup = dict()
    for i in range(len(value)):
        lookup[factor[i]] = value[i]
    df = df.replace(lookup)
    obj = (
          (
              (df.average_goal * df.home_advantage * df.home_team_offence * df.away_team_defence - df.home_team_average_goal) ** 2 +
              (df.average_goal / df.home_advantage * df.away_team_offence * df.home_team_defence - df.away_team_average_goal) ** 2
          ) * df.recentness
    )
    return np.sum(obj)

def solver(df: pd.DataFrame):
    df = df[df['status'] == 'complete']
    df = df[['date_unix', 'homeID', 'awayID', 'no_home_away', 'homeGoalCount', 'awayGoalCount', 'goal_timings_recorded', 'homeGoals', 'awayGoals', 'team_a_xg', 'team_b_xg']]
    df['recentness'] = calculate_recentness(df)
    df['goal_timings'] = df.apply(get_goal_timings_dict, axis=1)
    df = df.apply(reduce_goal_value, axis=1)
    df = calculate_adjusted_goal(df)
    df = calculate_average_goal(df)
    df = df.apply(set_calculable_string_in_df, axis=1)

    teams = get_team_id_list(df)
    factors = get_factors_array(teams)
    initial = initialise_factors(factors)
    cons = set_constraints(factors)
    solver = optimize.minimize(objective, args=(factors, df), x0=initial, method = 'SLSQP', constraints=cons, options={'maxiter':10000})
    result = pd.DataFrame({'factors': factors, 'values':solver.x})
    return result

if __name__ == '__main__':
    # api_key = get_api_key('credentials.json')
    api_key = 'example'
    df = get_match_df(2012)
    result = solver(df)
    print(result)