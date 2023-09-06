WITH latest_seasons AS (
  SELECT
    id, season.country, season.name
  FROM
    `mapping.league_info` mapping
  JOIN
    `footystats.latest_season` season
  ON
    mapping.country = season.country
    AND mapping.name = season.name
),

average AS (
  SELECT
    AVG(offence) AS offence,
    AVG(defence) AS defence
  FROM
    `solver.teams`
  WHERE
    team IN (
      SELECT id
      FROM `footystats.teams`
      WHERE competition_id IN (SELECT id FROM latest_seasons)
    )
),

factors AS (
  SELECT
    teams.id,
    GREATEST(1.35 + solver.offence - average.offence, 0.2) AS offence,
    GREATEST(1.35 + solver.defence - average.defence, 0.2) AS defence,
    seasons.country,
    seasons.name
  FROM
    `solver.teams` solver
  CROSS JOIN
    average
  JOIN
    `footystats.teams` teams ON teams.id = solver.team
  JOIN
    latest_seasons seasons ON seasons.id = teams.competition_id
),

match_probs AS (
  SELECT
    id,
    solver.matchProbs(offence, defence, 5)[OFFSET(0)] AS pct_win,
    solver.matchProbs(offence, defence, 5)[OFFSET(1)] AS pct_draw
  FROM
    factors
)

SELECT
  RANK() OVER(ORDER BY (pct_win * 3 + pct_draw) / 3 * 100 DESC) AS rank,
  mapping_team.transfermarkt_id AS team_icon,
  mapping_team.nameC AS team,
  mapping_league.transfermarkt_id AS league_icon,
  mapping_league.nameC AS league,
  ROUND(offence, 1) AS offence,
  ROUND(defence, 1) AS defence,
  ROUND((pct_win * 3 + pct_draw) / 3 * 100, 1) AS rating
FROM
  factors
JOIN
  `mapping.team_info` mapping_team ON factors.id = mapping_team.footystats_id
JOIN
  `mapping.league_info` mapping_league ON factors.country = mapping_league.country AND factors.name = mapping_league.name
JOIN
  match_probs ON factors.id = match_probs.id
ORDER BY
  rank;