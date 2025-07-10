// const movieSearchForm = document.getElementById("movieSearchForm")
// const csrfToken = document.getElementById("csrf_token")
// const searchTerm = document.getElementById("search_term")
// const submitButton = document.getElementById("submitButton")

const searchResults = document.getElementById('searchResults');

/**
 * Search functionality
 */

// movieSearchForm.addEventListener('submit', function(e) {
//   e.preventDefault();

//   searchResults.innerHTML = "";

//   const params = new URLSearchParams();
//   params.append('csrf_token', csrfToken.value);
//   params.append('search_term', searchTerm.value);

//   const config = {
//     headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
//   }

//   /**
//    * movie search request for first page of results
//    */

//   axios.post("/movie-search", params, config)
//   .then(function(resp){
//     data = resp.data;

//     let newH2 = document.createElement("h2")
//     newH2.innerText = `Search results for "${searchTerm.value}"`
//     searchResults.appendChild(newH2)

//     let newUL = document.createElement("ul");
//     newUL.classList.add("ml__search-results")

//     data.forEach(element => {
//       let newLI = document.createElement("li");
//       newLI.classList.add("ml__search-result");

//       let newA = document.createElement("a");
//       newA.setAttribute("href", `/movie/${element['imdbID']}`)

//       let newIMG = document.createElement("img")
//       newIMG.classList.add("ml__search-result--image");
//       if (element["Poster"] === "N/A" ) {
//         newIMG.setAttribute("src", "");
//       } else {
//         newIMG.setAttribute("src", element["Poster"]);
//       }
//       newA.appendChild(newIMG)

//       let newH3 = document.createElement("h3");
//       newH3.classList.add("ml__search-result--title");
//       newH3.innerText = element["Title"];
//       newA.appendChild(newH3)

//       let newP = document.createElement("p");
//       newP.classList.add("ml__search-result--year");
//       newP.innerText = "(" + element["Year"] + ")";
//       newA.appendChild(newP);

//       newLI.appendChild(newA);

//       // if the movie is already in our list, create a span with a note
//       if (element['ml_inList']) {
//         const newSpan = document.createElement("span")
//         newSpan.classList.add("ml__search-result--movie-in-list")
//         newSpan.innerText = "Already in My List";
//         newLI.appendChild(newSpan)
//       // if the movie is not in our list, create an "add" button
//       } else {
//         // create our "add" button and append to form
//         let newButton = document.createElement("button");
//         newButton.classList.add("ml__search-result--add-button")
//         newButton.setAttribute("data-id", element['imdbID']);
//         newButton.setAttribute("data-title", element['Title'])
//         newButton.setAttribute("data-year", element['Year'])
//         newButton.setAttribute("data-img", element['Poster'])
//         newButton.innerText = "Add to My List";
//         newLI.appendChild(newButton);
//       }

//       // append our completed li to the ul
//       newUL.appendChild(newLI)
//     });

//     // append our UL to the searchResults div
//     searchResults.appendChild(newUL)

//     // append our pagination our UL

//     searchTerm.value = ""

//   })
//   .catch(function(err){
//       console.log(err)
//   })
// })

/**
 * Add movie functionality
 */
searchResults.addEventListener('click', function (e) {
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
      .post(`/movie/${imdb_id}`, JSON.stringify(params), config)
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
