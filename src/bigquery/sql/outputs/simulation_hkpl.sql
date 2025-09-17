WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws + table.correction AS points,
    COALESCE(positions._1, 0) + COALESCE(positions._2, 0) + COALESCE(positions._3, 0) + COALESCE(positions._4, 0) + COALESCE(positions._5, 0) AS champ_group,
    COALESCE(positions._6, 0) + COALESCE(positions._7, 0) + COALESCE(positions._8, 0) + COALESCE(positions._9, 0) + COALESCE(positions._10, 0) AS challenge_group,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'Hong Kong Hong Kong Premier League'
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
  ROUND(champ_group, 3) AS champ_group,
  ROUND(challenge_group, 3) AS challenge_group,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY points DESC