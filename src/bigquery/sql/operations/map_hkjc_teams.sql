WITH
  hkjc AS (
  SELECT kick_off_time, tournament_name, home_id AS id, home_name AS name, home_name_en AS name_en
  FROM hkjc.odds_latest
  UNION ALL
  SELECT kick_off_time, tournament_name, away_id, away_name, away_name_en
  FROM hkjc.odds_latest)

SELECT MAX(kick_off_time) AS kick_off_time, tournament_name, id, hkjc.name, name_en, footystats_id
FROM hkjc
LEFT JOIN master.teams ON hkjc.id = teams.hkjc_id
WHERE transfermarkt_id IS NULL
    AND hkjc.name NOT LIKE '%U2_'
    AND hkjc.name NOT LIKE '%女足'
    AND hkjc.name NOT LIKE '%奧足'
GROUP BY tournament_name, id, hkjc.name, name_en, footystats_id
ORDER BY tournament_name, kick_off_time