/**
 * ajax functions for adding a favorite and
 * deleting a movie from users list
 */

const functionsBtnContainers = document.getElementsByClassName('ml__movie-list--functions-container')

const searchResults = document.getElementById('searchResults')
const movieList = document.getElementById('myMovieList');
const movieDetailModal = document.getElementById("ml__movie-detail-modal")
const movieDetailModalCloseBtn = document.getElementById("ml__movie-detail-modal-close-btn")

const sortIcon = document.getElementById('sortIcon')
const sortContainer = document.getElementById('sortContainer')
const sortForm = document.getElementById("sortForm")
const sortBy = document.getElementById("sort")
const sortOrderAsc = document.getElementById("order-asc")
const sortOrderDesc = document.getElementById("order-desc")
const sortButton = document.getElementById("myListSortButton")

const pageContent = document.getElementById('pageContent');
const backToMoviesLink = document.getElementById('backToMoviesLink')


movieList && movieList.addEventListener("click", showMovieDetailModal)

sortIcon && sortIcon.addEventListener("click", showHideSortBox)

sortForm && document.addEventListener("DOMContentLoaded", checkValuesSet);
sortForm && sortForm.addEventListener("change", checkValuesSet)

// add event listener
for (let item of functionsBtnContainers) {
  item.addEventListener("click", handleMovieFunctionsClick)
}

function checkValuesSet(e) { 
  if (sortBy.value && (sortOrderAsc.checked || sortOrderDesc.checked)) {
    sortButton.classList.remove("disabled")
  }
  else {
    sortButton.classList.add("disabled")
  }
}

function showHideSortBox(e) {
  sortContainer.classList.toggle("hidden")
}

// click handler
async function handleMovieFunctionsClick(e) {
  if (e.target.classList.contains('ml__movie--my-list')) {
    const imdb_id = e.target.parentElement.getAttribute('data-id');
    toggleMyList(imdb_id, e)
  }

  if (e.target.classList.contains('ml__movie--fav')) {
    const imdb_id = e.target.parentElement.getAttribute('data-id');
    toggleFavorite(imdb_id, e)
  }
}


// toggle functions

/**
 * add or remove a movie from myList
 *
 * if we are on the "my movies" view, dynamically
 * remove the movie from the list when deleting
 * 
 * if we are on the "movie search" view, toggle
 * the icon classes and dynamically show/hide the
 * favorite icon
 */

/**
 * favorite classes:
 * far = false
 * fas = true
 */
function toggleMyList(movieID, e) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
  };

  // add to my list
  if (e.target.parentElement.getAttribute('data-my-list') === "false") {
    // only need the below atts if we are adding a movie
    const title = e.target.parentElement.getAttribute('data-title');
    const release_year = e.target.parentElement.getAttribute('data-release-year');
    const imdb_img = e.target.parentElement.getAttribute('data-img');
    
    const params = { movieID, title, release_year, imdb_img };

    /* send a request to our internal api point to add a movie to our db */
    axios
      .post(`/api/movie/${movieID}`, JSON.stringify(params), config)
      .then((resp) => {
        if (resp.status == 201) {
          // do this regardless of view
          e.target.parentElement.setAttribute('data-my-list', "true")
          e.target.classList.add('fas');
          e.target.classList.remove('far');
          e.target.parentElement.children[0].classList.remove('hidden')
        }
      })
      .catch((err) => {
        if (err.response.status == 400) alert('Movie is already in your list');
      });
  }
    
  // remove from my list
  if (e.target.parentElement.getAttribute('data-my-list') === "true") {
    axios
      .delete(`/api/movie/${movieID}`, config)
      .then((resp) => {
        if (resp.status == 200) {
          // if we are on the search page, change the icon, set the attribute hide the fav icon
          if (searchResults) {
            e.target.parentElement.setAttribute('data-my-list', "false")
            e.target.classList.remove('fas');
            e.target.classList.add('far');

            // also remove the fav icon
            e.target.parentElement.children[0].classList.add("hidden") 
          }

          // if we are on the my movies page, remove the movie from the page
          if (movieList) {
            e.target.parentElement.parentElement.remove();

            /**
             * check if there are an <li>'s left, if all are gone,
             * reset the ui to "no movies found" condition:
             * remove the filter & sort box, 
             * remove the ul and replace with the <h3>
             */
            if (movieList.children.length == 0) {
              sortContainer.remove();
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
        }
      })
      .catch((err) => console.log('err: ', err));
  }
}

/**
 * favorite or unfavorite a movie.
 *
 * if we are on the favorites filter view, dynamically
 * remove the movie from the list when unfavoriting
 * 
 * if we are on the "my list" view, or the "movie search"
 * view, toggle the icon classes
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
          e.target.className = 'fas fa-heart favoriteIcon ml__movie--fav';
        } else {
          e.target.className = 'far fa-heart favoriteIcon ml__movie--fav';

          /* if we are on the favorites view, we should remove the movie */
          if (window.location.search.includes('filter=favorites')) {
            e.target.parentElement.parentElement.remove();

            /**
             * check if there are an <li>'s left, if all are gone,
             * remove the ul and replace with the <h3>
             */
            if (movieList.children.length == 0) {
              sortContainer.remove();
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

function showMovieDetailModal(e) {
  e.preventDefault()
  movieDetailModal.classList.add("show")

  movieDetailModalCloseBtn.addEventListener("click", function () {
    movieDetailModal.classList.remove("show")
  })
  console.log(e.target)
}