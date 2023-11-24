WITH maxmin AS (
  SELECT
    _TYPE,
    MAX(offence - defence) AS _max,
    MIN(offence - defence) AS _min
  FROM `solver.teams_7d` solver
  GROUP BY _TYPE
)

SELECT
  id,
  solver._TYPE,
  (offence - defence - _min) / (_max - _min) * 100 AS rating
FROM `solver.teams_7d` solver
JOIN maxmin ON solver._TYPE = maxmin._TYPE
ORDER BY rating DESC