SELECT
    solver._TYPE, MAX(date_unix) + 1 AS latest_match_date, MAX(_DATE_UNIX) AS last_run
FROM ${project_id}.footystats.matches
JOIN `${project_id}.master.teams` home_teams ON matches.homeID = home_teams.footystats_id
JOIN `${project_id}.master.teams` away_teams ON matches.awayID = away_teams.footystats_id
JOIN ${project_id}.master.leagues ON matches._NAME = leagues.footystats_name
JOIN ${project_id}.solver.leagues solver ON leagues.type = solver._TYPE
WHERE status = 'complete'
    AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP()) -- TODO Remove after 2024/09/15
    AND (home_teams.is_simulate
      OR away_teams.is_simulate
      OR leagues.is_simulate)
GROUP BY solver._TYPE
-- HAVING latest_match_date > last_run