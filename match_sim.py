import numpy as np
from scipy.stats import distributions

# parameters are number of expected goals calculated from solver
def goal_matrix(home_expected_goals, away_expected_goals):
    home_goals = np.array([])
    away_goals = np.array([])
    # calculate the probability of scoring up to 10 goals
    # increasing this range increases accuracy but takes more computation time
    matrix = np.zeros((11,11))
    draw_percentage = 0
    for i in range(10):
        # assuming poisson distribution
        home_goals = np.append(home_goals, [distributions.poisson.pmf(i, home_expected_goals)])
        away_goals = np.append(away_goals, [distributions.poisson.pmf(i, away_expected_goals)])
    home_goals = np.append(home_goals, 1 - home_goals.sum())
    away_goals = np.append(away_goals, 1 - away_goals.sum())
    for i in range(11):
        for j in range(11):
            matrix[i, j] = home_goals[i] * away_goals[j]
    for i in range(11):
        draw_percentage += matrix[i, i]
    for i in range(11):
        for j in range(11):
            if i == j:
                # increase probability of draw
                # according to 538, the increment is around 9 percent
                matrix[i, j] = matrix[i, j] * 1.09
            else:
                matrix[i, j] = matrix[i, j] / (1 - draw_percentage) * (1 - draw_percentage * 1.09)
    return matrix

def match_sim_percentage(goal_matrix):
    home_win_percentage = 0
    draw_percentage = 0
    away_win_percentage = 0
    for i in range(11):
        for j in range(11):
            if i > j:
                home_win_percentage += goal_matrix[i, j]
            elif i < j:
                away_win_percentage += goal_matrix[i, j]
            else:
                draw_percentage += goal_matrix[i, j]
    return home_win_percentage, draw_percentage, away_win_percentage
