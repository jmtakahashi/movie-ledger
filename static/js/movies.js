/**
 * ajax functions for adding a favorite and
 * deleting a movie from users list
 */

const functionsBtnContainers = document.getElementsByClassName('ml__movie-list--functions-container')

const searchResults = document.getElementById('searchResults')
const movieList = document.getElementById('myMovieList');
const movieListInfoContainers = document.getElementsByClassName("ml__movie-list--info-container")
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


for (let item of movieListInfoContainers) {
  item.addEventListener("click", showMovieDetailModal)
}
searchResults && searchResults.addEventListener("click", showMovieDetailModal)
// movieDetailModal && movieDetailModal.addEventListener("click", closeMovieDetailModal)
movieDetailModalCloseBtn && movieDetailModalCloseBtn.addEventListener("click", closeMovieDetailModal)

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
      .post(`/api/movies`, JSON.stringify(params), config)
      .then((resp) => {
        if (resp.status == 201) {
          // do this regardless of view.  show check mark
          e.target.parentElement.setAttribute('data-my-list', "true")
          e.target.classList.add('fa-check');
          e.target.classList.remove('fa-plus');
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
      .delete(`/api/movies/${movieID}`, config)
      .then((resp) => {
        if (resp.status == 200) {
          // if we are on the search page, change the mylist icon, set the attribute hide the fav icon
          if (searchResults) {
            e.target.parentElement.setAttribute('data-my-list', "false")
            e.target.classList.remove('fa-check');
            e.target.classList.add('fa-plus');

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
    .patch(`/api/movies/${movieID}`)
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

async function showMovieDetailModal(e) {
  e.preventDefault()

  const movieID = e.target.getAttribute("data-id")

    axios
      .get(`/api/movies/${movieID}`)
      .then((resp) => {
        if (resp.status == 200) {
          console.log(resp.data.movie)
          // {
          //     "date_added": "Sat, 26 Jul 2025 01:23:16 GMT",
          //     "date_viewed": null or "Wed, 01 Jan 2025 00:00:00 GMT",
          //     "favorite": true,
          //     "imdbID": "tt0208092",
          //     "in_list": true,
          //     "platform": null
          // }

          const movie = resp.data.movie

          if (!movie.in_list) {
            document.getElementById("not-in-list").classList.add("show")
            document.getElementById("add-or-update-button").innerHTML = '<i class="fas fa-plus"></i> My List'
            
            // populate form with create route
            document.getElementById("ml__add-edit-movie-form").setAttribute("action", `/movies`)

          }  else if (movie.in_list) {
            document.getElementById("in-list").classList.add("show")
            document.getElementById("add-or-update-button").innerText = "Update Details"
            
            const removeFromListBtn = document.getElementById("remove-from-list-button")
            removeFromListBtn.setAttribute("href", `/movies/${ movie['imdbID'] }/delete`)
            removeFromListBtn.classList.add("show")
            
            // populate form with update route
            document.getElementById("ml__add-edit-movie-form").setAttribute("action", `/movies/${movie["imdbID"]}`)
                  
          }

          // populate movie data.  does not rely on in-list
          document.getElementById("movie_details-image").setAttribute("style", `background-image: url(${ movie["Poster"] });`)
          document.getElementById("movie_details-title").innerText = movie["Title"]
          document.getElementById("movie_details-release-year").innerText = movie["Year"]
          document.getElementById("movie_details-rated").innerText = movie["Rated"]
          document.getElementById("movie_details-released").innerText = movie["Released"]
          document.getElementById("movie_details-runtime").innerText = movie["Runtime"]
          document.getElementById("movie_details-genre").innerText = movie["Genre"]
          document.getElementById("movie_details-actors").innerText = movie["Actors"]
          document.getElementById("movie_details-plot").innerText = movie["Plot"]

        
          //hidden fields. does not rely on in-list
          document.getElementById("imdb_id").value = movie["imdbID"]
          document.getElementById("title").value = movie["Title"]
          document.getElementById("release_year").value = movie["Year"]
          document.getElementById("imdb_img").value = movie["Poster"]
          document.getElementById("date_added").value = movie["date_added"]

          // not hidden fields. relies on in-list or not.
          if (movie.favorite) {
            document.getElementById("favorite").checked = true;
          }

          if (movie.in_list) {
            // values coming back from our api request could be null
            // if values are null, don't set the value attribute (will cause issues)
            movie["platform"] && (document.getElementById("platform").value = movie["platform"])
            // convert date to pre-populate date selector - https://stackoverflow.com/a/58880605/7207125
            // if (movie["date_viewed"]) {
            //   let d = new Date(movie["date_viewed"]);
            //   console.log(d)
            //   let datestring = d.getFullYear().toString().padStart(4, '0') + '-' + (d.getMonth()+1).toString().padStart(2, '0') + '-' + d.getDate().toString().padStart(2, '0');
            //   console.log(datestring)
            //   document.getElementById("platform").value = datestring
            // } 
            movie["date_viewed"] && (document.getElementById("date_viewed").value = movie["date_viewed"])
          }

          // show our modal
          movieDetailModal.classList.add("show")
        }
      })
      .catch((err) => console.log('err: ', err));
}

function closeMovieDetailModal(e) {
  movieDetailModal.classList.remove("show")

  // clear all data
  document.getElementById("movie_details-image").removeAttribute("style")
  document.getElementById("movie_details-title").innerText = ""
  document.getElementById("movie_details-release-year").innerText = ""
  document.getElementById("movie_details-rated").innerText = ""
  document.getElementById("movie_details-released").innerText = ""
  document.getElementById("movie_details-runtime").innerText = ""
  document.getElementById("movie_details-genre").innerText = ""
  document.getElementById("movie_details-actors").innerText = ""
  document.getElementById("movie_details-plot").innerText = ""

  // reset form action
  document.getElementById("ml__add-edit-movie-form").removeAttribute("action")

  // reset hidden fields
  document.getElementById("title").value = ""
  document.getElementById("release_year").value = ""
  document.getElementById("imdb_img").value = ""
  document.getElementById("date_added").value = ""

  // reset not hidden fields
  document.getElementById("favorite").checked = false;
  document.getElementById("platform").value = ""
  document.getElementById("date_viewed").value = ""
}