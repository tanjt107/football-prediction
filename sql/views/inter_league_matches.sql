SELECT
    matches.home_id,
    matches.away_id,
    matches.date_unix,
    matches.no_home_away,
    matches.home_avg,
    matches.away_avg,
    matches.total_xg > 0 AS have_xg,
    home.league AS home_league,
    home.competition_id AS home_season_id,
    away.league AS away_league,
    away.competition_id AS away_season_id
FROM
    matches
    LEFT JOIN match_season_map home ON matches.home_id = home.team_id
        AND matches.date_unix = home.date_unix
    LEFT JOIN match_season_map away ON matches.away_id = away.team_id
        AND matches.date_unix = away.date_unix
WHERE
    matches.status = 'complete'
        AND home.league <> away.league
ORDER BY matches.date_time 