SELECT
    t.league_name,
    t.id,
    t.start_date_unix,
    (LEAD(t.start_date_unix, 1, UNIX_TIMESTAMP())
        OVER (
        PARTITION BY t.league_name
        ORDER BY t.starting_year, t.ending_year ) - 1 ) AS end_date_unix
FROM
    (SELECT
        seasons.league_name,
        seasons.id,
        seasons.starting_year,
        seasons.ending_year,
        MIN(matches.date_unix) AS start_date_unix
    FROM seasons
        LEFT JOIN matches ON matches.competition_id = seasons.id
    WHERE seasons.format = 'Domestic League'
    GROUP BY
        seasons.league_name,
        seasons.id,
        seasons.starting_year,
        seasons.ending_year) t 