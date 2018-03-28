"""
Usage:

    USERNAME='...' PASSWORD='...' python import_past_winners > past_winners.geojson

"""

from itertools import chain
import json
import os
import requests
from sys import stderr


YEARS = [
    ('2013', 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/ourmiami/places'),
    ('2014', 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2014/places'),
    ('2015', 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2015/places'),
    ('2016', 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2016/places'),
    ('2017', 'https://shareaboutsapi.poepublic.com/api/v2/ourmiami/datasets/psc2017/places'),
]

WINNERS_2013 = {
    48892,
    47187,
    49940,
    49436,
    47513,
    50818,
    50860,
    45863,
    51279,
    48931,
    50520,
    45690,
    49984,
    49313,
    45559,
}

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']


def download_with_retries(url, retries=5, session=None):
    session = session or requests
    responses = []
    for _ in range(retries):
        print(f'Trying to download {url}', file=stderr)
        response = session.get(url)
        if response.status_code in (200, 204):
            return response
        responses.append(response)
    status_codes = [r.status_code for r in responses]
    raise Exception(f'Failed to download {url}. Response codes: {status_codes}')


def download_all_pages(url, session=None):
    pages = []
    while url:
        response = download_with_retries(url, session=session)
        page = response.json()
        pages.append(page)
        url = page['metadata']['next']
    return pages


def is_winner(feature):
    return (
        feature['properties'].get('ff') in (2, '2') or
        feature['id'] in WINNERS_2013
    )


data = {
    'type': 'FeatureCollection',
    'features': []
}

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
for year, url in YEARS:
    pages = download_all_pages(url, session=session)
    features = chain.from_iterable(p['features'] for p in pages)
    winners = list(filter(is_winner, features))

    for f in winners:
        f['properties']['pscyear'] = year
        f['properties']['category'] = f['properties']['location_type']
        f['properties']['category'] = f['properties']['ff'] = '2'
        f['properties']['location_type'] = f'Winner{year}'

    print(f'{len(winners)} winners from {year}', file=stderr)
    data['features'].extend(winners)

print(json.dumps(data, indent=1, sort_keys=True))
