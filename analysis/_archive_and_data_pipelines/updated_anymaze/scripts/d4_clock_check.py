"""Finds d4 trials whose AnyMaze duration disagrees with its save time, and measures the path up to the true end.
Usage: d4_clock_check.py <tracking_pilot> <out.csv>"""
import csv, glob, os, sys
import numpy as np
from scipy.signal import medfilt
P, OUT = sys.argv[1:]
CX, CY, PR = 638, 371, 376; PX, PY = 144, -186; OFF = .5; K = .155; s = 510 / PR
Q = list(csv.DictReader(open(glob.glob(os.path.join(P, 'tracks_d4', 'file1_*.csv'))[0], newline=''))); t = np.array([float(q['t_s']) for q in Q]); x0 = (np.array([float(q['x_px'] or np.nan) for q in Q]) - CX) * s; y0 = (np.array([float(q['y_px'] or np.nan) for q in Q]) - CY) * s
x, y = x0 - PX, y0 - PY
R = list(csv.DictReader(open(os.path.join(P, 'd4_tracker_vs_anymaze.csv'), newline='')))
def settle(r):
    rel, end = float(r['release_s']), float(r['run_end_s']); m = (t >= rel) & (t <= end) & ~np.isnan(x); tt, D = t[m] - rel, np.hypot(x[m], y[m])
    for i in range(len(tt)):
        w = (tt >= tt[i]) & (tt <= tt[i] + 2)
        if tt[-1] >= tt[i] + 2 and D[w].max() < 70: return float(tt[i])
    return None
def path(r, cap):
    rel = float(r['release_s']); m = (t >= rel) & (t <= rel + cap); ok = ~np.isnan(x0[m]); tt = t[m]
    fx, fy = medfilt(np.interp(tt, tt[ok], x0[m][ok]), 3), medfilt(np.interp(tt, tt[ok], y0[m][ok]), 3); ax, ay, L = fx[0], fy[0], 0.0
    for u, v in zip(fx, fy):
        q = np.hypot(u - ax, v - ay)
        if q >= 20: L += q; ax, ay = u, v
    return K * L
out = []
for r in R:
    if not r['release_s']: continue
    d, res = float(r['anymaze_s']), float(r['time_residual_s']); saved = d - res; st = settle(r)
    # Saved time relative to release is the end by the wall clock. It should sit near the settle time unless the trial hit the cap.
    late = abs(res) >= 3.5
    match = st is not None and abs(st - saved) <= 2.5
    end = min(30.0, st - OFF) if st is not None else 30.0
    out.append(dict(test=r['test'], rat_anymaze=r['rat_anymaze'], anymaze_s=d, anymaze_cm=r['anymaze_cm'], residual_s=res, end_by_save_s=round(saved, 1), settle_s=round(st, 1) if st is not None else '', clock_flag=late and match, new_s=round(end, 1), path_to_end_cm=round(path(r, end + OFF if end < 30 else 30.0), 1), methods_agree=r['methods_agree']))
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
A = [q for q in out if abs(q['residual_s']) < 3.5 and q['settle_s'] != '' and q['anymaze_s'] < 29.5]; e = [q['settle_s'] - q['end_by_save_s'] for q in A]; print(f'normal trials: settle minus save-time end median {np.median(e):+.2f}s, IQR {np.percentile(e, 25):+.2f} to {np.percentile(e, 75):+.2f}, n={len(A)}')
print('|residual| >= 3.5 s:')
for q in out:
    if abs(q['residual_s']) >= 3.5: print(f"  t{q['test']} rat{q['rat_anymaze']} AM {q['anymaze_s']}s {q['anymaze_cm']}cm | save says {q['end_by_save_s']} settle {q['settle_s']} | clock_flag={q['clock_flag']} -> {q['new_s']}s {q['path_to_end_cm']}cm agree={q['methods_agree']}")
for k in ('41', '97', '120'):
    q = next(z for z in out if z['test'] == k); print(f"t{k}: AM {q['anymaze_s']}s {q['anymaze_cm']}cm -> {q['new_s']}s {q['path_to_end_cm']}cm, save {q['end_by_save_s']}, settle {q['settle_s']}")
