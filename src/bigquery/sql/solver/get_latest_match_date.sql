SELECT
    MAX(date_unix) AS max_date_unix
FROM ${project_id}.footystats.matches
JOIN ${project_id}.master.leagues ON matches._NAME = leagues.footystats_id
WHERE matches.status = 'complete'
    AND leagues.type = _type