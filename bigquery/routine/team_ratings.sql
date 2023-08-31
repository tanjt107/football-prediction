WITH
  selected_leagues AS (
  SELECT
    ARRAY<STRING>['Argentina Primera División', 'Australia A-League', 'Belgium Pro League', 'Brazil Serie A',
      'Chile Primera División', 'China China League One', 'China Chinese Super League', 'England Championship',
      'England EFL League One', 'England EFL League Two', 'England Premier League', 'Finland Veikkausliiga',
      'France Ligue 1', 'France Ligue 2', 'Germany 2. Bundesliga', 'Germany Bundesliga',
      'Hong Kong Hong Kong Premier League', 'Italy Serie A', 'Japan J1 League', 'Japan J2 League',
      'Mexico Liga MX', 'Netherlands Eerste Divisie', 'Netherlands Eredivisie', 'Norway Eliteserien',
      'Portugal Liga NOS', 'Russia Russian Premier League', 'Scotland Premiership', 'South Korea K League 1',
      'Spain La Liga', 'Spain Segunda División', 'Sweden Allsvenskan', 'USA MLS'] AS leagues
  ),
  latest_seasons AS (
  SELECT
    country,
    name,
    id
  FROM
    `footystats.latest_season`
  WHERE
    CONCAT(country, ' ', name) IN (SELECT league FROM UNNEST((SELECT leagues FROM selected_leagues)) league)
  ),
  average AS (
  SELECT
    AVG(offence) AS avg_offence,
    AVG(defence) AS avg_defence
  FROM
    `solver.teams`
  WHERE
    team IN (
    SELECT
      id
    FROM
      `footystats.teams`
    WHERE
      competition_id IN (
      SELECT
        id
      FROM
        latest_seasons)
    )
  ),
  factors AS (
  SELECT
    t.id,
    GREATEST(1.35 + st.offence - a.avg_offence, 0.2) AS offence,
    GREATEST(1.35 + st.defence - a.avg_defence, 0.2) AS defence,
    CONCAT(s.country, ' ', s.name) AS league_name
  FROM
    `solver.teams` st
  CROSS JOIN
    average a
  JOIN
    `footystats.teams` t
  ON
    t.id = st.team
  JOIN
    latest_seasons s
  ON
    s.id = t.competition_id
  )
SELECT 
  id,
  offence,
  defence,
  league_name,
  (solver.matchProbs(offence, defence, 5)[OFFSET(0)] * 3 + solver.matchProbs(offence, defence, 5)[OFFSET(1)]) / 3 * 100 AS rating
FROM 
  factors
ORDER BY rating DESC;