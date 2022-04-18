SELECT
    "avg_goal" AS avg_goal,
    "home_adv" AS home_adv,
    home_id,
    CONCAT(home_id, "_off") AS home_off,
    CONCAT(home_id, "_def") AS home_def,
    away_id,
	CONCAT(away_id, "_off") AS away_off,
    CONCAT(away_id, "_def") AS away_def,
    is_home_away,
    home_avg,
    away_avg,
    0 AS home_league,
    0 AS away_league,
    date_unix
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