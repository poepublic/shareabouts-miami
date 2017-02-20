import csv
from pybars import Compiler
c = Compiler()
s = """<h3>Meet the 2015 challenge winners</h3>

{{#each row}}<p><strong><a href='/place/{{ id }}'>{{ title }}</a></strong> submitted by {{ submitter }}.</p>
{{/each}}"""
t = c.compile(s)

with open('2015-winners.csv', 'rU', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    row = list(reader)

for r in row:
    r['title'] = r['title'].strip()
    r['submitter'] = r['submitter'].rstrip(' .')

print(t({"row": row}))
