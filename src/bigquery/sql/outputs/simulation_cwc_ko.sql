WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    COALESCE(rounds.ROUND_OF_16, 0) AS r16,
    COALESCE(rounds.QUARTER_FINALS, 0) AS qf,
    COALESCE(rounds.SEMI_FINALS, 0) AS sf,
    COALESCE(rounds.FINAL, 0) AS f,
    COALESCE(rounds.WINNER, 0) AS winner,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'International FIFA Club World Cup'
  AND team_ratings._TYPE = 'Club'
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(r16, 3) AS r16,
  ROUND(qf, 3) AS qf,
  ROUND(sf, 3) AS sf,
  ROUND(f, 3) AS f,
  ROUND(winner, 3) AS winner,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 3 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY winner DESC, f DESC, sf DESC, qf DESC, r16 DESC, rating DESC