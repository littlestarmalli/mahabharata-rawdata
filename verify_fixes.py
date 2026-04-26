import json

d = json.load(open('output/json/bori_official.json', encoding='utf-8'))
for p in d['parvas']:
    for sp in p['sub_parvas']:
        if sp['number'] in [85, 91]:
            print('bori sp%d %s: adhyayas=%s, shlokas=%s' % (sp['number'], sp['name'], sp['adhyayas'], sp['shlokas']))

d2 = json.load(open('output/json/introduction.json', encoding='utf-8'))
for p in d2['parvas']:
    for sp in p.get('sub_parvas', []):
        if sp['number'] in [85, 91]:
            print('intro sp%d %s: adhyayas=%s, shlokas=%s' % (sp['number'], sp['name'], sp['adhyayas'], sp['shlokas']))

d3 = json.load(open('output/json/translation_data.json', encoding='utf-8'))
for p in d3['parvas']:
    for sp in p['sub_parvas']:
        if sp['number'] in [84, 85, 86, 91]:
            print('trans sp%d %s: chapters=%s, shlokas=%s' % (sp['number'], sp['name'], sp['chapters'], sp['shlokas_from_headers']))
