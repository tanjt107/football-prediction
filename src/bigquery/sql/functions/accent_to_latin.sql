(WITH lookups AS (
    SELECT
      'ç,æ,œ,á,é,í,ó,ú,à,è,ì,ò,ù,ä,ë,ï,ö,ü,ÿ,â,ê,î,ô,û,å,ø,Ø,Å,Á,À,Â,Ä,È,É,Ê,Ë,Í,Î,Ï,Ì,Ò,Ó,Ô,Ö,Ú,Ù,Û,Ü,Ÿ,Ç,Æ,Œ,ñ' AS accents,
      'c,ae,oe,a,e,i,o,u,a,e,i,o,u,a,e,i,o,u,y,a,e,i,o,u,a,o,O,A,A,A,A,A,E,E,E,E,I,I,I,I,O,O,O,O,U,U,U,U,Y,C,AE,OE,n' AS latins ),

  pairs AS (
    SELECT accent,
      latin
    FROM lookups,
    UNNEST(SPLIT(accents)) AS accent WITH OFFSET AS p1,
    UNNEST(SPLIT(latins)) AS latin WITH OFFSET AS p2
    WHERE p1 = p2 )

SELECT STRING_AGG(IFNULL(latin, char), '') AS name
FROM UNNEST(SPLIT(word, '')) char
LEFT JOIN pairs
ON char = accent)