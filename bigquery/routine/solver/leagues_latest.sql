SELECT t.*
FROM `solver.leagues` t
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS max_date_unix
  FROM `solver.leagues`
  GROUP BY _TYPE
) latest
ON t._TYPE = latest._TYPE AND t._DATE_UNIX = latest.max_date_unix