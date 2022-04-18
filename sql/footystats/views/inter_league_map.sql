SELECT DISTINCT
	t.date_unix,
    t.season_id,
    MAX(matches.date_unix) AS last_date_unix,
    MAX(matches.modified_date) AS modified_date
FROM (
	SELECT
		date_unix,
        status,
		home_season_id AS season_id
	FROM
		footystats.matches_details
	WHERE
		status = 'complete'
        AND home_season_id IS NOT NULL
		AND home_league <> away_league UNION
	SELECT
		date_unix,
        status,
		away_season_id AS season_id
	FROM
		footystats.matches_details
	WHERE
		status = 'complete'
        AND away_season_id IS NOT NULL
		AND home_league <> away_league) t
    LEFT JOIN matches ON t.season_id = matches.competition_id
    AND t.date_unix > matches.date_unix
GROUP BY t.date_unix, t.season_id