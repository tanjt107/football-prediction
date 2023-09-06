SELECT
  FORMAT_TIMESTAMP('%F %T', TIMESTAMP_SECONDS(date_unix), 'Asia/Hong_Kong') AS matchDate,
  league_info.transfermarkt_id AS league_transfermarkt_id,
  home_team_info.transfermarkt_id AS home_team_transfermarkt_id,
  home_team_info.nameC AS home_team_name,
  away_team_info.transfermarkt_id AS away_team_transfermarkt_id,
  away_team_info.nameC AS away_team_name,
  CONCAT(homeGoalCount, " - ", awayGoalCount) AS score,
  CONCAT(FORMAT("%.2f", team_a_xg), " - ", FORMAT("%.2f", team_b_xg)) AS xg
FROM
  `footystats.matches` matches
JOIN
  `footystats.season` season
ON
  matches.competition_id = season.id
JOIN
  `footystats.teams` home_teams
ON
  matches.homeID = home_teams.id
  AND matches.competition_id = home_teams.competition_id
JOIN
  `footystats.teams` away_teams
ON
  matches.awayID = away_teams.id
  AND matches.competition_id = away_teams.competition_id
LEFT JOIN
  `mapping.league_info` league_info
ON
  season.country = league_info.country
  AND season.name = league_info.name
LEFT JOIN
  `mapping.team_info` home_team_info
ON
  matches.homeID = home_team_info.footystats_id
LEFT JOIN
  `mapping.team_info` away_team_info
ON
  matches.awayID = away_team_info.footystats_id
WHERE
  matches.status = 'complete'
  AND ( home_teams.country = 'Hong Kong'
    OR away_teams.country = 'Hong Kong')
  AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), TIMESTAMP_SECONDS(date_unix), DAY) < 30
ORDER BY
  date_unix DESC