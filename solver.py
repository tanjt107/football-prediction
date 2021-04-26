import pandas as pd
import numpy as np
import datetime
import re
from scipy import optimize

def solver(filepath, home_advantage=True, recent=True, cut_off_date=None, cut_off_number_of_year=None):

    def transformation(df, cut_off_date=None, cut_off_number_of_year=None):
        # recentness factor gives less weight to games that were played further back in time
        def calculate_recentness(timestamp, recent=True, cut_off_date=None, cut_off_number_of_year=None):
            if recent == True:
                if cut_off_date is not None:
                    cut_off_timestamp = int(datetime.datetime.strptime(cut_off_date, "%d/%m/%Y").timestamp())
                elif cut_off_number_of_year is not None:
                    cut_off_timestamp = df.timestamp.max() - cut_off_number_of_year * 31536000
                else:
                    cut_off_timestamp = df.timestamp.min()
                # a bonus of up to 25 percent is given to games played within past past 25 days to reflect a team's most recent form
                if df.timestamp.max() - timestamp <= 2160000:
                    recentness = (timestamp - cut_off_timestamp) / (df.timestamp.max() - cut_off_timestamp) * (1 + (2628000 - df.timestamp.max() + timestamp) / 2628000 * 0.25)
                else:
                    recentness = max((timestamp - cut_off_timestamp) / (df.timestamp.max() - cut_off_timestamp), 0)
            else:
                recentness = 1
            return recentness

        def get_goal_timings_dict(df):
            for goal_timings in ['home_team_goal_timings', 'away_team_goal_timings']:
                if not pd.isnull(df[goal_timings]):
                    team = goal_timings.split('_')[0]
                    df[goal_timings] = re.sub(r"45('|0)[0-9]", '45', df[goal_timings])
                    df[goal_timings] = re.sub(r"90('|0)[0-9]", '90', df[goal_timings])
                    df[goal_timings] = re.sub(r"105('|0)[0-9]", '105', df[goal_timings])
                    df[goal_timings] = re.sub(r"120('|0)[0-9]", '120', df[goal_timings])
                    df[goal_timings] = df[goal_timings].split(',')
                    df[goal_timings] = {int(minute): team for minute in df[goal_timings]}
                else:
                    df[goal_timings] = {}
            goal_timings_dict = df.home_team_goal_timings.copy()
            goal_timings_dict.update(df.away_team_goal_timings)
            goal_timings_dict = {int(key): goal_timings_dict[key] for key in sorted(goal_timings_dict.keys())}
            return goal_timings_dict

        #reduce the value of goals scored late in a match when a team is already leading
        def calculate_adjusted_goal(df):
            if df.goal_timings != {}:
                if list(df.goal_timings)[-1] > 90:
                    playing_time = 120
                else:
                    playing_time = 90
                (home_team_goal, home_team_adjusted_goal, away_team_goal, away_team_adjusted_goal) = (0, 0, 0, 0)
                for timing in df.goal_timings:
                    # after the 70th minute, value of a goal when a team is leading decreases to the end of the game
                    # a goal is worth 0.5 goal in the eyes of 538's model.
                    if df.goal_timings[timing] == 'home':
                        home_team_goal += 1
                        if (playing_time - timing < 20) and (home_team_goal - away_team_goal > 1):
                            home_team_adjusted_goal += 0.5 + (playing_time - timing)/20 * 0.5
                        else:
                            home_team_adjusted_goal += 1.0
                    elif df.goal_timings[timing] == 'away':
                        away_team_goal +=1
                        if (playing_time - timing < 20) and (away_team_goal - home_team_goal > 1):
                            away_team_adjusted_goal += 0.5 + (playing_time - timing)/20 * 0.5
                        else:
                            away_team_adjusted_goal += 1.0
                if (home_team_goal > 0) and (away_team_goal > 0):
                    df['home_team_adjusted_goal'] = home_team_adjusted_goal / (home_team_adjusted_goal + away_team_adjusted_goal) * (home_team_goal + away_team_goal)
                    df['away_team_adjusted_goal'] = away_team_adjusted_goal / (home_team_adjusted_goal + away_team_adjusted_goal) * (home_team_goal + away_team_goal)
                else:
                    df['home_team_adjusted_goal'] = home_team_adjusted_goal
                    df['away_team_adjusted_goal'] = away_team_adjusted_goal
            else:
                df['home_team_adjusted_goal'] = df.home_team_goal_count
                df['away_team_adjusted_goal'] = df.away_team_goal_count
            return df

        # average of the two metrics
        def calculate_average_goal(df):
            # if xg stats are not available
            if (df.team_a_xg == 0) or (df.team_b_xg == 0):
                df['home_team_average_goal'] = df.home_team_adjusted_goal
                df['away_team_average_goal'] = df.away_team_adjusted_goal
            else:
                # take average of two metrics
                df['home_team_average_goal'] = (df.home_team_adjusted_goal + df.team_a_xg) / 2
                df['away_team_average_goal'] = (df.away_team_adjusted_goal + df.team_b_xg) / 2
            return df

        df = df[df['status'] == 'complete']
        df = df[['timestamp', 'home_team_name', 'away_team_name', 'home_team_goal_count', 'away_team_goal_count', 'home_team_goal_timings', 'away_team_goal_timings', 'team_a_xg', 'team_b_xg']]
        df['recentness'] = df['timestamp'].apply(calculate_recentness, cut_off_date=cut_off_date,cut_off_number_of_year=cut_off_number_of_year)
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
    
    def get_team_list(df):
        df = df[df['status'] == 'complete']
        return np.unique(df[['home_team_name', 'away_team_name']])

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