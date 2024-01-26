SELECT
    specific_tables.round,
    homeId,
    awayId,
    homeGoalCount,
    awayGoalCount
FROM ${project_id}.footystats.matches
JOIN ${project_id}.master.leagues ON matches._SEASON_ID = leagues.latest_season_id
JOIN ${project_id}.footystats.tables ON matches._SEASON_ID = tables._SEASON_ID
JOIN tables.specific_tables ON matches.roundID = specific_tables.round_id
WHERE matches._NAME = league
    AND specific_tables.round = stage
    AND status = 'complete'