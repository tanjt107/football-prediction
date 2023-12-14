WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    COALESCE(rounds.R16, 0) AS r16,
    COALESCE(rounds.QF, 0) AS qf,
    COALESCE(rounds.SF, 0) AS sf,
    COALESCE(rounds.F, 0) AS f,
    COALESCE(rounds.CHAMP, 0) AS champ,
    _DATE_UNIX + 2 * 60 * 60 AS _DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN `master.teams` teams ON leagues.team = teams.footystats_id
  JOIN `solver.team_ratings` ratings ON teams.solver_id = ratings.id
  WHERE _LEAGUE = 'Europe UEFA Champions League'
  AND ratings._TYPE = 'Club'
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
  ROUND(champ, 3) AS champ,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(_DATE_UNIX), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY f DESC, sf DESC, qf DESC, r16 DESC, rating DESC