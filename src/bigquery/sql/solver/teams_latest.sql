SELECT teams.*
FROM solver.teams
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS _DATE_UNIX
  FROM `solver.teams`
  GROUP BY _TYPE
) latest
ON teams._TYPE = latest._TYPE AND teams._DATE_UNIX = latest._DATE_UNIX