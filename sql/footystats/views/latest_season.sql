SELECT
    seasons.league_name,
	seasons.id,
    seasons.season
FROM
    seasons
    INNER JOIN (SELECT
        league_name,
        MAX(starting_year) AS last_starting_year,
        MAX(ending_year) AS last_ending_year
    FROM
        seasons
    WHERE
        format = 'Domestic League'
        AND status <> 'Not Started'
    GROUP BY league_name) t ON seasons.league_name = t.league_name
        AND seasons.starting_year = t.last_starting_year
        AND seasons.ending_year = t.last_ending_year
