WITH
  footystats AS (
    SELECT DISTINCT country, name
    FROM `footystats.season`
  ),
  hkjc AS (
    SELECT
      hkjc.id AS hkjc_id,
      mapping_hkjc.country,
      mapping_hkjc.name,
      nameC,
      transfermarkt_id
    FROM `hkjc.leagues` hkjc
    LEFT JOIN `mapping.hkjc_leagues` mapping_hkjc
    ON hkjc.code = mapping_hkjc.code
    LEFT JOIN footystats
    ON mapping_hkjc.country = footystats.country
    AND mapping_hkjc.name = footystats.name
    LEFT JOIN `mapping.transfermarkt_leagues` mapping_transfermarkt
    ON mapping_hkjc.country = mapping_transfermarkt.country
    AND mapping_hkjc.name = mapping_transfermarkt.name
  ),
  non_hkjc AS (
    SELECT
      CAST(NULL AS STRING) AS hkjc_id,
      non_hkjc.country,
      non_hkjc.name,
      nameC,
      transfermarkt_id
    FROM `mapping.non_hkjc_leagues` non_hkjc
    JOIN `mapping.transfermarkt_leagues` transfermarkt
    ON non_hkjc.country = transfermarkt.country
    AND non_hkjc.name = transfermarkt.name
  )
SELECT
  hkjc_id,
  country,
  name,
  nameC,
  transfermarkt_id
FROM
  hkjc
UNION ALL
SELECT
  hkjc_id,
  country,
  name,
  nameC,
  transfermarkt_id
FROM
  non_hkjc;