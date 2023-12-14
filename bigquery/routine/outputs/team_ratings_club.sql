WITH latest AS (
  SELECT
    RANK() OVER(ORDER BY ratings.rating DESC) AS rank,
    teams.transfermarkt_id AS team_transfermarkt_id,
    teams.name AS team_name,
    id,
    leagues.transfermarkt_id As league_transfermarkt_id,
    leagues.name AS league_name,
    ROUND(offence, 2) AS offence,
    ROUND(defence, 2) AS defence,
    ROUND(ratings.rating, 1) AS rating,
    _TYPE,
    _DATE_UNIX + 2 * 60 * 60 AS _DATE_UNIX
  FROM `solver.team_ratings` ratings
  JOIN `master.teams` teams ON ratings.id = teams.solver_id
    AND ratings._TYPE = teams.type
  JOIN `master.leagues` leagues ON teams.league_name = leagues.name
  WHERE (leagues.hkjc_id IS NOT NULL
      OR leagues.is_manual)
    AND ratings._TYPE = 'Club'
)

SELECT
  rank,
  RANK() OVER(ORDER BY _7d.rating DESC) - rank AS rank_7d_diff,
  team_transfermarkt_id,
  team_name,
  league_transfermarkt_id,
  league_name,
  offence,
  defence,
  latest.rating,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(_DATE_UNIX), 'Asia/Hong_Kong') AS date_unix
FROM latest
JOIN `solver.team_ratings_7d` _7d ON latest.id = _7d.id
  AND latest._TYPE = _7d._TYPE
ORDER BY rank;