WITH solver AS (
  SELECT
    id,
    _TYPE,
    GREATEST(1.35 + offence, 0.2) AS offence,
    GREATEST(1.35 + defence, 0.2) AS defence
  FROM `solver.teams_7d` solver
),

match_probs AS (
  SELECT
    id,
    _TYPE,
    functions.matchProbs(offence, defence, '0') AS match_prob
  FROM solver
)

SELECT
  id,
  _TYPE,
  (match_prob[OFFSET(0)] * 3 + match_prob[OFFSET(1)]) / 3 * 100 AS rating
FROM match_probs