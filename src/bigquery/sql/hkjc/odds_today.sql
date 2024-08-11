SELECT * EXCEPT(_TIMESTAMP)
FROM `hkjc.odds_clean`
WHERE _TIMESTAMP = (
    SELECT MAX(_TIMESTAMP)
    FROM `hkjc.odds`
  )
  AND tournament NOT IN ('E2Q', 'CLB', 'CUP')
  AND home_name NOT LIKE '%奧足'
  AND home_name NOT LIKE '%U2_'
  AND home_name NOT LIKE '%女足'