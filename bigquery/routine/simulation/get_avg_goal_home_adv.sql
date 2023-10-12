SELECT
    avg_goal,
    home_adv
FROM `${project_id}.solver.leagues` solver
JOIN `${project_id}.master.leagues` master ON solver.division = master.division
WHERE footystats_id = league