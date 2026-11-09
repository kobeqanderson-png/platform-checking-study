"""Matches d7 rat-present runs to AnyMaze trials, then scores agreement.
Rats stay in AnyMaze order and are matched as blocks of 4 runs. A whole rat or a stray run can be skipped; trials cannot be reordered.
Usage: d7_match.py <track-folder> <segments.csv> <KAcd7.csv> <out.csv>"""
import csv, os, sys
import numpy as np
from scipy.signal import medfilt
tracks, segs, raw, out = sys.argv[1:]
POOL = {'file1': (930, 551), 'file2': (989, 553), 'file3': (989, 552)}
NAMES = {'file1': 'file1_09-49-40.csv', 'file2': 'file2_10-44-54.csv', 'file3': 'file3_11-07-52.csv'}
FLAGGED = {1, 20, 21, 23, 92, 98, 100}
TR = {}
for k, n in NAMES.items():
    R = list(csv.DictReader(open(os.path.join(tracks, n), newline='')))
    TR[k] = dict(t=np.array([float(r['t_s']) for r in R]), a=np.array([float(r['area']) for r in R]),
                 x=np.array([float(r['x_px']) if r['x_px'] else np.nan for r in R]) - POOL[k][0],
                 y=np.array([float(r['y_px']) if r['y_px'] else np.nan for r in R]) - POOL[k][1])
# Platform: densest resting spot in pool-centred coordinates.
xs, ys = [], []
for p in TR.values():
    still = np.hypot(p['x'][10:] - p['x'][:-10], p['y'][10:] - p['y'][:-10]) < 8
    xs.append(p['x'][10:][still]); ys.append(p['y'][10:][still])
xs, ys = np.concatenate(xs), np.concatenate(ys)
h, ex, ey = np.histogram2d(xs, ys, bins=np.arange(-520, 521, 20))
i, j = np.unravel_index(np.argmax(h), h.shape)
sel = (np.abs(xs - ex[i] - 10) < 40) & (np.abs(ys - ey[j] - 10) < 40)
PX, PY = float(np.median(xs[sel])), float(np.median(ys[sel]))
print(f'platform in pool-centred px: ({PX:.0f},{PY:.0f}); share of still frames there: {100 * sel.mean():.0f}%')
runs = [r for r in csv.DictReader(open(segs, newline='')) if float(r['dur']) >= 5]
def measure(r, R):
    p = TR[r['file']]; m = (p['t'] >= float(r['start'])) & (p['t'] <= float(r['end']))
    t, x, y, a = p['t'][m], p['x'][m], p['y'][m], p['a'][m]
    # Release = end of the hand blob that opens the run. A later blob is the hand picking the rat up, so it must not count.
    big = np.where(a > 1000)[0]; i0 = 0
    if len(big) and t[big[0]] <= t[0] + 5:
        i0 = big[0]
        for b in big:
            if t[b] - t[i0] > 1.0: break
            i0 = b
        i0 += 1
    ok = np.where(~np.isnan(x))[0]; ok = ok[ok >= i0]
    if len(ok) < 5: return None
    i0 = ok[0]; tt = t[i0:]; fx = np.interp(tt, t[ok], x[ok]); fy = np.interp(tt, t[ok], y[ok])
    fx, fy = medfilt(fx, 3), medfilt(fy, 3)
    inside = np.where(np.hypot(fx - PX, fy - PY) < R)[0]
    lat = float(tt[inside[0]] - tt[0]) if len(inside) else np.nan
    e = inside[0] if len(inside) else len(tt) - 1
    ax, ay, s = fx[0], fy[0], 0.0
    for a1, b1 in zip(fx[:e + 1], fy[:e + 1]):
        d = np.hypot(a1 - ax, b1 - ay)
        if d >= 20: s += d; ax, ay = a1, b1
    return dict(latency=lat, path_px=s, release=float(tt[0]))
A = list(csv.DictReader(open(raw, encoding='latin-1', newline='')))
order = []
for r in A:
    if r['Animal'] not in order: order.append(r['Animal'])
rats = {a: [r for r in A if r['Animal'] == a] for a in order}
def build(R):
    return [measure(r, R) for r in runs]
def align(M):
    cost = lambda m, d: 30.0 if m is None else min(abs(min(30, m['latency'] if not np.isnan(m['latency']) else 30) - min(d, 30)), 30.0)
    n, k = len(order), len(runs); SKIPRAT, SKIPRUN = 45.0, 12.0
    D = np.full((n + 1, k + 1), np.inf); D[0, 0] = 0; B = {}
    for i in range(n + 1):
        for j in range(k + 1):
            if not np.isfinite(D[i, j]): continue
            if j < k and D[i, j] + SKIPRUN < D[i, j + 1]: D[i, j + 1] = D[i, j] + SKIPRUN; B[(i, j + 1)] = ('run', i, j)
            if i < n and D[i, j] + SKIPRAT < D[i + 1, j]: D[i + 1, j] = D[i, j] + SKIPRAT; B[(i + 1, j)] = ('rat', i, j)
            if i < n and j + 4 <= k:
                c = D[i, j] + sum(cost(M[j + q], float(rats[order[i]][q]['Duration (s)'])) for q in range(4))
                if c < D[i + 1, j + 4]: D[i + 1, j + 4] = c; B[(i + 1, j + 4)] = ('match', i, j)
            # A rat with only its first 3 trials on video costs a quarter of skipping it, so it needs a real fit to win.
            if i < n and j + 3 <= k:
                c = D[i, j] + SKIPRAT / 4 + sum(cost(M[j + q], float(rats[order[i]][q]['Duration (s)'])) for q in range(3))
                if c < D[i + 1, j + 3]: D[i + 1, j + 3] = c; B[(i + 1, j + 3)] = ('partial', i, j)
    i, j = n, k; pairs = []; skipped = []; stray = []
    while (i, j) != (0, 0):
        t, a, b = B[(i, j)]
        if t == 'match': pairs.append((a, b, 4))
        elif t == 'partial': pairs.append((a, b, 3))
        elif t == 'rat': skipped.append(order[a])
        else: stray.append(b)
        i, j = a, b
    return pairs[::-1], skipped[::-1], stray[::-1], D[n, k]
