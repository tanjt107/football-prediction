WITH latest_seasons AS (
  SELECT
    latest_season_id AS season_id,
    id AS league_id
  FROM `master.leagues`
  WHERE format = 'Domestic League'
    AND footystats_division > 0
    AND type = 'Club'),

latest_season_teams AS (
  SELECT
    teams.id,
    latest_seasons.league_id
  FROM `footystats.teams` teams
  JOIN latest_seasons ON teams.competition_id = latest_seasons.season_id
),

footystats_club AS (
  SELECT
    DISTINCT teams.id,
    name,
    country,
    'Club' AS type,
    CASE
      WHEN latest_season_teams.id IS NOT NULL THEN CAST(teams.id AS STRING)
      ELSE country
    END AS solver_id,
    league_id,
    latest_season_teams.id IS NOT NULL AS in_team_rating
  FROM `footystats.teams` teams
  LEFT JOIN latest_season_teams ON teams.id = latest_season_teams.id
  WHERE name NOT LIKE '%National Team'
),

footystats_international AS (
  SELECT
    DISTINCT teams.id,
    name,
    country,
    'International' AS type,
    CAST(teams.id AS STRING) AS solver_id,
    NULL AS league_id,
    transfermarkt.transfermarkt_id IS NOT NULL AS in_team_rating
  FROM `footystats.teams` teams
  LEFT JOIN `manual.transfermarkt_teams` transfermarkt ON teams.id = transfermarkt.footystats_id
  WHERE name LIKE '%National Team'
),

footystats AS (
  SELECT
    id,
    name,
    country,
    type,
    solver_id,
    league_id,
    in_team_rating
  FROM footystats_club
  UNION ALL
  SELECT
    id,
    name,
    country,
    type,
    solver_id,
    CAST(league_id AS STRING) AS league_id,
    in_team_rating
  FROM footystats_international
),

hkjc AS (
  SELECT
    hkjc.id AS hkjc_id,
    mapping_hkjc.footystats_id,
    nameC
  FROM `hkjc.teams` hkjc
  LEFT JOIN `manual.hkjc_teams` mapping_hkjc ON CAST(id AS INT64) = hkjc_id
),

non_hkjc AS (
  SELECT
    CAST(NULL AS STRING) AS hkjc_id,
    footystats_id,
    nameC
  FROM `manual.non_hkjc_teams` 
),

hk AS (
  SELECT
    hkjc_id,
    footystats_id,
    nameC
  FROM
    hkjc
  UNION ALL
  SELECT
    hkjc_id,
    footystats_id,
    nameC
  FROM
    non_hkjc 
)

SELECT
  COALESCE(CONCAT('FS', CAST(footystats.id AS STRING)), CONCAT('JC', hkjc_id)) AS id,
  COALESCE(nameC, name) AS name,
  country,
  type,
  footystats.id AS footystats_id,
  hkjc_id,
  transfermarkt_id,
  solver_id,
  league_id,
  COALESCE(in_team_rating, FALSE) AS in_team_rating
FROM footystats
LEFT JOIN `manual.transfermarkt_teams` transfermarkt ON footystats.id = transfermarkt.footystats_id
FULL OUTER JOIN hk ON footystats.id = hk.footystats_id