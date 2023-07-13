
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


Problem: when I tried implementing the query string route the AJAX toggle favorites function resulted in removing all favorites from the movie list correct, BUT when refreshing the page, will show the "Movies found" and a Search Button.  We don't need the search button when we refresh the page for favorites.  We could code this into our html template using jinja.  Or we could write a whole different route...with a different template, but this would require us to duplicate a template.
- we should try staying on this route and rewriting the jinja (finished)

/movies
Added a "filters" flag to pass to our template so that we can prefill the Sort & Filter Form with the current Sort and Filter values on initial page load.  This is just a visual indicator, along with our notification, to help the user experience.
- need to figure our the default sorting when a user first loads the page!


/movie-search (api call):
whenever we make an api call, we should request the current requests, as well as the next page so we can tell if we need a "next page" link.  if the results contain a "False" response, we can NOT show the "next page" link.

if we make enter a page var directly in the url and there are no results, then we should let the user know that there are no results for the current page! we should also change the "Search results for..." to NOT include a page.

since we get the api results for the current page, as well as the next page, we should try to use the results from the next_page as well!, we shouldn't have to make another api call if we already have the results for the next page! THE PROBLEM is how to persist the results_next data and use it on our next page call.  we can use session for this!!!! LATER functionality!
