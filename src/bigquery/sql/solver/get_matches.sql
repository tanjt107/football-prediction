WITH matches AS (
  SELECT
    matches.id,
    home_teams.solver_id AS home_id,
    away_teams.solver_id AS away_id,
    division,
    CASE
      WHEN home_teams.country = away_teams.country AND league_type = 'Club' THEN 1
      ELSE 5
    END
    AS cut_off_year,
    date_unix,
    home_avg,
    away_avg
  FROM `${project_id}.footystats.matches` matches
  JOIN `${project_id}.master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `${project_id}.master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN `${project_id}.master.leagues` leagues ON matches._NAME = leagues.footystats_id
  JOIN `${project_id}.footystats.matches_transformed` matches_transformed ON matches.id = matches_transformed.id
  WHERE matches.status = 'complete'
    AND date_unix <= max_time
    AND home_teams.solver_id <> away_teams.solver_id
    AND leagues.type = league_type
),

recentness AS (
  SELECT
    id,
    1 - (max_time - date_unix) / (365 * 24 * 60 * 60 * cut_off_year) AS recent,
    (1 - (max_time - date_unix) / (25 * 24 * 60 * 60 * cut_off_year)) * 0.25 AS recent_bonus
  FROM matches
  WHERE max_time - date_unix < 365 * 24 * 60 * 60 * cut_off_year
  )

SELECT
  matches.id,
  division AS league_name,
  home_id,
  away_id,
  recent + GREATEST(recent_bonus, 0) AS recent,
  home_avg,
  away_avg
FROM matches
JOIN recentness ON matches.id = recentness.id