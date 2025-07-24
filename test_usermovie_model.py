
"""Movie model tests."""

# run these tests like:
#    python -m unittest test_movie_model.py

from app import app
from unittest import TestCase

from models import db, Movie, User, UserMovie


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

class UserMovieModelTestCase(TestCase):
    """Test Movie model."""

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

        # start fresh with no db
        UserMovie.query.delete()
        Movie.query.delete()
        User.query.delete()

        # create 1 user in our Users model.
        u = User(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            img_url=""
        )

        db.session.add(u)
        db.session.commit()

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
            user_id=u.id,
            movie_id="testID456",
        )

        db.session.add(um)
        db.session.commit()

        self.id = u.id
        self.mid = m.imdb_id

        self.client = app.test_client()

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # testing

    def test_usermovie_model(self):
        """Does basic model work?"""

        # User should have 1 movie from setups
        self.assertEqual(len(Movie.query.all()), 1)

        um = UserMovie.query.get((self.id, self.mid))

        self.assertEqual(
            f"<UserMovie user_id={um.user_id} movie_id={um.movie_id} favorite={um.favorite}>", str(um))

    def test_fail_on_duplicate_primary_key(self):
        """Does movie fail on adding a duplicate movie with the same user_id?"""

        # try to add a duplicated user movie
        um = UserMovie(
            user_id=self.id,
            movie_id="testID456",
        )

        db.session.add(um)

        # should raise an IntegrityError on commit
        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_fail_on_nonexistant_user_id(self):
        """Does movie fail if a user_id doesn't exist in the user's table?"""

        # create a movie from the recently created user with a user ID that doesn't exist
        m = Movie(
            imdb_id="testID456",
            title="Test Movie 2",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(m)

        um = UserMovie(
            user_id=self.id+1,
            movie_id="testID456"
        )

        db.session.add(um)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_fail_on_nonexistant_movie_id(self):
        """Does movie fail if a user_id doesn't exist in the user's table?"""

        um = UserMovie(
            user_id=self.id,
            movie_id="testID789"
        )

        db.session.add(um)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_movie_user_relationship(self):
        """Does the User relationship work properly on the movie model?"""

        # get our existing usermovie
        um = UserMovie.query.get((self.id, self.mid))

        m = Movie.query.get(self.mid)

        # we should be able access details of our user from the movie model
        # username should be the same regardless of how we access it
        self.assertEqual(um.movie_details.title, m.title)

    def test_movie_user_delete(self):
        """Can we delete a UserMovie relation?"""

        # get our existing usermovie
        um = UserMovie.query.get((self.id, self.mid))

        db.session.delete(um)
        db.session.commit()

        num_movies = UserMovie.query.get((self.id,  self.mid))

        # there should be no movies with our user_id/movie_id in our db
        self.assertEqual(num_movies, None)
