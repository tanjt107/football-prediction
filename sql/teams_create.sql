CREATE TABLE IF NOT EXISTS teams(
team_id INT NOT NULL,
team_name VARCHAR(255),
team_clean_name VARCHAR(255),
country VARCHAR(255),
competition_id INT NOT NULL,
modified_on TIMESTAMP NOT NULL,
UNIQUE INDEX (team_id, competition_id)
) 