WITH latest AS (
  SELECT
    RANK() OVER(ORDER BY rating DESC) AS rank,
    transfermarkt_id,
    id,
    name,
    CASE
      WHEN league_name = 'International WC Qualification Asia' THEN '亞洲'
      WHEN league_name = 'International WC Qualification Africa' THEN '非洲'
      WHEN league_name = 'International WC Qualification Europe' THEN '歐洲'
      WHEN league_name = 'International WC Qualification Oceania' THEN '大洋洲'
      WHEN league_name = 'International WC Qualification CONCACAF' THEN '中北美洲'
      WHEN league_name = 'International WC Qualification South America' THEN '南美洲'
    END AS confederation,
    ROUND(offence, 2) AS offence,
    ROUND(defence, 2) AS defence,
    ROUND(rating, 1) AS rating,
    _TYPE,
    _DATE_UNIX
  FROM solver.team_ratings
  JOIN master.teams ON team_ratings.id = teams.solver_id
    AND _TYPE = type
  WHERE team_ratings._TYPE = 'International'
    AND teams.in_team_rating
)

SELECT
  rank,
  RANK() OVER(ORDER BY team_ratings_7d.rating DESC) - rank AS rank_7d_diff,
  transfermarkt_id,
  name,
  confederation,
  offence,
  defence,
  latest.rating,
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_ADD(TIMESTAMP_SECONDS(_DATE_UNIX), INTERVAL 2 HOUR), 'Asia/Hong_Kong') AS date_unix
FROM latest
JOIN solver.team_ratings_7d USING(id, _TYPE)
ORDER BY rank;