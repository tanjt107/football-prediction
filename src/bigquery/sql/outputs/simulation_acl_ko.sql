WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    leagues.group,
    CASE
      WHEN leagues.group BETWEEN 'F' AND 'J' THEN 'East'
      ELSE 'West'
    END AS region,
    rating,
    offence,
    defence,
    COALESCE(rounds.ROUND_OF_16, 0) AS r16,
    COALESCE(rounds.QUARTER_FINALS, 0) AS qf,
    COALESCE(rounds.SEMI_FINALS, 0) AS sf,
    COALESCE(rounds.FINAL, 0) AS f,
    COALESCE(rounds.CHAMPS, 0) AS champs,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'Asia AFC Champions League'
    AND team_ratings._TYPE = 'Club'
),

slots AS (
  SELECT
    region,
    SUM(r16) AS r16,
    SUM(qf) AS qf,
    SUM(sf) AS sf,
    SUM(f) AS f
  FROM result
  GROUP BY region
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(result.r16 / slots.r16 * 8, 3) AS r16,
  ROUND(result.qf / slots.qf * 4, 3) AS qf,
  ROUND(result.sf / slots.sf * 2, 3) AS sf,
  ROUND(result.f / slots.f, 3) AS f,
  ROUND(result.champs / slots.f / 2, 3) AS champs,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 3 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
JOIN slots USING (region)
ORDER BY champs DESC, f DESC, sf DESC, qf DESC, r16 DESC, rating DESC