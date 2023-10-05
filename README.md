# Multiplicative Rating Model for Football

## Introduction
This model makes reference to the [course material](https://www.coursera.org/learn/mathematics-sport/lecture/nR8wd/8-4-multiplicative-rating-models-for-soccer) of Math behind Moneyball instructed by Professor Wayne Winston and FiveThirtyEight's [club soccer predictions](https://projects.fivethirtyeight.com/soccer-predictions). In the lecture, Professor used solver add-in in Excel for calculation, which takes a long time in finding solutions. To speed up the process, this python script uses a solver from `pulp` which is much times faster in some cases.

## Result
[Hong Kong Football Prediction (in Traditional Chinese)](https://docs.google.com/spreadsheets/d/1mlWjjkJEDogGUujwi0ShMBhc36J1-il67fTG8ldaZqg/)

## Methodology
The expected goals for home team and away team are calculated as follows:
```
home_team_forecasted_goals = average_goals + home_advantage + home_team_offensive_rating + away_team_defensive_rating
away_team_forecasted_goals = average_goals - home_advantage + away_team_offensive_rating + home_team_defensive_rating
```
And the solver finds the best values for each rating by minimising the following function:
```
objective_function = abs(home_team_forecasted_goals - home_team_adjusted_goals) + abs(away_team_forecasted_goals - awya_team_adjusted_goals)
```
A 0.35 offensive rating means the team is expected to score 0.35 more goal and a 0.35 defensive rating means the team is expected to concede 0.35 more goal compared to an average team.

Unlike the 
[Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system), a team rating does not necessarily improve whenever it wins a match. If the team performs worse than the model expected, its ratings can decline.

In addition, recent matches are given more weight to reflect a team's recent performance.

## Adjusting Goals
Soccer is a tricky sport to model because there are so few goals scored in each match. The final result may not reflect the performance of each team well. To migrate the randomness and estimate team ratings better, two metrics are used in the calculation using in-depth match stats from [Footy Stats API](https://docs.footystats.org/):

1. For *adjusted goals*, goals scored late by a leading team may not be important. Using `goal_timings` columns, the value of a goal by a leading team decreases linearly after the 70th minute. A goal in the 90th minute or later only worths 0.5 goals in the calculation.

2. For [*expected goals*](https://youtu.be/w7zPZsLGK18), `xg` columns (if available) are used.

The average of the above two metrics is used as `forecasted goals` in the calculation.


## Simulating Matches
Poisson distributions are used here.

## Team Rating
To calculate team rating, the expected goal to score and expected goal concede of each team against an average team in the model can be calculated using the same formula above. The percentage of possible points against an average team is the team rating. For example, if a team is forecast to have a 50% probability to win (scoring three points), 25% to draw (scoring one point), 25% to lose (scoring no points) against an average team. The team rating of the team is:
```
(0.50 * 3 + 0.25 * 1 + 0.25 * 0)/3 = 58.3
```
From the formulae, the distribution of team ratings is not linear. Below is a general guideline from [ESPN](https://www.espn.com/world-cup/story/_/id/4447078/ce/us/guide-espn-spi-ratings):

Rating | Strength
--- | ---
85-100 | Elite
80-84 | Very Strong
75-79 | Strong
70-74| Good
60-69| Competitive
50-59| Marginal
25-49| Weak
0-24| Very Weak

Theoretically, a team with a rating of 100 would win every other team, while a team with a rating of 0 would lose to every other team in the model.

## Simulating Seasons Using Monte Carlo Method
To be updated.
