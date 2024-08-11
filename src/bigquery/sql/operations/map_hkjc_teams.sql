WITH
  hkjc AS (
  SELECT matchDate, tournament.name_ch AS tournament_name, homeTeam.id, homeTeam.name_ch, homeTeam.name_en
  FROM hkjc.results
  UNION ALL
  SELECT matchDate, tournament.name_ch AS tournament_name, awayTeam.id, awayTeam.name_ch, awayTeam.name_en
  FROM hkjc.results)

SELECT MAX(matchDate) AS matchDate, tournament_name, id, name_ch, name_en, teams.footystats_id
FROM hkjc
LEFT JOIN master.teams ON hkjc.id = teams.hkjc_id
WHERE teams.transfermarkt_id IS NULL
    AND name_ch NOT LIKE '%U2_'
    AND name_ch NOT LIKE '%女足'
    AND name_ch NOT LIKE '%奧足'
GROUP BY tournament_name, id, name_ch, name_en, teams.footystats_id
ORDER BY tournament_name, matchDate