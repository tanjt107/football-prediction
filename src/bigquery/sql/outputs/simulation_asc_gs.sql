WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    leagues.group,
    rating,
    offence,
    defence,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(positions._1, 0) AS _1st,
    COALESCE(positions._2, 0) AS _2nd,
    COALESCE(positions._3, 0) AS _3rd,
    COALESCE(rounds.R16, 0) AS r16,
    COALESCE(rounds.QF, 0) AS qf,
    COALESCE(rounds.SF, 0) AS sf,
    COALESCE(rounds.F, 0) AS f,
    COALESCE(rounds.CHAMP, 0) AS champ,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'International AFC Asian Cup'
  AND team_ratings._TYPE = 'International'
)

SELECT
  transfermarkt_id,
  name,
  result.group,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(_1st, 3) AS _1st,
  ROUND(_2nd, 3) AS _2nd,
  ROUND(_3rd, 3) AS _3rd,
  ROUND(r16, 3) AS r16,
  ROUND(qf, 3) AS qf,
  ROUND(sf, 3) AS sf,
  ROUND(f, 3) AS f,
  ROUND(champ, 3) AS champ,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY result.group <> 'C', result.group, points DESC