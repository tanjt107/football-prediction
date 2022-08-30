SELECT
	matches.date_unix,
	matches.home_id,
    matches.away_id,
    matches.is_home_away,
    matches.home_avg,
    matches.away_avg,
    home_league.strength AS home_league,
    away_league.strength AS away_league,
	"avg_goal" as avg_goal,
    "home_adv" as home_adv,
    IF(matches.home_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s),
        CONCAT(matches.home_id, "_off"),
        COALESCE(home_solver.offence, 1.25)) AS home_off,
    IF(matches.home_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s),
        CONCAT(matches.home_id, "_def"),
        COALESCE(home_solver.defence, 0.8)) AS home_def,
	IF(matches.away_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s),
        CONCAT(matches.away_id, "_off"),
        COALESCE(away_solver.offence, 1.25)) AS away_off,
    IF(matches.away_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s),
        CONCAT(matches.away_id, "_def"),
        COALESCE(away_solver.defence, 0.8)) AS away_def
FROM
	footystats.matches_details matches
    LEFT JOIN solver.inter_league home_league ON matches.home_league = home_league.league
    LEFT JOIN footystats.inter_league_map home_map ON matches.date_unix = home_map.date_unix
        AND matches.home_season_id = home_map.season_id
    LEFT JOIN solver.domestic home_solver ON home_map.last_date_unix = home_solver.date_unix
        AND matches.home_id = home_solver.team
    LEFT JOIN solver.inter_league away_league ON matches.away_league = away_league.league
    LEFT JOIN footystats.inter_league_map away_map ON matches.date_unix = away_map.date_unix
        AND matches.away_season_id = home_map.season_id
    LEFT JOIN solver.domestic away_solver ON away_map.last_date_unix = away_solver.date_unix
        AND matches.away_id = away_solver.team
    WHERE status = 'complete'
        AND (home_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s)
        OR away_id IN (SELECT
            team_id
        FROM
            footystats.teams
        WHERE
            competition_id = %(season_id)s))
        AND matches.date_unix > (SELECT
            MAX(date_unix)
        FROM
            footystats.matches_details
        WHERE status = 'complete'
            AND (home_season_id = %(season_id)s
            OR away_season_id = %(season_id)s)) - 31536000