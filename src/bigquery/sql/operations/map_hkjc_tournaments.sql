SELECT MAX(kick_off_time) AS kick_off_time, tournament_id, tournament_name
FROM hkjc.odds_latest
LEFT JOIN master.leagues ON odds_latest.tournament_id = leagues.hkjc_id
WHERE leagues.transfermarkt_id IS NULL
  AND tournament_id NOT IN ('CUP', 'CLB', 'INT')
  AND tournament_name NOT LIKE '女%'
  AND tournament_name NOT LIKE 'U%'
GROUP BY tournament_id, tournament_name