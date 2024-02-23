SELECT
  DISTINCT _NAME AS name,
  _SEASON_ID AS season_id,
  _COUNTRY AS country,
  _YEAR AS year
FROM `${project_id}.footystats.matches`
WHERE 
  date_unix > UNIX_SECONDS(TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -3 DAY))
  AND ((status = 'incomplete' AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP()))
    OR (status = 'complete' AND total_xg = 0))