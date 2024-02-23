SELECT
    avg_goal,
    home_adv
FROM `${project_id}.solver.leagues` solver
JOIN `${project_id}.master.leagues` master USING (division)
WHERE footystats_name = league