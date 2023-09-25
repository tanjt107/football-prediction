WITH solver AS (
  SELECT
    id,
    GREATEST(1.35 + offence, 0.2) AS offence,
    GREATEST(1.35 + defence, 0.2) AS defence
  FROM `solver.teams` solver
),

match_probs AS (
  SELECT
    id,
    functions.matchProbs(offence, defence, '0') AS match_prob
  FROM solver
),

ratings AS (
  SELECT
    id,
    (match_prob[OFFSET(0)] * 3 + match_prob[OFFSET(1)]) / 3 * 100 AS rating
  FROM match_probs  
)

SELECT
  solver.id,
  offence,
  defence,
  rating
FROM solver
JOIN ratings ON solver.id = ratings.id;