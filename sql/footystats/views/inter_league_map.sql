SELECT DISTINCT
	t.date_unix,
    t.season_id,
    MAX(matches.date_unix) AS last_date_unix
FROM (
	SELECT
		date_unix,
		home_season_id AS season_id
	FROM
		footystats.inter_league_matches UNION SELECT
		date_unix,
		away_season_id AS season_id
	FROM
		footystats.inter_league_matches) t
    LEFT JOIN matches ON t.season_id = matches.competition_id
        AND t.date_unix > matches.date_unix
WHERE
    season_id IS NOT NULL
GROUP BY t.date_unix, t.season_id