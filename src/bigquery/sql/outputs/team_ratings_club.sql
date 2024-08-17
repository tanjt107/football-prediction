WITH latest AS (
  SELECT
    RANK() OVER(ORDER BY team_ratings.rating DESC) AS rank,
    teams.transfermarkt_id AS team_transfermarkt_id,
    teams.name AS team_name,
    id,
    leagues.transfermarkt_id As league_transfermarkt_id,
    leagues.name AS league_name,
    offence,
    defence,
    team_ratings.rating,
    _TYPE,
    _DATE_UNIX
  FROM solver.team_ratings
  JOIN master.teams ON team_ratings.id = teams.solver_id
    AND team_ratings._TYPE = teams.type
  JOIN master.leagues ON teams.league_name = leagues.footystats_name
  WHERE (leagues.hkjc_id IS NOT NULL
      OR leagues.is_manual)
    AND team_ratings._TYPE = 'Club'
    AND leagues.footystats_name <> 'Mexico Ascenso MX'
)

SELECT
  rank,
  RANK() OVER(ORDER BY team_ratings_7d.rating DESC) - rank AS rank_7d_diff,
  team_transfermarkt_id,
  team_name,
  league_transfermarkt_id,
  league_name,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(latest.rating, 1) AS rating,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM latest
LEFT JOIN solver.team_ratings_7d USING(id, _TYPE)
ORDER BY rank;