def table(R):
    M = build(R); pairs, skipped, stray, c = align(M); rows = []
    for a, b, nq in pairs:
        if nq == 3: print(f'    partial block: rat {order[a]} matched first 3 trials')
        for q in range(nq):
            am = rats[order[a]][q]; m = M[b + q]; r = runs[b + q]
            rows.append(dict(rat=order[a], test=int(am['Test']), file=r['file'], run_start_s=r['start'], release_s=round(m['release'], 1) if m else '', anymaze_s=float(am['Duration (s)']),
                             tracker_s=round(min(30.0, 30.0 if np.isnan(m['latency']) else m['latency']), 1) if m else np.nan, reached=bool(m and not np.isnan(m['latency'])),
                             anymaze_cm=float(am['Distance (cm)']), path_px=m['path_px'] if m else np.nan))
    return rows, skipped, stray, c
best = None
for R in (40, 60, 80, 100, 120, 150):
    rows, sk, st, c = table(R)
    S = [r for r in rows if r['test'] not in FLAGGED and int(r['rat']) % 2]
    e = np.nanmedian([abs(r['tracker_s'] - min(r['anymaze_s'], 30)) for r in S])
    print(f'  R={R}: matched rats={len(rows) // 4} skipped={sk} stray runs={len(st)} cost={c:.0f} median err={e:.2f}s')
    if best is None or e < best[0]: best = (e, R, rows, sk, st)
_, R, rows, sk, st = best
cal = [r for r in rows if r['test'] not in FLAGGED and int(r['rat']) % 2 and r['reached'] and r['anymaze_s'] < 29.5]
L = np.array([r['path_px'] for r in cal]); D = np.array([r['anymaze_cm'] for r in cal]); k = (L @ D) / (L @ L)
for r in rows:
    r['tracker_cm'] = round(k * r['path_px'], 1); del r['path_px']
    r['group'] = 'audit_flagged' if r['test'] in FLAGGED else ('calibration' if int(r['rat']) % 2 else 'held_out')
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f'\nplatform radius={R}px scale={k:.3f} cm/px implied pool diameter={2 * 510 * k:.0f}cm; skipped rats={sk}; stray runs={[(runs[i]["file"], runs[i]["start"], runs[i]["dur"]) for i in st]}')
for g in ('calibration', 'held_out'):
    S = [r for r in rows if r['group'] == g]; nan = [r['test'] for r in S if np.isnan(r['tracker_s'])]
    S = [r for r in S if not np.isnan(r['tracker_s'])]; a = np.array([min(r['anymaze_s'], 30) for r in S]); b = np.array([r['tracker_s'] for r in S])
    print(f'{g} n={len(S)} unmeasured={nan}: time r={np.corrcoef(a, b)[0, 1]:.3f} median|err|={np.median(np.abs(a - b)):.2f}s bias={np.mean(b - a):+.2f}s within2s={np.mean(np.abs(a - b) <= 2) * 100:.0f}%')
    E = [r for r in S if r['reached'] and r['anymaze_s'] < 29.5]; a = np.array([r['anymaze_cm'] for r in E]); b = np.array([r['tracker_cm'] for r in E])
    print(f'   distance, trials ending at platform n={len(E)}: r={np.corrcoef(a, b)[0, 1]:.3f} median|err|={np.median(np.abs(a - b)):.1f}cm')
print('\nheld-out and calibration trials with time error over 3s:')
for r in rows:
    if r['group'] != 'audit_flagged' and abs(r['tracker_s'] - min(r['anymaze_s'], 30)) > 3:
        print(f"  rat{r['rat']} t{r['test']} {r['file']}@{r['run_start_s']} anymaze={r['anymaze_s']} tracker={r['tracker_s']} reached={r['reached']} cm {r['anymaze_cm']}->{r['tracker_cm']}")
print('\naudit-flagged:')
for r in rows:
    if r['group'] == 'audit_flagged': print(f"  rat{r['rat']} t{r['test']} {r['file']}@{r['run_start_s']} anymaze={r['anymaze_s']}s/{r['anymaze_cm']}cm tracker={r['tracker_s']}s/{r['tracker_cm']}cm reached={r['reached']}")
seen = []
for r in rows:
    if (r['rat'], r['file']) not in seen: seen.append((r['rat'], r['file']))
print('\nrats by file:', seen)
print('trials matched:', len(rows), 'of 120')
