SELECT
  RANK() OVER(ORDER BY rating DESC) AS rank,
  transfermarkt_id,
  name,
  ROUND(offence, 1) AS offence,
  ROUND(defence, 1) AS defence,
  ROUND(rating, 1) AS rating
FROM `solver.team_ratings` ratings
JOIN `master.teams` teams ON ratings.id = teams.solver_id
  AND _TYPE = type
WHERE transfermarkt_id IS NOT NULL
  AND _TYPE = 'International'
ORDER BY rank;