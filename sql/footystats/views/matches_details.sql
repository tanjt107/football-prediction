SELECT
	matches.id,
	matches.date_unix,
    matches.status,
    matches.is_home_away,
    matches.home_id,
    home1.competition_id AS home_season_id,
    COALESCE(period_home.league_name,
        home2.country) AS home_league,
    matches.away_id,
    away1.competition_id AS away_season_id,
    COALESCE(period_away.league_name,
        away2.country) AS away_league,
    matches.home_avg,
    matches.away_avg
FROM
	matches
	LEFT JOIN (teams home1
	INNER JOIN season_period period_home ON home1.competition_id = period_home.id) ON matches.home_id = home1.team_id
        AND matches.date_unix >= period_home.start_date_unix
        AND matches.date_unix <= period_home.end_date_unix
--        AND matches.id NOT IN ()
	LEFT JOIN teams home2 ON matches.home_id = home2.team_id
        AND matches.competition_id = home2.competition_id
	LEFT JOIN (teams away1
	INNER JOIN season_period period_away ON away1.competition_id = period_away.id) ON matches.away_id = away1.team_id
		AND matches.date_unix >= period_away.start_date_unix
        AND matches.date_unix <= period_away.end_date_unix
--        AND matches.id NOT IN ()
	LEFT JOIN teams away2
		ON matches.away_id = away2.team_id
        AND matches.competition_id = away2.competition_id