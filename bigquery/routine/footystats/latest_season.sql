SELECT
  country,
  name,
  ARRAY_AGG(STRUCT(id,season) ORDER BY ending_year DESC, starting_year DESC LIMIT 1)[OFFSET(0)].*
FROM
  `footystats.season`
WHERE
  division > 0
  AND format = 'Domestic League'
  AND country <> 'International' OR name IN (SELECT name FROM `mapping.intl_club_competitions`)
GROUP BY
  country,
  name