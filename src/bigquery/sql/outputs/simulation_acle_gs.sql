WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    CASE
      WHEN leagues.group = 'East' THEN '東'
      ELSE '西'
    END AS _group,
    rating,
    offence,
    defence,
    table.wins * 3 + table.draws + COALESCE(table.correction, 0) AS points,
    COALESCE(rounds.round_of_16, 0) AS r16,
    COALESCE(rounds.quarter_finals, 0) AS qf,
    COALESCE(rounds.semi_finals, 0) AS sf,
    COALESCE(rounds.final, 0) AS f,
    COALESCE(rounds.winner, 0) AS winner,
    leagues._DATE_UNIX
  FROM `simulation.leagues_latest` leagues
  JOIN master.teams ON leagues.team = teams.footystats_id
  JOIN solver.team_ratings ON teams.solver_id = team_ratings.id
  WHERE _LEAGUE = 'Asia AFC Champions League'
  AND team_ratings._TYPE = 'Club'
)

SELECT
  transfermarkt_id,
  name,
  _group,
  ROUND(rating, 1) AS rating,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(r16, 3) AS r16,
  ROUND(qf, 3) AS qf,
  ROUND(sf, 3) AS sf,
  ROUND(f, 3) AS f,
  ROUND(winner, 3) AS winner,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM result
ORDER BY _group, points DESC