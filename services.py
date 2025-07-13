"""Handle connecting to our external api"""

import os
import requests


API_KEY = os.environ.get('OMDB_API_KEY')
API_BASE_URL = f"http://www.omdbapi.com/?apikey={API_KEY}&"


def movie_search(search_term, page=1):
    """Make the search request to the omdb movie database"""

    api_url = f"{API_BASE_URL}s={search_term}&page={page}"

    api_resp = requests.get(api_url)

    # the api returns a response with json
    # but we need to convert to a python dictionary
    results = api_resp.json()

    # import pdb
    # pdb.set_trace()

    return results


def movie_search_by_id(movie_id):
    """Make search request to the omdb movie database using the omdb movie id"""

    api_url = f"{API_BASE_URL}i={movie_id}"

    api_resp = requests.get(api_url)

    # the api returns a response with json
    # but we need to convert to a python dictionary
    results = api_resp.json()

    return results
