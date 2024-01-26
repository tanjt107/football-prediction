SELECT teams.*
FROM solver.teams
JOIN (
  SELECT _TYPE, MAX(_DATE_UNIX) AS _DATE_UNIX
  FROM `solver.teams`
  WHERE _DATE_UNIX <= (
    SELECT MAX(_DATE_UNIX) - (7 * 24 * 60 * 60) 
    FROM `solver.teams`
  )
  GROUP BY _TYPE
) latest
ON teams._TYPE = latest._TYPE AND teams._DATE_UNIX = latest._DATE_UNIX