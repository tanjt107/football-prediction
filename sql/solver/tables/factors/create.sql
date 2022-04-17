CREATE TABLE IF NOT EXISTS solver.factors(
	season INT,
	avg_goal FLOAT,
    home_adv FLOAT,
    modified_on TIMESTAMP,
    UNIQUE INDEX (season)
)