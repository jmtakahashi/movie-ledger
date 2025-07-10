/**
 * ajax functions for adding a favorite and
 * deleting a movie from my list
 */

const removeButtons = document.getElementsByClassName(
  'ml__my-list--remove-button'
);
const favButtons = document.getElementsByClassName('ml__my-list--fav');

const movieList = document.getElementById('myMovieList');
const mainContent = document.getElementById('mainContent');

/**
 * remove movies from list dynamically throug ajax
 */
for (let el of removeButtons) {
  el.addEventListener('click', deleteMovie);
}

function deleteMovie(e) {
  e.preventDefault();

  const movieID = e.target.getAttribute('data-id');

  const config = {
    headers: { 'Content-Type': 'application/json' },
  };

  axios
    .delete(`/movie/${movieID}`, config)
    .then((resp) => {
      if (resp.status == 200) {
        e.target.parentElement.parentElement.remove();
        /**
         * check if there are an <li>'s left, if all are gone,
         * remove the ul and replace with the <h3>
         */
        if (movieList.children.length == 0) {
          movieList.remove();
          const h3 = document.createElement('h3');
          h3.innerText = 'No movies found....';

          // mainContent is defined at the top
          mainContent.appendChild(h3);
        }
      }
    })
    .catch((err) => console.log('err: ', err));
}

/**
 * favorite or unfavorite a movie.
 *
 * if we are on the favorites filter view, dynamically
 * remove the movie from the list when unfavoriting
 */
for (let el of favButtons) {
  el.addEventListener('click', toggleFavorite);
}

function toggleFavorite(e) {
  e.preventDefault();

  const movieID = e.target.getAttribute('data-id');

  /**
   * favorite classes:
   * far = false
   * fas = true
   */

  axios
    .post(`/movie/${movieID}/favorite`)
    .then((resp) => {
      if (resp.status == 200) {
        // console.log("Favorite: ", resp.data.favorite)
        /**
         * checking for resp.data.favorite ensures that our front
         * end correctly represents the data in our database
         */
        if (resp.data.favorite) { 
          e.target.className = 'fas fa-star ml__my-list--fav';
        } else {
          e.target.className = 'far fa-star ml__my-list--fav';

          /* if we are on the favorites view, we should remove the movie */
          if (window.location.search.includes('filter=favorites')) {
            e.target.parentElement.parentElement.remove();

            /**
             * check if there are an <li>'s left, if all are gone,
             * remove the ul and replace with the <h3>
             */
            if (movieList.children.length == 0) {
              movieList.remove();
              const h3 = document.createElement('h3');
              h3.innerText = 'No movies found....';

              // mainContent is defined at the top
              mainContent.appendChild(h3);
            }
          }
        }
      }
    })
    .catch((err) => console.log('err: ', err));
}