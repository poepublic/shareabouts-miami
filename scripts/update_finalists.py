"""
Usage:

    USERNAME='...' PASSWORD='...' python upload_data.py < data.geojson

"""

import csv
import json
import os
import requests
from request_utils import download_all_pages, request_with_retries
from sys import stderr, stdin


USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true'}

PSC_YEAR = 2019
IDEAS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2019/places'

# Read the finalists in CSV format from stdin.
reader = csv.DictReader(stdin)
finalist_data = list(reader)

# Download all the ideas and map them by ID
pages = download_all_pages(IDEAS_URL, session=session)
ideas_by_id = {str(idea['id']): idea for ideas in pages for idea in ideas['features'] if idea['id']}

for count, row in enumerate(finalist_data):
    fid = str(row['ID'])
    idea = ideas_by_id.get(fid)

    if not idea:
        print(f'Idea with ID {fid!r} not found.', file=stderr)
        continue

    url = idea['properties']['url']
    print(f'Marking #{count + 1} - {url}', file=stderr)
    request_with_retries('patch', url, session=session,
        data=json.dumps({'type': 'Feature', 'properties': {'ff': 1, 'pscyear': PSC_YEAR}}),
    )
