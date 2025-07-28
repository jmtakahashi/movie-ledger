/**
 * ajax functions for adding, deleting and favorite movie
 */
const movieListInfoContainers = document.getElementsByClassName("ml__movie-list--info-container")
const functionsBtnContainers = document.getElementsByClassName('ml__movie--functions-container')
const modalFunctionsBtnContainer = document.getElementById('ml__movie-modal--functions-container')
const searchResults = document.getElementById('searchResults')
const movieDetailModalCloseBtn = document.getElementById("ml__movie-detail-modal-close-btn")
const sortIcon = document.getElementById('sortIcon')
const sortForm = document.getElementById("sortForm")

// ony used in checkValuesSet
const sortBy = document.getElementById("sort")
const sortOrderAsc = document.getElementById("order-asc")
const sortOrderDesc = document.getElementById("order-desc")
const sortButton = document.getElementById("myListSortButton")

const movieDetailModal = document.getElementById("ml__movie-detail-modal")
const sortContainer = document.getElementById('sortContainer')

const movieList = document.getElementById('myMovieList');
const pageContent = document.getElementById('pageContent');
const sortNoteContainer = document.getElementById('ml__my-list--sort-note-container')

/* --------------------------------------------------------------------------- */
// event listeners

// movie detail modal
for (let item of movieListInfoContainers) {
  item.addEventListener("click", showMovieDetailModal)
}
movieDetailModalCloseBtn && movieDetailModalCloseBtn.addEventListener("click", closeMovieDetailModal)

/* sort dropdown box */
sortIcon && sortIcon.addEventListener("click", showHideSortBox)
sortForm && document.addEventListener("DOMContentLoaded", checkValuesSet);
sortForm && sortForm.addEventListener("change", checkValuesSet)

/* add/remove/favorite buttons - movie list and search results */
for (let item of functionsBtnContainers) {
  item.addEventListener("click", handleMovieFunctionsClick)
}

/* --------------------------------------------------------------------------- */

// sort box functions

function showHideSortBox(e) {
  sortContainer.classList.toggle("hidden")
}
// enables or disables sort "apply" button based on existence of values
function checkValuesSet(e) { 
  if (sortBy.value && (sortOrderAsc.checked || sortOrderDesc.checked)) {
    sortButton.classList.remove("disabled")
  }
  else {
    sortButton.classList.add("disabled")
  }
}

// movie add/remove + fav/unfav click handler. click listener is on the encompassing div
async function handleMovieFunctionsClick(e) {
  if (e.target.classList.contains('ml__movie--my-list')) {
    toggleMyList(e)
  }

  if (e.target.classList.contains('ml__movie--fav')) {
    toggleFavorite(e)
  }
}

/**
 * icon classes:
 * far = false - not fav
 * fas = true - fav
 * check = fa-check - added to list
 * plus = fa-plus - add to list
 */

/**
 * add or remove a movie from myList
 *
 * if we are on the "my movies" view, dynamically
 * remove the movie from the list when deleting
 */
