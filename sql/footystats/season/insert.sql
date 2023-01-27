INSERT INTO season (id, name, country, format, division, starting_year, ending_year) 
VALUES (:id, :name, :country, :format, :division, :starting_year, :ending_year)
ON CONFLICT (id) 
DO UPDATE SET name = excluded.name, country = excluded.country, format = excluded.format, division = excluded.division, starting_year = excluded.starting_year, ending_year = excluded.ending_year;