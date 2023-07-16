# https://jt-flask-movie-ledger.herokuapp.com/

Site Title: The Movie Ledger

Description: A place to keep to a record of all the movies you've watched, regardless of platform. Never rack your brain again, trying to remember "What was that movie or series, again?!"

Features

- Profile: create an anonymous profile. With just a username, password and email address (necessary for password resets). No sensitive information required. Edit your profile at anytime!

- Profile export: export your list of movies at anytime!

- Profile delete: delete your profile at any time, all data is wiped from our database.

- Movie/Series Search: using the the OMDB api, browse through thousands of movies or series to find the title you are looking for.

- Store: store the movie or series title in your list for quick browsing.

- Movie/Series Detail: access details of the movie or series you have stored in your list!

- Platform Viewed: optionally, add the platform that viewed the movie/series on. Especially good if the series/movie was an "original"!

- Favorite: Add your movie as a favorite movie, so that it will appear at the top of your list!

- Movie Sort: sort your viewed movies by title, year, or date added to your list.

User Flow:

1. User visits the home page. They can login, or signup.
2. User signs up for our service and is directed to the movie search page.
   - user is greeted with a note
3. User searches for a movie using the title, or actor.
   - an api call is made to the OMDB api
   - user can browse through the search results page by page
   - each movie/series displayed has an ajax "Add to My List" button
   - if the movie/series is already in the users list, an "Movie in My List" note is displayed with a link to "My List"
   - User can add the movie from this page (ajax)
4. User clicks on a result and the details of that movie are displayed on a new page.
   - this will be another API call to get the movie details by ID
5. User can add the movie, edit the movie if the movie is aready in their list, or go back to view the results of the search.
   - this add function will be a form submission
   - if a user adds this movie, they will be redirected to their My List page
   - the go back function should NOT refresh the previous page, but keep the results of the search for that page
6. "My List" page contains a list of the movies the the user has viewed. Here, a users can:
   - use the filter to view ONLY favorites
   - users can sort the movies based on Title, Year, Date Added, or Date Viewed
7. Movie Sort function (working)

Technology Stack:
PostgreSQL
Flask (backend)
Html, css, javascript (front end)

Whn importing local db to newly created db:

$ pg_dump -O car_rental | psql [render db psql command]

When deploying:

install unicorn
(venv) $ pip install gunicorn
export deps
pip freeze > requirements.txt

start command: gunicorn app:app

add environmental vars:
DATABASE_URL: URL from ElephantSQL (change postgres: → postgresql:)SECRET_KEY: anything you want (to be secure: long and random)PYTHON_VERSION: 3.X.X - whichever version you are using

Tables

Users (
id (PrimaryKey, Autoincrement),
username (Unique),
password
email
img_url
)

Movies (
imdb_id (PrimaryKey),
user_id (ForeignKey (Users.id), PrimaryKey),
year,
poster
)

issue with signup on flask app!

- can get errors in the console, but need to figure out how to print errors to the user correctly! - maybe we don't have to, since errors on the front end will be detected by the forms(?)

Todo:
add loading icons/screens
