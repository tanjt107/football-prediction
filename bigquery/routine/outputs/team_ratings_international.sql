WITH latest AS (
  SELECT
    RANK() OVER(ORDER BY rating DESC) AS rank,
    transfermarkt_id,
    id,
    name,
    ROUND(offence, 2) AS offence,
    ROUND(defence, 2) AS defence,
    ROUND(rating, 1) AS rating,
    _TYPE
  FROM `solver.team_ratings` ratings
  JOIN `master.teams` teams ON ratings.id = teams.solver_id
    AND _TYPE = type
  WHERE (hkjc_id IS NOT NULL
    OR is_manual)
    AND _TYPE = 'International')

SELECT
  rank,
  RANK() OVER(ORDER BY _7d.rating DESC) - rank AS rank_7d_diff,
  transfermarkt_id,
  name,
  offence,
  defence,
  latest.rating
FROM latest
JOIN `solver.team_ratings_7d` _7d ON latest.id = _7d.id
  AND latest._TYPE = _7d._TYPE
ORDER BY rank;