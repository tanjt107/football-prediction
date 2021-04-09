# Multiplicative Rating Models for Soccer

## Introduction
This model makes reference to the [course material][1] of Math behind Moneyball instructed by Professor Wayne Winston and FiveThirtyEight's [club soccer predictions][2]. In the lecture, Professor used solver add-in in Excel for calculation, which takes a long time in finding solutions. To speed up the process, this script uses a solver for non-linear problems from `scipy.optimize` which is up to 10,000 times faster in some cases.

## Methodology
The expected goals for home team and away team are calculated as follows:
```
home_team_forecasted_goals = average_goals * home_advantage * home_team_offence_rating / away_team_defence_rating
away_team_forecasted_goals = average_goals / home_advantage * away_team_offence_rating / home_team_defence_rating
```
And the solver finds the best values for each rating by minimising the following function:
```
objective_function = (home_team_expected_goals - home_team_adjusted_goals)^2 + (away_team_expected_goals - awya_team_adjusted_goals)^2
```
Unlike the 
[Elo rating system][3], a team rating does not necessarily improve whenever it wins a match. If the team performs worse than the model expected, its ratings can decline.

In addition, recent matches are given more weight to reflect a team's recent performance.

## Adjusting Goals
Soccer is a tricky sport to model because there are so few goals scored in each match. The final result may not reflect the performance of each team. To migrate the randomness and estimate team ratings better, two metrics are used in the calculation using in-depth match stats from [Footy Stats][4] (sample csv is available):

1. For *adjusted goals*, goals scored late by a leading team may not be important. Using `goal_timings` columns, the value of a goal by a leading team decreases linearly after the 70th minute. A goal in the 90th minute or later only worths 0.5 goals in the calculation.

2. For [*expected goals*][5], `xg` columns (if available) are used.

The average of the above two metrics is used as `adjusted goals` in the calculation.

## Inter-league Matches
To be updated.

## Simulating Matches
To be updated.

## Simulating Seasons Using Monte Carlo Method
To be updated.

[1]:https://www.coursera.org/learn/mathematics-sport/lecture/nR8wd/8-4-multiplicative-rating-models-for-soccer
[2]:https://projects.fivethirtyeight.com/soccer-predictions/
[3]:https://en.wikipedia.org/wiki/Elo_rating_system
[4]:https://footystats.org/
[5]:https://youtu.be/w7zPZsLGK18
