WITH maxmin AS (
  SELECT
    _TYPE,
    MAX(offence - defence) AS _max,
    MIN(offence - defence) AS _min
  FROM solver.teams_latest
  JOIN master.teams ON teams_latest.id = teams.solver_id
    AND teams_latest._TYPE = teams.type
  WHERE hkjc_id IS NOT NULL
    OR is_manual
  GROUP BY _TYPE
)

SELECT
  id,
  teams_latest._TYPE,
  GREATEST(1.35 + offence, 0.2) AS offence,
  GREATEST(1.35 + defence, 0.2) AS defence,
  CASE
    WHEN offence - defence > 0 THEN (offence - defence) / _max * 50 + 50
    WHEN offence - defence < 0 THEN (1 - (offence - defence) / _min) * 50
    ELSE 50
  END AS rating,
  _DATE_UNIX
FROM solver.teams_latest
JOIN maxmin ON teams_latest._TYPE = maxmin._TYPE