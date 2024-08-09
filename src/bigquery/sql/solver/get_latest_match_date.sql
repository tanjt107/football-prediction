SELECT
    MAX(date_unix) AS max_date_unix
FROM ${project_id}.footystats.matches
JOIN `${project_id}.master.teams` home_teams ON matches.homeID = home_teams.footystats_id
JOIN `${project_id}.master.teams` away_teams ON matches.awayID = away_teams.footystats_id
JOIN ${project_id}.master.leagues ON matches._NAME = leagues.footystats_name
WHERE leagues.type = _type
    AND status = 'complete'
    AND date_unix < UNIX_SECONDS(CURRENT_TIMESTAMP())
    AND (EXISTS (
        SELECT 1
        FROM ${project_id}.simulation.params
        WHERE home_teams.league_name = params.league
            OR away_teams.league_name = params.league
            OR leagues.footystats_name = params.league )
        OR leagues.is_manual)