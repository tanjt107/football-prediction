SELECT
    footystats.id AS name,
    offence,
    defence
FROM ${project_id}.master.leagues
JOIN `${project_id}.footystats.teams` footystats ON leagues.latest_season_id = footystats._SEASON_ID
JOIN `${project_id}.master.teams` master ON footystats.id = master.footystats_id
JOIN `${project_id}.solver.teams_latest` solver ON master.solver_id = solver.id
WHERE leagues.footystats_id = league
  AND leagues.type = solver._TYPE