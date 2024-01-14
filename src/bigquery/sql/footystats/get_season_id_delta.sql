SELECT
  DISTINCT _NAME AS name,
  _SEASON_ID AS season_id,
  _COUNTRY AS country,
  _YEAR AS year
FROM `${project_id}.footystats.matches`
WHERE status = 'incomplete'
  AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP())