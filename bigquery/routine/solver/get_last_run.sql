SELECT
    COALESCE(MAX(_DATE_UNIX), 0) AS last_run
FROM `${project_id}.solver.teams` teams
WHERE _TYPE = _type