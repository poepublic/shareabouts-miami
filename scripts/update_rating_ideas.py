"""
Usage:

    USERNAME='...' PASSWORD='...' python update_rating_ideas.py < ideas_to_rate.csv

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

IDEAS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2018/places?include_private'

# Read the ideas to rate in CSV format from stdin to get the ids of the ideas
# to rate.
reader = csv.DictReader(stdin)
review_data = list(reader)
ids_to_rate = [int(idea['ID']) for idea in review_data]

# Download all the ideas and map them by ID
pages = download_all_pages(IDEAS_URL, session=session)
ideas_by_id = {idea['id']: idea for ideas in pages for idea in ideas['features'] if idea['id']}

# Assign ideas to the appropriate judging groups
assignments = {
    'PublicSpaces': 'judges-1',
    'GreenwaysAndBlueways': 'judges-2',
    'ParksAndNaturalAreas': 'judges-2',
    'SafeRoutesToParks': 'judges-1',
}

for idea_id in ids_to_rate:
    feature = ideas_by_id[idea_id]
    category = feature['properties']['location_type']
    print(f'Idea {idea_id} ({category}) to {assignments[category]}')
    feature['properties']['judgeGroup'] = assignments[category]

# *****************************************************************************
# NOTE: We're also going to do some custom logic so that the SafeRoutesToParks
# ideas get evenly distributed to keep the size of the judging groups even.
# This is definitely NOT something to keep from year to year.
g1_size = sum(1 for _, feature in ideas_by_id.items() if feature['properties'].get('judgeGroup') == 'judges-1')
g2_size = sum(1 for _, feature in ideas_by_id.items() if feature['properties'].get('judgeGroup') == 'judges-2')
print(f'Group sizes: 1 - {g1_size}, 2 - {g2_size}')

for idea_id in ids_to_rate:
    if g2_size >= g1_size:
        break

    feature = ideas_by_id[idea_id]
    category = feature['properties']['location_type']
    if category == 'SafeRoutesToParks':
        print(f'Moving {idea_id} ({category}) to judges-2')
        feature['properties']['judgeGroup'] = 'judges-2'
        g1_size -= 1
        g2_size += 1
#
# *****************************************************************************

# Upload the grouped ideas
for index, idea_id in enumerate(ids_to_rate):
    feature = ideas_by_id[idea_id]

    url = feature['properties']['url']
    print(f'{index + 1} - Patching {url}')
    request_with_retries('patch', url, session=session, data=json.dumps(feature))
