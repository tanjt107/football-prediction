WITH matches AS (
  SELECT
    functions.matchProbs(avg_goal + league_solver.home_adv * odds_latest.home_adv + home_solver.offence + away_solver.defence, avg_goal - league_solver.home_adv * odds_latest.home_adv + away_solver.offence + home_solver.defence, handicap) AS hdc_probs,
    HDC_H,
    HDC_A,
    CAST(SPLIT(handicap, '/')[0] AS FLOAT64) AS HG1,
    CAST(SPLIT(handicap, '/')[SAFE_OFFSET(1)] AS FLOAT64) AS HG2,
    home_score - away_score AS goal_diff
    FROM hkjc.odds_latest
    JOIN hkjc.scores USING(id)
    JOIN `master.teams` home_teams ON odds_latest.home_id = home_teams.hkjc_id
    JOIN `solver.teams` home_solver ON home_solver.id = home_teams.solver_id
      AND home_solver._TYPE = home_teams.type
      AND odds_latest._TIMESTAMP >= TIMESTAMP_SECONDS(home_solver._DATE_UNIX)
    JOIN `master.teams` away_teams ON odds_latest.away_id = away_teams.hkjc_id
    JOIN `solver.teams` away_solver ON away_solver.id = away_teams.solver_id 
      AND away_solver._TYPE = away_teams.type
      AND away_solver._DATE_UNIX = home_solver._DATE_UNIX
    JOIN master.leagues ON odds_latest.tournament_id = leagues.hkjc_id
    JOIN `solver.leagues` league_solver ON leagues.division = league_solver.division
      AND league_solver._TYPE = leagues.type
      AND league_solver._DATE_UNIX = home_solver._DATE_UNIX
  WHERE
    (SAFE_CAST(home_teams.solver_id AS INT64) IS NOT NULL OR home_teams.type = 'International')
    AND (SAFE_CAST(away_teams.solver_id AS INT64) IS NOT NULL OR away_teams.type = 'International')
    AND kick_off_time >= '2024-09-28'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY odds_latest.id ORDER BY home_solver._DATE_UNIX DESC) = 1
),

kelly AS (
  SELECT
    hdc_H,
    hdc_A,
    hdc_probs[0] - hdc_probs[2] / (hdc_H - 1) AS kelly_hdc_home,
    hdc_probs[2] - hdc_probs[0] / (hdc_A - 1) AS kelly_hdc_away,
    CASE
      WHEN goal_diff + HG1 > 0 THEN 1
      WHEN goal_diff + HG1 = 0 THEN 0
      ELSE -1
    END AS hdc_home_win1,
    CASE
      WHEN HG2 IS NOT NULL THEN
      CASE
        WHEN goal_diff + HG2 > 0 THEN 1
        WHEN goal_diff + HG2 = 0 THEN 0
        ELSE -1
      END
    END AS hdc_home_win2,
    kelly_ratio
  FROM matches
  CROSS JOIN UNNEST(GENERATE_ARRAY(20, 200, 20)) kelly_ratio
),

results AS (
  SELECT
    hdc_H AS odds,
    kelly_hdc_home / kelly_ratio AS amount,
    CASE
      WHEN hdc_home_win2 IS NULL THEN hdc_home_win1
      ELSE (hdc_home_win1 + hdc_home_win2) / 2
    END AS result,
    kelly_ratio
    FROM kelly
    WHERE kelly_hdc_home > 0
    UNION ALL
  SELECT
    hdc_A,
    kelly_hdc_away / kelly_ratio,
    CASE
      WHEN hdc_home_win2 IS NULL THEN -hdc_home_win1
      ELSE -(hdc_home_win1 + hdc_home_win2) / 2
    END,
    kelly_ratio
    FROM kelly
    WHERE kelly_hdc_away > 0
)

SELECT
  kelly_ratio,
  EXP(SUM(LOG(CASE
    WHEN result > 0 THEN 1 + amount * (odds - 1) * result
    ELSE 1 + amount * result
  END))) AS product
FROM results
GROUP BY kelly_ratio
ORDER BY product DESC
LIMIT 1