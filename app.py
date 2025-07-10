import os
import json

from termcolor import colored

from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session, g
from sqlalchemy.exc import IntegrityError

# import text so we can use fstrings in our filter/sort queries
from sqlalchemy.sql import text

from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import (UserAddForm, LoginForm, UserEditForm,
                   UserDeleteForm, MovieAddEditForm)
from models import db, connect_db, User, Movie, UserMovie
from services import movie_search, movie_search_by_id

app = Flask(__name__)
cors = CORS()

# Get DB_URI from env variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///movie_ledger'))
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

toolbar = DebugToolbarExtension(app)

# this is the key we use to store the user id in the session
CURR_USER_KEY = "curr_user"


###############################################################################
# do this before every request!

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    # g.user will contain movies as well
    # we set up the relationship in our model
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


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

    If username already exists, flash message and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        # send our user info to be registered
        u = User.signup(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data,
            img_url=form.img_url.data or User.img_url.default.arg
        )

        db.session.add(u)

        try:
            db.session.commit()

        except IntegrityError as exc:
            # need to find a way to figure out which error
            flash("Username already exists!", 'danger')

            return render_template('/signup.html', form=form)

        do_login(u)

        return redirect('/movie-search')

    return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle login of user.

    Authenticate credentials and redirect to the movies page.
    """

    form = LoginForm()

    if form.validate_on_submit():
        u = User.authenticate(form.username.data, form.password.data)

        if u:
            do_login(u)

            return redirect("/movies")

        flash("Invalid login credentials.", 'danger')
        return redirect('/login')

    return render_template('login.html', form=form)


@app.route('/logout', methods=["POST"])
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have been logged out successfully!", "success")
    return redirect('/')


###############################################################################
# user routes

@app.route("/profile", methods=["GET", "POST"])
def edit_profile():
    """Show/handle the user profile editing page.  Require auth!"""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    editForm = UserEditForm(obj=g.user)
    deleteForm = UserDeleteForm()

    if editForm.validate_on_submit():
        u = User.authenticate(g.user.username, editForm.password.data)

        if u:
            # update our user with the new data
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
                flash("Username already exists!", "danger")
                return redirect("/profile")

            flash("Your profile has been updated!", "success")
            return redirect("/profile")

        flash("Current password incorrect!", "danger")
        return redirect("/profile")

    return render_template("profile.html", editForm=editForm, deleteForm=deleteForm, user=g.user)


@app.route('/profile/delete', methods=["POST"])
def delete_profile():
    """Delete the current user's information.  Require auth!"""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    deleteForm = UserDeleteForm()

    if deleteForm.validate_on_submit():
        u = User.authenticate(g.user.username, deleteForm.password.data)

        if u:
            # need to use db.session.delete(obj) if we want the delete cascade to work
            db.session.delete(u)
            db.session.commit()

            do_logout()

            flash("Your profile has been deleted!", "danger")
            return redirect("/")

        flash("Incorrect password! Your profile has not been deleted!", "danger")
        return redirect("/profile")

    return redirect("/profile")


###############################################################################
# movie routes

@app.route('/movies')
def show_my_movies():
    """Show all user's movies, adding filters or sort if selected."""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    ###########################################################################
    # initialize

    # initialize our **kwargs for filter_by()
    # kwargs = {"id": g.user.id}

    # initalize our filter flags list to pass to our template
    filters = {}

    ###########################################################################
    # filter check

    # if there's a filter add to our filter flags list arg
    # so we can pass this to our template
    if request.args.get('filter'):

        filters["filters"] = ['favorites']

    ###########################################################################
    # sort check

    # if there's a sort option, begin our sort_str
    if request.args.get('sort'):

        # initialize our sort_str
        sort_str = ""

        # append to our sort_str based on the query string arg
        # and add to our filters flags list arg
        if request.args['sort'] == "title":
            sort_str = sort_str + "title"
            filters["sort"] = 'title'
        if request.args['sort'] == "year":
            sort_str = sort_str + "year"
            filters["sort"] = 'year'
        if request.args['sort'] == "date_added":
            sort_str = sort_str + "date_added"
            filters["sort"] = 'date_added'
        if request.args['sort'] == "date_viewed":
            sort_str = sort_str + "date_viewed"
            filters["sort"] = 'date_viewed'

        # if there's an order, append the order to our sort_str
        if request.args.get("order"):

            # ascending order
            if request.args['order'] == "asc":
                sort_str = sort_str + " asc"
                filters["order"] = 'ascending'

            # descending order
            if request.args['order'] == "desc":
                sort_str = sort_str + " desc"
                filters["order"] = 'descending'

        # WITH SORT TERM: make our final query using our built sort_str
        u = User.query.get(g.user.id)

        # we can access movies from our user object using
        # the relationship we setup on our user model
        movies = u.user_movie_detail

        # be sure to pass the necessary flags to the template
        return render_template('movies.html', user=g.user, movies=movies, filters=filters)

    # NO SORT TERM: our final query with filter_by(**kwargs) only
    u = User.query.get(g.user.id)

    # we can access UserMovies from our user object using
    # the relationship we setup on our user model.  each obj will also
    # have our list details, and also have access to the movie detail
    # movie.favorite, movie.date_added, movie.platform, etc.
    # movie.movie_detail.title, movie.movie_details.imdb_img
    movies = u.user_movie_detail

    return render_template('movies.html', user=g.user, movies=movies, filters=filters)


