"""
For uploading data to the site listing all-time winners.

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

    feature['properties']['original_submitter'] = feature['properties'].pop('submitter')
    feature['properties']['original_attachments'] = feature['properties'].pop('attachments')
    feature['properties']['original_submission_sets'] = feature['properties'].pop('submission_sets')

    if idea:
        url = idea['properties']['url']
        request_with_retries('put', url, session=session, data=json.dumps(feature))
    else:
        url = WINNERS_URL
        request_with_retries('post', url, session=session, data=json.dumps(feature))
