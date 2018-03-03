CREATE DATABASE blog;

USE blog;

CREATE TABLE users(
    id INT(11) auto_increment NOT NULL PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100), 
    email VARCHAR(100),
    username VARCHAR(30),
    password VARCHAR(100),
    register_date TIMESTAMP default current_timestamp);

CREATE TABLE articles(
    id INT(11) auto_increment PRIMARY KEY,
    title VARCHAR(300), 
    author VARCHAR(100),
    body TEXT, 
    create_date TIMESTAMP default current_timestamp);
