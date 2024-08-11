SELECT
  COALESCE(name_ch, _NAME) AS name,
  _COUNTRY AS country,
  CASE
    WHEN _COUNTRY = 'International' AND EXISTS (
      SELECT 1
      FROM footystats.teams
      WHERE seasons._SEASON_ID = teams._SEASON_ID
      AND teams.name LIKE '% National Team'
    )
    THEN 'International'
    ELSE 'Club'
  END AS type,
  CASE
    WHEN MAX(division) OVER (PARTITION BY _COUNTRY) > 1 AND division > 1 
    THEN CONCAT(_COUNTRY, division)
    ELSE _COUNTRY
  END AS division,
  display_order, -- TODO Add HKJC display order
  format = 'Domestic League' AND division > 0 AS is_league,
  display_order IS NOT NULL AS is_manual,
  seasons.id AS latest_season_id,
  _YEAR AS latest_season_year,
  _NAME AS footystats_name,
  hkjc_id,
  transfermarkt_id
FROM footystats.seasons 
LEFT JOIN manual.leagues ON seasons._NAME = leagues.footystats_id
QUALIFY ROW_NUMBER() OVER (PARTITION BY _NAME ORDER BY RIGHT(_YEAR, 4) DESC, LEFT(_YEAR, 4) DESC) = 1