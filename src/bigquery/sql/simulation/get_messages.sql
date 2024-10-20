SELECT
    footystats_name, MAX(date_unix) AS latest_match_date, MAX(_DATE_UNIX) AS last_run
FROM ${project_id}.master.leagues master
JOIN ${project_id}.footystats.matches ON master.latest_season_id = matches._SEASON_ID
LEFT JOIN ${project_id}.simulation.leagues simulation ON master.footystats_name = simulation._LEAGUE
WHERE status = 'complete'
    AND is_simulate
    AND type = type
GROUP BY footystats_name
HAVING latest_match_date > last_run