SELECT
  RANK() OVER(ORDER BY rating DESC) AS rank,
  teams.transfermarkt_id AS team_transfermarkt_id,
  teams.name AS team_name,
  leagues.transfermarkt_id As league_transfermarkt_id,
  leagues.name AS league_name,
  ROUND(offence, 1) AS offence,
  ROUND(defence, 1) AS defence,
  ROUND(rating, 1) AS rating
FROM `master.team_ratings` ratings
JOIN `master.teams` teams ON ratings.id = teams.solver_id
JOIN `master.leagues` leagues ON teams.league_id = leagues.id
WHERE in_team_rating AND teams.type = 'Club'
ORDER BY rank;