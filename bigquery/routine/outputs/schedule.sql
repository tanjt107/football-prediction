WITH
  odds AS (
  SELECT
    matchID,
    matchDate,
    home_teams.id AS home_id,
    away_teams.id AS away_id,
    CAST(SPLIT(hadodds.H, '@')[OFFSET(1)] AS FLOAT64) AS had_H,
    CAST(SPLIT(hadodds.D, '@')[OFFSET(1)] AS FLOAT64) AS had_D,
    CAST(SPLIT(hadodds.A, '@')[OFFSET(1)] AS FLOAT64) AS had_A,
    CAST(venue IS NULL AS INT64) AS home_adv
  FROM `hkjc.odds_had` odds
  JOIN `master.teams` home_teams ON odds.homeTeam.teamID = home_teams.hkjc_id
  JOIN `master.teams` away_teams ON odds.awayTeam.teamID = away_teams.hkjc_id
  WHERE matchState = 'PreEvent' 
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
    GREATEST(home_exp, 0.2) AS home_exp,
    GREATEST(away_exp, 0.2) AS away_exp
  FROM non_hkjc
  ),

  match_probs AS (
  SELECT
    matchID,
    functions.matchProbs(home_exp, away_exp, 5) AS match_prob
  FROM matches 
  ),

  had_probs AS (
  SELECT
    matchID,
    match_prob[OFFSET(0)] AS prob_home,
    match_prob[OFFSET(1)] AS prob_draw,
    match_prob[OFFSET(2)] AS prob_away
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
  ROUND(prob_home, 2) AS prob_home,
  ROUND(prob_draw, 2) AS prob_draw,
  ROUND(prob_away, 2) AS prob_away,
  had_H,
  had_D,
  had_A,
  ROUND(GREATEST(prob_home - (1 - prob_home) / (had_H - 1),0), 2) AS kelly_home,
  ROUND(GREATEST(prob_draw - (1 - prob_draw) / (had_D - 1),0), 2) AS kelly_draw,
  ROUND(GREATEST(prob_away - (1 - prob_away) / (had_A - 1),0), 2) AS kelly_away
FROM matches
JOIN `master.teams` home_teams ON matches.home_id = home_teams.id
JOIN `master.teams` away_teams ON matches.away_id = away_teams.id
JOIN had_probs ON matches.matchID = had_probs.matchID
LEFT JOIN `master.leagues` leagues ON matches.league_id = leagues.id
ORDER BY matchDate, matches.matchID;