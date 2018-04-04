"""
Usage:

    USERNAME='...' PASSWORD='...' python upload_data.py < data.geojson

"""

import os
import requests
from request_utils import download_all_pages, request_with_retries
from sys import stderr


USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true'}

WINNERS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc-winners/places'

pages = download_all_pages(WINNERS_URL)
for page in pages:
    for feature in page['features']:
        url = feature['properties']['url']
        request_with_retries('delete', url, session=session)
