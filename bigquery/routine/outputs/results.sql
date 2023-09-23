SELECT
  FORMAT_TIMESTAMP('%F %H:%M', TIMESTAMP_SECONDS(date_unix), 'Asia/Hong_Kong') AS matchDate,
  leagues.transfermarkt_id AS league_transfermarkt_id,
  home_teams.transfermarkt_id AS home_team_transfermarkt_id,
  home_teams.name AS home_team_name,
  away_teams.transfermarkt_id AS away_team_transfermarkt_id,
  away_teams.name AS away_team_name,
  CONCAT(homeGoalCount, " - ", awayGoalCount) AS score,
  CONCAT(FORMAT("%.2f", team_a_xg), " - ", FORMAT("%.2f", team_b_xg)) AS xg
FROM `footystats.matches` matches
JOIN `footystats.seasons` seasons ON matches.competition_id = seasons.id
JOIN `master.leagues` leagues
  ON seasons.country = leagues.country
    AND seasons.name = leagues.footystats_name
JOIN `master.teams` home_teams ON matches.homeID = home_teams.footystats_id
JOIN `master.teams` away_teams ON matches.awayID = away_teams.footystats_id
WHERE
  matches.status = 'complete'
  AND ( home_teams.country = 'Hong Kong'
    OR away_teams.country = 'Hong Kong')
  AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), TIMESTAMP_SECONDS(date_unix), DAY) < 30
ORDER BY date_unix DESC