SELECT MAX(matchDate) AS matchDate, tournament.code, tournament.name_ch
FROM hkjc.results
LEFT JOIN master.leagues ON results.tournament.code = leagues.hkjc_id
WHERE leagues.transfermarkt_id IS NULL
  AND tournament.code NOT in ('CUP', 'OLW')
GROUP BY code, name_ch