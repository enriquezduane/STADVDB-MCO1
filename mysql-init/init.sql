CREATE DATABASE steam_games_data_warehouse;
USE steam_games_data_warehouse;

-- Dimension Tables
CREATE TABLE dim_game (
    game_key INT AUTO_INCREMENT PRIMARY KEY,
    game_id INT,
    name VARCHAR(255),
    required_age INT,
    price DECIMAL(10, 2),
    metacritic_score INT,
    achievements INT
);

CREATE TABLE dim_platform (
    platform_key INT AUTO_INCREMENT PRIMARY KEY,
    windows BOOLEAN,
    mac BOOLEAN,
    linux BOOLEAN
);

CREATE TABLE dim_time (
    time_key INT AUTO_INCREMENT PRIMARY KEY,
    release_date DATE,
    year INT,
    month INT,
    day INT
);

CREATE TABLE dim_ownership (
    ownership_key INT AUTO_INCREMENT PRIMARY KEY,
    estimated_owners_min INT,
    estimated_owners_max INT
);

-- Fact Table
CREATE TABLE fact_game_sales (
    game_key INT,
    platform_key INT,
    time_key INT,
    ownership_key INT,
    recommendations INT,
    user_score DECIMAL(3, 1),
    positive_reviews INT,
    negative_reviews INT,
    average_playtime_forever INT,
    peak_ccu INT,
    FOREIGN KEY (game_key) REFERENCES dim_game(game_key),
    FOREIGN KEY (platform_key) REFERENCES dim_platform(platform_key),
    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (ownership_key) REFERENCES dim_ownership(ownership_key)
);
