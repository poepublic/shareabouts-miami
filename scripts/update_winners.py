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


reader = csv.DictReader(stdin)
data = list(reader)

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true'}

PSC_YEAR = 2018
IDEAS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2018/places'

pages = download_all_pages(IDEAS_URL)
ideas_by_id = {idea['id']: idea for ideas in pages for idea in ideas['features']}
for row in data:
    idea_id = row['ID']
    idea = ideas_by_id.get(idea_id)
    idea_props = idea['properties']

    idea_update = {'ff': 2, 'pscyear': PSC_YEAR}

    # Save the original title and submitter if they're not already saved.
    if 'original_title' not in idea_props:
        idea_update['original_title'] = idea_props['title']

    if 'original_submitter' not in idea_props:
        idea_update['original_submitter'] = idea_props['submitter'] or idea_props['submitter_name']

    # Set the new title and submitter name. Only set the submitter name if it's
    # different than the current one.
    idea_update['title'] = row['New Project Title']

    if idea_props['submitter'] is None:
        idea_update['submitter_name'] = row['New Submitter']
    elif idea_props['submitter']['name'] != row['New Submitter']:
        idea_update['submitter'] = None
        idea_update['submitter_name'] = row['New Submitter']

    # Upload the updated idea.
    url = idea_props['url']
    request_with_retries('patch', url, session=session,
        data=json.dumps({'type': 'Feature', 'properties': idea_update})
    )
