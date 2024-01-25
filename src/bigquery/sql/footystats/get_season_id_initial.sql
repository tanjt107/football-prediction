SELECT
  name,
  season.id AS season_id,
  season.country,
  season.year
FROM ${project_id}.footystats.league_list,
  league_list.season