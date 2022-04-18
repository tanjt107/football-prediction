CREATE TABLE IF NOT EXISTS solver.factors(
	season INT,
	avg_goal FLOAT,
    home_adv FLOAT,
    modified_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX (season)
)