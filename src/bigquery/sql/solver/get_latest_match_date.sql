SELECT
    MAX(date_unix) AS max_date_unix
FROM ${project_id}.footystats.matches
JOIN ${project_id}.simulation.params ON matches._NAME = params.league
WHERE status = 'complete'
    AND type = 'Club'