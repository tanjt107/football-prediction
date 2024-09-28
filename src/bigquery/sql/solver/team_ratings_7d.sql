WITH match_probs AS (
  SELECT
  id,
  _TYPE,
  functions.matchProbs(GREATEST(1.37 + offence, 0.2), GREATEST(1.37 + defence, 0.2), '0') AS had_probs,
  _DATE_UNIX
  FROM solver.teams_7d
)

SELECT
  id,
  _TYPE,
  (had_probs[0] * 3 + had_probs[1]) / 3 * 100 AS rating
FROM match_probs