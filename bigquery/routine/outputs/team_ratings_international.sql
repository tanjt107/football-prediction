WITH solver AS (
  SELECT
    solver.id,
    teams.transfermarkt_id,
    teams.name,
    GREATEST(1.35 + offence, 0.2) AS offence,
    GREATEST(1.35 + defence, 0.2) AS defence
  FROM `solver.teams` solver
  JOIN `master.teams` teams ON solver.id = teams.solver_id
  WHERE in_team_rating AND type = 'International'
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
  RANK() OVER(ORDER BY rating DESC) AS rank,
  transfermarkt_id,
  name,
  ROUND(offence, 2) AS offence,
  ROUND(defence, 2) AS defence,
  ROUND(rating, 1) AS rating
FROM solver
JOIN ratings ON solver.id = ratings.id
ORDER BY rank;