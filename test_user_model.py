"""User model tests."""

# run these tests like:
#    python -m unittest test_user_model.py

from app import app
from unittest import TestCase

from models import db, User, Movie, UserMovie


################################################################################
# testing config

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///movie_ledger_test"
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['SQLALCHEMY_ECHO'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


################################################################################
# tests

class UserModelTestCase(TestCase):
    """Test User model."""

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

        # start fresh with no db entries
        UserMovie.query.delete()
        Movie.query.delete()
        User.query.delete()

        # add a user to our db to test against, use User.signup
        u = User.signup(
            username="TestUser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            img_url=""
        )

        db.session.add(u)
        db.session.commit()

        self.id = u.id

        self.client = app.test_client()

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # testing

    def test_user_model(self):
        """Does the basic user model work?"""

        # add a user, we already have 1 user in the db
        u = User(
            username="TestUser2",
            email="test2@test.com",
            password="HASHED_PASSWORD",
            img_url=""
        )

        db.session.add(u)
        db.session.commit()

        # User __repr__ should return "<User #{self.id}: {self.username}, {self.email}>
        self.assertEqual(
            str(u), f"<User id={u.id} username={u.username} img_url={u.img_url}>")

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        u = User.signup(
            username="TestUser2",
            email="test2@test.com",
            password="HASHED_PASSWORD",
            img_url=""
        )

        db.session.add(u)
        db.session.commit()

        # this will return 2 users
        users = User.query.all()

        self.assertEqual(len(users), 2)

    def test_user_signup_fail_email(self):
        """Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        # we already have "test@test.com" in our db
        u = User(
            username="TestUser2",
            email="test@test.com",
            password="HASHED_PASSWORD",
            img_url=""
        )

        # this should fail because u1.username is the same as u
        db.session.add(u)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_signup_fail_no_data(self):
        """Does User.signup fail to create a new user if any of the required data is missing?"""

        # we already have "test@test.com" in our db
        u = User(
        )

        # this should fail because u1.username is the same as u
        db.session.add(u)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""

        u1 = User.query.get(self.id)

        # add a user to our db to test against, use User.signup to
        u2 = User.authenticate(
            email="test@test.com", password="HASHED_PASSWORD")

        # check User.authenticate
        self.assertEqual(u1, u2)

    def test_user_authenticate_fail_email(self):
        """Does User.authenticate fail to return a user when the email is invalid?"""

        # we already have "test@test.com" in our db, so we test with a diff. email
        self.assertEqual(User.authenticate(
            email="test2@test.com", password="HASHED_PASSWORD"), False)

    def test_user_authenticate_fail_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""

        # we already have "TestUser" in our db, so we test with a diff. pwd
        self.assertEqual(User.authenticate(
            email="test@test.com", password="HSHD_PWD"), False)

    def test_relationship_on_user_model(self):
        """Does the relationship work?
        Can we access a user's movies through the user model?
        """

        # add a user to our db to test against, use User.signup to
        u = User.query.get(self.id)

        # we haven't added any movies so user should have no UserMovies
        self.assertEqual(len(u.user_movies_details), 0)
        self.assertEqual(len(u.movies), 0)

        # add a UserMovie which should automatically add a movie
        m = Movie(
            imdb_id="testID456",
            title="Test Movie 2",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(m)
        db.session.commit()

        um = UserMovie(
            user_id=self.id,
            movie_id="testID456",
        )

        db.session.add(um)
        db.session.commit()

        # get our already created user
        u = User.query.get(self.id)

        # there should be 1 of each in our relationships
        self.assertEqual(len(u.user_movies_details), 1)
        self.assertEqual(len(u.movies), 1)

        # we should be able to get the details of the movie through user relationship
        self.assertEqual(u.movies[0].title, m.title)
        self.assertEqual(u.movies[0].release_year, 2023)
