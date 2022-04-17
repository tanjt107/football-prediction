SELECT
    home_id,
    away_id,
    date_unix,
    no_home_away,
    total_xg > 0 AS have_xg,
    home_avg,
    away_avg,
    1 AS home_league,
    1 AS away_league
FROM
    footystats.matches
WHERE
    status = 'complete'
        AND date_unix BETWEEN %(last_date_unix)s - 31536000 AND %(last_date_unix)s
        AND home_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s)
        AND away_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s)