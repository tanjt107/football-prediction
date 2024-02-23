SELECT
  COALESCE(leagues.nameC, non_hkjc_leagues.nameC, _NAME) AS name,
  seasons._COUNTRY AS country,
  CASE
    WHEN _COUNTRY = 'International' AND _SEASON_ID IN (
      SELECT _SEASON_ID
      FROM `footystats.teams`
      WHERE name LIKE '% National Team'
    )
    THEN 'International'
    ELSE 'Club'
  END AS type,
  CASE
    WHEN MAX(division) OVER (PARTITION BY _COUNTRY) > 1 AND division > 1 
    THEN CONCAT(_COUNTRY, division)
    ELSE _COUNTRY
  END AS division,
  COALESCE(display_order, REGEXP_EXTRACT(tournament.displayOrder, r'^([0-9]+)\.')) AS display_order,
  format = 'Domestic League' AND division > 0 AS is_league,
  non_hkjc_leagues.footystats_id IS NOT NULL AS is_manual,
  seasons.id AS latest_season_id,
  _YEAR AS latest_season_year,
  _NAME AS footystats_name,
  hkjc_id,
  transfermarkt_id
FROM footystats.seasons 
LEFT JOIN manual.hkjc_leagues ON seasons._NAME = hkjc_leagues.footystats_id 
LEFT JOIN hkjc.odds_had ON hkjc_leagues.hkjc_id = odds_had.tournament.tournamentShortName
LEFT JOIN hkjc.leagues ON hkjc_leagues.hkjc_id = leagues.code
LEFT JOIN manual.transfermarkt_leagues ON seasons._NAME = transfermarkt_leagues.footystats_id
LEFT JOIN manual.non_hkjc_leagues ON seasons._NAME = non_hkjc_leagues.footystats_id
QUALIFY ROW_NUMBER() OVER (PARTITION BY _NAME ORDER BY RIGHT(_YEAR, 4) DESC, LEFT(_YEAR, 4) DESC) = 1