SELECT
    MAX(date_unix) AS max_date_unix
FROM `${project_id}.footystats.matches`
WHERE _NAME = league
  AND status = 'complete'
  AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP())