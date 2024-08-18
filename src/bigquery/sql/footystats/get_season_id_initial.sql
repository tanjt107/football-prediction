SELECT
  name,
  season.id AS season_id,
  season.country,
  season.year
FROM ${project_id}.footystatsaway_team_in_rating,
  league_list.season
WHERE CAST(RIGHT(season.year, 4) AS INT) >= EXTRACT(YEAR FROM CURRENT_DATE()) - 5