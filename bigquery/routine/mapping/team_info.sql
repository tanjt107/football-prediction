WITH
  footystats AS (
    SELECT DISTINCT id
    FROM `footystats.teams`
  ),
  hkjc AS (
    SELECT
      hkjc.id AS hkjc_id,
      mapping_hkjc.footystats_id,
      nameC,
      transfermarkt_id
    FROM `hkjc.teams` hkjc
    LEFT JOIN `mapping.hkjc_teams` mapping_hkjc
    ON id = CAST(hkjc_id AS STRING)
    LEFT JOIN footystats
    ON footystats_id = footystats.id
    LEFT JOIN `mapping.transfermarkt_teams` mapping_transfermarkt
    ON mapping_hkjc.footystats_id = mapping_transfermarkt.footystats_id
  ),
  non_hkjc AS (
    SELECT
      CAST(NULL AS STRING) AS hkjc_id,
      footystats_id,
      nameC,
      transfermarkt_id
    FROM `mapping.non_hkjc_teams` non_hkjc
    JOIN `mapping.transfermarkt_teams` transfermarkt
    ON id = footystats_id
  )
SELECT
  hkjc_id,
  footystats_id,
  nameC,
  transfermarkt_id
FROM
  hkjc
UNION ALL
SELECT
  hkjc_id,
  footystats_id,
  nameC,
  transfermarkt_id
FROM
  non_hkjc;