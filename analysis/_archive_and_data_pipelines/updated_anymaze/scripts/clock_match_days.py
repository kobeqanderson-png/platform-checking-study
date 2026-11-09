"""Matches recording runs to AnyMaze tests by wall clock, using start times from the .szd files, and checks AnyMaze's duration against when the rat settled.
Usage: clock_match_days.py <tracking_pilot> <raw Check folder> <audit.csv> <log folder> <work folder> <days, e.g. 1,2,3>"""
import contextlib, csv, datetime as dt, glob, io, os, re, runpy, sys
import numpy as np
from scipy.signal import medfilt
P, RAW, AUDIT, LOGS, W, DAYS = sys.argv[1:]
LOG = {1: 'bdb3nt5ap', 2: 'ba4m8e3at', 3: 'bhqef3ln6', 5: 'bnmm6tpty'}
D7LOG = os.path.join(W, 'd7_pools.log')
open(D7LOG, 'w').write('pool source px=(930,551,r511)\npool source px=(989,553,r510)\npool source px=(989,552,r510)\n')
ST = list(csv.DictReader(open(os.path.join(P, 'szd_test_starts.csv'), newline='')))
for day in [int(x) for x in DAYS.split(',')]:
    out = os.path.join(W, f'cm_d{day}.csv'); argv = sys.argv; sys.argv = ['match_day.py', str(day), os.path.join(P, f'tracks_d{day}'), D7LOG if day == 7 else os.path.join(LOGS, LOG[day] + '.output'), os.path.join(RAW, f'KAcd{day}.csv'), AUDIT, out]
    with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path(os.path.join(P, 'match_day.py'))
    sys.argv = argv; runs, TR, R, k, PX, PY = g['runs'], g['TR'], g['R'], g['k'], g['PX'], g['PY']; M = [g['measure'](r, R) for r in runs]
    names = sorted(glob.glob(os.path.join(P, f'tracks_d{day}', 'file*.csv')), key=lambda f: int(re.search(r'file(\d+)_', f).group(1)))
    FS = {f"file{i}": dt.datetime.strptime('2026-11-04 ' + re.search(r'_(\d\d-\d\d-\d\d)', os.path.basename(n)).group(1), '%Y-%m-%d %H-%M-%S') if day == 7 else dt.datetime.strptime(re.search(r'(\d{4}-\d\d-\d\d[ _]\d\d-\d\d-\d\d)', os.path.basename(n)).group(1).replace('_', ' '), '%Y-%m-%d %H-%M-%S') for i, n in enumerate(names, 1)}
    W0 = min(FS.values()); wall = lambda r, m: (FS[r['file']] - W0).total_seconds() + (m['release'] if m else r['start'])
    A = sorted(csv.DictReader(open(os.path.join(RAW, f'KAcd{day}.csv'), encoding='latin-1', newline='')), key=lambda r: int(r['Test']))
    S = sorted(dt.datetime.fromisoformat(r['start']) for r in ST if r['day'] == str(day)); assert len(S) == len(A), (len(S), len(A))
    s = [(x - W0).total_seconds() for x in S]; rw = np.array([wall(r, m) for r, m in zip(runs, M)])
    # Clock difference between the AnyMaze computer and the camera: the value that puts most starts next to a release.
    cand = [x - y for x in s for y in rw if abs(x - y) < 600]; h, e = np.histogram(cand, bins=np.arange(-600, 601, 2)); off = float(e[np.argmax(h)] + 1); off = float(np.median([c for c in cand if abs(c - off) < 4]))
    rows = []; PB = {int(r['test']): r for r in csv.DictReader(open(os.path.join(P, 'd7_tracker_vs_anymaze.csv') if day == 7 else out, newline=''))}
    for a, x in zip(A, s):
        t = int(a['Test']); d = float(a['Duration (s)']); j = int(np.argmin(abs(rw + off - x))); r, m = runs[j], M[j]; lag = x - (rw[j] + off); p = TR[r['file']]
        st = None; path = ''; lat = None
        if m:
            rel = m['release']; q = (p['t'] >= rel) & (p['t'] <= r['end']) & ~np.isnan(p['x']); tt, D = p['t'][q] - rel, np.hypot(p['x'][q] - PX, p['y'][q] - PY)
            for i in range(len(tt)):
                w = (tt >= tt[i]) & (tt <= tt[i] + 2)
                if tt[-1] >= tt[i] + 2 and D[w].max() < 70: st = float(tt[i]); break
        b = PB.get(t); agree = bool(b and b['release_s'] and m and b['file'] == r['file'] and abs(float(b['release_s']) - m['release']) < .5)
        rows.append(dict(test=t, rat=a['Animal'], file=r['file'], release_s=round(m['release'], 1) if m else '', run_end_s=round(r['end'], 1), lag_s=round(lag, 1), anymaze_s=d, anymaze_cm=a['Distance (cm)'], end_by_clock_s=round(d + lag, 1), settle_s=round(st, 1) if st is not None else '', run_len_s=round(r['end'] - (m['release'] if m else r['start']), 1), old_match_agrees=agree, old_tracker_s=b['tracker_s'] if b else ''))
    with open(os.path.join(P, f'd{day}_clock_match.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    L = np.array([r['lag_s'] for r in rows]); good = [r for r in rows if abs(r['lag_s']) < 30]
    E = [r['settle_s'] - r['end_by_clock_s'] for r in good if r['settle_s'] != '' and r['anymaze_s'] < 29.5 and abs(r['lag_s']) < 3.5]
    print(f'\n=== d{day}: clock offset {off:+.1f} s; start within 3.5 s of a release {int((abs(L) < 3.5).sum())}/{len(L)}, no nearby run (over 30 s) {int((abs(L) >= 30).sum())}; old match agrees {sum(r["old_match_agrees"] for r in rows)}; settle minus clock end median {np.median(E):+.2f} IQR {np.percentile(E, 25):+.2f} to {np.percentile(E, 75):+.2f} n={len(E)}')
    print(' timer candidates (lag 3.5-30 s):')
    for r in rows:
        if 3.5 <= abs(r['lag_s']) < 30: print(f"  t{r['test']} rat{r['rat']} AM {r['anymaze_s']}s {r['anymaze_cm']}cm lag {r['lag_s']:+} clock_end {r['end_by_clock_s']} settle {r['settle_s']} run {r['run_len_s']} oldmatch {r['old_match_agrees']}")
    print(' start lines up, duration ended before settle by over 4 s:', [(r['test'], r['anymaze_s'], r['settle_s'], r['old_match_agrees']) for r in rows if abs(r['lag_s']) < 3.5 and r['anymaze_s'] < 29 and r['settle_s'] != '' and r['settle_s'] - r['end_by_clock_s'] > 4])
    print(' old match wrong (clock points to a different run):', [(r['test'], r['old_tracker_s'], r['settle_s'], r['anymaze_s']) for r in rows if abs(r['lag_s']) < 3.5 and not r['old_match_agrees']])
