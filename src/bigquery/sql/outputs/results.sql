WITH matches AS (
  SELECT
    matches.id,
    leagues.display_order,
    matches.date_unix,
    leagues.transfermarkt_id AS league_transfermarkt_id,
    leagues.division AS league_division,
    home_teams.transfermarkt_id AS home_team_transfermarkt_id,
    home_teams.name AS home_team_name,
    home_teams.solver_id AS home_solver_id,
    away_teams.transfermarkt_id AS away_team_transfermarkt_id,
    away_teams.name AS away_team_name,
    away_teams.solver_id AS away_solver_id,
    homeGoalCount,
    awayGoalCount,
    home_adj,
    away_adj,
    CASE
      WHEN team_a_xg > 0 THEN team_a_xg
      ELSE NULL
    END AS team_a_xg,
    CASE
      WHEN team_b_xg > 0 THEN team_b_xg
      ELSE NULL
    END AS team_b_xg,
    leagues.type
  FROM footystats.matches
  JOIN footystats.matches_transformed USING (id)
  JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN master.leagues ON matches._NAME = leagues.footystats_id
  WHERE matches.status = 'complete'
    AND (home_teams.league_name IN (
      '香港超級聯賽', '中國超級聯賽', '中國甲級聯賽', '英格蘭超級聯賽', '西班牙甲組聯賽', '德國甲組聯賽', '意大利甲組聯賽', '法國甲組聯賽', '日本職業聯賽'
      )
      OR away_teams.league_name IN (
      '香港超級聯賽', '中國超級聯賽', '中國甲級聯賽', '英格蘭超級聯賽', '西班牙甲組聯賽', '德國甲組聯賽', '意大利甲組聯賽', '法國甲組聯賽', '日本職業聯賽'
      )
      OR leagues.name IN ('亞洲盃', '非洲國家盃', '世盃外圍賽', '亞洲聯賽冠軍盃', '亞洲足協盃', '歐洲聯賽冠軍盃')
    )
  ORDER BY date_unix DESC, matches.id
  LIMIT 100
),

solver AS (
  SELECT
    matches.id,
    ARRAY_AGG(leagues ORDER BY leagues._DATE_UNIX DESC LIMIT 1)[0] AS league_solver,
    ARRAY_AGG(home_solver ORDER BY home_solver._DATE_UNIX DESC LIMIT 1)[0] AS home_solver,
    ARRAY_AGG(away_solver ORDER BY away_solver._DATE_UNIX DESC LIMIT 1)[0] AS away_solver,
  FROM matches
  JOIN solver.leagues ON leagues._DATE_UNIX < date_unix
    AND matches.type = leagues._TYPE
    AND matches.league_division = leagues.division
  JOIN `solver.teams` home_solver ON leagues._DATE_UNIX = home_solver._DATE_UNIX
    AND leagues._TYPE = home_solver._TYPE
    AND matches.home_solver_id = home_solver.id
  JOIN `solver.teams` away_solver ON leagues._DATE_UNIX = away_solver._DATE_UNIX
    AND leagues._TYPE = away_solver._TYPE
    AND matches.away_solver_id = away_solver.id
  GROUP BY matches.id
),

match_probs AS (
  SELECT
    id,
    functions.matchProbs(
      league_solver.avg_goal + league_solver.home_adv + home_solver.offence + away_solver.defence,
      league_solver.avg_goal - league_solver.home_adv + away_solver.offence + home_solver.defence,
       '0') AS had_probs
  FROM solver
),

probs AS (
  SELECT
    id,
    had_probs[0] AS had_home,
    had_probs[1] AS had_draw,
    had_probs[2] AS had_away
  FROM match_probs
  )

SELECT
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(date_unix), 'Asia/Hong_Kong') AS matchDate,
  league_transfermarkt_id,
  home_team_transfermarkt_id,
  home_team_name,
  away_team_transfermarkt_id,
  away_team_name,
  ROUND(had_home, 2) AS had_home,
  ROUND(had_draw, 2) AS had_draw,
  ROUND(had_away, 2) AS had_away,
  homeGoalCount,
  awayGoalCount,
  ROUND(home_adj, 2) AS home_adj,
  ROUND(away_adj, 2) AS away_adj,
  ROUND(team_a_xg, 2) AS team_a_xg,
  ROUND(team_b_xg, 2) AS team_b_xg
FROM matches
LEFT JOIN probs USING (id)
ORDER BY display_order, league_transfermarkt_id, date_unix DESC, matches.id