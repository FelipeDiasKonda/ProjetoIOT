CREATE DATABASE IF NOT EXISTS weather_data;
USE weather_data;

CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rain_level FLOAT NULL,
    average_wind_speed FLOAT NULL,
    wind_direction FLOAT NULL,
    humidity FLOAT NULL,
    uv_index FLOAT NULL,
    solar_radiation FLOAT NULL,
    temperature FLOAT NULL,
    timestamp BIGINT NOT NULL,
    UNIQUE KEY unique_timestamp (timestamp)
);