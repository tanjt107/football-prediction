CREATE TABLE IF NOT EXISTS teams(
    team_id INT NOT NULL,
    team_name VARCHAR(255),
    team_clean_name VARCHAR(255),
    country VARCHAR(255),
    competition_id INT NOT NULL,
    modified_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX (team_id, competition_id)
) 