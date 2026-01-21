SELECT teams.*
FROM solver.teams
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS _DATE_UNIX
  FROM `solver.teams` t1
  WHERE t1._DATE_UNIX <= (
    SELECT MAX(_DATE_UNIX) - (7 * 24 * 60 * 60)
    FROM `solver.teams` t2
    WHERE t1._TYPE = t2._TYPE
  ) 
  GROUP BY _TYPE
) latest
USING (_TYPE, _DATE_UNIX)