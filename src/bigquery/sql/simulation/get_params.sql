SELECT
    footystats_name
FROM ${project_id}.master.leagues
WHERE is_simulate
    AND type = type