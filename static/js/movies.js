/**
 * ajax functions for adding a favorite and
 * deleting a movie from users list
 */

const functionsBtnContainers = document.getElementsByClassName('ml__my-list--functions-container')
const movieList = document.getElementById('myMovieList');
const sortFilterContainer = document.getElementById('sortFilterContainer')
const pageContent = document.getElementById('pageContent');
const backToMoviesLink = document.getElementById('backToMoviesLink')


movieList && movieList.addEventListener('click', (e) => {
  console.log(e.target.className)
  if (e.target.classList.contains('ml__my-list--fav')) {
    const movieID = e.target.getAttribute('data-id');
    toggleFavorite(movieID, e)
  }

  if (e.target.classList.contains('ml__my-list--remove-button')) {
    const movieID = e.target.getAttribute('data-id');
    deleteMovie(movieID, e)
  }
  
});


/**
 * remove movies from list dynamically throug ajax
 */
function deleteMovie(movieID, e) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
  };

  axios
    .delete(`/api/movie/${movieID}`, config)
    .then((resp) => {
      if (resp.status == 200) {
        e.target.parentElement.parentElement.remove();
        /**
         * check if there are an <li>'s left, if all are gone,
         * reset the ui to "no movies found" condition:
         * remove the filter & sort box, 
         * remove the ul and replace with the <h3>
         */
        if (movieList.children.length == 0) {
          sortFilterContainer.remove();
          movieList.remove();

          const h3 = document.createElement('h3');
          const link = document.createElement('a')

          if (window.location.search.includes('filter=favorites')) {
            backToMoviesLink.remove();

            h3.innerText = 'No favorites found...';

            link.innerText = 'Back to All Movies'
            link.setAttribute('href', '/movies')            
          } else {
            h3.innerText = 'No movies found...';

            link.innerText = 'Search Now'
            link.setAttribute('href', '/movie-search')
            link.classList.add('button')
          }

          pageContent.appendChild(h3);
          pageContent.appendChild(link)
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

/**
 * favorite classes:
 * far = false
 * fas = true
 */
function toggleFavorite(movieID, e) {
  axios
    .patch(`/api/movie/${movieID}`)
    .then((resp) => {
      if (resp.status == 200) {
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
              sortFilterContainer.remove();
              movieList.remove();
              backToMoviesLink.remove();

              const h3 = document.createElement('h3');
              h3.innerText = 'No favorites found...';

              const link = document.createElement('a')
              link.innerText = 'Back to All Movies'
              link.setAttribute('href', '/movies')
              
              pageContent.appendChild(h3);
              pageContent.appendChild(link)
            }
          }
        }
      }
    })
    .catch((err) => console.log('err: ', err));
}