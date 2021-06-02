# Multiplicative Rating Models for Soccer

## Introduction
This model makes reference to the [course material](https://www.coursera.org/learn/mathematics-sport/lecture/nR8wd/8-4-multiplicative-rating-models-for-soccer) of Math behind Moneyball instructed by Professor Wayne Winston and FiveThirtyEight's [club soccer predictions](https://projects.fivethirtyeight.com/soccer-predictions). In the lecture, Professor used solver add-in in Excel for calculation, which takes a long time in finding solutions. To speed up the process, this python script uses a solver for non-linear problems from `scipy.optimize` which is much times faster in some cases.

## Result
[Hong Kong Football Prediction (in Traditional Chinese)](https://docs.google.com/spreadsheets/d/1KZoV2Zyi8pnzVi5pNCcixdcNon-56jZEpZgalRXsOAs/edit?usp=sharing)

## Methodology
The expected goals for home team and away team are calculated as follows:
```
home_team_forecasted_goals = average_goals * home_advantage * home_team_offensive_rating / away_team_defensive_rating
away_team_forecasted_goals = average_goals / home_advantage * away_team_offensive_rating / home_team_defensive_rating
```
And the solver finds the best values for each rating by minimising the following function:
```
objective_function = (home_team_forecasted_goals - home_team_adjusted_goals)^2 + (away_team_forecasted_goals - awya_team_adjusted_goals)^2
```
A 1.35 offensive rating means the team is expected to score 35% more and a 1.35 defensive rating means the team is expected to concede 35% more compared to an average team.

Unlike the 
[Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system), a team rating does not necessarily improve whenever it wins a match. If the team performs worse than the model expected, its ratings can decline.

In addition, recent matches are given more weight to reflect a team's recent performance.

## Adjusting Goals
Soccer is a tricky sport to model because there are so few goals scored in each match. The final result may not reflect the performance of each team well. To migrate the randomness and estimate team ratings better, two metrics are used in the calculation using in-depth match stats from [Footy Stats](https://footystats.org/) (a sample csv is available):

1. For *adjusted goals*, goals scored late by a leading team may not be important. Using `goal_timings` columns, the value of a goal by a leading team decreases linearly after the 70th minute. A goal in the 90th minute or later only worths 0.5 goals in the calculation.

2. For [*expected goals*](https://youtu.be/w7zPZsLGK18), `xg` columns (if available) are used.

The average of the above two metrics is used as `forecasted goals` in the calculation.

## Inter-league Matches
Matches played between teams from two different leagues, like those in the UEFA Champions League and AFC Champions league are used to calculate the relative strength of different leagues. Matches of the last five years are used for calculation. The country ratings are found as follows:
```
home_team_forecasted_goals = average_goals * home_advantage * home_team_offensive_rating / away_team_defensive_rating + home_country_rating - away_country_rating
away_team_forecasted_goals = average_goals / home_advantage * away_team_offensive_rating / home_team_defensive_rating + away_country_rating - away_country_rating
```
`team_rating` factors are constants calculated domestically.

## Simulating Matches
There are debates about the best statistical model to forecast the number of goals scored by both teams. Poisson distributions with diagonal inflation are used here. The forecasted goals calculated above are used as parameters and draw probabilities are then increased by around 9 percent to avoid undercounting draws.

![alt text](https://fivethirtyeight.com/wp-content/uploads/2018/08/boice-CLUBSOCCER-02.png?w=1150)
Source: [FiveThirtyEight](https://projects.fivethirtyeight.com/soccer-predictions)

From the matrix, win probabilities of both teams and draw probabilities can be found.

## Team Rating
To calculate team rating, the expected goal to score and expected goal concede of each team against an average team in the model can be calculated using the same formula above. The percentage of possible points against an average team is the team rating. For example, if a team is forecast to have a 35% probability to win (scoring three points), 30% to draw (scoring one point), 35% to lose (scoring no points) against an average team. The team rating of the team is:
```
(0.35 * 3 + 0.30 * 1 + 0.35 * 0)/3 = 45.0
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
