SELECT
    homeId,
    awayId,
    homeGoalCount,
    awayGoalCount
FROM `${project_id}.footystats.matches` matches
JOIN `${project_id}.master.leagues` leagues ON matches._SEASON_ID = leagues.latest_season_id
WHERE status = 'complete'
    AND footystats_id = league