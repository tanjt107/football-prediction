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
    COALESCE(positions.1 + positions.2 * 0.5, 0) AS acle,
    COALESCE(positions.2 * 0.5 + positions.3, 0) AS acl2,
    COALESCE(positions.15 + positions.16, 0) AS relegation
  FROM `simulation.csl` sim
  JOIN `master.teams` teams ON sim.team = teams.solver_id
  JOIN `master.team_ratings` ratings ON sim.team = ratings.id
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 1) AS offence,
  ROUND(defence, 1) AS defence,
  ROUND(goal_diff, 1) AS goal_diff,
  ROUND(points, 1) AS points,
  ROUND(champ, 2) AS champ,
  ROUND(acle, 2) AS acle,
  ROUND(acl2, 2) AS acl2,
  ROUND(relegation, 2) AS relegation
FROM result
ORDER BY points DESC