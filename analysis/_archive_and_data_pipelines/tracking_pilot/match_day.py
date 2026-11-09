"""Splits a day's recordings into rat-present runs, matches them to AnyMaze trials, and scores agreement.
Positions are scaled so the pool radius is 510 units in every file, whatever its resolution.
Rats stay in AnyMaze order; a whole rat or stray run can be skipped, but trials cannot be reordered.
Usage: match_day.py <day number> <track-folder> <run-log> <KAcdN.csv> <audit.csv> <out.csv>"""
import csv, glob, os, re, sys
import numpy as np
from scipy.signal import medfilt
day, tracks, log, raw, audit, out = sys.argv[1:]
UNIT = 510.0; GAP, MINRUN = 4.0, 5.0
num = lambda s: float(s) if s not in ('', None) else np.nan
pools = re.findall(r'pool source px=\((\d+),(\d+),r(\d+)\)', open(log, encoding='utf-8', errors='ignore').read().replace('\x00', ''))
files = sorted(glob.glob(os.path.join(tracks, 'file*.csv')), key=lambda f: int(re.search(r'file(\d+)_', f).group(1)))
assert len(pools) == len(files), (len(pools), len(files))
TR = {}; runs = []
for f, (cx, cy, r) in zip(files, pools):
    k = os.path.basename(f).split('_')[0]; cx, cy, r = float(cx), float(cy), float(r); s = UNIT / r
    R = list(csv.DictReader(open(f, newline='')))
    p = TR[k] = dict(t=np.array([float(q['t_s']) for q in R]), a=np.array([float(q['area']) for q in R]),
                     x=(np.array([num(q['x_px']) for q in R]) - cx) * s, y=(np.array([num(q['y_px']) for q in R]) - cy) * s)
    idx = np.where(~np.isnan(p['x']))[0]; a = b = idx[0]; prev = None
    for i in list(idx[1:]) + [None]:
        if i is None or p['t'][i] - p['t'][b] > GAP:
            if p['t'][b] - p['t'][a] >= MINRUN: runs.append(dict(file=k, start=p['t'][a], end=p['t'][b], gap=(p['t'][a] - prev) if prev is not None else 9999)); prev = p['t'][b]
            a = i
        b = i
xs, ys = [], []
for p in TR.values():
    still = np.hypot(p['x'][10:] - p['x'][:-10], p['y'][10:] - p['y'][:-10]) < 8
    xs.append(p['x'][10:][still]); ys.append(p['y'][10:][still])
xs, ys = np.concatenate(xs), np.concatenate(ys)
h, ex, ey = np.histogram2d(xs, ys, bins=np.arange(-520, 521, 20)); i, j = np.unravel_index(np.argmax(h), h.shape)
sel = (np.abs(xs - ex[i] - 10) < 40) & (np.abs(ys - ey[j] - 10) < 40); PX, PY = float(np.median(xs[sel])), float(np.median(ys[sel]))
def measure(r, R):
    p = TR[r['file']]; m = (p['t'] >= r['start']) & (p['t'] <= r['end']); t, x, y, a = p['t'][m], p['x'][m], p['y'][m], p['a'][m]
    big = np.where(a > 1000)[0]; i0 = 0
    if len(big) and t[big[0]] <= t[0] + 5:
        i0 = big[0]
        for b in big:
            if t[b] - t[i0] > 1.0: break
            i0 = b
        i0 += 1
    ok = np.where(~np.isnan(x))[0]; ok = ok[ok >= i0]
    if len(ok) < 5: return None
    tt = t[ok[0]:]; fx = medfilt(np.interp(tt, t[ok], x[ok]), 3); fy = medfilt(np.interp(tt, t[ok], y[ok]), 3)
    inside = np.where(np.hypot(fx - PX, fy - PY) < R)[0]; lat = float(tt[inside[0]] - tt[0]) if len(inside) else np.nan
    e = inside[0] if len(inside) else len(tt) - 1; ax, ay, s = fx[0], fy[0], 0.0
    for u, v in zip(fx[:e + 1], fy[:e + 1]):
        d = np.hypot(u - ax, v - ay)
        if d >= 20: s += d; ax, ay = u, v
    return dict(latency=lat, path=s, release=float(tt[0]))
