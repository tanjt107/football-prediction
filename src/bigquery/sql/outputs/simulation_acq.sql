WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    RIGHT(leagues.group, 1) AS _group,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(positions._1, 0) AS ac,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'International Asian Cup Qualification'
  AND team_ratings._TYPE = 'International'
)

SELECT
  transfermarkt_id,
  name,
  _group,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(goal_diff, 1) AS goal_diff,
  ROUND(points, 1) AS points,
  ROUND(ac, 3) AS ac,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY _group <> 'C', _group, points DESC