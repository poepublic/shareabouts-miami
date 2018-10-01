"""
For updating winning ideas at the end of the challenge.

Usage:

    USERNAME='...' PASSWORD='...' python upload_data.py < winners.csv

"""

import csv
import json
import os
import requests
from request_utils import download_all_pages, request_with_retries
from sys import stderr, stdin


data = csv.DictReader(stdin)

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true'}

IDEAS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2018/places'

pages = download_all_pages(IDEAS_URL)
ideas_by_id = {idea['id']: idea for ideas in pages for idea in ideas['features']}
for row in data:
    idea_id = row['ID']
    idea = ideas_by_id.get(idea_id)
    props = idea['properties']

    # Save the original title and submitter if they're not already saved.
    if 'original_title' not in props:
        props['original_title'] = props['title']

    if 'original_submitter' not in props:
        props['original_submitter'] = props['submitter'] or props['submitter_name']

    # Set the new title and submitter name. Only set the submitter name if it's
    # different than the current one.
    props['title'] = row['New Project Title']

    if props['submitter'] is None:
        props['submitter_name'] = idea['New Submitter']
    elif props['submitter']['name'] != idea['New Submitter']:
        props['submitter'] = None
        props['submitter_name'] = idea['New Submitter']

    # Upload the updated idea.
    if idea:
        url = idea['properties']['url']
        request_with_retries('put', url, session=session, data=json.dumps(idea))
    else:
        url = IDEAS_URL
        request_with_retries('post', url, session=session, data=json.dumps(idea))
