WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws AS points,
    COALESCE(positions._1, 0) AS champ,
    COALESCE(positions._1, 0) + COALESCE(positions._2, 0) + COALESCE(positions._3, 0) + COALESCE(positions._4, 0) * 0.5 AS ucl,
    COALESCE(positions._4, 0) * 0.5 + COALESCE(positions._5, 0) AS uel,
    COALESCE(positions._16, 0) * 0.5 + COALESCE(positions._17, 0) + COALESCE(positions._18, 0) AS relegation
  FROM `simulation.leagues_latest` leagues
  JOIN `master.teams` teams ON leagues.team = teams.footystats_id
  JOIN `solver.team_ratings` ratings ON teams.solver_id = ratings.id
  WHERE _LEAGUE = 'France Ligue 1'
  AND ratings._TYPE = 'Club'
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(goal_diff, 1) AS goal_diff,
  ROUND(points, 1) AS points,
  ROUND(champ, 3) AS champ,
  ROUND(ucl, 3) AS ucl,
  ROUND(uel, 3) AS uel,
  ROUND(relegation, 3) AS relegation
FROM result
ORDER BY points DESC