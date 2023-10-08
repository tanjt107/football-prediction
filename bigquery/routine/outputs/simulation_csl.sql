WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws AS points,
    COALESCE(positions.1, 0) AS champ,
    COALESCE(positions.1, 0) + COALESCE(positions.2, 0) * 0.5 AS acle,
    COALESCE(positions.2, 0) * 0.5 + COALESCE(positions.3, 0) AS acl2,
    COALESCE(positions.15, 0) + COALESCE(positions.16, 0) AS relegation
  FROM `simulation.csl` sim
  JOIN `master.teams` teams ON CAST(sim.team AS INT64) = teams.footystats_id
  JOIN `master.team_ratings` ratings ON teams.solver_id = ratings.id
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
  ROUND(acle, 3) AS acle,
  ROUND(acl2, 3) AS acl2,
  ROUND(relegation, 3) AS relegation
FROM result
ORDER BY points DESC