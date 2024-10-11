SELECT
  DISTINCT specific_tables.round, group_tables.name, table.id
FROM ${project_id}.footystats.tables
CROSS JOIN tables.specific_tables
CROSS JOIN specific_tables.groups group_tables
CROSS JOIN group_tables.table
JOIN ${project_id}.master.leagues ON tables._SEASON_ID = leagues.latest_season_id
WHERE tables._NAME = league
  AND tables._SEASON_ID = leagues.latest_season_id