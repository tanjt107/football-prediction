SELECT
  country,
  name,
  ARRAY_AGG(STRUCT(id,season) ORDER BY ending_year DESC, starting_year DESC LIMIT 1)[OFFSET(0)].*
FROM
  `footystats.season`
WHERE
  division > 0
  AND format = 'Domestic League'
GROUP BY
  country,
  name