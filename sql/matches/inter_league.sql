SELECT
    "avg_goal" AS avg_goal,
    "home_adv" AS home_adv,
	footystats.matches_details.id,
    footystats.matches_details.date_unix,
    footystats.matches_details.is_home_away,
    footystats.matches_details.home_league,
	IF(footystats.matches_details.home_season_id IS NULL,
        1.25,
        solver_home.offence) AS home_off,
    IF(footystats.matches_details.home_season_id IS NULL,
        0.8,
        solver_home.defence) AS home_def,
	IF(footystats.matches_details.away_season_id IS NULL,
        1.25,
        solver_away.offence) AS away_off,
    IF(footystats.matches_details.away_season_id IS NULL,
        0.8,
        solver_away.defence) AS away_def,
	footystats.matches_details.away_league,
    footystats.matches_details.home_avg,
    footystats.matches_details.away_avg
FROM
    footystats.matches_details
    LEFT JOIN footystats.inter_league_map map_home ON footystats.matches_details.date_unix = map_home.date_unix
        AND footystats.matches_details.home_season_id = map_home.season_id
    LEFT JOIN solver.domestic solver_home ON solver_home.season = footystats.matches_details.home_season_id
        AND map_home.last_date_unix = solver_home.date_unix
        AND footystats.matches_details.home_id = solver_home.team
    LEFT JOIN footystats.inter_league_map map_away ON footystats.matches_details.date_unix = map_away.date_unix
        AND footystats.matches_details.away_season_id = map_away.season_id
    LEFT JOIN solver.domestic solver_away ON solver_away.season = footystats.matches_details.away_season_id
        AND map_away.last_date_unix = solver_away.date_unix
        AND footystats.matches_details.away_id = solver_away.team
WHERE
    footystats.matches_details.status = 'complete'
    AND footystats.matches_details.home_league <> footystats.matches_details.away_league
    AND footystats.matches_details.date_unix > (SELECT
        MAX(date_unix)
    FROM
        footystats.matches_details
    WHERE
        status = 'complete'
        AND home_league <> away_league) - 31536000 * 5