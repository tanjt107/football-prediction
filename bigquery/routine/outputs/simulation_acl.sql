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
    COALESCE(rounds.QF, 0) AS r16,
    COALESCE(rounds.SF, 0) AS qf,
    COALESCE(rounds.F, 0) AS sf,
    COALESCE(rounds.CHAMP, 0) AS f
  FROM `simulation.leagues_latest` leagues
  JOIN `master.teams` teams ON CAST(leagues.team AS INT64) = teams.footystats_id
  JOIN `solver.team_ratings` ratings ON teams.solver_id = ratings.id
  WHERE _LEAGUE = 'Asia AFC Champions League'
  AND ratings._TYPE = 'Club'
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
  ROUND(r16, 3) AS r16,
  ROUND(qf, 3) AS qf,
  ROUND(sf, 3) AS sf,
  ROUND(f, 3) AS f,
FROM result
ORDER BY result.group, points DESC