SELECT
    COALESCE(MAX(date_unix), -1) AS max_date_unix
FROM `${project_id}.footystats.matches`
WHERE _NAME = league
  AND status = 'complete'