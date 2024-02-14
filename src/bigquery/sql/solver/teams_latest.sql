SELECT teams.*
FROM solver.teams
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS _DATE_UNIX
  FROM `solver.teams`
  GROUP BY _TYPE
) latest
USING (_TYPE, _DATE_UNIX)