SELECT
  RANK() OVER(ORDER BY rating DESC) AS rank,
  transfermarkt_id,
  name,
  ROUND(offence, 1) AS offence,
  ROUND(defence, 1) AS defence,
  ROUND(rating, 1) AS rating
FROM `master.team_ratings` ratings
JOIN `master.teams` teams ON ratings.id = teams.solver_id
WHERE in_team_rating AND type = 'International'
ORDER BY rank;