@app.route("/movie/<movie_id>", methods=["GET", "POST"])
def handle_movie(movie_id):
    """Get a single movie based on the id.
    Add the movie if a post request is coming in.
    """

    # since this route will handle both our add function and
    # edit function, we need to pre-populate the fields with
    # both api information, as well as db information (if the
    # movie exists in our db).
    #
    # if the movie already exists in our database, we should
    # should replace the "add to ledger" button with an "update"
    # button and a note that the movie is already in our list.
    #
    # on submission of the form, we should check to see if the
    # movie is in our db again

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    form = MovieAddEditForm()

    ###########################################################################
    # add movie to user's list by form (from movie detail page)
    if form.validate_on_submit():

        # if date_added field contains data, this movie already exists
        # in the current user's list, so this form submission will be an
        # update to the UserMovie table row. This also means that the
        # movie already exists in the Movies table.
        if form.date_added.data:

            # query our movie object to get the in
            um = UserMovie.query.filter_by(
                user_id=g.user.id, movie_id=movie_id).first()

            # update values.  there will only be 3 that we can modify
            um.favorite = form.favorite.data
            um.platform = None if not form.platform.data else form.platform.data
            um.date_viewed = form.date_viewed.data

            try:
                db.session.commit()

            except:
                flash("There was an error adding to your list!", "danger")
                return redirect(f"/movie/{movie_id}")

            flash("Movie updated!", "success")

        # save a new movie to our user's list.  but we still need to
        # check if the movie exists in the Movie table.  it may already
        # exist there from another user's addition.
        else:
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
                               favorite=form.favorite.data,
                               platform=None if not form.platform.data else form.platform.data,
                               date_viewed=form.date_viewed.data,
                               )

                db.session.add(um)

                try:
                    db.session.commit()

                except IntegrityError as exc:
                    flash("Movie is already in your list!", "danger")
                    return redirect(f"/movie/{movie_id}")

                flash("Movie added to your list!", "success")

            else:
                # we need to add a new Movie entry and UserMovie entry
                m = Movie(imdb_id=movie_id,
                          title=form.title.data,
                          year=form.year.data[0:4],
                          actors=form.actors.data,
                          imdb_img=form.imdb_img.data)

                db.session.add(m)

                try:
                    db.session.commit()

                except IntegrityError as exc:
                    flash("Movie is already in your list!", "danger")
                    return redirect(f"/movie/{movie_id}")

                um = UserMovie(movie_id=movie_id,
                               user_id=g.user.id,
                               favorite=form.favorite.data,
                               platform=None if not form.platform.data else form.platform.data,
                               date_viewed=form.date_viewed.data,
                               )

                db.session.add(um)

                try:
                    db.session.commit()

                except IntegrityError as exc:
                    flash("Movie is already in your list!", "danger")
                    return redirect(f"/movie/{movie_id}")

                flash("Movie added to your list!", "success")

        return redirect("/movies")

    ###########################################################################
    # add movie to user's list through ajax (from search page)
    if request.headers.get('Content-Type') == "application/json":
        # to get actors, we need to make an api call
        # our movie_id comes from the route, which is
        # created in our js code
        movie = movie_search_by_id(movie_id)

        # save a new movie to our user's list.  but we still need to
        # check if the movie exists in the Movie table.  it may already
        # exist there from another user's addition.
        movie_in_movies_table = Movie.query.get(movie_id)

        if movie_in_movies_table:
            um = UserMovie(movie_id=movie_id,
                           user_id=g.user.id,
                           )

            db.session.add(um)

            try:
                db.session.commit()

            except IntegrityError as exc:
                print("Error: ", exc)
                resp = jsonify({"message": "There was an error"})
                return (resp, 400)

            # success response goes here
            resp = jsonify({"message": "Movie added to list!"})
            return (resp, 201)

        else:
            # favorite will take the default value from our model
            # date_added will take the default from our model
            # date_viewed is optional so None <class 'NoneType'> will
            #   be our value and db field will be blank
            # platform is optional so None <class 'NoneType'> will
            #   be our value and db field will be blank
            m = Movie(imdb_id=request.json["imdb_id"],
                      title=request.json["title"],
                      year=request.json["year"][0:4],
                      actors=movie['Actors'],
                      imdb_img=request.json["imdb_img"],
                      )

            g.user.movies.append(m)

            try:
                db.session.add(g.user)

                db.session.commit()

            except IntegrityError as exc:
                print("Error: ", exc)
                resp = jsonify({"message": "There was an error"})
                return (resp, 400)

            # success response goes here
            resp = jsonify({"message": "Movie added to list!"})
            return (resp, 201)

    ###########################################################################
    # GET request functionality below

    # get the movie data from the api.  data returned will be
    # a dictionary containing a key title "Response".
    # If "True", a movie was found.  if "False", no movie found.
    try:
        movie = movie_search_by_id(movie_id)

    except:
        flash("Sorry, There was an error processing your request", "danger")
        return redirect("/movie-search")

    # if the movie id doesn't exist, redirect to search and flash a message
    if movie["Response"] == "False":
        flash("Sorry, we can't find the movie you are looking for.", "danger")
        return redirect("/movie-search")

    # update our wtform data on the front end to match the movie
    # details of the movie we are viewing, so when we submit the
    # MovieAddEditForm our values will be correct
    form.title.data = movie['Title']
    form.year.data = movie['Year']
    form.actors.data = movie['Actors']
    form.imdb_img.data = movie['Poster']

    # check if this movie is already in our current user's list
    # by querying the UserMovies table
    # .first() returns the movie, or no movies
    movie_in_users_list = UserMovie.query.filter_by(
        user_id=g.user.id, movie_id=movie['imdbID']).first()

    # if the movie is already in the current user's list we can pre-populate
    # the data that is exclusive to our db into our form as well.
    # the date_added hidden field is included in wtforms as a flag
    # to pass to our post route and used to determine if the post is a
    # new save, or an update.
    if movie_in_users_list:
        form.favorite.data = movie_in_users_list.favorite
        form.platform.data = movie_in_users_list.platform
        form.date_viewed.data = movie_in_users_list.date_viewed
        form.date_added.data = movie_in_users_list.date_added

    return render_template("movie-detail.html", form=form, movie=movie, movie_in_users_list=movie_in_users_list)


