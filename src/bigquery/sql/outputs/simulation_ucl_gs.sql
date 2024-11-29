WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    rating,
    offence,
    defence,
    table.scored - table.conceded AS goal_diff,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(positions._1, 0) + COALESCE(positions._2, 0) + COALESCE(positions._3, 0) + COALESCE(positions._4, 0) + COALESCE(positions._5, 0) + COALESCE(positions._6, 0) + COALESCE(positions._7, 0) + COALESCE(positions._8, 0) + COALESCE(positions._9, 0) + COALESCE(positions._10, 0) + COALESCE(positions._11, 0) + COALESCE(positions._12, 0) + COALESCE(positions._13, 0) + COALESCE(positions._14, 0) + COALESCE(positions._15, 0) + COALESCE(positions._16, 0) + COALESCE(positions._17, 0) + COALESCE(positions._18, 0) + COALESCE(positions._19, 0) + COALESCE(positions._20, 0) + COALESCE(positions._21, 0) + COALESCE(positions._22, 0) + COALESCE(positions._23, 0) + COALESCE(positions._24, 0) AS top24,
    COALESCE(positions._1, 0) + COALESCE(positions._2, 0) + COALESCE(positions._3, 0) + COALESCE(positions._4, 0) + COALESCE(positions._5, 0) + COALESCE(positions._6, 0) + COALESCE(positions._7, 0) + COALESCE(positions._8) AS top8,
    COALESCE(rounds.knockout_round_play_offs, 0) AS po,
    COALESCE(rounds.round_of_16, 0) AS r16,
    COALESCE(rounds.quarter_finals, 0) AS qf,
    COALESCE(rounds.semi_finals, 0) AS sf,
    COALESCE(rounds.final, 0) AS f,
    COALESCE(rounds.winner, 0) AS winner,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'Europe UEFA Champions League'
  AND team_ratings._TYPE = 'Club'
  AND ROUND(table.wins + table.draws + table.losses) = 8
)

SELECT
  transfermarkt_id,
  name,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(goal_diff, 1) AS goal_diff,
  ROUND(points, 1) AS points,
  ROUND(po, 3) AS po,
  ROUND(r16, 3) AS r16,
  ROUND(qf, 3) AS qf,
  ROUND(sf, 3) AS sf,
  ROUND(f, 3) AS f,
  ROUND(winner, 3) AS winner,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY points DESC