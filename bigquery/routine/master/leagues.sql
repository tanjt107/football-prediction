SELECT
  COALESCE(hkjc.nameC, non_hkjc.nameC, _NAME) AS name,
  footystats._COUNTRY AS country,
  CASE
    WHEN _COUNTRY = 'International' AND intl.name IS NULL
    THEN 'International'
    ELSE 'Club'
  END AS type,
  CASE
    WHEN MAX(division) OVER (PARTITION BY _COUNTRY) > 1 AND division > 1 
    THEN CONCAT(_COUNTRY, division)
    ELSE _COUNTRY
  END AS division,
  format = 'Domestic League' AND division > 0 AS is_league,
  footystats.id AS latest_season_id,
  _NAME AS footystats_id,
  hkjc_id,
  transfermarkt_id
FROM `footystats.seasons` footystats
LEFT JOIN `manual.hkjc_leagues` mapping_hkjc ON footystats._NAME = mapping_hkjc.footystats_id 
LEFT JOIN `hkjc.leagues` hkjc ON hkjc.code = mapping_hkjc.hkjc_id
LEFT JOIN `manual.transfermarkt_leagues` transfermarkt ON footystats._NAME = transfermarkt.footystats_id
LEFT JOIN `manual.non_hkjc_leagues` non_hkjc ON footystats._NAME = non_hkjc.footystats_id
LEFT JOIN `manual.intl_club_competitions` intl ON footystats._NAME = intl.name
QUALIFY ROW_NUMBER() OVER (PARTITION BY _NAME ORDER BY RIGHT(_YEAR, 4) DESC, LEFT(_YEAR, 4) DESC) = 1