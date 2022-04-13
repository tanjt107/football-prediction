REPLACE INTO teams
(team_id,
team_name,
team_clean_name,
country,
competition_id,
modified_on)
VALUES
(%s,
%s,
%s,
%s,
%s,
%s) 