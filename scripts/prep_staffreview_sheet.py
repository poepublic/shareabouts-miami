"""
Usage:

    USERNAME='...' PASSWORD='...' python prep_staffreview_sheet.py > sheet.csv

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
REVIEWS_URL = 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2018/reviews'

idea_pages = download_all_pages(IDEAS_URL, session=session)
review_pages = download_all_pages(REVIEWS_URL, session=session)

# Don't include invisible
header = [
    'ID',
    'URL',  # On the miami site
    'Title',
    'Category',
    'Description',
    'Detail',
    'Submitter',  # Fall back to submitter_name
    'Approximate Address',
    '# of Likes',
    '# of Comments',
]

reviews_by_idea_url = collections.defaultdict(list)
seen_reviewers = set()
rows = []
total_reviews = collections.defaultdict(int)
total_reviewed = collections.defaultdict(int)

for reviews in review_pages:
    for review in reviews['results']:
        idea_url = review['place']
        reviews_by_idea_url[idea_url].append(review)

for ideas in idea_pages:
    for idea in ideas['features']:
        row = {}
        props = idea['properties']

        row['ID'] = idea['id']
        row['URL'] = f'https://www.publicspacechallenge.org/place/{row["ID"]}'
        row['Title'] = props['title']
        row['Category'] = props['location_type']
        row['Description'] = props['description']
        row['Detail'] = props['details']
        row['Submitter'] = props['submitter']['name'] if props['submitter'] else props.get('submitter_name', '')
        row['Approximate Address'] = props['address']
        row['# of Likes'] = props['submission_sets'].get('support', {}).get('length', 0)
        row['# of Comments'] = props['submission_sets'].get('comments', {}).get('length', 0)

        for review in reviews_by_idea_url[props['url']]:
            reviewer = review['submitter']['username']
            total_reviews[reviewer] += 1

            if f'{reviewer} Decision' in row:
                print(f'{reviewer} has more than one review for {row["ID"]}; keeping the latest one.', file=stderr)
            else:
                row[f'{reviewer} Decision'] = review.get('review', '')
                row[f'{reviewer} Notes'] = review.get('review_notes', '')
                total_reviewed[reviewer] += 1

            if reviewer not in seen_reviewers:
                header.append(f'{reviewer} Decision')
                header.append(f'{reviewer} Notes')
                seen_reviewers.add(reviewer)

        rows.append(row)

writer = csv.DictWriter(stdout, header)
writer.writeheader()
writer.writerows(rows)

print('\nCount of total reviews (including duplicates)', file=stderr)
print(json.dumps(total_reviews, indent=2, sort_keys=True), file=stderr)
print('\nCount of total ideas reviewed (no duplicates)', file=stderr)
print(json.dumps(total_reviewed, indent=2, sort_keys=True), file=stderr)
