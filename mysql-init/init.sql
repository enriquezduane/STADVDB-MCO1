CREATE DATABASE IF NOT EXISTS games_data_warehouse;

USE games_data_warehouse;

CREATE TABLE test (
    test_id INT NOT NULL AUTO_INCREMENT,
    test_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (test_id)
);
