SELECT MAX(kick_off_time) AS kick_off_time, tournament_id, tournament_name
FROM hkjc.odds_last
LEFT JOIN master.leagues ON odds_last.tournament_id = leagues.hkjc_id
WHERE leagues.transfermarkt_id IS NULL
  AND tournament_id NOT in ('CUP', 'OLW', 'CLB', 'INT')
GROUP BY tournament_id, tournament_name