A = list(csv.DictReader(open(raw, encoding='latin-1', newline='')))
order = []
for r in A:
    if r['Animal'] not in order: order.append(r['Animal'])
rats = {a: [r for r in A if r['Animal'] == a] for a in order}
AUD = {int(r['test']): r for r in csv.DictReader(open(audit, encoding='utf-8', newline='')) if r['day'] == day}
FLAG = {t for t, r in AUD.items() if r['verdict'] == 'A_RETRACK'}
def align(M):
    def cost(m, d):
        if m is None: return 30.0
        lat = 30.0 if np.isnan(m['latency']) else min(30.0, m['latency'])
        return min(abs(lat - min(d, 30.0)), 30.0)
    # Gaps within a rat are short and gaps between rats are long, so a block that breaks this pattern costs extra.
    def shape(j, size): return (10.0 if runs[j]['gap'] < 13 else 0.0) + sum(15.0 for q in range(1, size) if runs[j + q]['gap'] > 15)
    n, k = len(order), len(runs); SKIPRAT, SKIPRUN = 45.0, 12.0
    D = np.full((n + 1, k + 1), np.inf); D[0, 0] = 0; B = {}
    def relax(i2, j2, c, tag):
        if c < D[i2, j2]: D[i2, j2] = c; B[(i2, j2)] = tag
    for i in range(n + 1):
        for j in range(k + 1):
            if not np.isfinite(D[i, j]): continue
            if j < k: relax(i, j + 1, D[i, j] + SKIPRUN, ('run', i, j))
            if i < n:
                relax(i + 1, j, D[i, j] + SKIPRAT, ('rat', i, j)); T = rats[order[i]]; size = len(T)
                if j + size <= k: relax(i + 1, j + size, D[i, j] + shape(j, size) + sum(cost(M[j + q], float(T[q]['Duration (s)'])) for q in range(size)), ('match', i, j, size))
                if size == 4 and j + 3 <= k: relax(i + 1, j + 3, D[i, j] + shape(j, 3) + SKIPRAT / 4 + sum(cost(M[j + q], float(T[q]['Duration (s)'])) for q in range(3)), ('match', i, j, 3))
    i, j = n, k; pairs, skipped, stray = [], [], []
    while (i, j) != (0, 0):
        t = B[(i, j)]
        if t[0] == 'match': pairs.append((t[1], t[2], t[3]))
        elif t[0] == 'rat': skipped.append(order[t[1]])
        else: stray.append(t[2])
        i, j = t[1], t[2]
    return pairs[::-1], skipped[::-1], stray[::-1]
def table(R):
    M = [measure(r, R) for r in runs]; pairs, sk, st = align(M); rows = []; partial = []
    for a, b, nq in pairs:
        if nq < len(rats[order[a]]): partial.append(order[a])
        for q in range(nq):
            am = rats[order[a]][q]; m = M[b + q]; r = runs[b + q]
            rows.append(dict(block_gap_ok=(runs[b]['gap'] >= 13 and all(runs[b + z]['gap'] <= 15 for z in range(1, nq))), block_size=nq, rat=order[a], test=int(am['Test']), file=r['file'], run_start_s=round(r['start'], 1), release_s=round(m['release'], 1) if m else '', anymaze_s=float(am['Duration (s)']),
                             tracker_s=round(30.0 if np.isnan(m['latency']) else min(30.0, m['latency']), 1) if m else np.nan, reached=bool(m and not np.isnan(m['latency'])), anymaze_cm=float(am['Distance (cm)']), path=m['path'] if m else np.nan))
    return rows, sk, st, partial
best = None
for R in (40, 60, 80, 100, 120):
    rows, sk, st, partial = table(R)
    S = [r for r in rows if r['test'] not in FLAG and int(r['rat']) % 2 and not np.isnan(r['tracker_s'])]
    e = np.median([abs(r['tracker_s'] - min(r['anymaze_s'], 30)) for r in S])
    if best is None or e < best[0]: best = (e, R, rows, sk, st, partial)
