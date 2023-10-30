WITH matches AS (
  SELECT
    matches.id,
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
    _TYPE,
    MAX(_DATE_UNIX) as _DATE_UNIX
  FROM `footystats.matches` matches
  JOIN `footystats.matches_transformed` matches_transformed ON matches.id = matches_transformed.id
  JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN `master.leagues` leagues ON matches._NAME = leagues.footystats_id
  LEFT JOIN `solver.leagues` ON _DATE_UNIX < date_unix AND leagues.type = _TYPE
  WHERE matches.status = 'complete'
    AND ( home_teams.country = 'Hong Kong'
      OR away_teams.country = 'Hong Kong')
  GROUP BY matches.id,
    matches.date_unix,
    leagues.transfermarkt_id,
    leagues.division,
    home_teams.transfermarkt_id,
    home_teams.name,
    home_teams.solver_id,
    away_teams.transfermarkt_id,
    away_teams.name,
    away_teams.solver_id,
    homeGoalCount,
    awayGoalCount,
    home_adj,
    away_adj,
    team_a_xg,
    team_b_xg,
    _TYPE
  ORDER BY date_unix DESC
  LIMIT 100
),

match_probs AS (
  SELECT
    matches.id,
    functions.matchProbs(
      avg_goal + league_solver.home_adv + home_solver.offence + away_solver.defence,
      avg_goal - league_solver.home_adv + away_solver.offence + home_solver.defence,
       '0') AS had_probs
  FROM matches
  JOIN `solver.teams` home_solver ON matches.home_solver_id = home_solver.id
    AND matches._TYPE = home_solver._TYPE
    AND matches._DATE_UNIX = home_solver._DATE_UNIX
  JOIN `solver.teams` away_solver ON matches.away_solver_id = away_solver.id
    AND matches._TYPE = away_solver._TYPE
    AND matches._DATE_UNIX = away_solver._DATE_UNIX
  JOIN `solver.leagues` league_solver ON matches.league_division = league_solver.division
    AND matches._TYPE = league_solver._TYPE
    AND matches._DATE_UNIX = league_solver._DATE_UNIX
),

probs AS (
  SELECT
    id,
    had_probs[OFFSET(0)] AS had_home,
    had_probs[OFFSET(1)] AS had_draw,
    had_probs[OFFSET(2)] AS had_away
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
LEFT JOIN probs ON matches.id = probs.id
ORDER BY date_unix DESC