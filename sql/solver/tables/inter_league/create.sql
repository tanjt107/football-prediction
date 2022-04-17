CREATE TABLE IF NOT EXISTS solver.inter_league (
  league VARCHAR(255) NOT NULL,
  strength FLOAT,
  modified_on TIMESTAMP,
  UNIQUE INDEX (league)
)