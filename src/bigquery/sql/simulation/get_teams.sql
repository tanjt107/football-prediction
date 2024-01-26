SELECT
    footystats.id AS name,
    offence,
    defence
FROM `${project_id}.master.teams` master
JOIN `${project_id}.footystats.teams` footystats ON master.footystats_id = footystats.id
JOIN `${project_id}.master.leagues` leagues ON footystats._SEASON_ID = leagues.latest_season_id
JOIN `${project_id}.solver.teams_latest` solver ON master.solver_id = solver.id
  AND leagues.type = solver._TYPE
WHERE leagues.footystats_id = league