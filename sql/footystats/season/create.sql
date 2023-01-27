CREATE TABLE IF NOT EXISTS season (
    id INTEGER PRIMARY KEY,
    name TEXT,
    country TEXT,
    format TEXT,
    division INTEGER,
    starting_year INTEGER,
    ending_year INTEGER
);