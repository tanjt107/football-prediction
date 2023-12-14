WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws + table.correction AS points,
    COALESCE(positions._1, 0) AS champ,
    COALESCE(positions._1, 0) + COALESCE(positions._2, 0) + COALESCE(positions._3, 0) + COALESCE(positions._4, 0) AS ucl,
    COALESCE(positions._5, 0) AS uel,
    COALESCE(positions._18, 0) + COALESCE(positions._19, 0) + COALESCE(positions._20, 0) AS relegation,
    _DATE_UNIX + 2 * 60 * 60 AS _DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN `master.teams` teams ON leagues.team = teams.footystats_id
  JOIN `solver.team_ratings` ratings ON teams.solver_id = ratings.id
  WHERE _LEAGUE = 'Italy Serie A'
  AND ratings._TYPE = 'Club'
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
  ROUND(ucl, 3) AS ucl,
  ROUND(uel, 3) AS uel,
  ROUND(relegation, 3) AS relegation,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(_DATE_UNIX), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY points DESC