function toggleMyList(e) {
  const movieID = e.target.parentElement.getAttribute('data-id');

  const config = {
    headers: { 'Content-Type': 'application/json' },
  };

  // add to my list
  if (e.target.parentElement.getAttribute('data-my-list') === "false") {
    // only need the below atts if we are adding a movie
    const title = e.target.parentElement.getAttribute('data-title');
    const release_year = e.target.parentElement.getAttribute('data-release-year');
    const imdb_img = e.target.parentElement.getAttribute('data-img');
    
    const data = { movieID, title, release_year, imdb_img };

    /* send a request to our internal api point to add a movie to our db */
    axios
      .post(`/api/movies`, JSON.stringify(data), config)
      .then((resp) => {
        if (resp.status == 201) {
          // do this regardless of view.  show check mark
          e.target.parentElement.setAttribute('data-my-list', true)
          e.target.classList.remove('fa-plus');
          e.target.classList.add('fa-check');

          // sync the modal and main page UI
          if (e.target.parentElement.getAttribute("data-click-source") == "modal") {
            document.getElementById(`ml__movie--functions-container--${movieID}`).setAttribute('data-my-list', true)
            document.getElementById(`ml__movie-my-list-icon--${movieID}`).classList.remove('fa-plus');
            document.getElementById(`ml__movie-my-list-icon--${movieID}`).classList.add('fa-check');

            // show the form
            document.getElementById("ml__edit-movie-form").classList.add("show")
          }
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
          // if we are on the search page, change the mylist icon, set the attribute
          if (searchResults) {
            e.target.parentElement.setAttribute('data-my-list', false)
            e.target.classList.remove('fa-check');
            e.target.classList.add('fa-plus');

            // if the item was a favorite, remove the favorite icon status
            e.target.parentElement.children[1].classList.remove("fas")
            e.target.parentElement.children[1].classList.add("far")

            // sync the modal and main page UI
            if (e.target.parentElement.getAttribute("data-click-source") == "modal") {
              document.getElementById(`ml__movie--functions-container--${movieID}`).setAttribute('data-my-list', false)
              document.getElementById(`ml__movie-my-list-icon--${movieID}`).classList.remove('fa-check');
              document.getElementById(`ml__movie-my-list-icon--${movieID}`).classList.add('fa-plus');

              // hide the form
              document.getElementById("ml__edit-movie-form").classList.remove("show")
            }
          }

          // if we are on the my movies page, remove the movie from the page, 
          // if we are clicking from the modal, close the modal
          if (movieList) {
            document.getElementById(`ml__movie-list-item-${movieID}`).remove()

            if (e.target.parentElement.getAttribute("data-click-source") == "modal") {
              closeMovieDetailModal()
            }

            /**
             * check if there are an <li>'s left, if all are gone,
             * reset the ui to "no movies found" condition:
             * remove the ul and replace with the <h3>
             */
            if (movieList.children.length == 0) {
              movieList.remove();

              const h3 = document.createElement('h3');
              const link = document.createElement('a')

              // if we are filtering and there are no more elements
              if (window.location.search.includes('filter=favorites')) {
                sortNoteContainer.remove();

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
 * favoriting a movie thats not in the user list should
 * automatically add to it to the user list
 */
function toggleFavorite(e) {
 
  const movieID = e.target.parentElement.getAttribute('data-id');
  const inList = e.target.parentElement.getAttribute("data-my-list")

  // if the movie is not in users list when toggling the favorite
  // we need to add it, so we need to send all the movie data with the request
  data = {}
  
  if (inList == "false") {
    data["movieID"] = movieID
    data["title"] = e.target.parentElement.getAttribute("data-title")
    data["release_year"] = e.target.parentElement.getAttribute("data-release-year")
    data["imdb_img"] = e.target.parentElement.getAttribute("data-img")
  }

  const config = {
    headers: { 'Content-Type': 'application/json' },
  };

  axios
    .patch(`/api/movies/${movieID}`, JSON.stringify(data), config)
    .then((resp) => {
      if (resp.status == 200 || 201) {
        /**
         * checking for resp.data.movieDetails.favorite ensures that our front
         * end correctly represents the data in our database
         */
        if (resp.data.movieDetails.favorite) { 
          e.target.classList.remove('far');
          e.target.classList.add('fas');

          // if movie not already in list, we should toggle the check mark. and show the edit form
          if (inList == "false") {
            e.target.parentElement.setAttribute("data-my-list", true)
            e.target.parentElement.children[0].classList.remove("fa-plus")
            e.target.parentElement.children[0].classList.add("fa-check")
          }

          // if we are doing this from the modal, sync the modal and main page UI
          if (e.target.parentElement.getAttribute("data-click-source") == "modal") {
            document.getElementById(`ml__movie-fav-icon--${movieID}`).classList.remove('far');
            document.getElementById(`ml__movie-fav-icon--${movieID}`).classList.add('fas');

            if (inList == "false") {
              document.getElementById(`ml__movie--functions-container--${movieID}`).setAttribute("data-my-list", true)
              document.getElementById(`ml__movie-my-list-icon--${movieID}`).classList.remove("fa-plus")
              document.getElementById(`ml__movie-my-list-icon--${movieID}`).classList.add("fa-check")

              // show edit form
              document.getElementById("ml__edit-movie-form").classList.add("show")
            } 
          }

        } else {
          // resp.data.movieDetails.favorite returns false
          e.target.classList.remove("fas")
          e.target.classList.add("far")

          // do below only if we are in the movie modal sync ui with main page
          if (e.target.parentElement.getAttribute("data-click-source") == "modal") {
            document.getElementById(`ml__movie-fav-icon--${movieID}`).classList.remove('fas');
            document.getElementById(`ml__movie-fav-icon--${movieID}`).classList.add('far');
          }
          
          // if we are on the favorites view, we should remove the movie
          // if we are clicking from the modal, close the modal
          if (window.location.search.includes('filter=favorites')) {
            document.getElementById(`ml__movie-list-item-${movieID}`).remove()

            if (e.target.parentElement.getAttribute("data-click-source") == "modal") {
              closeMovieDetailModal()
            }

            /**
             * check if there are an <li>'s left, if all are gone,
             * reset the ui to "no favorites found" condition:
             * remove the ul and replace with the <h3>
             */
            if (movieList.children.length == 0) {
              movieList.remove();
              sortNoteContainer.remove();

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

  // add event listeners for add/remove from list and fav/unfav
  modalFunctionsBtnContainer.addEventListener("click", handleMovieFunctionsClick)
  
  const movieID = e.target.getAttribute("data-id")

  movieDetailModalCloseBtn.setAttribute("data-id", movieID)
  
  axios
    .get(`/api/movies/${movieID}`)
    .then((resp) => {
      if (resp.status == 200) {
        // {
        //     "date_added": "Sat, 26 Jul 2025 01:23:16 GMT",
        //     "date_viewed": null or "Wed, 01 Jan 2025 00:00:00 GMT",
        //     "favorite": true,
        //     "imdbID": "tt0208092",
        //     "in_list": true,
        //     "platform": null
        // }

        const movie = resp.data.movie

        // populate button functions container atts          
        modalFunctionsBtnContainer.setAttribute("data-id", movie["imdbID"])
        modalFunctionsBtnContainer.setAttribute("data-title", movie["Title"])
        modalFunctionsBtnContainer.setAttribute("data-release-year", movie["Year"])
        modalFunctionsBtnContainer.setAttribute("data-img", movie["Poster"])

        if (!movie.in_list) {
          modalFunctionsBtnContainer.setAttribute("data-my-list", false)
          document.getElementById(`ml__movie-modal-my-list-icon`).classList.add("fa-plus")            
          
        } else if (movie.in_list) {
          modalFunctionsBtnContainer.setAttribute("data-my-list", true)
          document.getElementById(`ml__movie-modal-my-list-icon`).classList.add("fa-check")
          // show form
          document.getElementById("ml__edit-movie-form").classList.add("show")
        }

        if (movie.favorite) {
          document.getElementById(`ml__movie-modal-fav-icon`).classList.add("fas")
        } else {
          document.getElementById(`ml__movie-modal-fav-icon`).classList.add("far")
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

        // populate form with create route
        document.getElementById("ml__edit-movie-form").setAttribute("action", `/movies/${movie["imdbID"]}`)

        // hidden fields. does not rely on in-list. used for update form/route
        document.getElementById("imdb_id").value = movie["imdbID"]
        document.getElementById("title").value = movie["Title"]
        document.getElementById("release_year").value = movie["Year"]
        document.getElementById("imdb_img").value = movie["Poster"]
        document.getElementById("date_added").value = movie["date_added"]

        // shown fields. relies on in-list. used for update form/route
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

function closeMovieDetailModal() {

  // remove event listeners
  modalFunctionsBtnContainer.removeEventListener("click", handleMovieFunctionsClick)

  // hide the modal
  movieDetailModal.classList.remove("show")

  // remove functions container atts
  modalFunctionsBtnContainer.removeAttribute("data-id")
  modalFunctionsBtnContainer.removeAttribute("data-title")
  modalFunctionsBtnContainer.removeAttribute("data-release-year")
  modalFunctionsBtnContainer.removeAttribute("data-img")

  modalFunctionsBtnContainer.removeAttribute("data-my-list")

  // // reset all icons
  document.getElementById(`ml__movie-modal-my-list-icon`).classList.remove("fa-plus")
  document.getElementById(`ml__movie-modal-my-list-icon`).classList.remove("fa-check")
  document.getElementById(`ml__movie-modal-fav-icon`).classList.remove("fas")
  document.getElementById(`ml__movie-modal-fav-icon`).classList.remove("far")

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

  // reset form
  document.getElementById("ml__edit-movie-form").classList.remove("show")
  document.getElementById("ml__edit-movie-form").removeAttribute("action")

  // reset hidden fields
  document.getElementById("imdb_id").value = ""
  document.getElementById("title").value = ""
  document.getElementById("release_year").value = ""
  document.getElementById("imdb_img").value = ""
  document.getElementById("date_added").value = ""

  // reset not hidden fields
  document.getElementById("platform").value = ""
  document.getElementById("date_viewed").value = ""
}