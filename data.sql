-- in terminal: 
--   psql < data.sql
--   psql [database_name]

DROP DATABASE IF EXISTS movie_ledger;
CREATE DATABASE movie_ledger;

DROP DATABASE IF EXISTS movie_ledger_test;
CREATE DATABASE movie_ledger_test;

-- for supabase
-- \c postgres

-- for local or other
\c movie_ledger

DROP TABLE user_movies;
DROP TABLE movies;
DROP TABLE users;


CREATE TABLE users
(
  id SERIAL PRIMARY KEY, 
  username TEXT NOT NULL, 
  email TEXT UNIQUE NOT NULL, 
  password TEXT NOT NULL, 
  img_url TEXT NOT NULL
);

CREATE TABLE movies
(
  imdb_id TEXT PRIMARY KEY, 
  title TEXT NOT NULL, 
  release_year INT NOT NULL, 
  imdb_img TEXT NOT NULL
);

CREATE TABLE users_movies
(
  user_id INT REFERENCES users (id) ON DELETE CASCADE, 
  movie_id TEXT REFERENCES movies (imdb_id), 
  PRIMARY KEY (user_id, movie_id),
  date_added TIMESTAMP NOT NULL,
  platform TEXT,
  date_viewed DATE,
  favorite BOOLEAN NOT NULL DEFAULT false
);
