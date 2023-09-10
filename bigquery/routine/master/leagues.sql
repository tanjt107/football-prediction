WITH max_division AS (
  SELECT 
    country,
    MAX(division) AS division
  FROM `footystats.seasons`
  GROUP BY country
),

footystats AS (
  SELECT 
    country,
    name,
    id,
    division,
    format,
    CASE
      WHEN country = 'International' AND name NOT IN (
      SELECT name FROM `manual.intl_club_competitions`
      )
      THEN 'International'
      ELSE 'Club'
    END AS type
  FROM `footystats.seasons`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY country, name ORDER BY ending_year DESC, starting_year DESC) = 1
),

hkjc AS (
  SELECT DISTINCT
    hkjc.code,
    country,
    name,
    nameC
  FROM `hkjc.leagues` hkjc
  LEFT JOIN `manual.hkjc_leagues` mapping_hkjc ON hkjc.code = mapping_hkjc.code
),

non_hkjc AS (
  SELECT 
    CAST(NULL AS STRING) AS code,
    country,
    name,
    nameC
  FROM `manual.non_hkjc_leagues`
),

hk AS (
  SELECT 
    code,
    country,
    name,
    nameC
  FROM hkjc
  UNION ALL
  SELECT 
    code,
    country,
    name,
    nameC
  FROM non_hkjc
)

SELECT 
  COALESCE(CONCAT('JC', hk.code), CONCAT('FS', footystats.country, REPLACE(footystats.name, ' ', ''))) AS id,
  COALESCE(nameC, CONCAT(footystats.country, ' ', footystats.name)) AS name,
  footystats.country,
  footystats.name AS footystats_name,
  format,
  CASE
    WHEN max_division.division > 1 AND footystats.division > 1 
    THEN CONCAT(footystats.country, footystats.division)
    ELSE footystats.country
  END AS division,
  footystats.division AS footystats_division,
  type,
  footystats.id AS latest_season_id,
  hk.code AS hkjc_id,
  transfermarkt_id
FROM footystats
JOIN max_division ON footystats.country = max_division.country
LEFT JOIN `manual.transfermarkt_leagues` transfermarkt 
  ON footystats.country = transfermarkt.country
  AND footystats.name = transfermarkt.name
FULL OUTER JOIN hk 
  ON footystats.country = hk.country
  AND footystats.name = hk.name