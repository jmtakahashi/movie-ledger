"""User view tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py

from flask import session

from app import app, CURR_USER_KEY
from unittest import TestCase
from datetime import datetime

from models import db, User, Movie, UserMovie


################################################################################
# testing config

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///movie_ledger_test"
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['SQLALCHEMY_ECHO'] = False

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


################################################################################
# tests

class UserViewTestCase(TestCase):
    """Test views for users."""

    ########################################################################
    # this will run once before all tests run

    # @classmethod
    # def setUpClass(cls) -> None:
    #     return super().setUpClass()

    ########################################################################
    # this will run once after all tests complete

    @classmethod
    def tearDownClass(cls):
        UserMovie.query.delete()
        Movie.query.delete()
        User.query.delete()
        db.session.commit()

    ########################################################################
    # this will run before every individual test

    def setUp(self):
        """Create test client, add sample data."""

        UserMovie.query.delete()
        Movie.query.delete()
        User.query.delete()

        # create an initial user
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    img_url="")

        db.session.add(self.testuser)
        db.session.commit()

        # create a movie
        self.testmovie = Movie(
            imdb_id="testID123",
            title="Test Movie",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(self.testmovie)
        db.session.commit()

        self.client = app.test_client()

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # testing

    def test_header_logged_out(self):
        """Test the header ui when user not logged in.
        Should show logo, login, signup links."""

        with self.client as c:

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertIn('<a class="logo" href="/">MYFLIX</a>', html)
            self.assertIn('<a href="/login">Login</a>', html)
            self.assertIn('<a href="/signup">Signup</a>', html)

    def test_header_logged_in(self):
        """Test the header ui when user is logged in.
        Should show logo, profile icon, signout icon."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            print(resp.status_code)

            self.assertIn(
                '<a href="/movie-search" class="searchIcon-wrapper"><i class="fas fa-search searchIcon"></i></a>', html)
            self.assertIn('<i class="fas fa-user profileIcon"></i>', html)
            self.assertIn(
                '<i class="fas fa-sign-out-alt logoutIcon"></i>', html)
            self.assertIn('<a href="/movies">My List</a>', html)
            self.assertIn(
                '<a href="/movies?filter=favorites">Favorites</a>', html)
            self.assertIn(
                '<a href="/movie-search" class="my-list-links__movie-search-link">Movie Search</a>', html)
            self.assertIn('<i class="fas fa-search searchIcon"></i>', html)

    def test_footer(self):
        """Test the footer ui.  
        Should show the correct year in the copyright and the link to my site."""

        with self.client as c:
            resp = c.get("/")
            html = resp.get_data(as_text=True)

            self.assertIn(
                '<a class="credit" href="https://whoisjaytee.com" target="_blank">Who is Jaytee?</a>', html)
