CREATE DATABASE IF NOT EXISTS ai_conversation;

USE ai_conversation;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    profile_language VARCHAR(50),
    profile_level VARCHAR(50),
    profile_purpose VARCHAR(100),
    profile_minutes_per_day INT
);
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_message VARCHAR(50),
    assistance_response VARCHAR(50)    
)