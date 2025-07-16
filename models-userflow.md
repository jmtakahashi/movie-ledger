Models
User
Register
Signup
Authenticate
Add User
Update user
Add movie
Delete Movie
Update Movie

Views
Home
Signup
Login
User Profile
Movie Search - frim here add a movie

Endpoints
User:
Register
Login
Get User - get user info and movies - get our user and then all movies associated
Update User
Delete User

Movie:
Add Movie
Delete Movie
Update viewed or not viewed

NOTE: created a search page as well as search results page so that a user doesn't have to make a new api call when going back to the search page from the movie details page

NOTE: made the "add movie button" an ajax call so that the user can

check on json errors!

Still not sure whether I should use a get request or a post request for the filter and sort options.

Problem: when I tried implementing the query string route the AJAX toggle favorites function resulted in removing all favorites from the movie list correct, BUT when refreshing the page, will show the "Movies found" and a Search Button. We don't need the search button when we refresh the page for favorites. We could code this into our html template using jinja. Or we could write a whole different route...with a different template, but this would require us to duplicate a template.

- we should try staying on this route and rewriting the jinja (finished)

/movies
Added a "filters" flag to pass to our template so that we can prefill the Sort & Filter Form with the current Sort and Filter values on initial page load. This is just a visual indicator, along with our notification, to help the user experience.

- need to figure our the default sorting when a user first loads the page!

/movie-search (api call):
whenever we make an api call, we should request the current requests, as well as the next page so we can tell if we need a "next page" link. if the results contain a "False" response, we can NOT show the "next page" link.

if we make enter a page var directly in the url and there are no results, then we should let the user know that there are no results for the current page! we should also change the "Search results for..." to NOT include a page.

since we get the api results for the current page, as well as the next page, we should try to use the results from the next_page as well!, we shouldn't have to make another api call if we already have the results for the next page! THE PROBLEM is how to persist the results_next data and use it on our next page call. we can use session for this!!!! LATER functionality!

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

## Tables

### Users (

id (PrimaryKey, Autoincrement),
username (Unique),
password
email
img_url
)

### Movies (

imdb_id (PrimaryKey),
user_id (ForeignKey (Users.id), PrimaryKey),
year,
poster
)

### issue with signup on flask app!

- can get errors in the console, but need to figure out how to print errors to the user correctly! - maybe we don't have to, since errors on the front end will be detected by the forms(?)

Todo:
add loading icons/screens

## When importing local db to newly created db:

`$ pg_dump -O car_rental | psql [render db psql command]`

## When deploying:

```
# install unicorn
$ pip install gunicorn
# export dependancies
$ pip freeze > requirements.txt
```

start command: `gunicorn app:app`

add environmental vars:
DATABASE_URL: URL from ElephantSQL (change postgres: → postgresql:)
SECRET_KEY: anything you want (to be secure: long and random)
PYTHON_VERSION: 3.X.X - whichever version you are using






https://freelancefootprints.substack.com/p/yet-another-password-reset-tutorial
Cannot get mail to send