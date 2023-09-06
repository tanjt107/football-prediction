WITH
  odds_had AS (
  SELECT
    matchID,
    matchDate,
    tournament.tournamentShortName AS tournament,
    homeTeam.teamID AS homeID,
    awayTeam.TeamID AS awayID,
    CAST(SPLIT(hadodds.H, '@')[OFFSET(1)] AS FLOAT64) AS had_H,
    CAST(SPLIT(hadodds.D, '@')[OFFSET(1)] AS FLOAT64) AS had_D,
    CAST(SPLIT(hadodds.A, '@')[OFFSET(1)] AS FLOAT64) AS had_A,
    CAST(venue IS NULL AS INT64) AS home_adv
  FROM
    `hkjc.odds_had`
  WHERE
    matchState = 'PreEvent'),

  divisions AS (
  SELECT
    DISTINCT country,
    name,
    CASE
      WHEN country IN ( SELECT country FROM `footystats.season` GROUP BY country HAVING MAX(division) > 1 ) AND division > 0 THEN CONCAT(country, division)
    ELSE
    country
  END
    AS country_division
  FROM
    `footystats.season` ),

  matches AS (
  SELECT
    date_unix,
    matches.competition_id,
    homeID,
    home_team.country AS home_country,
    awayID,
    away_team.country AS away_country,
    avg_goal + home_solver.offence + away_solver.defence AS home_exp,
    avg_goal + away_solver.offence + home_solver.defence AS away_exp,
    home_adv
  FROM
    `footystats.matches` matches
  JOIN
    `footystats.season` season
  ON
    competition_id = season.id
  JOIN
    `footystats.teams` home_team
  ON
    matches.homeID = home_team.id
    AND matches.competition_id = home_team.competition_id
  JOIN
    `footystats.teams` away_team
  ON
    matches.awayID = away_team.id
    AND matches.competition_id = away_team.competition_id
  LEFT JOIN
    `solver.teams` home_solver
  ON
    homeID = home_solver.team
  LEFT JOIN
    `solver.teams` away_solver
  ON
    awayID = away_solver.team
  JOIN
    divisions
  ON
    season.country = divisions.country
    AND season.name = divisions.name
  JOIN
    `solver.leagues` leagues
  ON
    country_division = leagues.league
  WHERE
    matches.status = 'incomplete'),

  exp_goals_hkjc AS (
  SELECT
    matchID,
    COALESCE(matches_home.home_exp + matches_home.home_adv * odds.home_adv, matches_away.away_exp + matches_away.home_adv * odds.home_adv) AS home_exp,
    COALESCE(matches_home.away_exp - matches_home.home_adv * odds.home_adv, matches_away.home_exp - matches_away.home_adv * odds.home_adv) AS away_exp
  FROM
    odds_had odds
  LEFT JOIN
    `mapping.team_info` home_team
  ON
    odds.homeID = home_team.hkjc_id
  LEFT JOIN
    `mapping.team_info` away_team
  ON
    odds.awayID = away_team.hkjc_id
  LEFT JOIN
    matches matches_home
  ON
    ABS(TIMESTAMP_DIFF(odds.matchDate, TIMESTAMP_SECONDS(matches_home.date_unix), HOUR) ) < 1
    AND (home_team.footystats_id = matches_home.homeID
      AND away_team.footystats_id = matches_home.awayID)
  LEFT JOIN
    matches matches_away
  ON
    ABS(TIMESTAMP_DIFF(odds.matchDate, TIMESTAMP_SECONDS(matches_away.date_unix), HOUR) ) < 1
    AND (home_team.footystats_id = matches_away.awayID
      AND away_team.footystats_id = matches_away.homeID)),

  had_probs_hkjc AS (
  SELECT
    matchID,
    home_exp,
    away_exp,
    solver.matchProbs(home_exp, away_exp, 5)[OFFSET(0)] AS prob_home,
    solver.matchProbs(home_exp, away_exp, 5)[OFFSET(1)] AS prob_draw,
    solver.matchProbs(home_exp, away_exp, 5)[OFFSET(2)] AS prob_away
  FROM
    exp_goals_hkjc ),

  hkjc AS (
  SELECT
    FORMAT_TIMESTAMP('%F %T', matchDate, 'Asia/Hong_Kong') AS matchDate,
    league.transfermarkt_id AS league_transfermarkt_id,
    home_team.transfermarkt_id AS home_transfermarkt_id,
    home_team.nameC AS home_nameC,
    away_team.transfermarkt_id AS away_transfermarkt_id,
    away_team.nameC AS away_nameC,
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
  FROM
    odds_had odds
  LEFT JOIN
    `mapping.hkjc_leagues` mapping
  ON
    odds.tournament = mapping.code
  LEFT JOIN
    `mapping.league_info` league
  ON
    mapping.country = league.country
    AND mapping.name = league.name
  LEFT JOIN
    `mapping.team_info` home_team
  ON
    odds.homeID = home_team.hkjc_id
  LEFT JOIN
    `mapping.team_info` away_team
  ON
    odds.awayID = away_team.hkjc_id
  LEFT JOIN
    had_probs_hkjc
  ON
    odds.matchID = had_probs_hkjc.matchID),

  exp_goals_hk AS (
  SELECT
    homeID,
    awayID,
    home_exp + home_adv AS home_exp,
    away_exp - home_adv AS away_exp
  FROM
    matches
  WHERE
    TIMESTAMP_DIFF(TIMESTAMP_SECONDS(date_unix), CURRENT_TIMESTAMP(), DAY) <= 5
    AND ( matches.home_country = 'Hong Kong'
      OR matches.away_country = 'Hong Kong' )),

  had_probs_hk AS (
  SELECT
    homeID,
    awayID,
    home_exp,
    away_exp,
    solver.matchProbs(home_exp, away_exp, 5)[OFFSET(0)] AS prob_home,
    solver.matchProbs(home_exp, away_exp, 5)[OFFSET(1)] AS prob_draw,
    solver.matchProbs(home_exp, away_exp, 5)[OFFSET(2)] AS prob_away
  FROM
    exp_goals_hk ),

  hk AS (
  SELECT
    FORMAT_TIMESTAMP('%F %T', TIMESTAMP_SECONDS(date_unix), 'Asia/Hong_Kong') AS matchDate,
    league.transfermarkt_id AS league_transfermarkt_id,
    home_team.transfermarkt_id AS home_transfermarkt_id,
    home_team.nameC AS home_nameC,
    away_team.transfermarkt_id AS away_transfermarkt_id,
    away_team.nameC AS away_nameC,
    ROUND(had_probs_hk.home_exp, 2) AS home_exp,
    ROUND(had_probs_hk.away_exp, 2) AS away_exp,
    ROUND(prob_home, 2) AS prob_home,
    ROUND(prob_draw, 2) AS prob_draw,
    ROUND(prob_away, 2) AS prob_away,
    NULL AS had_H,
    NULL AS had_D,
    NULL AS had_A,
    NULL AS kelly_home,
    NULL AS kelly_draw,
    NULL AS kelly_away
  FROM
    had_probs_hk
  JOIN
    matches
  ON
    matches.homeID= had_probs_hk.homeID
    AND matches.awayID = had_probs_hk.awayID
  JOIN
    `footystats.season` season
  ON
    matches.competition_id = season.id
  LEFT JOIN
    `mapping.league_info` league
  ON
    season.country = league.country
    AND season.name = league.name
  LEFT JOIN
    `mapping.team_info` home_team
  ON
    matches.homeID = home_team.footystats_id
  LEFT JOIN
    `mapping.team_info` away_team
  ON
    matches.awayID = away_team.footystats_id )

SELECT
  *
FROM
  hkjc
UNION ALL
SELECT
  *
FROM
  hk
ORDER BY matchDate;