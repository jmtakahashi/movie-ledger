"""User view tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py

from flask import session

from app import app, CURR_USER_KEY
from unittest import TestCase

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

    def test_signup_get(self):
        """Test the signup view GET route."""

        with self.client as c:

            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form id="ml__signup-form" method="POST">', html)

    def test_signup_get_logged_in(self):
        """Test the signup view GET route when a user logged in.
        Should redirect to /movies"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/signup')
            self.assertEqual(resp.status_code, 302)

            resp = c.get('/signup', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<h1 class="pageTitle">My List</h1>', html)

    def test_signup_post(self):
        """ Test the signup view POST route with data.
        Should log the user in and redirect to /movie-search."""

        with self.client as c:

            # we already have a user with username "testuser"
            data = {
                'username': 'testuser2',
                'password': 'password2',
                'email': 'test2@test.com',
                'img_url': ''
            }

            resp = c.post('/signup', data=data)

            # check that the user that we added is added to the session in do_login
            self.assertIn(CURR_USER_KEY, session)

            # check that our response code is the redirect coming from the view
            self.assertEqual(resp.status_code, 302)

            u = User.query.filter_by(username="testuser2").first()

            self.assertIsInstance(u, User)

    def test_signup_post_logged_in(self):
        """ Test the signup view POST route while logged in.  Should redirect to /."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # we already have a user with username "testuser"
            data = {
                'username': 'testuser2',
                'password': 'password2',
                'email': 'test2@test.com',
                'img_url': ''
            }
            resp = c.post('/signup', data=data)

            # check that our response code is the redirect coming from the view
            self.assertEqual(resp.status_code, 302)

            u = User.query.filter_by(email="test2@test.com").first()

            # check that the user is not added
            self.assertEqual(u, None)

    def test_login_get(self):
        """ Test the login view GET route."""

        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form id="ml__login-form" method="POST">', html)

    def test_login_get_logged_in(self):
        """ Test the login view GET route when user is already logged in.."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/login')
            self.assertEqual(resp.status_code, 302)

            resp = c.get('/login', follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<h1 class="pageTitle">My List</h1>', html)

    def test_login_post(self):
        """ Test the login view POST route with correct credentials."""
        with self.client as c:
            data = {
                'email': 'test@test.com',
                'password': 'password'
            }
            # following the redirect to the "/" route
            resp = c.post('/login', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            # username is test user and it should be flashed on the page for a successful redirect
            self.assertIn(
                '<h1 class="pageTitle">My List</h1>', html)

    def test_login_post_incorrect_data(self):
        """ Test the login view POST route with incorrect credentials."""
        with self.client as c:
            data = {
                'email': 'test@test.com',
                'password': 'asdfasdfasdf'
            }
            # following the redirect to the "/" route
            resp = c.post('/login', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            # username is test user and it should be flashed on the page for a successful redirect
            self.assertIn(
                '<form id="ml__login-form" method="POST">', html)

    def test_logout_get(self):
        """ Test the logout view GET route."""

        with self.client as c:
            # following the redirect to the "/" route
            resp = c.get('/logout')

            # check that we are redirected to the home page
            self.assertEqual(resp.status_code, 405)

    def test_logout_post_not_logged_in(self):
        """ Test the logout view POST route."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # following the redirect to the "/" route
            resp = c.post('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<h1 class="ml__welcome-heading logo">MYFLIX</h1>', html)

    def test_logout_post_logged_in(self):
        """ Test the logout view POST route."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # following the redirect to the "/" route
            resp = c.post('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You have been logged out.", html)
            self.assertIn(
                '<h1 class="ml__welcome-heading logo">MYFLIX</h1>', html)

            # check that session has been cleared after running do_logout()
            self.assertNotIn(CURR_USER_KEY, session)

    def test_user_profile_get_no_auth(self):
        """ Test that profile route is inaccessible without logging in."""

        with self.client as c:
            resp = c.get('/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # that we are redirected to the login page
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form id="ml__login-form" method="POST">', html)

    def test_user_profile_get(self):
        """ Test user show profile route when user is logged in."""
        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # check that the profile page is displayed
            resp = c.get('/profile')
            html = resp.get_data(as_text=True)

            # check our status code
            self.assertEqual(resp.status_code, 200)
            # check that our username is in the html
            self.assertIn(
                '<form id="ml__profile-edit-form" method="POST">', html)

    def test_user_profile_post_correct_pw(self):
        """ Test our edit profile POST route with correct password."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # changing our profile details (except for pw)
            data = {
                'username': 'testuser2',
                'password': 'password',
                'email': 'test2@test.com',
                'img_url': ''
            }

            resp = c.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="ml__profile-edit-form" method="POST">', html)
            self.assertIn(
                'Your profile has been updated.', html)

    def test_user_profile_post_incorrect_pw(self):
        """ Test our edit profile POST route with incorrect password."""
        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # changing our profile details (except for pw)
            data = {
                'username': 'testuser2',
                'password': 'incorrectpassword',
                'email': 'test2@test.com',
                'img_url': ''
            }

            resp = c.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Current password incorrect.", html)

    def test_delete_user_correct_pw(self):
        """ Test profile delete POST route with the correct pw."""
        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # include correct password
            resp = c.post(
                '/profile/delete', data={"password": "password"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page with our flash message
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Your profile has been deleted", html)

            # check that our user has been deleted
            num_users = User.query.filter_by(id=self.testuser.id).count()
            self.assertEqual(num_users, 0)

    def test_delete_user_incorrect_pw(self):
        """ Test profile delete POST route with an incorrect pw."""
        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # include incorrect pw
            resp = c.post('/profile/delete',
                          data={"password": "drowssap"})

            # check that we are redirected to the edit profile page
            self.assertEqual(resp.status_code, 302)
