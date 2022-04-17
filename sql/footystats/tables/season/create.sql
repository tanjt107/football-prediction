CREATE TABLE IF NOT EXISTS seasons(
id INT PRIMARY KEY NOT NULL,
name VARCHAR(255) NOT NULL,
country VARCHAR(255) NOT NULL,
status VARCHAR(255),
format VARCHAR(255),
division INT,
starting_year INT,
ending_year INT,
club_num INT,
season VARCHAR(9),
total_matches INT,
matches_completed INT,
canceled_matches_num INT,
game_week INT,
total_game_week INT,
league_name VARCHAR(255),
modified_on TIMESTAMP NOT NULL
); 