WITH
  hkjc AS (
  SELECT
    id AS match_id,
    kick_off_time,
    leagues.division AS league_division,
    leagues.type AS league_type,
    leagues.transfermarkt_id AS league_transfermarkt_id,
    COALESCE(display_order, '31') AS display_order,
    home_teams.solver_id AS home_solver_id,
    home_teams.transfermarkt_id AS home_transfermarkt_id,
    home_teams.type AS home_type,
    home_name,
    away_teams.solver_id AS away_solver_id,
    away_teams.transfermarkt_id AS away_transfermarkt_id,
    away_teams.type AS away_type,
    away_name,
    home_adv,
    HAD_H,
    HAD_D,
    HAD_A,
    update_at
  FROM hkjc.odds_today
  LEFT JOIN `master.teams` home_teams ON odds_today.home_id = home_teams.hkjc_id
  LEFT JOIN `master.teams` away_teams ON odds_today.away_id = away_teams.hkjc_id
  LEFT JOIN master.leagues ON odds_today.tournament_id = leagues.hkjc_id
  ),

  footystats AS (
  SELECT
    matches.id,
    date_unix,
    leagues.division AS league_division,
    leagues.type AS league_type,
    leagues.transfermarkt_id AS league_transfermarkt_id,
    COALESCE(leagues.display_order, '00') AS display_order,
    home_teams.solver_id AS home_solver_id,
    home_teams.transfermarkt_id AS home_transfermarkt_id,
    home_teams.type AS home_type,
    home_teams.name AS home_name,
    away_teams.solver_id AS away_solver_id,
    away_teams.transfermarkt_id AS away_transfermarkt_id,
    away_teams.type AS away_type,
    away_teams.name AS away_name,
    no_home_away
  FROM footystats.matches
  JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN master.leagues ON matches._NAME = leagues.footystats_name
  WHERE matches.status = 'incomplete'
    AND date_unix <= UNIX_SECONDS(TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 3 DAY))
    AND (home_teams.country = 'Hong Kong'
      OR away_teams.country = 'Hong Kong'
      OR leagues.is_manual)
  ),

  matches AS (
  SELECT
    match_id,
    kick_off_time,
    league_division,
    league_type,
    league_transfermarkt_id,
    display_order,
    home_solver_id,
    home_transfermarkt_id,
    home_type,
    home_name,
    away_solver_id,
    away_transfermarkt_id,
    away_type,
    away_name,
    home_adv,
    had_H,
    had_D,
    had_A,
    update_at
  FROM hkjc
  UNION ALL
  SELECT
    footystats.id,
    TIMESTAMP_SECONDS(date_unix),
    league_division,
    league_type,
    league_transfermarkt_id,
    display_order,
    home_solver_id,
    home_transfermarkt_id,
    home_type,
    home_name,
    away_solver_id,
    away_transfermarkt_id,
    away_type,
    away_name,
    1 - no_home_away,
    NULL,
    NULL,
    NULL,
    NULL
  FROM footystats
  ),

  exp_goals AS (
  SELECT
    match_id,
    GREATEST(avg_goal + leagues_latest.home_adv * matches.home_adv + home_solver.offence + away_solver.defence, 0.2) AS home_exp,
    GREATEST(avg_goal - leagues_latest.home_adv * matches.home_adv + away_solver.offence + home_solver.defence, 0.2) AS away_exp
  FROM matches
  JOIN `solver.teams_latest` home_solver ON matches.home_solver_id = home_solver.id
    AND matches.home_type = home_solver._TYPE
  JOIN `solver.teams_latest` away_solver ON matches.away_solver_id = away_solver.id
    AND matches.away_type = away_solver._TYPE
  JOIN solver.leagues_latest ON matches.league_division = leagues_latest.division
    AND matches.league_type = leagues_latest._TYPE
  ),

  match_probs AS (
  SELECT
    match_id,
    home_exp,
    away_exp,
    functions.matchProbs(home_exp, away_exp, '0') AS had_probs
  FROM exp_goals 
  )

SELECT
  FORMAT_TIMESTAMP('%F %H:%M', kick_off_time, 'Asia/Hong_Kong') AS kick_off_time,
  league_transfermarkt_id,
  home_transfermarkt_id,
  home_name,
  away_transfermarkt_id,
  away_name,
  ROUND(home_ratings.rating, 1) AS home_rating,
  ROUND(away_ratings.rating, 1) AS away_rating,
  ROUND(home_exp, 2) AS home_exp,
  ROUND(away_exp, 2) AS away_exp,
  ROUND(had_probs[0], 2) AS had_home,
  ROUND(had_probs[1], 2) AS had_draw,
  ROUND(had_probs[2], 2) AS had_away,
  had_H,
  had_D,
  had_A,
  FORMAT_TIMESTAMP('%F %H:%M', update_at, 'Asia/Hong_Kong') AS update_at
FROM matches
LEFT JOIN `solver.team_ratings` home_ratings ON matches.home_solver_id = home_ratings.id
  AND matches.home_type = home_ratings._TYPE
LEFT JOIN `solver.team_ratings` away_ratings ON matches.away_solver_id = away_ratings.id
  AND matches.away_type = away_ratings._TYPE
LEFT JOIN match_probs USING (match_id)
ORDER BY FORMAT_TIMESTAMP('%F', matches.kick_off_time, 'Etc/GMT+4'), display_order, league_transfermarkt_id, kick_off_time, match_id;