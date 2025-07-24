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

db.create_all()


################################################################################
# tests

class MovieModelTestCase(TestCase):
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

        self.id = u.id

        self.client = app.test_client()

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # testing

    def test_movie_model(self):
        """Does basic model work?"""

        # create a movie
        m1 = Movie(
            imdb_id="testID123",
            title="Test Movie",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(m1)
        db.session.commit()

        # User should have 1 movie
        self.assertEqual(len(Movie.query.all()), 1)

        # create another movie from the recently created user
        m2 = Movie(
            imdb_id="testID456",
            title="Test Movie 2",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(m2)
        db.session.commit()

        # should have 2 movies
        self.assertEqual(len(Movie.query.all()), 2)

        self.assertEqual(
            f"<Movie imdb_id={m1.imdb_id} title={m1.title} release_year={m1.release_year}>", str(m1))
        self.assertEqual(
            f"<Movie imdb_id={m2.imdb_id} title={m2.title} release_year={m2.release_year}>", str(m2))

    def test_fail_on_duplicate_movie(self):
        """Does movie fail on adding a duplicate movie with the same imdb_id?"""

        # create a movie for the user
        m1 = Movie(
            imdb_id="testID456",
            title="Test Movie 2",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(m1)
        db.session.commit()

        # need to close the current session or sqlalchemy will throw an error
        db.session.close()

        # create the a movie for recently created user
        dupMovie = Movie(
            imdb_id="testID456",
            title="Test Movie 2",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(dupMovie)

        # should raise an IntegrityError on commit
        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_movie_user_relationship(self):
        """Does the User relationship work properly on the movie model?"""

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

        # we should be able access details of our users from the movie model
        # username should be the same regardless of how we access it
        self.assertEqual(len(m.users), 1)
        self.assertEqual(m.users[0].email, 'test@test.com')

    def test_movie_delete(self):
        """Does the deleting a movie fail if there is an associate UserMovie?"""

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

        all_movie = Movie.query.all()
        all_user_movie = UserMovie.query.all()

        print("")
        print(all_movie)
        print(all_user_movie)
        print("")

        # attempt to delete our new movie
        db.session.delete(m)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)
