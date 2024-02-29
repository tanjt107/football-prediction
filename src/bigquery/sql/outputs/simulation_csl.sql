WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(positions._1, 0) AS champ,
    COALESCE(positions._1, 0) + COALESCE(positions._2, 0) + COALESCE(positions._3, 0) * 0.5 AS acle,
    COALESCE(positions._3, 0) * 0.5 + COALESCE(positions._4, 0) AS acl2,
    COALESCE(positions._15, 0) + COALESCE(positions._16, 0) AS relegation,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'China Chinese Super League'
  AND team_ratings._TYPE = 'Club'
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(goal_diff, 1) AS goal_diff,
  ROUND(points, 1) AS points,
  ROUND(champ, 3) AS champ,
  ROUND(acle, 3) AS acle,
  ROUND(acl2, 3) AS acl2,
  ROUND(relegation, 3) AS relegation,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY points DESC