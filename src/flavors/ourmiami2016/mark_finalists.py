#!/usr/bin/env python

import csv
import json
import requests
import sys

finalists = []
with open('finalists.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    finalists = list(reader)

url_tmp = ('http://shareaboutsapi2.herokuapp.com/api/v2/'
           'ourmiami/datasets/psc2016/places/{ID}')

username = sys.argv[1]
password = sys.argv[2]

for finalist in finalists:
    url = url_tmp.format(**finalist)

    update = {'type': 'Feature', 'properties': {'ff': 1}}
    changed_name = finalist['Title Name Change']
    changed_submitter = finalist['Submitter Name Change']
    if changed_name:
        update['properties']['title'] = changed_name
    if changed_submitter:
        update['properties']['submitter_name'] = changed_submitter
        update['properties']['submitter'] = None

    print(json.dumps(update))

    response = requests.patch(url,
        headers={'Content-type': 'application/json', 'X-Shareabouts-silent': 'true'},
        auth=(username, password),
        data=json.dumps(update))

    if response.status_code != 200:
        print('failed to update {}'.format(url))
        import pdb; pdb.set_trace()
    else:
        print('updated {}'.format(url))