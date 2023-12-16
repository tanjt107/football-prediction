WITH maxmin AS (
  SELECT
    _TYPE,
    MAX(offence - defence) AS _max,
    MIN(offence - defence) AS _min
  FROM `solver.teams_7d` solver
  WHERE id NOT IN ('American Samoa', 'Tonga') -- Exclude outliers. To be reviewed in Feb 2024.
  GROUP BY _TYPE
)

SELECT
  id,
  solver._TYPE,
  CASE
    WHEN offence - defence > 0 THEN (offence - defence) / _max * 50 + 50
    WHEN offence - defence < 0 THEN (1 - (offence - defence) / _min) * 50
    ELSE 50
  END AS rating
FROM `solver.teams_7d` solver
JOIN maxmin ON solver._TYPE = maxmin._TYPE
ORDER BY rating DESC