WITH matches AS (
  SELECT
    matches.id,
    home_teams.solver_id AS home_id,
    home_teams.is_team_rating AS is_home_team_rating,
    away_teams.solver_id AS away_id,
    away_teams.is_team_rating AS is_away_team_rating,
    division,
    CASE
      WHEN (is_league OR home_teams.country = away_teams.country)AND league_type = 'Club' THEN 1
      ELSE 5
    END
    AS cut_off_year,
    date_unix,
    home_avg,
    away_avg
  FROM ${project_id}.footystats.matches
  JOIN `${project_id}.master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `${project_id}.master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN ${project_id}.master.leagues ON matches._NAME = leagues.footystats_name
  JOIN ${project_id}.footystats.matches_transformed USING (id)
  WHERE matches.status = 'complete'
    AND date_unix <= max_time
    AND home_teams.solver_id <> away_teams.solver_id
    AND home_teams.type = league_type
    AND away_teams.type = league_type
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
  is_home_team_rating,
  away_id,
  is_away_team_rating,
  recent + GREATEST(recent_bonus, 0) AS recent,
  home_avg,
  away_avg
FROM matches
JOIN recentness USING (id)