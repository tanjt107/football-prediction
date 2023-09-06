WITH
  var AS (
  SELECT MAX(date_unix) AS max_time
  FROM `${project_id}.footystats.matches`
  WHERE status = 'complete' ),
  team_ids AS (
  SELECT id
  FROM `${project_id}.footystats.teams`
  WHERE competition_id IN ( SELECT id FROM `${project_id}.footystats.latest_season`) ),
  matches AS (
  SELECT
    matches.id,
    homeID,
    awayID,
    matches.competition_id,
    date_unix,
    matches_transformed.home_avg,
    matches_transformed.away_avg,
    GREATEST(
        1 - ((var.max_time - date_unix) / (31536000 * 
                  CASE
                    WHEN home_teams.country = away_teams.country
                    THEN cut_off_year
                    ELSE inter_league_cut_off_year
                  END
                    )), 0) 
    +
    GREATEST(
        1 - ((var.max_time - date_unix) / (2160000 *
                  CASE
                    WHEN home_teams.country = away_teams.country
                    THEN cut_off_year
                    ELSE inter_league_cut_off_year
                  END
                  )), 0) * 0.25 AS recent
  FROM
    `${project_id}.footystats.matches` matches
  JOIN
    `${project_id}.footystats.teams` home_teams
  ON
    matches.homeID = home_teams.id
    AND matches.competition_id = home_teams.competition_id
  JOIN
    `${project_id}.footystats.teams` away_teams
  ON
    matches.awayID = away_teams.id
    AND matches.competition_id = away_teams.competition_id
  JOIN
    `${project_id}.footystats.matches_transformed` matches_transformed
  ON
    matches.id = matches_transformed.id
  CROSS JOIN
    var
  WHERE
    matches.status = 'complete')

SELECT
  matches.id,
  (CASE
      WHEN seasons.country IN (
        SELECT country
        FROM `${project_id}.footystats.season`
        GROUP BY country
        HAVING MAX(division) > 1 
        ) AND seasons.division > 0
      THEN seasons.country || seasons.division
      ELSE seasons.country
  END
    ) AS league_name,
  homeID,
  awayID,
  recent,
  home_avg,
  away_avg
FROM
  matches
JOIN
  `${project_id}.footystats.season` seasons
ON
  matches.competition_id = seasons.id
WHERE
  recent > 0