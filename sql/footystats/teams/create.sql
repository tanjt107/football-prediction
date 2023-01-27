CREATE TABLE IF NOT EXISTS teams (
    id INTEGER,
    name TEXT,
    country TEXT,
    competition_id INTEGER,
    PRIMARY KEY (id, competition_id)
);