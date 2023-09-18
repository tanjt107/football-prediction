WITH
  odds AS (
  SELECT
    odds_had.matchID,
    odds_had.matchDate,
    home_teams.id AS home_id,
    away_teams.id AS away_id,
    CAST(SPLIT(hadodds.H, '@')[OFFSET(1)] AS FLOAT64) AS had_H,
    CAST(SPLIT(hadodds.D, '@')[OFFSET(1)] AS FLOAT64) AS had_D,
    CAST(SPLIT(hadodds.A, '@')[OFFSET(1)] AS FLOAT64) AS had_A,
    hdcodds.HG AS hdc,
    CAST(SPLIT(hdcodds.H, '@')[OFFSET(1)] AS FLOAT64) AS hdc_H,
    CAST(SPLIT(hdcodds.A, '@')[OFFSET(1)] AS FLOAT64) AS hdc_A,
    CAST(odds_had.venue IS NULL AS INT64) AS home_adv
  FROM `hkjc.odds_had` odds_had
  JOIN `master.teams` home_teams ON odds_had.homeTeam.teamID = home_teams.hkjc_id
  JOIN `master.teams` away_teams ON odds_had.awayTeam.teamID = away_teams.hkjc_id
  LEFT JOIN `hkjc.odds_hdc` odds_hdc ON odds_had.matchID = odds_hdc.matchID
  WHERE odds_had.matchState = 'PreEvent' 
  ),

  footystats AS (
  SELECT
    matches.id,
    TIMESTAMP_SECONDS(date_unix) AS matchDate,
    leagues.id AS league_id,
    home_teams.id AS home_id,
    away_teams.id AS away_id,
    avg_goal + home_solver.offence + away_solver.defence AS home_exp,
    avg_goal + away_solver.offence + home_solver.defence AS away_exp,
    home_adv
  FROM `footystats.matches` matches
  JOIN `footystats.seasons` seasons ON competition_id = seasons.id
  JOIN `master.leagues` leagues
  ON seasons.country = leagues.country
    AND seasons.name = leagues.footystats_name
  JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  LEFT JOIN `solver.teams` home_solver ON home_teams.id = home_solver.id
  LEFT JOIN `solver.teams` away_solver ON away_teams.id = away_solver.id
  LEFT JOIN `solver.leagues` league_solver ON leagues.division = league_solver.division
    AND leagues.type = REGEXP_EXTRACT(league_solver._FILE_NAME, r".*/(.*)\.json")
  WHERE matches.status = 'incomplete' 
  ),

  hkjc AS (
  SELECT
    matchID,
    odds.matchDate,
    COALESCE(footystats_home.league_id, footystats_away.league_id) AS league_id,
    odds.home_id,
    odds.away_id,
    had_H,
    had_D,
    had_A,
    hdc,
    hdc_H,
    hdc_A,
    COALESCE(footystats_home.home_exp + footystats_home.home_adv * odds.home_adv, footystats_away.away_exp + footystats_away.home_adv * odds.home_adv) AS home_exp,
    COALESCE(footystats_home.away_exp - footystats_home.home_adv * odds.home_adv, footystats_away.home_exp - footystats_away.home_adv * odds.home_adv) AS away_exp,
  FROM odds
  LEFT JOIN footystats footystats_home
  ON ABS(TIMESTAMP_DIFF(odds.matchDate, footystats_home.matchDate, HOUR) ) < 1
    AND odds.home_id = footystats_home.home_id
    AND odds.away_id = footystats_home.away_id
  LEFT JOIN footystats footystats_away
  ON ABS(TIMESTAMP_DIFF(odds.matchDate, footystats_away.matchDate, HOUR) ) < 1
    AND odds.home_id = footystats_away.away_id
    AND odds.away_id = footystats_away.home_id
  ),

  non_hkjc AS (
  SELECT
    CAST(footystats.id AS STRING) AS matchID,
    matchDate,
    footystats.league_id,
    home_id,
    away_id,
    NULL AS had_H,
    NULL AS had_D,
    NULL AS had_A,
    CAST(NULL AS STRING) AS hdc,
    NULL AS hdc_H,
    NULL AS hdc_A,
    home_exp + home_adv AS home_exp,
    away_exp - home_adv AS away_exp
  FROM footystats
  JOIN `master.teams` home_teams ON footystats.home_id = home_teams.id
  JOIN `master.teams` away_teams ON footystats.away_id = away_teams.id
  WHERE TIMESTAMP_DIFF(matchDate, CURRENT_TIMESTAMP(), DAY) <= 5
    AND ( home_teams.country = 'Hong Kong'
      OR away_teams.country = 'Hong Kong' )
  ),

  matches AS (
  SELECT
    matchID,
    matchDate,
    league_id,
    home_id,
    away_id,
    had_H,
    had_D,
    had_A,
    hdc,
    hdc_H,
    hdc_A,
    GREATEST(home_exp, 0.2) AS home_exp,
    GREATEST(away_exp, 0.2) AS away_exp
  FROM hkjc
  UNION ALL
  SELECT
    matchID,
    matchDate,
    league_id,
    home_id,
    away_id,
    had_H,
    had_D,
    had_A,
    hdc,
    hdc_H,
    hdc_A,
    GREATEST(home_exp, 0.2) AS home_exp,
    GREATEST(away_exp, 0.2) AS away_exp
  FROM non_hkjc
  ),

  match_probs AS (
  SELECT
    matchID,
    functions.matchProbs(home_exp, away_exp, '0', 5) AS had_probs,
    functions.matchProbs(home_exp, away_exp, hdc, 5) AS hdc_probs
  FROM matches 
  ),

  probs AS (
  SELECT
    matchID,
    had_probs[OFFSET(0)] AS had_home,
    had_probs[OFFSET(1)] AS had_draw,
    had_probs[OFFSET(2)] AS had_away,
    hdc_probs[OFFSET(0)] AS hdc_home,
    hdc_probs[OFFSET(2)] AS hdc_away,
  FROM match_probs
  )

