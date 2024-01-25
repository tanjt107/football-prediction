SELECT leagues.*
FROM simulation.leagues
JOIN (
  SELECT _LEAGUE, MAX(_DATE_UNIX) AS max_date_unix
  FROM `simulation.leagues`
  GROUP BY _LEAGUE
) latest
ON leagues._LEAGUE = latest._LEAGUE AND leagues._DATE_UNIX = latest.max_date_unix