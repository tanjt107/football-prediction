WITH divisions AS (
  SELECT
    DISTINCT CONCAT(country, ' ', name) AS league,
    CASE
      WHEN country IN (
        SELECT country 
        FROM `footystats.season` 
        GROUP BY country 
        HAVING MAX(division) > 1
      ) AND division > 0 THEN CONCAT(country, division)
      ELSE country
    END AS country_division
  FROM `footystats.season`
)

SELECT
  homeID,
  awayID,
  avg_goal + home.offence + away.defence AS home_exp,
  avg_goal + away.offence + home.defence AS away_exp,
  home_adv
FROM `footystats.matches`
JOIN `footystats.season` season ON competition_id = season.id
LEFT JOIN `solver.teams` home ON homeID = home.team
LEFT JOIN `solver.teams` away ON awayID = away.team
JOIN divisions ON CONCAT(country, ' ', name) = divisions.league
JOIN `solver.leagues` leagues ON country_division = leagues.league
WHERE
  date_unix > UNIX_SECONDS(CURRENT_TIMESTAMP())
  AND date_unix < UNIX_SECONDS(TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 3 DAY))
ORDER BY date_unix;