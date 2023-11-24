WITH maxmin AS (
  SELECT
    _TYPE,
    MAX(offence - defence) AS _max,
    MIN(offence - defence) AS _min
  FROM `solver.teams_latest` solver
  GROUP BY _TYPE
)

SELECT
  id,
  solver._TYPE,
  GREATEST(1.35 + offence, 0.2) AS offence,
  GREATEST(1.35 + defence, 0.2) AS defence,
  (offence - defence - _min) / (_max - _min) * 100 AS rating
FROM `solver.teams_latest` solver
JOIN maxmin ON solver._TYPE = maxmin._TYPE
ORDER BY rating DESC