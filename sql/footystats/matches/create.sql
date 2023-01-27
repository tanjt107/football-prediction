CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    home_id INTEGER,
    away_id INTEGER,
    status TEXT,
    home_goal_count INTEGER,
    away_goal_count INTEGER,
    date_unix INTEGER,
    competition_id INTEGER,
    no_home_away INTEGER,
    home_adj REAL,
    away_adj REAL
);