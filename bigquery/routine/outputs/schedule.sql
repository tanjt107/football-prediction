WITH
  hkjc AS (
  SELECT
    odds_had.matchID,
    odds_had.matchDate,
    leagues.division AS league_division,
    leagues.type AS league_type,
    leagues.transfermarkt_id AS league_transfermarkt_id,
    home_teams.solver_id AS home_solver_id,
    home_teams.transfermarkt_id AS home_transfermarkt_id,
    odds_had.homeTeam.teamNameCH AS home_name,
    away_teams.solver_id AS away_solver_id,
    away_teams.transfermarkt_id AS away_transfermarkt_id,
    odds_had.awayTeam.teamNameCH AS away_name,
    CAST(odds_had.venue IS NULL AS INT64) AS home_adv,
    CAST(SPLIT(hadodds.H, '@')[OFFSET(1)] AS FLOAT64) AS had_H,
    CAST(SPLIT(hadodds.D, '@')[OFFSET(1)] AS FLOAT64) AS had_D,
    CAST(SPLIT(hadodds.A, '@')[OFFSET(1)] AS FLOAT64) AS had_A,
    hdcodds.HG AS hdc,
    CAST(SPLIT(hdcodds.H, '@')[OFFSET(1)] AS FLOAT64) AS hdc_H,
    CAST(SPLIT(hdcodds.A, '@')[OFFSET(1)] AS FLOAT64) AS hdc_A
  FROM `hkjc.odds_had` odds_had
  JOIN `master.leagues` leagues ON odds_had.tournament.tournamentShortName = leagues.hkjc_id
  JOIN `master.teams` home_teams ON odds_had.homeTeam.teamID = home_teams.hkjc_id
  JOIN `master.teams` away_teams ON odds_had.awayTeam.teamID = away_teams.hkjc_id
  LEFT JOIN `hkjc.odds_hdc` odds_hdc ON odds_had.matchID = odds_hdc.matchID
  WHERE odds_had.matchState = 'PreEvent'
  ),

  footystats AS (
  SELECT
    matches.id,
    date_unix,
    leagues.division AS league_division,
    leagues.type AS league_type,
    leagues.transfermarkt_id AS league_transfermarkt_id,
    home_teams.solver_id AS home_solver_id,
    home_teams.transfermarkt_id AS home_transfermarkt_id,
    home_teams.name AS home_name,
    away_teams.solver_id AS away_solver_id,
    away_teams.transfermarkt_id AS away_transfermarkt_id,
    away_teams.name AS away_name
  FROM `footystats.matches` matches
  JOIN `footystats.seasons` seasons ON competition_id = seasons.id
  JOIN `master.leagues` leagues
  ON seasons.country = leagues.country
    AND seasons.name = leagues.footystats_name
  JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  WHERE matches.status = 'incomplete'
    AND date_unix <= UNIX_SECONDS(TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 5 DAY))
    AND ( home_teams.country = 'Hong Kong'
      OR away_teams.country = 'Hong Kong' ) 
  ),

  matches AS (
  SELECT
    matchID,
    matchDate,
    league_division,
    league_type,
    league_transfermarkt_id,
    home_solver_id,
    home_transfermarkt_id,
    home_name,
    away_solver_id,
    away_transfermarkt_id,
    away_name,
    home_adv,
    had_H,
    had_D,
    had_A,
    hdc,
    hdc_H,
    hdc_A
  FROM hkjc
  UNION ALL
  SELECT
    CAST(footystats.id AS STRING) AS matchID,
    TIMESTAMP_SECONDS(date_unix) AS matchDate,
    league_division,
    league_type,
    league_transfermarkt_id,
    home_solver_id,
    home_transfermarkt_id,
    home_name,
    away_solver_id,
    away_transfermarkt_id,
    away_name,
    1,
    NULL,
    NULL,
    NULL,
    CAST(NULL AS STRING),
    NULL,
    NULL
  FROM footystats
  ),

  exp_goals AS (
  SELECT
    matchID,
    hdc,
    avg_goal + league_solver.home_adv * matches.home_adv + home_solver.offence + away_solver.defence AS home_exp,
    avg_goal - league_solver.home_adv * matches.home_adv + away_solver.offence + home_solver.defence AS away_exp
  FROM matches
  LEFT JOIN `solver.leagues` league_solver ON matches.league_division = league_solver.division
    AND matches.league_type = league_solver.type
  LEFT JOIN `solver.teams` home_solver ON matches.home_solver_id = home_solver.id
  LEFT JOIN `solver.teams` away_solver ON matches.away_solver_id = away_solver.id
  ),

  match_probs AS (
  SELECT
    matchID,
    home_exp,
    away_exp,
    functions.matchProbs(home_exp, away_exp, '0') AS had_probs,
    functions.matchProbs(home_exp, away_exp, hdc) AS hdc_probs
  FROM exp_goals 
  ),

  probs AS (
  SELECT
    matchID,
    home_exp,
    away_exp,
    had_probs[OFFSET(0)] AS had_home,
    had_probs[OFFSET(1)] AS had_draw,
    had_probs[OFFSET(2)] AS had_away,
    hdc_probs[OFFSET(0)] AS hdc_home,
    hdc_probs[OFFSET(2)] AS hdc_away,
  FROM match_probs
  )

SELECT
  FORMAT_TIMESTAMP('%F %H:%M', matchDate, 'Asia/Hong_Kong') AS matchDate,
  league_transfermarkt_id,
  home_transfermarkt_id,
  home_name,
  away_transfermarkt_id,
  away_name,
  ROUND(home_exp, 2) AS home_exp,
  ROUND(away_exp, 2) AS away_exp,
  ROUND(had_home, 2) AS had_home,
  ROUND(had_draw, 2) AS had_draw,
  ROUND(had_away, 2) AS had_away,
  had_H,
  had_D,
  had_A,
  ROUND(GREATEST(had_home - (1 - had_home) / (had_H - 1), 0), 2) AS kelly_had_home,
  ROUND(GREATEST(had_draw - (1 - had_draw) / (had_D - 1), 0), 2) AS kelly_had_draw,
  ROUND(GREATEST(had_away - (1 - had_away) / (had_A - 1), 0), 2) AS kelly_had_away,
  hdc,
  ROUND(hdc_home, 2) AS hdc_home,
  ROUND(hdc_away, 2) AS hdc_away,
  hdc_H,
  hdc_A,
  ROUND(GREATEST(hdc_home - hdc_away / (hdc_H - 1), 0), 2) AS kelly_hdc_home,
  ROUND(GREATEST(hdc_away - hdc_home / (hdc_A - 1), 0), 2) AS kelly_hdc_away
FROM matches
JOIN probs ON matches.matchID = probs.matchID
ORDER BY matchDate, matches.matchID;