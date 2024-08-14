SELECT MAX(kick_off_time) AS kick_off_time, tournament_id, tournament_name
FROM hkjc.odds_today
LEFT JOIN master.leagues ON odds_today.tournament_id = leagues.hkjc_id
WHERE leagues.transfermarkt_id IS NULL
  AND tournament_id NOT in ('CUP', 'OLW')
GROUP BY tournament_id, tournament_name