# internal api route - delete a movie ajax
@app.route("/movie/<movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    """Delete a movie from our db."""

    # below we delete the item in sqlalchemy, but we need db.session.commit()
    UserMovie.query.filter_by(user_id=g.user.id, movie_id=movie_id).delete()

    db.session.commit()

    resp = jsonify({"message": "success"})

    return (resp, 200)


# internal api route - favorite a movie ajax
@app.route('/movie/<movie_id>/favorite', methods=["POST"])
def add_remove_favorite(movie_id):
    """Add or remove a movie as a favorite"""

    m = UserMovie.query.filter_by(user_id=g.user.id, movie_id=movie_id).first()

    m.favorite = not m.favorite

    db.session.commit()

    # send back our boolean value for "favorite" so we can
    # keep the front end in sync with our database data
    resp = jsonify({"message": "success", "favorite": m.favorite})

    return (resp, 200)


###############################################################################
# movie search route

# search movies from the omdb database.  must be logged in!
@app.route("/movie-search")
def search_movies():
    """Get all the movies based on a search term from form data"""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

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

            user_movies = [movie.imdb_id for movie in g.user.movies]

            for movie in results_curr['Search']:
                if movie['imdbID'] in user_movies:
                    movie["ml_inList"] = True

        # make the call to our external api for the NEXT page
        #
        # pass the "Response" returned to our template
        #
        # based on the val of "Response" we can render a next_page link or not
        results_next = movie_search(search_term, page=page+1)

        next_page = results_next['Response']

        # render our template and pass the results of the api request
        # along with the search term (so we can create our search note)
        #
        # we'll handle the rendering of our data in our template
        return render_template("movie-search.html", results=results_curr, search_term=search_term, page=page, next_page=next_page)

    # no search term submitted, so we just render our starting search page
    return render_template("movie-search.html", user=g.user)


###############################################################################
# homepage

@app.route("/")
def homepage():
    """Show homepage."""

    return render_template("home.html")
