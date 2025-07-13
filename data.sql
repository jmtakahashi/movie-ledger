-- in terminal: 
--   psql < data.sql
--   psql [database_name]

-- DROP DATABASE IF EXISTS movie_ledger;

-- CREATE DATABASE movie_ledger;

-- \c movie_ledger

\c postgres

-- DROP TABLE user_movies;
-- DROP TABLE users;
-- DROP TABLE movies;


-- CREATE TABLE users
-- (
--   id SERIAL PRIMARY KEY, 
--   username TEXT UNIQUE NOT NULL, 
--   email TEXT NOT NULL, 
--   password TEXT NOT NULL, 
--   img_url TEXT
-- );

-- CREATE TABLE movies
-- (
--   imdb_id TEXT PRIMARY KEY, 
--   title TEXT NOT NULL, 
--   year DATE NOT NULL, 
--   imdb_img TEXT NOT NULL
-- );

CREATE TABLE users_movies
(
  user_id INT REFERENCES users (id), 
  movie_id TEXT REFERENCES movies (imdb_id), 
  PRIMARY KEY (user_id, movie_id),
  date_added TIMESTAMP NOT NULL,
  platform TEXT,
  date_viewed DATE,
  favorite BOOLEAN NOT NULL DEFAULT false
);
