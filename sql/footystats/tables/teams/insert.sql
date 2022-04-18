INSERT INTO teams
SET
    team_id = %(id)s,
    team_name = %(name)s,
    team_clean_name = %(cleanName)s,
    country = %(country)s,
    competition_id = %(competition_id)s
ON DUPLICATE KEY UPDATE
    team_name = %(name)s,
    team_clean_name = %(cleanName)s,
    country = %(country)s