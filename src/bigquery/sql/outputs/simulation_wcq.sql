WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    RIGHT(leagues.group, 1) AS _group,
    rating,
    offence,
    defence,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(positions._1, 0) +  COALESCE(positions._2, 0) AS r3,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'International WC Qualification Asia'
  AND team_ratings._TYPE = 'International'
)

SELECT
  transfermarkt_id,
  name,
  _group,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(r3, 3) AS r3,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY _group = 'E' DESC, _group, points DESC