SELECT t.*
FROM `solver.teams` t
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS _DATE_UNIX
  FROM `solver.teams`
  WHERE _DATE_UNIX <= (
    SELECT MAX(_DATE_UNIX) - (7 * 24 * 60 * 60) 
    FROM `solver.teams`
  )
  GROUP BY _TYPE
) latest
ON t._TYPE = latest._TYPE AND t._DATE_UNIX = latest._DATE_UNIX