import os
import json

from termcolor import colored

from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session, g
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# import text so we can use fstrings in our filter/sort queries
from sqlalchemy.sql import text

from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import (UserAddForm, LoginForm, UserEditForm,
                   UserDeleteForm, MovieEditForm)
from models import db, connect_db, User, Movie, UserMovie
from services import movie_search, movie_search_by_id

from utils import DebugUtilities

app = Flask(__name__)
cors = CORS(app)

# Get DB_URI from env variable (useful for production/testing) or,
# if not set there, use development local db.

if os.environ.get('FLASK_ENV') == "development":
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL', 'postgresql:///movie_ledger'))
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('SUPABASE_DATABASE_URL'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")


###############################################################################
# debugging

app_config_dict = {}

# dict(app.config).items() returns a list of tuples
# we iterate through the tuples, check the val and add it to our
# app_config_dict if the val can be serialized by json.dumps()

for key, val in dict(app.config).items():
    if type(val) is str or type(val) is bool:
        # print(key, val, type(val))
        app_config_dict[key] = val

app_config = json.dumps(app_config_dict, indent=4, sort_keys=True)
os_environ = json.dumps(dict(os.environ), indent=4, sort_keys=True)

print("\033[1m\033[96m=> app.config: \033[0m",
      colored(app_config, "white"))
print("\033[1m\033[96m=> os.environ: \033[0m",
      colored(os_environ, "white"))


###############################################################################

connect_db(app)

# toolbar = DebugToolbarExtension(app)

# this is the key we use to store the user id in the session
CURR_USER_KEY = "curr_user"


###############################################################################
# do this before every request!

@app.before_request
def add_user_to_g():
    """If we're logged in (session[CURR_USER_KEY] is sent from the client),
    add curr user to Flask global."""

    # g.user will contain movies as well
    # we set up the relationship in our model
    if CURR_USER_KEY in session:
        # this check addresses an edge case where the user was deleted
        # from the database but was still in a session in the browser.
        #
        # check that the user data actually exists in the db
        u = User.query.get(session[CURR_USER_KEY])

        if u:
            g.user = u

        else:
            g.user = None
            do_logout()

    else:
        g.user = None

    g.year = datetime.now().strftime("%Y")


###############################################################################
# login, signup, logout

def do_login(user):
    """Login user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to /movie-search.

    If form not valid, present form.

    If email already exists, flash message and re-present form.
    """

    if CURR_USER_KEY in session:
        return redirect("/movies")

    form = UserAddForm()

    if form.validate_on_submit():
        # send our user info to be registered
        u = User.signup(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data,
            img_url=form.img_url.data or User.img_url.default.arg
        )

        try:
            db.session.add(u)
            db.session.commit()

        except IntegrityError as exc:
            # need to find a way to figure out which error
            flash("Email already exists.", 'danger')
            return render_template('signup.html', form=form)

        do_login(u)

        # on successfull signup, template will show a welcome message
        return redirect('/movie-search')

    return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle login of user.

    Authenticate credentials and redirect to the movies page.
    """

    if CURR_USER_KEY in session:
        return redirect("/movies")

    form = LoginForm()

    if form.validate_on_submit():
        u = User.authenticate(form.email.data, form.password.data)

        if u:
            do_login(u)

            return redirect("/movies")

        flash("Invalid login credentials.", 'danger')
        return redirect('/login')

    return render_template('login.html', form=form)


@app.route('/logout', methods=["POST"])
def logout():
    """Handle logout of user."""

    if CURR_USER_KEY not in session:
        return redirect("/")

    do_logout()

    flash("You have been logged out.", "success")
    return redirect('/')


###############################################################################
# homepage

@app.route("/")
def homepage():
    """Show homepage."""

    return render_template("home.html")


###############################################################################
# user routes

@app.route("/profile", methods=["GET", "POST"])
def edit_profile():
    """Show/handle the user profile editing page.  Require auth!"""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    editForm = UserEditForm(obj=g.user)
    deleteForm = UserDeleteForm()

    if editForm.validate_on_submit():
        u = User.authenticate(g.user.email, editForm.password.data)

        if u:
            # update the user with the new data
            u.username = editForm.username.data
            u.email = editForm.email.data
            u.img_url = editForm.img_url.data

            # if user is changing passwords, hash the new pw before commiting
            if editForm.new_password.data:
                newPW = User.hash_password(editForm.new_password.data)
                u.password = newPW

            # we do not need to db.session.add() since sqlalchemy
            # already has the user in memory
            try:
                db.session.commit()

            except IntegrityError as exc:
                flash("Email already exists.", "danger")
                return redirect("/profile")

            flash("Your profile has been updated.", "success")
            return redirect("/profile")

        flash("Current password incorrect.", "danger")
        return redirect("/profile")

    return render_template("profile.html", editForm=editForm, deleteForm=deleteForm, user=g.user)


@app.route('/profile/delete', methods=["POST"])
def delete_profile():
    """Delete the current user's information.  Require auth!"""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    deleteForm = UserDeleteForm()

    if deleteForm.validate_on_submit():
        u = User.authenticate(g.user.email, deleteForm.password.data)

        if u:
            try:
                db.session.delete(u)
                db.session.commit()

            except:
                flash("There was an error, please refresh and try again.", "danger")
                return redirect("/profile")

            do_logout()

            flash("Your profile has been deleted.", "danger")
            return redirect("/")

        flash("Incorrect password. Your profile has not been deleted.", "danger")
        return redirect("/profile")

    return redirect("/profile")


###############################################################################
# movie routes

@app.route('/movies', methods=["GET"])
def show_users_movies():
    """Show all user's movies, including filters or sort if selected."""

    # we can access movies from the user object, which already exists
    # on the flask global "g", using the relationship we setup on the
    # user model. we can also acccess details from UserMovie and Movie
    #
    # user_movie.favorite, user_movie.date_added, user_movie.platform, etc.
    # user_movie.movie_details.title, user_movie.movie_details.imdb_img

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    ###########################################################################
    # initialize

    # initalize the display params to pass to our template
    #   display_params={ "filters": [list of filters], "sort": { "sort_term": "sort_term, "sort_order": "sort_order"}}
    display_params = {}
    sort_str = None
    movies = []

    ###########################################################################
    # filter check

    # if there's a filter add to the filter flags list arg
    if request.args.get('filter'):

        display_params["filters"] = ['favorites']
        sort_str = "Showing favorites only.  "

        for m in g.user.user_movies_details:
            if m.favorite:
                movies.append(m)
    else:
        movies = g.user.user_movies_details

        sort_str = ""

    ###########################################################################
    # sort check

    # if there's a sort option selected, add to the sort string
    if request.args.get('sort') and request.args.get('order'):

        display_params["sort"] = {}
        sort_str = sort_str + "Sorting by "

        # append to the sort_str based on the query string arg
        # and add to the display_params
        if request.args['sort'] == "title":
            sort_str = sort_str + "Title"
            display_params["sort"]["sort_term"] = 'title'

            def key(x): return x.movie_details.title

        elif request.args['sort'] == "release_year":
            sort_str = sort_str + " Release Year"
            display_params["sort"]["sort_term"] = 'release_year'

            def key(x): return x.movie_details.release_year

        elif request.args['sort'] == "date_added":
            sort_str = sort_str + "Date Added"
            display_params["sort"]["sort_term"] = 'date_added'

            def key(x): return x.date_added

        elif request.args['sort'] == "date_viewed":
            sort_str = sort_str + "Date Viewed"
            display_params["sort"]["sort_term"] = 'date_viewed'

            # we add the if/else statement since data might be null
            def key(x): return x.date_viewed if x.date_viewed else ""

        # ascending/descending order
        if request.args['order'] == "asc":
            sort_str = sort_str + " (ascending)"
            display_params["sort"]["sort_order"] = 'ascending'

            reverse = False

        elif request.args['order'] == "desc":
            sort_str = sort_str + " (descending)"
            display_params["sort"]["sort_order"] = 'descending'

            reverse = True

        # our final sort function based on the given vars
        movies.sort(key=key, reverse=reverse)

    # format date to human readable (date_added and date_viewed)
    for m in movies:
        m.date_added = m.date_added.strftime("%m.%d.%y")
        m.date_viewed = m.date_viewed.strftime(
            "%m.%d.%y") if m.date_viewed else None

    # add the movie add edit form to our modal
    # we will populate field values with javascript
    movie_add_edit_form = MovieEditForm()

    return render_template('movies.html', user=g.user, movies=movies, display_params=display_params, sort_str=sort_str, form=movie_add_edit_form)


@app.route('/movies', methods=["POST"])
def add_user_movie():
    """Add a user movie through form data."""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    form = MovieEditForm()

    ###########################################################################
    # add movie to user's list by form (from movie detail page)
    if form.validate_on_submit():

        movie_id = form.imdb_id.data

        movie_in_movies_table = Movie.query.get(movie_id)

        if movie_in_movies_table:
            # we only need to add a new UserMovie entry

            # date_added will take the default value from our UserMovie model
            # date_viewed will be set to None <class 'NoneType'> if user doesn't
            #   add a date so our db entry will be empty
            # platform needs to be explicitly set to None <class 'NoneType'>
            #   if no data is sent because wtforms sends us an empty string
            #   for value="" (different than date_viewed) and sqlalchemy will
            #   store that empty string in our db.
            um = UserMovie(movie_id=movie_id,
                           user_id=g.user.id,
                           favorite=False if not form.favorite.data else form.favorite.data,
                           platform=None if not form.platform.data else form.platform.data,
                           date_viewed=form.date_viewed.data,
                           )

            try:
                db.session.add(um)
                db.session.commit()

            except IntegrityError as exc:
                flash("Movie is already in your list.", "danger")
                return redirect("/movies")

            flash("Movie added to your list.", "success")

        else:
            # we need to add a new Movie entry and UserMovie entry
            m = Movie(imdb_id=movie_id,
                      title=form.title.data,
                      release_year=form.release_year.data[0:4],
                      imdb_img=form.imdb_img.data)

            try:
                g.user.movies.append(m)
                db.session.add(g.user)
                db.session.commit()

            except IntegrityError as exc:
                flash("Movie is already in your list.", "danger")
                return redirect("/movies")

            flash("Movie added to your list.", "success")

        return redirect("/movies")

    flash("Movie not added to your list. Please try again", "danger")
    return redirect(request.referrer)


@app.route("/movies/<movie_id>", methods=["POST"])
def edit_user_movie(movie_id):
    """Edit a user's movie."""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    form = MovieEditForm()

    ###########################################################################
    # add movie to user's list by form (from movie detail page)
    if form.validate_on_submit():

        # query the existing UserMovie entry
        um = UserMovie.query.get((session[CURR_USER_KEY], movie_id))

        # update values.  there will only be 2 that we can modify
        # favorites value is edited by ajax
        um.platform = None if not form.platform.data else form.platform.data
        um.date_viewed = form.date_viewed.data

        try:
            db.session.commit()

        except:
            flash("There was an error adding the movie to your list.", "danger")
            return redirect("/movies")

        flash("Movie details updated.", "success")
        return redirect("/movies")

    flash("Movie details not updated. Please try again", "danger")
    return redirect(request.referrer)

    ###########################################################################
    # GET request functionality below (removed for now)

    # # get the movie data from the api.  data returned will be
    # # a dictionary containing a key title "Response".
    # # If "True", a movie was found.  if "False", no movie found.
    # try:
    #     movie = movie_search_by_id(movie_id)

    # except:
    #     flash("Sorry, There was an error processing your request.", "danger")
    #     return redirect("/movie-search")

    # # if the movie id doesn't exist, redirect to search and flash a message
    # if movie["Response"] == "False":
    #     flash("Sorry, we can't find the movie you are looking for.", "danger")
    #     return redirect("/movie-search")

    # # update our wtform data on the front end to match the movie
    # # details of the movie we are viewing, so when we submit the
    # # MovieEditForm our values will be correct
    # form.title.data = movie['Title']
    # form.release_year.data = movie['Year']
    # form.imdb_img.data = movie['Poster']

    # # check if this movie is already in our current user's list
    # # by querying the UserMovies table
    # # .first() returns the movie, or no movies
    # movie_in_users_list = UserMovie.query.filter_by(
    #     user_id=g.user.id, movie_id=movie['imdbID']).first()

    # # if the movie is already in the current user's list we can pre-populate
    # # the data that is exclusive to our db into our form as well.
    # # the date_added hidden field is included in wtforms as a flag
    # # to pass to our post route and used to determine if the post is a
    # # new save, or an update.
    # if movie_in_users_list:
    #     form.favorite.data = movie_in_users_list.favorite
    #     form.platform.data = movie_in_users_list.platform
    #     form.date_viewed.data = movie_in_users_list.date_viewed
    #     form.date_added.data = movie_in_users_list.date_added

    # return render_template("movie-detail.html", form=form, movie=movie, movie_in_users_list=movie_in_users_list)


@app.route("/movies/<movie_id>/delete")
def delete_user_movie(movie_id):

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    um = UserMovie.query.get((session[CURR_USER_KEY], movie_id))

    if um:
        try:
            db.session.delete(um)
            db.session.commit()

        except:
            flash(
                "Sorry, There was an error removing the movie from your list.  Please try again.", "danger")
            return redirect(f"/movie/{movie_id}")

        flash("Movie removed from your list.", "success")
        return redirect("/movies")

    else:
        flash('Movie not found.', 'error')
        return redirect("/movies")


###############################################################################
# movie search route

# search movies from the omdb database.  must be logged in!
@app.route("/movie-search")
def search_movies():
    """Get all the movies based on a search term from form data"""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    # add the movie add edit form to our modal
    # we will populate field values with javascript
    movie_add_edit_form = MovieEditForm()

    # if a search term is provided, process the search
    if request.args.get('term'):

        search_term = request.args['term']

        # get our requested page from the query string.
        #
        # if there is no page in the
        # query string, default to page 1, and pass to our api req.
        #
        # page needs to contain an int so that we can check:
        # if page > 1 then render our prev page when necessary.
        page = int(request.args['page']) if request.args.get('page') else 1

        # make the call to our external api
        #
        # results will be a python dictionary (from services.py)
        results_curr = movie_search(search_term, page=page)

        # if we get any search results in our CURRENT api call,
        # run a check to see if any of the returned results
        # are already in our list database
        #
        # if so, set a new attribute "ml_inList" on our movie
        #
        # we can use this attribute to determine if we show an
        # "Add to My List"  button or a note "Already in My List"
        if results_curr['Response'] == "True":

            user_movies = {
                movie.movie_id: movie.favorite for movie in g.user.user_movies_details}

            for movie in results_curr['Search']:
                if movie['imdbID'] in list(user_movies.keys()):
                    movie["ml_inList"] = True

                    # get the tuple from user_movies that matches our movie id, and check the favorite val
                    movie["favorite"] = user_movies[movie['imdbID']]

        # make the call to our external api for the NEXT page
        # and pass the "Response" returned to our template.
        # based on the val of "Response" we can render a next_page link or not
        results_next = movie_search(search_term, page=page+1)

        next_page = results_next['Response']

        # render our template and pass the results of the api request
        # along with the search term (so we can create our search note)
        #
        # we'll handle the rendering of our data in our template
        return render_template("movie-search.html", results=results_curr, search_term=search_term, page=page, next_page=next_page, form=movie_add_edit_form)

    # no search term submitted, so we just render our starting search page
    return render_template("movie-search.html", user=g.user, form=movie_add_edit_form)


###############################################################################
# internal api routes for use with ajax functions

# internal api route - add a movie to user's list ajax
@app.route("/api/movies", methods=["POST"])
def add_movie():
    """Add a movie to the user's list."""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    data = request.json
    data["user_id"] = session[CURR_USER_KEY]
    data["favorite"] = request.json.get("favorite") or False

    return UserMovie.add_movie_to_list(data=data)


# internal api route - get movie details (accessed when opening details modal)
@app.route('/api/movies/<movie_id>', methods=["GET"])
def get_movie_details(movie_id):
    """Get movie details for a single movie"""

    # get the movie data from the api.  data returned will be
    # a dictionary containing a key title "Response".
    # If "True", a movie was found.  if "False", no movie found.
    try:
        movie = movie_search_by_id(movie_id)

    except:
        resp = jsonify(
            {"message": "There was an error.  Please try again."})
        return (resp, 400)

    if movie["Response"] == "False":
        resp = jsonify(
            {"message": "Sorry, we can't find the movie you are looking for."})
        return (resp, 404)

    # .first() returns the movie, or no movies
    movie_in_users_list = UserMovie.query.filter_by(
        user_id=g.user.id, movie_id=movie['imdbID']).first()

    # if the movie is already in the current user's list we can pre-populate
    # the data that is exclusive to our db into our response as well.
    # the date_added hidden field is included in wtforms as a flag
    # to pass to our post route and used to determine if the post is a
    # new save, or an update.
    if movie_in_users_list:
        movie["in_list"] = True
        movie["favorite"] = movie_in_users_list.favorite
        movie["platform"] = movie_in_users_list.platform
        movie["date_viewed"] = movie_in_users_list.date_viewed
        movie["date_added"] = movie_in_users_list.date_added

    resp = jsonify({"movie": movie})
    return (resp, 200)


# internal api route - update favorite ajax (favorite button)
@app.route('/api/movies/<movie_id>', methods=["PATCH"])
def add_remove_favorite(movie_id):
    """Add or remove a movie as a favorite.  If not in UserMovie list yet, add it."""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    um = UserMovie.query.filter_by(
        user_id=session[CURR_USER_KEY], movie_id=movie_id).first()

    if um:
        um.favorite = not um.favorite

        try:
            db.session.commit()

        except:
            resp = jsonify(
                {"message": "There was an error.  Please try again."})
            return (resp, 400)

        # send back our boolean value for "favorite" so we can
        # keep the front end in sync with our database data
        resp = jsonify(
            {"message": "success", "movieDetails": UserMovie.serialize(um)})
        return (resp, 200)

    # if no movie exists in the user list, add the movie as a favorite
    else:
        data = request.json
        data["user_id"] = session[CURR_USER_KEY]
        data["favorite"] = True

        return UserMovie.add_movie_to_list(data=data)


# internal api route - delete movie from user list ajax (my list checkmark button)
@app.route("/api/movies/<movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    """Delete a movie from our db."""

    if not CURR_USER_KEY in session:
        flash("Please login.", "danger")
        return redirect("/login")

    um = UserMovie.query.get((session[CURR_USER_KEY], movie_id))

    if um:

        # below we delete the item in sqlalchemy, but we need db.session.commit()
        try:
            db.session.delete(um)
            db.session.commit()

        except:
            resp = jsonify(
                {"message": "There was an error.  Please try again."})
            return (resp, 400)

        resp = jsonify({"message": "success"})
        return (resp, 200)

    else:
        resp = jsonify({"message": "movie not found"})
        return (resp, 404)


###############################################################################
# movie routes
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e)
