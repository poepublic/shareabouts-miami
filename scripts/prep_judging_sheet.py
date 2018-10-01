"""
Usage:

    USERNAME='...' PASSWORD='...' python prep_judging_sheet.py > sheet.csv

"""

import collections
import csv
import itertools
import json
import os
import requests
from request_utils import download_all_pages
from sys import stderr, stdout


USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true'}

IDEAS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2018/places?include_private'
REVIEWS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2018/ratings'

idea_pages = download_all_pages(IDEAS_URL, session=session)
rating_pages = download_all_pages(REVIEWS_URL, session=session)

# Don't include invisible
header = [
    'ID',
    'URL',  # On the miami site
    'Title',
    'Category',
    'Description',
    'Detail',
    'Submitter',  # Fall back to submitter_name
    'Submitter Email',
    'Approximate Address',
    '# of Likes',
    '# of Comments',
    'Judge Group',
]

ratings_by_idea_url = collections.defaultdict(list)
seen_judges = set()
rows = []
total_ratings = collections.defaultdict(int)
total_judged = collections.defaultdict(int)

for ratings in rating_pages:
    for rating in ratings['results']:
        idea_url = rating['place']
        ratings_by_idea_url[idea_url].append(rating)

for ideas in idea_pages:
    for idea in ideas['features']:
        row = {}
        props = idea['properties']

        if 'judgeGroup' not in props:
            continue

        row['ID'] = idea['id']
        row['URL'] = f'https://www.publicspacechallenge.org/place/{row["ID"]}'
        row['Title'] = props['title']
        row['Category'] = props['location_type']
        row['Description'] = props['description']
        row['Detail'] = props['details']
        row['Submitter'] = props['submitter']['name'] if props['submitter'] else props.get('submitter_name', '')
        row['Submitter Email'] = props['private-email']
        row['Approximate Address'] = props['address']
        row['# of Likes'] = props['submission_sets'].get('support', {}).get('length', 0)
        row['# of Comments'] = props['submission_sets'].get('comments', {}).get('length', 0)
        row['Judge Group'] = props['judgeGroup'][-1]

        for rating in ratings_by_idea_url[props['url']]:
            judge = rating['submitter']['username']
            if judge == 'mjumbewu': continue
            total_ratings[judge] += 1

            if f'{judge} Score' in row:
                print(f'{judge} has more than one rating for {row["ID"]}; keeping the latest one.', file=stderr)
            else:
                optout = rating.get('optout', '')
                row[f'{judge} Score'] = rating.get('rating', '') if not optout else ''
                row[f'{judge} Opt Out'] = optout
                row[f'{judge} Opt Out Reason'] = rating.get('optout_reason', '') if optout else ''
                total_judged[judge] += 1

            if judge not in seen_judges:
                header.append(f'{judge} Score')
                header.append(f'{judge} Opt Out')
                header.append(f'{judge} Opt Out Reason')
                seen_judges.add(judge)

        rows.append(row)

writer = csv.DictWriter(stdout, header)
writer.writeheader()
writer.writerows(rows)

print('\nCount of total ratings (including duplicates)', file=stderr)
print(json.dumps(total_ratings, indent=2, sort_keys=True), file=stderr)
print('\nCount of total ideas judged (no duplicates)', file=stderr)
print(json.dumps(total_judged, indent=2, sort_keys=True), file=stderr)
