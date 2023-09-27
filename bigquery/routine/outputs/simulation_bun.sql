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
    COALESCE(positions.1, 0) + COALESCE(positions.2, 0) + COALESCE(positions.3, 0) + COALESCE(positions.4, 0) AS ucl,
    COALESCE(positions.5, 0) AS uel,
    COALESCE(positions.16 * 0.5 + positions.17 + positions.18, 0) AS relegation
  FROM `simulation.bun` sim
  JOIN `master.teams` teams ON sim.team = teams.solver_id
  JOIN `master.team_ratings` ratings ON sim.team = ratings.id
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(goal_diff) AS goal_diff,
  ROUND(points) AS points,
  ROUND(champ, 2) AS champ,
  ROUND(ucl, 2) AS ucl,
  ROUND(uel, 2) AS uel,
  ROUND(relegation, 2) AS relegation
FROM result
ORDER BY points DESC