e, R, rows, sk, st, partial = best
cal = [r for r in rows if r['test'] not in FLAG and int(r['rat']) % 2 and r['reached'] and r['anymaze_s'] < 29.5 and r['tracker_s'] < 29.5]
L = np.array([r['path'] for r in cal]); D = np.array([r['anymaze_cm'] for r in cal]); k = (L @ D) / (L @ L)
for r in rows:
    r['tracker_cm'] = round(k * r['path'], 1); del r['path']
    r['group'] = 'audit_flagged' if r['test'] in FLAG else ('calibration' if int(r['rat']) % 2 else 'held_out')
    r['audit_flags'] = AUD[r['test']]['flags'] if r['test'] in AUD else ''
# Confidence per rat: the gap pattern fits, all trials are present, and unflagged times agree. Capped trials count only if both systems reach the cap.
for rat in {r['rat'] for r in rows}:
    B = [r for r in rows if r['rat'] == rat]; U = [r for r in B if r['group'] != 'audit_flagged' and not np.isnan(r['tracker_s'])]
    errs = [abs(r['tracker_s'] - min(r['anymaze_s'], 30)) for r in U]
    good = B[0]['block_gap_ok'] and B[0]['block_size'] == len(rats[rat]) and errs and max(errs) <= 5
    for r in B: r['match_confidence'] = 'high' if good else 'low'
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f'\n===== d{day}: files={len(files)} usable runs={len(runs)} matched trials={len(rows)}/{len(A)} rats skipped={sk} partial={partial} stray runs={[(runs[i]["file"], round(runs[i]["start"])) for i in st]}')
print(f'platform=({PX:.0f},{PY:.0f}) share of still frames={100 * sel.mean():.0f}% radius={R} scale={k:.3f} implied diameter={2 * 510 * k:.0f}cm')
for g in ('calibration', 'held_out'):
    S = [r for r in rows if r['group'] == g and not np.isnan(r['tracker_s'])]; a = np.array([min(r['anymaze_s'], 30) for r in S]); b = np.array([r['tracker_s'] for r in S])
    E = [r for r in S if r['reached'] and r['anymaze_s'] < 29.5 and r['tracker_s'] < 29.5]; c = np.array([r['anymaze_cm'] for r in E]); d = np.array([r['tracker_cm'] for r in E])
    print(f'{g}: n={len(S)} time r={np.corrcoef(a, b)[0, 1]:.3f} med|err|={np.median(np.abs(a - b)):.2f}s bias={np.mean(b - a):+.2f}s within2s={100 * np.mean(np.abs(a - b) <= 2):.0f}% | dist n={len(E)} r={np.corrcoef(c, d)[0, 1]:.3f} med|err|={np.median(np.abs(c - d)):.1f}cm')
hi = [r for r in rows if r['match_confidence'] == 'high']
print(f"confidence: rats high={len({r['rat'] for r in hi})} low={sorted({r['rat'] for r in rows} - {r['rat'] for r in hi}, key=int)}; trials high={len(hi)}")
for g in ('calibration', 'held_out'):
    S = [r for r in hi if r['group'] == g and r['anymaze_s'] < 29.5 and not np.isnan(r['tracker_s'])]
    if len(S) > 2:
        a = np.array([r['anymaze_s'] for r in S]); b = np.array([r['tracker_s'] for r in S])
        print(f'  high-confidence {g}, trials ending before the cap: n={len(S)} r={np.corrcoef(a, b)[0, 1]:.3f} med|err|={np.median(np.abs(a - b)):.2f}s bias={np.mean(b - a):+.2f}s')
print('flagged: ' + '; '.join(f"t{r['test']} {r['anymaze_s']:.1f}s/{r['anymaze_cm']:.0f}cm->{r['tracker_s']}s/{r['tracker_cm']:.0f}cm" for r in rows if r['group'] == 'audit_flagged'))
print('unflagged, time off by over 5s: ' + ('; '.join(f"t{r['test']} rat{r['rat']} {r['anymaze_s']:.1f}->{r['tracker_s']}s" for r in rows if r['group'] != 'audit_flagged' and abs(r['tracker_s'] - min(r['anymaze_s'], 30)) > 5) or 'none'))
matched = {r['test'] for r in rows}
print('flagged not on video: ' + str(sorted(FLAG - matched)))
