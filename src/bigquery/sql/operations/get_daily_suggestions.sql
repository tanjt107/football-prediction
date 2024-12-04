WITH matches AS (
  SELECT
    hkjc.id,
    kick_off_time,
    tournament_name,
    home_name,
    away_name,
    functions.matchProbs(
        avg_goal + league_solver.home_adv * hkjc.home_adv + home_solver.offence + away_solver.defence,
        avg_goal - league_solver.home_adv * hkjc.home_adv + away_solver.offence + home_solver.defence,
        handicap
        ) AS hdc_probs,
    HDC_H,
    HDC_A,
    handicap,
    CAST(SPLIT(handicap, '/')[0] AS FLOAT64) AS HG1,
    CAST(SPLIT(handicap, '/')[SAFE_OFFSET(1)] AS FLOAT64) AS HG2
    FROM hkjc.odds_today hkjc
    JOIN `master.teams` home_teams ON hkjc.home_id = home_teams.hkjc_id
    JOIN `solver.teams_latest` home_solver ON home_solver.id = home_teams.solver_id
      AND home_solver._TYPE = home_teams.type
    JOIN `master.teams` away_teams ON hkjc.away_id = away_teams.hkjc_id
    JOIN `solver.teams_latest` away_solver ON away_solver.id = away_teams.solver_id 
      AND away_solver._TYPE = away_teams.type
    JOIN master.leagues ON hkjc.tournament_id = leagues.hkjc_id
    JOIN `solver.leagues_latest` league_solver ON leagues.division = league_solver.division
      AND league_solver._TYPE = leagues.type
  WHERE
    (SAFE_CAST(home_teams.solver_id AS INT64) IS NOT NULL OR home_teams.type = 'International')
    AND (SAFE_CAST(away_teams.solver_id AS INT64) IS NOT NULL OR away_teams.type = 'International')
),

kelly AS (
  SELECT
    id,
    kick_off_time,
    tournament_name,
    home_name,
    away_name,
    hdc_H,
    hdc_A,
    handicap,
    hdc_probs[0] - hdc_probs[2] / (hdc_H - 1) AS kelly_hdc_home,
    hdc_probs[2] - hdc_probs[0] / (hdc_A - 1) AS kelly_hdc_away,
  FROM matches
)

SELECT
  id,
  kick_off_time,
  tournament_name,
  home_name,
  away_name,
  '主' AS team,
  handicap,
  hdc_H AS odds,
  kelly_hdc_home AS amount,
  FROM kelly
  WHERE kelly_hdc_home > 0
UNION ALL
SELECT
  id,
  kick_off_time,
  tournament_name,
  home_name,
  away_name,
  '客' AS team,
  handicap,
  hdc_A,
  kelly_hdc_away,
  FROM kelly
  WHERE kelly_hdc_away > 0
ORDER BY amount DESC