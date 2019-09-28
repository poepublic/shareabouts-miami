"""
Usage:

    USERNAME='...' PASSWORD='...' python3 make_winners_page.py \
        < [year]winners.csv \
        > ../src/flavors/ourmiami[year]/jstemplates/pages/winners.html

The only required columns in the winners.csv file is 'ID'.

"""

import csv
import html
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

IDEAS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2019/places'

# Read the finalists in CSV format from stdin.
reader = csv.DictReader(stdin)
winner_data = list(reader)

# Download all the ideas and map them by ID
pages = download_all_pages(IDEAS_URL, session=session)
ideas_by_id = {str(idea['id']): idea for ideas in pages for idea in ideas['features'] if idea['id']}

def html_escape(s):
    # First take care of common characters
    s = html.escape(s)

    # Then replace other non-ascii characters
    s = s.encode('ascii', 'xmlcharrefreplace').decode('ascii')

    return s

ideas = []
for row in winner_data:
    fid = str(row['ID'])
    idea = ideas_by_id.get(fid)

    if not idea:
        print(f'Idea with ID {fid!r} not found.', file=stderr)
        continue

    ideas.append(idea)

# Output the page header
print(f'''<h3>Meet the 2019 Challenge Winners</h3>''')
print(f'''''')

def alphanum(s):
    return ''.join(c for c in s if c.isalnum())

#for idea in sorted(ideas, key=lambda idea: alphanum(idea['properties']['title']).lower()):
for idea in ideas:
    idea_id = idea['id']
    title = html_escape(idea['properties']['title']).strip().replace('\r\n', ': ').replace('\n', ': ')
    submitter = html_escape(idea['properties']['submitter'].get('name') if idea['properties']['submitter'] else idea['properties'].get('submitter_name')).strip()
    print(f'''<p><strong><a href="/place/{idea_id}">{title}</a></strong> submitted by {submitter}</p>''')
