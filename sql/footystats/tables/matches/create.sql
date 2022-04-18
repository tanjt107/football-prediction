CREATE TABLE IF NOT EXISTS matches(
    id INT NOT NULL,
    date_unix INT,
    competition_id INT NOT NULL,
    home_id INT NOT NULL,
    away_id INT NOT NULL,
    status VARCHAR(255),
    home_goal_count INT,
    away_goal_count INT,
    is_home_away BOOLEAN,
    goal_timings_recorded BOOLEAN,
    home_goals VARCHAR(255),
    away_goals VARCHAR(255),
    is_xg BOOLEAN,
    team_a_xg FLOAT,
    team_b_xg FLOAT,
    home_adj FLOAT,
    away_adj FLOAT,
    home_avg FLOAT,
    away_avg FLOAT,
    modified_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX(id)
) 