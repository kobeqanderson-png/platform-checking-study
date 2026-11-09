from pathlib import Path
import json, re, hashlib, zipfile
import numpy as np
from scipy.stats import spearmanr
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SITE=ROOT/'dlc_cleaned/site'
p=json.loads((HERE/'exports/profile_data.json').read_text())
for src in p['sources']:
    assert hashlib.sha256((ROOT/src['file']).read_bytes()).hexdigest()==src['sha256']
for s in p['sessions']:
    assert s['area_successes']<=s['complete_excursions']
    assert s['repeat_p1_trips']==max(0,s['area_successes']-1)
    returned=[]
    for e in s['return_timeline']:
        assert 0<=e['start']<e['end']<=120
        assert not e['complete'] or (e['returned'] and e['onset_known'])
        if e['p1_entry_s'] is not None:assert e['start']<=e['p1_entry_s']<e['end']
        if e['returned']:returned.append(e['end'])
    assert len(returned)==len(set(returned))==s['observed_placement_returns']
    assert len([e for e in s['return_timeline'] if e['complete']])==s['complete_excursions']
    if s['complete_excursions']==0:assert s['area_success_pct'] is None and s['median_round_trip_s'] is None
    if s['cohort']=='SP1':assert not s['training']
for name in ['profiles.html','explorer.html','index.html']:
    h=(SITE/name).read_text(encoding='utf-8')
    for link in re.findall(r'(?:src|href)="([^"#]+)"',h):
        if not re.match(r'^(https?:|data:)',link):assert (SITE/link.split('?')[0]).exists(),(name,link)
assert 'tail' not in (SITE/'profiles.html').read_text(encoding='utf-8').lower().replace('details','').replace('detail','')
expected=[]
for cond in p['labels']:
    for x,y in [('head_sweeps_per_min','area_successes'),('head_sweeps_per_min','area_success_pct')]:
        g=[s for s in p['sessions'] if s['cond']==cond and s[x] is not None and s[y] is not None]
        expected.append(dict(cond=cond,x=x,y=y,n=len(g),rho=float(spearmanr([s[x] for s in g],[s[y] for s in g]).statistic)))
(HERE/'expected_correlations.json').write_text(json.dumps(expected))
files=[dict(file=str(f.relative_to(SITE)).replace('\\','/'),sha=hashlib.sha1(f.read_bytes()).hexdigest(),size=f.stat().st_size) for f in SITE.rglob('*') if f.is_file() and not any(part.startswith('.') for part in f.relative_to(SITE).parts)]
(HERE/'deploy_files.json').write_text(json.dumps(files))
with zipfile.ZipFile(ROOT/'dlc_cleaned/platform_checking_site.zip','w',zipfile.ZIP_DEFLATED) as out:
    for f in files:out.write(SITE/f['file'],f['file'])
print(json.dumps(dict(sessions=len(p['sessions']),animals=len({s['animal_id'] for s in p['sessions']}),site_files=len(files),repetition_events=sum(len(s['return_timeline']) for s in p['sessions']),checks='source hashes, identities, event times, no duplicate returns, missingness, links, offline archive passed')))
