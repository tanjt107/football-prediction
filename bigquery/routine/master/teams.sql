WITH latest_seasons AS (
  SELECT
    latest_season_id AS season_id,
    id AS league_id
  FROM `master.leagues`
  WHERE type = 'Club'
    AND footystats_division > 0
    AND format = 'Domestic League' ),

latest_season_teams AS (
SELECT
  teams.id,
  latest_seasons.league_id
FROM `footystats.teams` teams
JOIN latest_seasons ON teams.competition_id = latest_seasons.season_id
),

footystats AS (
SELECT
  DISTINCT teams.id,
  name,
  country,
  CASE
    WHEN name LIKE '%National Team' THEN 'International'
  ELSE 'Club'
  END AS type,  
  league_id,
  latest_season_teams.id IS NOT NULL AS in_team_rating
FROM `footystats.teams` teams
LEFT JOIN latest_season_teams ON teams.id = latest_season_teams.id
),

hkjc AS (
SELECT
  hkjc.id AS hkjc_id,
  mapping_hkjc.footystats_id,
  nameC
FROM `hkjc.teams` hkjc
LEFT JOIN `manual.hkjc_teams` mapping_hkjc ON id = CAST(hkjc_id AS STRING) 
),

non_hkjc AS (
SELECT
  CAST(NULL AS STRING) AS hkjc_id,
  footystats_id,
  nameC
FROM
  `manual.non_hkjc_teams` 
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
  league_id,
  COALESCE(in_team_rating, FALSE) AS in_team_rating
FROM footystats
LEFT JOIN `manual.transfermarkt_teams` transfermarkt ON footystats.id = transfermarkt.footystats_id
FULL OUTER JOIN hk ON footystats.id = hk.footystats_id