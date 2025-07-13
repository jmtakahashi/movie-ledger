/**
 * ajax function for adding a movie to the users list
 */

const searchResults = document.getElementById('searchResults');

/**
 * Add movie functionality
 */
searchResults && searchResults.addEventListener('click', function (e) {
  if (e.target.className === 'ml__search-result--add-button') {
    e.preventDefault();

    /**
     * results of our api search do not contain actors
     * if we want the actors, we need to make another
     * api call to get the movie details before we send
     * our post request to add our movie to our db
     */

    let imdb_id = e.target.getAttribute('data-id');
    let title = e.target.getAttribute('data-title');
    let year = e.target.getAttribute('data-year');
    let imdb_img = e.target.getAttribute('data-img');

    const params = { imdb_id, title, year, imdb_img };
    const config = {
      headers: { 'Content-Type': 'application/json' },
    };

    /* send a request to our internal api point to add a movie to our db */
    axios
      .post(`/api/movie/${imdb_id}`, JSON.stringify(params), config)
      .then((resp) => {
        if (resp.status == 201) {
          const li = e.target.parentElement;
          e.target.remove();
          const newSpan = document.createElement('span');
          newSpan.classList.add('ml__search-result--add-movie-success');
          newSpan.innerHTML = 'Added to <a href="/movies">My List</a>';
          li.appendChild(newSpan);
        }
      })
      .catch((err) => {
        if (err.response.status == 400) alert('Movie is already in your list');
      });
  }
});
