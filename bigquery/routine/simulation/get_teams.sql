SELECT
    footystats.id AS name,
    offence,
    defence
FROM `${project_id}.master.leagues` leagues
JOIN `${project_id}.footystats.teams` footystats ON leagues.latest_season_id = footystats.competition_id
JOIN `${project_id}.master.teams` master_teams ON footystats.id = master_teams.footystats_id
JOIN `${project_id}.solver.teams_latest` solver ON master_teams.solver_id = solver.id
WHERE leagues.footystats_id = league
  AND leagues.type = solver._TYPE