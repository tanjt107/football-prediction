WITH
  divisions AS (
    SELECT
      id,
      (
        CASE
          WHEN country IN (
            SELECT
              country
            FROM
              `${project_id}.footystats.season`
            GROUP BY
              country
            HAVING
              MAX(division) > 1
          ) AND division > 0
            THEN country || division
          ELSE
            country
        END
      ) AS league_name
    FROM
      `${project_id}.footystats.season`
    WHERE
      (country <> 'International'
        OR name IN (
          SELECT
            name
          FROM
            `${project_id}.mapping.intl_club_competitions`
        )
      )
  ),

  matches AS (
    SELECT
      id,
      homeID,
      awayID,
      competition_id,
      date_unix
    FROM
      `${project_id}.footystats.matches` matches
    WHERE
      status = 'complete'
      AND competition_ID IN (
        SELECT
          id
        FROM
          divisions
      )
  ),

  var AS (
    SELECT
      MAX(date_unix) AS max_time
    FROM
      matches
  ),

  recentness AS (
    SELECT
      matches.id,
      1 - ((var.max_time - date_unix) / (31536000 *
        CASE
          WHEN home_teams.country = away_teams.country THEN cut_off_year
          ELSE inter_league_cut_off_year
        END
      )) + GREATEST( 1 - ((var.max_time - date_unix) / (2160000 *
        CASE
          WHEN home_teams.country = away_teams.country THEN cut_off_year
          ELSE inter_league_cut_off_year
        END
      )), 0) * 0.25 AS recent
    FROM
      matches
    JOIN
      `${project_id}.footystats.teams` home_teams
        ON homeID = home_teams.id
        AND matches.competition_id = home_teams.competition_id
    JOIN
      `${project_id}.footystats.teams` away_teams
        ON awayID = away_teams.id
        AND matches.competition_id = away_teams.competition_id
    CROSS JOIN
      var
  )
  
SELECT
  matches.id,
  league_name,
  homeID,
  awayID,
  recent,
  home_avg,
  away_avg
FROM
  matches
JOIN
  divisions
    ON competition_id = divisions.id
JOIN
  recentness
    ON matches.id = recentness.id
JOIN
  `${project_id}.footystats.matches_transformed` matches_transformed
    ON matches.id = matches_transformed.id
WHERE
  recent > 0