SELECT
  COALESCE(hkjc.nameC, non_hkjc.nameC, footystats.name) AS name,
  footystats.country,
  CASE
    WHEN footystats.id IN (
      SELECT id
      FROM `footystats.teams`
      WHERE _NAME LIKE 'International WC Qualification %'
    ) THEN 'International'
    ELSE 'Club'
  END AS type,
  footystats.id AS footystats_id,
  mapping_hkjc.hkjc_id,
  transfermarkt.transfermarkt_id,
  CASE
    WHEN latest_season_id IS NOT NULL THEN CAST(footystats.id AS STRING)
    ELSE footystats.country
  END AS solver_id,
  non_hkjc.footystats_id IS NOT NULL AS is_manual,
  leagues.name AS league_name
FROM `footystats.teams` footystats
LEFT JOIN `manual.hkjc_teams` mapping_hkjc ON footystats.id = CAST(mapping_hkjc.footystats_id AS INT64)
LEFT JOIN `hkjc.teams` hkjc ON mapping_hkjc.hkjc_id = hkjc.id
LEFT JOIN `manual.transfermarkt_teams` transfermarkt ON footystats.id = CAST(transfermarkt.footystats_id AS INT64)
LEFT JOIN `master.leagues` leagues ON _SEASON_ID = latest_season_id AND is_league
LEFT JOIN `manual.non_hkjc_teams` non_hkjc ON footystats.id = CAST(non_hkjc.footystats_id AS INT64)
QUALIFY ROW_NUMBER() OVER (PARTITION BY footystats.id ORDER BY is_league DESC) = 1