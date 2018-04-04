"""
Usage:

    USERNAME='...' PASSWORD='...' python upload_data.py < data.geojson

"""

import json
import os
import requests
from request_utils import download_all_pages, request_with_retries
from sys import stderr, stdin


data = json.load(stdin)

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true'}

WINNERS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc-winners/places'

pages = download_all_pages(WINNERS_URL)
ideas_by_id = {idea['properties']['original_id']: idea for ideas in pages for idea in ideas['features']}
for feature in data['features']:
    fid = feature['properties']['original_id'] = feature.pop('id')
    idea = ideas_by_id.get(fid)

    if idea:
        url = idea['properties']['url']
        request_with_retries('patch', url, session=session, data=json.dumps(feature))
    else:
        url = WINNERS_URL
        feature['properties'].pop('submitter')
        request_with_retries('post', url, session=session, data=json.dumps(feature))
