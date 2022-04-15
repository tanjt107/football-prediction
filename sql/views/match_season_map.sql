SELECT
    temp.team_id,
    temp.date_unix,
    CONCAT(season_period.country, ' ', season_period.name) AS league,
    teams.competition_id
FROM
    (SELECT
        matches.home_id AS team_id,
        matches.date_time,
        matches.date_unix
    FROM
        matches UNION SELECT
        matches.away_id AS team_id,
        matches.date_time,
        matches.date_unix
    FROM matches) temp
    JOIN teams ON temp.team_id = teams.team_id
    JOIN season_period ON teams.competition_id = season_period.id
        AND temp.date_time BETWEEN season_period.start_date AND season_period.end_date 