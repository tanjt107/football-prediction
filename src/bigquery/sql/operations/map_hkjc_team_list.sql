SELECT
  DISTINCT fs_teams.id AS footystats_id,
  hkjc_teams.id AS hkjc_id,
  hkjc_teams.name_en,
  fs_teams.name,
  fs_teams.cleanName,
  fs_teams.english_name,
  hkjc_teams.name_ch,
  fs_teams.country
FROM hkjc.teams hkjc_teams
JOIN footystats.teams fs_teams ON REPLACE(hkjc_teams.name_en, 'Utd', 'United') =  functions.accent_to_latin(fs_teams.cleanName)
  OR REPLACE(hkjc_teams.name_en, 'Utd', 'United') = functions.accent_to_latin(fs_teams.english_name)
WHERE
  NOT EXISTS (
    SELECT 1
    FROM manual.teams manual_teams
    WHERE hkjc_teams.id = manual_teams.hkjc_id
    )
  AND NOT EXISTS (
    SELECT 1
    FROM manual.teams manual_teams
    WHERE fs_teams.id = manual_teams.footystats_id)