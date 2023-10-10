WITH footystats AS (
  SELECT 
    _COUNTRY,
    _NAME,
    id,
    format,
    division,
    CASE
      WHEN _COUNTRY = 'International' AND name NOT IN (
      SELECT name FROM `manual.intl_club_competitions`
      )
      THEN 'International'
      ELSE 'Club'
    END AS type
  FROM `footystats.seasons`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY _NAME ORDER BY RIGHT(_YEAR, 4) DESC, LEFT(_YEAR, 4) DESC) = 1
),

max_division AS (
  SELECT 
    _COUNTRY,
    MAX(division) AS division
  FROM footystats
  GROUP BY _COUNTRY
),

hkjc AS (
  SELECT DISTINCT
    hkjc_id,
    footystats_id,
    nameC
  FROM `hkjc.leagues` hkjc
  JOIN `manual.hkjc_leagues` mapping_hkjc ON hkjc.code = mapping_hkjc.hkjc_id
),

non_hkjc AS (
  SELECT 
    CAST(NULL AS STRING) AS hkjc_id,
    footystats_id,
    nameC
  FROM `manual.non_hkjc_leagues`
),

hk AS (
  SELECT 
    hkjc_id,
    footystats_id,
    nameC
  FROM hkjc
  UNION ALL
  SELECT 
    hkjc_id,
    footystats_id,
    nameC
  FROM non_hkjc
)

SELECT 
  COALESCE(nameC, CONCAT(footystats._NAME)) AS name,
  footystats._COUNTRY AS country,
  CASE
    WHEN max_division.division > 1 AND footystats.division > 1 
    THEN CONCAT(footystats._COUNTRY, footystats.division)
    ELSE footystats._COUNTRY
  END AS division,
  format = 'Domestic League' AND footystats.division > 0 AS is_league,
  footystats.id AS latest_season_id,
  footystats._NAME AS footystats_id,
  hkjc_id,
  transfermarkt_id
FROM footystats
JOIN max_division ON footystats._COUNTRY = max_division._COUNTRY
LEFT JOIN `manual.transfermarkt_leagues` transfermarkt ON footystats._NAME = transfermarkt.footystats_id
LEFT JOIN hk ON footystats._NAME = hk.footystats_id