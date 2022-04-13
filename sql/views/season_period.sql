SELECT
    t.country,
    t.name,
    t.id,
    t.start_date,
    ( LEAD(t.start_date, 1, NOW())
        OVER (
        PARTITION BY t.country, t.name
        ORDER BY t.starting_year, t.ending_year ) - INTERVAL 1 SECOND ) AS end_date
FROM
    (SELECT
        seasons.country,
        seasons.name,
        seasons.id,
        seasons.starting_year,
        seasons.ending_year,
        MIN(matches.date_time) AS start_date
    FROM seasons
        LEFT JOIN matches ON matches.competition_id = seasons.id
    WHERE seasons.format = 'Domestic League'
        AND seasons.country NOT IN ( 'International', 'Asia' )
    GROUP BY
        seasons.country,
        seasons.name,
        seasons.id,
        seasons.starting_year,
        seasons.ending_year) t 