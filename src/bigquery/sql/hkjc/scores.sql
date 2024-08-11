SELECT
  id,
  homeResult AS home_score,
  awayResult AS away_score
FROM hkjc.results,
  UNNEST(results.results) AS _results
WHERE stageID = 5
  AND resultType = 1