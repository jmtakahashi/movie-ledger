"""Models for Movie Ledger."""

from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt

from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()


def connect_db(app):
    """Connect to the database."""
    db.app = app
    db.init_app(app)


###############################################################################
# user model

class User(db.Model):
    """User model"""

    __tablename__ = "users"

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    username = db.Column(db.String(20),
                         nullable=False)
    email = db.Column(db.Text,
                      unique=True,
                      nullable=False)
    password = db.Column(db.Text,
                         nullable=False)
    date_created = db.Column(
        db.DateTime, default=datetime.now, nullable=False)
    # since we set nullable to false, we cannot add a "None" or "Null" value as the default
    img_url = db.Column(db.String(50),
                        default="./static/images/generic-user-icon-600px.jpg",
                        nullable=False)

    # define our relationship for users to movies, and backref
    #
    # the first arg in the relationship method is the class name
    # of the model we want to reference with this relationship
    # adding the backref allows us to access the user from the movie
    # model so we dont' have to add a relationship in the movie model.
    # secondary is the through table that we need to access
    user_movies_details = db.relationship(
        "UserMovie", backref="user", order_by='UserMovie.date_added.desc()')

    movies = db.relationship(
        "Movie", secondary="users_movies", backref="users")

    def __repr__(self):
        """Show Info about pet"""

        u = self

        return f"<User id={u.id} username={u.username} img_url={u.img_url}>"

    @classmethod
    def signup(cls, username, password, email, img_url):
        """Signup a user with a hashed password and return the user."""

        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_pwd = hashed.decode("utf8")

        # create our user object with the newly hashed password and
        # the data passed from app.py /signup route
        u = User(
            username=username,
            password=hashed_pwd,
            email=email,
            img_url=img_url
        )

        return u

    @classmethod
    def authenticate(cls, email, password):
        """Validate that user exists and password is correct."""

        # return user if valid, else return false
        u = User.query.filter_by(email=email).first()

        if u and bcrypt.check_password_hash(u.password, password):
            return u
        else:
            return False

    def hash_password(password):
        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_pwd = hashed.decode("utf8")
        return hashed_pwd


###############################################################################
# movie model


class Movie(db.Model):
    """Movie model"""

    __tablename__ = "movies"

    imdb_id = db.Column(db.String(10),
                        unique=True,
                        primary_key=True)
    title = db.Column(db.Text,
                      nullable=False)
    release_year = db.Column(db.Integer(),
                             nullable=False)
    imdb_img = db.Column(db.Text,
                         nullable=False)

    def __repr__(self):
        """Show Info about movie"""

        m = self

        return f"<Movie imdb_id={m.imdb_id} title={m.title} release_year={m.release_year}>"


###############################################################################
# user_movie model

class UserMovie(db.Model):
    """User Movie model"""

    __tablename__ = "users_movies"

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete="cascade"), primary_key=True)

    movie_id = db.Column(db.String(10), db.ForeignKey(
        'movies.imdb_id'), primary_key=True)

    date_added = db.Column(
        db.DateTime, default=datetime.now, nullable=False)

    platform = db.Column(db.Text, nullable=True)

    date_viewed = db.Column(db.Date, nullable=True)

    favorite = db.Column(db.Boolean, default=False, nullable=False)

    # relationships
    movie_details = db.relationship("Movie")

    def __repr__(self):
        """Show Info about the user movie relationship"""

        um = self

        return f"<UserMovie user_id={um.user_id} movie_id={um.movie_id} favorite={um.favorite}>"

    @classmethod
    def add_movie_to_list(cls, data):
        """Add a movie to the users list.  Should handle ajax or form data."""
        movie_id = data["movieID"]

        # save a new movie to our user's list.  but we still need to
        # check if the movie exists in the Movie table.  it may already
        # exist there from another user's addition.
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
                           user_id=data["user_id"],
                           favorite=data["favorite"]
                           )

            # um = UserMovie(movie_id=movie_id,
            #                user_id=session[CURR_USER_KEY],
            #                favorite=False if not form.favorite.data else form.favorite.data,
            #                platform=None if not form.platform.data else form.platform.data,
            #                date_viewed=form.date_viewed.data,
            #                )

            try:
                db.session.add(um)
                db.session.commit()

            except IntegrityError as exc:
                if (data["source"] == "form-data"):
                    return None

                else:
                    print("Error: ", exc)
                    resp = jsonify({"message": "There was an error"})
                    return (resp, 400)

        else:
            # favorite will take the value coming from the ajax req
            # date_added will take the default from our model
            # date_viewed is optional so None <class 'NoneType'> will
            #   be our value and db field will be blank
            # platform is optional so None <class 'NoneType'> will
            #   be our value and db field will be blank
            u = User.query.get(data["user_id"])
            m = Movie(imdb_id=movie_id,
                      title=data["title"],
                      release_year=data["release_year"][0:4],
                      imdb_img=data["imdb_img"],
                      )

            try:
                u.movies.append(m)
                db.session.add(u)
                db.session.commit()

            except IntegrityError as exc:
                if (data["source"] == "form-data"):
                    return None

                else:
                    print("Error: ", exc)
                    resp = jsonify({"message": "There was an error"})
                    return (resp, 400)

            um = UserMovie.query.get((data["user_id"], movie_id))

        # success response goes here
        if (data["source"] == "form-data"):
            return um
        else:
            resp = jsonify({"message": "Movie added to list.",
                            "movieDetails": UserMovie.serialize(um)})
            return (resp, 201)

    def serialize(self):
        """Serialze a userMovie SQLAlchemy obj to dict."""

        return {
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "date_added": self.date_added,
            "platform": self.platform,
            "date_viewed": self.date_viewed,
            "favorite": self.favorite
        }
