SELECT t.*
FROM `simulation.leagues` t
JOIN (
  SELECT _LEAGUE, MAX(_DATE_UNIX) AS max_date_unix
  FROM `simulation.leagues`
  GROUP BY _LEAGUE
) latest
ON t._LEAGUE = latest._LEAGUE AND t._DATE_UNIX = latest.max_date_unix