"""Movie View tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py

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

class MovieViewTestCase(TestCase):
    """Test views for movies."""

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
                                    password="testuser",
                                    img_url='')

        db.session.add(self.testuser)
        db.session.commit()

        # create an initial movie
        self.testmovie = Movie(
            imdb_id="testID123",
            title="Test Movie",
            release_year="2023",
            imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
        )

        db.session.add(self.testmovie)
        db.session.commit()

        self.testusermovie = UserMovie(
            user_id=self.testuser.id,
            movie_id=self.testmovie.imdb_id,
            favorite=True
        )

        db.session.add(self.testusermovie)
        db.session.commit()

        self.user_id = self.testuser.id
        self.movie_id = self.testmovie.imdb_id

        self.client = app.test_client()

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # testing

    def test_movies_get_route_no_auth_redirect(self):
        """Are we redirected if not logged in and try to visit /movies?"""

        with self.client as c:
            resp = c.get("/movies")
            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 302)

            resp = c.get("/movies", follow_redirects=True)
            html = resp.get_data(as_text=True)

    def test_movies_get_route_no_auth_redirect_location(self):
        """Are we redirected correctly to /login if not logged in and try to visit /movies?"""

        with self.client as c:
            resp = c.get("/movies", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn('<form id="ml__login-form" method="POST">', html)

    def test_movies_get_route_with_auth(self):
        """Can we retrieve list of movies."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.get("/movies")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="pageTitle">My List</h1>', html)
            self.assertIn("Test Movie", html)

    def test_movies_get_route_favorites(self):
        """Does our favorite filter work."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.get("/movies?filter=favorites")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="pageTitle">Favorites</h2>', html)
            self.assertIn("Test Movie", html)

    # # can test sorting for /movies route, including the sorting
    def test_movies_get_route_sorting_title(self):
        """Does our sort function work. Title/asc"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

        resp = c.get("/movies?sort=title&order=asc")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sorting by Title (ascending)', html)

    def test_get_movie_detail_no_auth_redirect(self):
        """Are we redirected if we are not logged in?"""

        with self.client as c:
            resp = c.get(f"/movie/{self.testmovie.imdb_id}")

            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 302)

    def test_get_movie_detail_no_auth(self):
        """Are we redirected to /login if we are not logged in?"""

        with self.client as c:
            resp = c.get(
                f"/movie/{self.testmovie.imdb_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login.", html)
            self.assertIn('<form id="ml__login-form" method="POST">', html)

    def test_get_movie_detail_with_auth_movie_not_found_redirect(self):
        """Are we redirected if a movie is not found through the api?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            # since this will fail on our api side, we should get a 302
            resp = c.get("/movie/testID123")
            self.assertEqual(resp.status_code, 302)

    def test_get_movie_detail_with_auth_movie_not_found(self):
        """Are we redirected back to /movie-searh if not found through the api?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.get("/movie/testID123",
                         follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Sorry, we can&#39;t find the movie you are looking for.", html)

    def test_add_usermovie_by_form(self):
        """Can user add a movie to their list by form?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            data = {
                "imdb_id": "testID456",
                "title": "Test Movie 2",
                "release_year": "2023",
                "favorite": False,
                "imdb_img": "http://www.test-url.com/test-directory/static/images/test.jpg",
                "platform": "",
                "date_viewed": None,
            }

            resp = c.post("/movie/testID456", data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects back to /movies
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Test Movie 2', html)

            # check if movie was added
            movie = UserMovie.query.get((self.user_id, 'testID456'))
            self.assertEqual(movie.movie_id, "testID456")

    def test_edit_usermovie_by_form(self):
        """Can user edit a movie on their list by form?  The only editable fields are
        date_viewed, favorite, and platform."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            m = Movie.query.get(self.movie_id)
            um = UserMovie.query.get((self.user_id, self.movie_id))

            # edit the favorite and send as new data
            data = {
                "imdb_id": m.imdb_id,
                "title": m.title,
                "release_year": m.release_year,
                "imdb_img": m.imdb_img,
                "favorite": False,
                "platform": "",
                "date_viewed": "",
                "date_added": um.date_added,
            }

            resp = c.post(f"/movie/{self.movie_id}",
                          data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="pageTitle">My List</h1>', html)
            self.assertIn('Movie details updated.', html)

            # print("")
            # print("*****************")
            # print("From test function: ")
            # print(html)
            # print("*****************")
            # print("")

            # check if movie was edited in db
            # self.assertEqual(um.favorite, False)

    def test_remove_movie_post_route(self):
        """Will we be returned a 405 for this method??"""

        with self.client as c:
            resp = c.post("/movie/testID123/delete")

            self.assertEqual(resp.status_code, 405)

    def test_remove_movie_form_not_logged_in_redirect(self):
        """Will we be redirected if not logged in?"""

        with self.client as c:

            resp = c.get("/movie/testID123/delete")

            self.assertEqual(resp.status_code, 302)

    def test_remove_movie_form_not_logged_in_redirect_location(self):
        """Will we be redirected to /login?"""

        with self.client as c:

            resp = c.get("/movie/testID123/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form id="ml__login-form" method="POST">', html)

    def test_remove_movie_form_logged_in(self):
        """Can user remove a movie through the details page form?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.get("/movie/testID123/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Movie removed from your list.', html)

    def test_add_movie_by_json_movie_in_db(self):
        """Can user add a movie through ajax?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            # first remove our already existing UserMovie
            um = UserMovie.query.get(
                (self.user_id, self.movie_id))

            db.session.delete(um)
            db.session.commit()

            # re-add the UserMovie connection, this should hit trigger movie_in_movies_table
            json = {
                'imdb_id': 'testID123',
                'title': 'Test Movie 2',
                'release_year': '2023',
                'imdb_img': 'http://www.test-url.com/test-directory/static/images/test.jpg'
            }

            resp = c.post("/api/movie/testID123", json=json)

            self.assertEqual(resp.status_code, 201)
            self.assertEqual(resp.json, {"message": "Movie added to list."})

            movies = UserMovie.query.all()
            self.assertEqual(len(movies), 1)

    def test_edit_movie_favorite_by_json(self):
        """Can user edit a movie favorite status through ajax?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.patch("/api/movie/testID123", json={})

            self.assertEqual(resp.status_code, 200)
            # favorite was true, should now be false
            self.assertEqual(
                resp.json, {"message": "success", "favorite": False})

            movie = Movie.query.one()
            self.assertEqual(movie.imdb_id, "testID123")

    def test_remove_movie_json(self):
        """Can user remove a movie through ajax?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.delete(
                f"/api/movie/testID123")

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json, {"message": "success"})

            um_count = UserMovie.query.all()
            self.assertEqual(len(um_count), 0)
