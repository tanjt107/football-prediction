WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    leagues.group,
    rating,
    offence,
    defence,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(positions._1, 0) +  COALESCE(positions._2, 0) AS r3,
    _DATE_UNIX + 2 * 60 * 60 AS _DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN `master.teams` teams ON leagues.team = teams.footystats_id
  JOIN `solver.team_ratings` ratings ON teams.solver_id = ratings.id
  WHERE _LEAGUE = 'International WC Qualification Asia'
  AND ratings._TYPE = 'International'
)

SELECT
  transfermarkt_id,
  name,
  result.group,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(r3, 3) AS r3,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(_DATE_UNIX), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY result.group <> 'E', result.group, points DESC