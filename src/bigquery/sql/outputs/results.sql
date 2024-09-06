WITH matches AS (
  SELECT
    matches.id,
    leagues.display_order,
    matches.date_unix,
    leagues.transfermarkt_id AS league_transfermarkt_id,
    home_teams.transfermarkt_id AS home_team_transfermarkt_id,
    home_teams.name AS home_team_name,
    away_teams.transfermarkt_id AS away_team_transfermarkt_id,
    away_teams.name AS away_team_name,
    homeGoalCount,
    awayGoalCount,
    home_adj,
    away_adj,
    CASE
      WHEN team_a_xg > 0 THEN team_a_xg
    END AS team_a_xg,
    CASE
      WHEN team_b_xg > 0 THEN team_b_xg
    END AS team_b_xg,
    functions.matchProbs(
      league_solver.avg_goal + league_solver.home_adv + home_solver.offence + away_solver.defence,
      league_solver.avg_goal - league_solver.home_adv + away_solver.offence + home_solver.defence,
       '0') AS had_probs
  FROM footystats.matches
  JOIN footystats.matches_transformed USING (id)
  JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN master.leagues ON matches._NAME = leagues.footystats_name
  JOIN `solver.leagues` league_solver ON league_solver._DATE_UNIX < date_unix
    AND leagues.type = league_solver._TYPE
    AND leagues.division = league_solver.division
  JOIN `solver.teams` home_solver ON league_solver._DATE_UNIX = home_solver._DATE_UNIX
    AND league_solver._TYPE = home_solver._TYPE
    AND home_teams.solver_id = home_solver.id
  JOIN `solver.teams` away_solver ON league_solver._DATE_UNIX = away_solver._DATE_UNIX
    AND league_solver._TYPE = away_solver._TYPE
    AND away_teams.solver_id = away_solver.id
  WHERE matches.status = 'complete'
    AND date_unix >= UNIX_SECONDS(TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -5 DAY))
    AND (home_teams.is_simulate
      OR away_teams.is_simulate
      OR leagues.is_simulate)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY matches.id ORDER BY league_solver._DATE_UNIX DESC) = 1
  ORDER BY date_unix DESC, display_order, matches.id
  LIMIT 100
)

SELECT
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(date_unix), 'Asia/Hong_Kong') AS matchDate,
  league_transfermarkt_id,
  home_team_transfermarkt_id,
  home_team_name,
  away_team_transfermarkt_id,
  away_team_name,
  ROUND(had_probs[0], 2) AS had_home,
  ROUND(had_probs[1], 2) AS had_draw,
  ROUND(had_probs[2], 2) AS had_away,
  homeGoalCount,
  awayGoalCount,
  ROUND(home_adj, 2) AS home_adj,
  ROUND(away_adj, 2) AS away_adj,
  ROUND(team_a_xg, 2) AS team_a_xg,
  ROUND(team_b_xg, 2) AS team_b_xg
FROM matches
ORDER BY display_order, league_transfermarkt_id, date_unix DESC, matches.id