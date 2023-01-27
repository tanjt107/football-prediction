SELECT
    m.id,
    (CASE
        WHEN s.division = -1 THEN s.country
        ELSE s.country || s.division
    END) AS league_name,
    home_id,
    away_id,
    (CASE 
        WHEN ht.country = at.country THEN (31536000.0 * :cut_off_year - :max_time + date_unix) / 31536000 * :cut_off_year
        ELSE (31536000.0 * :inter_league_cut_off_year - :max_time + date_unix) / (31536000 * :inter_league_cut_off_year)
     END) AS recent,
    no_home_away,
    home_adj,
    away_adj
FROM matches m
JOIN season s ON m.competition_id = s.id
JOIN teams ht ON m.home_id = ht.id AND m.competition_id = ht.competition_id
JOIN teams at ON m.away_id = at.id AND m.competition_id = at.competition_id
WHERE m.status = 'complete' AND recent > 0;