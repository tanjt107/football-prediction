import pandas as pd
import numpy as np
from scipy import optimize
from common import *

def solver(filepath, home_advantage=True, recent=True, cut_off_date=None, cut_off_number_of_year=None):

    def transformation(df, cut_off_date=None, cut_off_number_of_year=None):
        df = df[df['status'] == 'complete']
        df = df[['timestamp', 'home_team_name', 'away_team_name', 'home_team_goal_count', 'away_team_goal_count', 'home_team_goal_timings', 'away_team_goal_timings', 'team_a_xg', 'team_b_xg']]
        df['recentness'] = df['timestamp'].apply(calculate_recentness, df=df, cut_off_date=cut_off_date,cut_off_number_of_year=cut_off_number_of_year)
        df['goal_timings'] = df.apply(get_goal_timings_dict, axis=1)
        df = df.apply(calculate_adjusted_goal, axis=1)
        df = df.apply(calculate_average_goal, axis=1)
        df['average_goal'] = 'average_goal'
        df['home_advantage'] = 'home_advantage'
        df['home_team_offence'] = df['home_team_name'] + "_offence"
        df['home_team_defence'] = df['home_team_name'] + "_defence"
        df['away_team_offence'] = df['away_team_name'] + "_offence"
        df['away_team_defence'] = df['away_team_name'] + "_defence"
        return df

    #second argument is the corresponding strings forarray values
    def get_factor_array(teams):
        average_goal = pd.DataFrame({'value': ['average_goal']})
        home_advantage = pd.DataFrame({'value': ['home_advantage']})
        team_offence = pd.DataFrame({'value': teams})
        team_offence.value += "_offence"
        team_defence = pd.DataFrame({'value': teams})
        team_defence.value += "_defence"
        return np.concatenate([team_offence, home_advantage, average_goal, team_defence], axis=None).astype(object)

    # first argument required by optimize is a 1d array with some number of values and set a reasonable initial value for the solver
    def initialise_factors(factors):
        return np.repeat(1, factors.size)

    # turn df strings into values that can be calculated
    def objective(value, factor, df):
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

    def constraints(teams, home_advantage=True):
        def average_offence(factors):
            return np.average(factors[:teams.size]) - 1
        def average_defence(factors):
            return np.average(factors[-teams.size:]) - 1
        def minimum_offence(factors):
            return factors[:teams.size].min()
        def minimum_defence(factors):
            return factors[-teams.size:].min()
        def minimum_home_advantage(factors):
            return factors[teams.size] - 1
        con_avg_offence = {'type': 'eq', 'fun': average_offence}
        con_avg_defence = {'type': 'eq', 'fun': average_defence}
        if home_advantage == True:
            con_home_advantage = {'type': 'ineq', 'fun': minimum_home_advantage}
        else:
            con_home_advantage = {'type': 'eq', 'fun': minimum_home_advantage}
        con_min_offence = {'type': 'ineq', 'fun': minimum_offence}
        con_min_defence = {'type': 'ineq', 'fun': minimum_defence}
        return [con_avg_offence, con_avg_defence, con_home_advantage, con_min_offence, con_min_defence]      

    df = pd.read_csv(filepath)
    teams = get_team_list(df)
    factors = get_factor_array(teams)
    initial = initialise_factors(factors)
    cons = constraints(teams, home_advantage)
    df = transformation(df, cut_off_date, cut_off_number_of_year)
    solver = optimize.minimize(objective, args=(factors, df), x0=initial, method = 'SLSQP', constraints=cons, options={'maxiter':10000})
    result = pd.DataFrame({'factors': factors, 'values':solver.x})
    return result

filepath = 'england-premier-league-matches-2018-to-2019-stats.csv'
result = solver(filepath)
print(result)