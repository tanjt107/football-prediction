SELECT
  COALESCE(hkjc.name_ch, manual.name_ch, footystats.name) AS name,
  footystats.country,
  CASE
    WHEN is_wcq THEN 'International'
    ELSE 'Club'
  END AS type,
  footystats.id AS footystats_id,
  hkjc.id AS hkjc_id,
  manual.transfermarkt_id,
  CASE
    WHEN latest_season_id IS NULL OR is_wcq THEN footystats.country
    ELSE CAST(footystats.id AS STRING)
  END AS solver_id,
  manual.name_ch IS NOT NULL AS is_manual,
  COALESCE(is_simulate, FALSE) AS is_simulate,
  CASE
    WHEN is_wcq THEN (hkjc.id IS NOT NULL OR manual.name_ch IS NOT NULL)
    ELSE (leagues.hkjc_id IS NOT NULL OR leagues.is_manual IS TRUE) AND leagues.footystats_name <> 'Mexico Ascenso MX'
  END AS in_team_rating,
  footystats_name AS league_name
FROM `footystats.teams` footystats
LEFT JOIN `manual.teams` manual ON footystats.id = manual.footystats_id
LEFT JOIN `hkjc.teams` hkjc ON manual.hkjc_id = hkjc.id
LEFT JOIN master.leagues ON _NAME = footystats_name
QUALIFY ROW_NUMBER() OVER (PARTITION BY footystats.id ORDER BY is_wcq DESC, is_league DESC, _SEASON_ID = latest_season_id DESC) = 1