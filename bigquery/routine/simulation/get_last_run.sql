SELECT COALESCE(MAX(_DATE_UNIX), 0) AS last_run
FROM `${project_id}.simulation.leagues`
WHERE _LEAGUE = league