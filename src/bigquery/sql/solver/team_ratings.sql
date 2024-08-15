WITH match_probs AS (
  SELECT
  id,
  _TYPE,
  GREATEST(1.35 + offence, 0.2) AS offence,
  GREATEST(1.35 + defence, 0.2) AS defence,
  functions.matchProbs(GREATEST(1.35 + offence, 0.2), GREATEST(1.35 + defence, 0.2), '0') AS had_probs,
  _DATE_UNIX
  FROM solver.teams_latest
)

SELECT
  id,
  _TYPE,
  offence,
  defence,
  (had_probs[0] * 3 + had_probs[1]) / 3 * 100 AS rating,
  _DATE_UNIX
FROM match_probs