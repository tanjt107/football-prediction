CREATE TABLE IF NOT EXISTS solver.domestic (
season INT,
date_unix INT,
team INT,
offence FLOAT,
defence FLOAT,
modified_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
UNIQUE INDEX (season, date_unix, team)
)