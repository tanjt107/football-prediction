WITH result AS (
  SELECT
    teams.transfermarkt_id,
    teams.name,
    leagues.group,
    rating,
    offence,
    defence,
    table.wins * 3 + table.draws AS points,
    COALESCE(positions.1, 0) AS _1st,
    COALESCE(positions.2, 0) AS _2nd,
    COALESCE(positions.1, 0) +  COALESCE(positions.2, 0) AS r3
  FROM `simulation.leagues_latest` leagues
  JOIN `master.teams` teams ON CAST(leagues.team AS INT64) = teams.footystats_id
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
  ROUND(_1st, 3) AS _1st,
  ROUND(_2nd, 3) AS _2nd,
  ROUND(r3, 3) AS r3
FROM result
ORDER BY result.group, points DESC