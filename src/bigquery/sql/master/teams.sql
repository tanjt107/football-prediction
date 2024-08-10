SELECT
  COALESCE(hkjc.name_ch, manual.name_ch, footystats.name) AS name,
  footystats.country,
  CASE
    WHEN _NAME LIKE 'International WC Qualification %' THEN 'International'
    ELSE 'Club'
  END AS type,
  footystats.id AS footystats_id,
  hkjc.id AS hkjc_id,
  manual.transfermarkt_id,
  CASE
    WHEN latest_season_id IS NOT NULL THEN CAST(footystats.id AS STRING)
    ELSE footystats.country
  END AS solver_id,
  manual.name_ch IS NOT NULL AS is_manual,
  footystats_name AS league_name
FROM `footystats.teams` footystats
LEFT JOIN `manual.teams` manual ON footystats.id = manual.footystats_id
LEFT JOIN `hkjc.teams` hkjc ON manual.hkjc_id = hkjc.id
LEFT JOIN master.leagues ON _SEASON_ID = latest_season_id AND is_league
QUALIFY ROW_NUMBER() OVER (PARTITION BY footystats.id ORDER BY _NAME LIKE 'International WC Qualification %' DESC, is_league DESC) = 1