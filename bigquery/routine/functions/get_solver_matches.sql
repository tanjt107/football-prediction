WITH matches AS (
  SELECT
  matches.id,
  home_teams.id AS home_id,
  away_teams.id AS away_id,
  leagues.division,
  CASE
    WHEN home_teams.country <> away_teams.country OR leagues.type = 'International'
    THEN inter_league_cut_off_year
    ELSE cut_off_year
  END
  AS cut_off_year,
  date_unix
  FROM `${project_id}.footystats.matches` matches
  JOIN `${project_id}.master.teams` home_teams ON matches.homeID = home_teams.footystats_id
  JOIN `${project_id}.master.teams` away_teams ON matches.awayID = away_teams.footystats_id
  JOIN `${project_id}.footystats.seasons` seasons ON matches.competition_id = seasons.id
  JOIN `${project_id}.master.leagues` leagues ON seasons.country = leagues.country
    AND seasons.name = leagues.footystats_name
  WHERE matches.status = 'complete'
    AND leagues.type = league_type
),

recentness AS (
  SELECT
    id,
    1 - (max_time - date_unix) / (31536000 * cut_off_year) AS recent,
    (1 - (max_time - date_unix) / (2160000 * cut_off_year)) * 0.25 AS recent_bonus
  FROM
    matches )

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
JOIN `${project_id}.footystats.matches_transformed` matches_transformed ON matches.id = matches_transformed.id
WHERE recent > 0