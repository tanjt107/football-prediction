INSERT INTO teams (id, name, country, competition_id) 
VALUES (:id, :cleanName, :country, :competition_id) 
ON CONFLICT(id, competition_id) 
DO UPDATE SET name = :cleanName, country = :country;