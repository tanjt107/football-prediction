WITH _odds AS (
  SELECT odds.id,
    MAX(CASE WHEN pool.oddsType = "HAD" AND combination.str = "H" THEN combination.currentOdds END) AS HAD_H,
    MAX(CASE WHEN pool.oddsType = "HAD" AND combination.str = "D" THEN combination.currentOdds END) AS HAD_D,
    MAX(CASE WHEN pool.oddsType = "HAD" AND combination.str = "A" THEN combination.currentOdds END) AS HAD_A,
    MAX(CASE WHEN pool.oddsType = "HDC" AND combination.str = "H" THEN combination.currentOdds END) AS HDC_H,
    MAX(CASE WHEN pool.oddsType = "HDC" AND combination.str = "A" THEN combination.currentOdds END) AS HDC_A,
    MAX(CASE WHEN pool.oddsType = "HDC" THEN line.condition END) AS handicap,
    _TIMESTAMP
  FROM hkjc.odds,
    UNNEST(foPools) AS pool,
    UNNEST(pool.lines) AS line,
    UNNEST(line.combinations) AS combination
  WHERE odds.status = 'PREEVENT'
    AND line.status = 'AVAILABLE'
  GROUP BY odds.id, _TIMESTAMP
)

SELECT
  id,
  kickOffTime AS kick_off_time,
  sequence,
  homeTeam.id AS home_id,
  homeTeam.name_ch AS home_name,
  homeTeam.name_en AS home_name_en,
  awayTeam.id AS away_id,
  awayTeam.name_ch AS away_name,
  awayTeam.name_en AS away_name_en,
  tournament.code AS tournament_id,
  tournament.name_ch AS tournament_name,
  CAST(venue.code IS NULL AS INT64) AS home_adv,
  HAD_H,
  HAD_D,
  HAD_A,
  HDC_H,
  HDC_A,
  handicap,
  updateAt AS update_at,
  _TIMESTAMP
FROM hkjc.odds
JOIN _odds USING (id, _TIMESTAMP)