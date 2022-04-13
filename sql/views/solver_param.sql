SELECT DISTINCT
    t.season_id,
    t.last_date_unix
FROM
    (SELECT 
        tt.date_unix,
        tt.season_id,
        MAX(matches.date_unix) AS last_date_unix
    FROM
        (SELECT 
        inter_league_matches.date_unix,
        inter_league_matches.home_season_id AS season_id
    FROM
        inter_league_matches UNION SELECT 
        inter_league_matches.date_unix,
        inter_league_matches.away_season_id AS season_id
    FROM
        inter_league_matches) tt
    LEFT JOIN matches ON tt.season_id = matches.competition_id
        AND matches.date_unix < tt.date_unix
    GROUP BY tt.date_unix , tt.season_id) t
WHERE
    t.last_date_unix IS NOT NULL
ORDER BY t.last_date_unix