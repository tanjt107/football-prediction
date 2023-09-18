WITH average AS (
  SELECT
    AVG(offence) AS offence,
    AVG(defence) AS defence
  FROM `solver.teams` solver
  JOIN `master.teams` master ON solver.id = master.id
  WHERE in_team_rating AND type = 'International'
),

factors AS (
  SELECT
    id,
    GREATEST(1.35 + solver.offence - average.offence, 0.2) AS offence,
    GREATEST(1.35 + solver.defence - average.defence, 0.2) AS defence
  FROM `solver.teams` solver
  CROSS JOIN average
),

match_probs AS (
  SELECT
    id,
    functions.matchProbs(offence, defence, '0', 5) AS match_prob
  FROM factors
),

ratings AS (
  SELECT
    id,
    (match_prob[OFFSET(0)] * 3 + match_prob[OFFSET(1)]) / 3 * 100 AS rating
  FROM match_probs  
)

SELECT
  RANK() OVER(ORDER BY rating DESC) AS rank,
  teams.transfermarkt_id AS team_icon,
  teams.name AS team,
  ROUND(offence, 1) AS offence,
  ROUND(defence, 1) AS defence,
  ROUND(rating, 1) AS rating
FROM factors
JOIN `master.teams` teams ON factors.id = teams.id
JOIN ratings ON factors.id = ratings.id
WHERE in_team_rating AND type = 'International'
ORDER BY rank;