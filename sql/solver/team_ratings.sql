WITH latest AS (
    SELECT name, MAX(starting_year) AS starting_year, MAX(ending_year) AS ending_year
    FROM season
    WHERE format = 'Domestic League'
    GROUP BY name
), season_ids AS (
    SELECT id
    FROM season
    JOIN latest
    ON season.name = latest.name AND season.starting_year = latest.starting_year AND season.ending_year = latest.ending_year
), team_ids AS (
    SELECT id
    FROM teams
    WHERE competition_id IN season_ids
), average AS (
    SELECT AVG(offence) AS avg_off, AVG(defence) AS avg_def
    FROM solver_teams
    WHERE team IN team_ids
)

SELECT Team, offence - average.avg_off, defence - average.avg_def
FROM solver_teams, average
WHERE team IN team_ids;