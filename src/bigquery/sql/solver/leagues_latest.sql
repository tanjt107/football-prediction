SELECT leagues.*
FROM solver.leagues
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS max_date_unix
  FROM `solver.leagues`
  GROUP BY _TYPE
) latest
ON leagues._TYPE = latest._TYPE AND leagues._DATE_UNIX = latest.max_date_unix