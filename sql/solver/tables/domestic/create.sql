CREATE TABLE IF NOT EXISTS solver.domestic (
season INT,
date_unix INT,
team INT,
offence FLOAT,
defence FLOAT,
modified_on TIMESTAMP,
UNIQUE INDEX (season, date_unix, team)
)