SELECT
  FORMAT_TIMESTAMP('%F %H:%M', matchDate, 'Asia/Hong_Kong') AS matchDate,
  leagues.transfermarkt_id AS league_logo,
  home_teams.transfermarkt_id AS home_team_logo,
  home_teams.name AS home_team_name,
  away_teams.transfermarkt_id AS away_team_logo,
  away_teams.name AS away_team_name,
  ROUND(home_exp, 2) AS home_exp,
  ROUND(away_exp, 2) AS away_exp,
  ROUND(had_home, 2) AS had_home,
  ROUND(had_draw, 2) AS had_draw,
  ROUND(had_away, 2) AS had_away,
  had_H,
  had_D,
  had_A,
  ROUND(GREATEST(had_home - (1 - had_home) / (had_H - 1),0), 2) AS kelly_had_home,
  ROUND(GREATEST(had_draw - (1 - had_draw) / (had_D - 1),0), 2) AS kelly_had_draw,
  ROUND(GREATEST(had_away - (1 - had_away) / (had_A - 1),0), 2) AS kelly_had_away,
  hdc,
  ROUND(hdc_home, 2) AS hdc_home,
  ROUND(hdc_away, 2) AS hdc_away,
  hdc_H,
  hdc_A,
  ROUND(GREATEST(hdc_home - hdc_away / (hdc_H - 1),0), 2) AS kelly_hdc_home,
  ROUND(GREATEST(hdc_away - hdc_home / (hdc_A - 1),0), 2) AS kelly_hdc_away
FROM matches
JOIN `master.teams` home_teams ON matches.home_id = home_teams.id
JOIN `master.teams` away_teams ON matches.away_id = away_teams.id
JOIN probs ON matches.matchID = probs.matchID
LEFT JOIN `master.leagues` leagues ON matches.league_id = leagues.id
ORDER BY matchDate, matches.matchID;