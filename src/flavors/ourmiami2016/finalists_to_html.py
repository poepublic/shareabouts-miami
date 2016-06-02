#!/usr/bin/env python

import csv

finalists = []
with open('finalists.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    finalists = list(reader)

finalist_p = ("<p><strong>"
              "<a href='/place/{id}'>{title}</a>"
              "</strong> submitted by {submitter}.</p>")

for finalist in finalists:
    # import pdb; pdb.set_trace()
    print(finalist_p.format(
        id = finalist['ID'],
        title=finalist['Title Name Change'] 
            or finalist['Title'],
        submitter=finalist['Submitter Name Change'] 
            or finalist['Manual Submitter Name'] 
            or finalist['Social Submitter Name'])
    )
