INSERT INTO season (id, name, country, division) 
VALUES (:id, :name, :country, :division)
ON CONFLICT (id) 
DO UPDATE SET name = excluded.name, country = excluded.country, division = excluded.division;