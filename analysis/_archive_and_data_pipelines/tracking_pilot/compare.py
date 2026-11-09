"""Compares tracker output with AnyMaze for d8.
Odd tests calibrate (cm/px, deadband, P2 centre and radius, camera->AnyMaze map); even tests are held out.
Usage: compare.py <track-folder> <KAcd8.csv> <out.csv>"""
import csv, os, sys
import numpy as np
from scipy.signal import medfilt
tracks, raw, out = sys.argv[1:]
EXCLUDE = {4, 25}   # AnyMaze itself under 90% tracked on these, so it is not a fair reference
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan
ref = {}
for r in csv.DictReader(open(raw, encoding='latin-1', newline='')):
    ref[int(r['Test'])] = dict(animal=r['Animal'], dur=num(r['Duration (s)']), dist=num(r['Distance (cm)']), p2=num(r['P2: SE : time (s)']),
                               x=num(r['Average X position (%)']), y=num(r['Average Y position (%)']), trk=num(r['Tracked (%)']))
paths = {}
for t in ref:
    rows = list(csv.DictReader(open(os.path.join(tracks, f'track_test{t:02d}.csv'), newline='')))
    ts = np.array([float(r['t_s']) for r in rows]); keep = ts <= ref[t]['dur']
    xy = np.array([[num(r['x_px']), num(r['y_px'])] for r in rows])[keep]; ts = ts[keep]
    found = ~np.isnan(xy[:, 0])
    # Drop single-frame teleports (over ~1.5 pool radii per second at 10 Hz), then bridge gaps.
    good = np.where(found)[0]; last = good[0]; jumps = 0
    for i in good[1:]:
        if np.hypot(*(xy[i] - xy[last])) > 75 * max(i - last, 1): found[i] = False; jumps += 1
        else: last = i
    x = np.interp(ts, ts[found], xy[found, 0]); y = np.interp(ts, ts[found], xy[found, 1])
    paths[t] = dict(ts=ts, x=medfilt(x, 5), y=medfilt(y, 5), found=100 * found.mean(), jumps=jumps)
def path_len(p, band):
    ax, ay, total = p['x'][0], p['y'][0], 0.0
    for x, y in zip(p['x'], p['y']):
        d = np.hypot(x - ax, y - ay)
        if d >= band: total += d; ax, ay = x, y
    return total
tests = sorted(t for t in ref if t not in EXCLUDE)
train = [t for t in tests if t % 2]; test = [t for t in tests if not t % 2]
# Deadband and scale: chosen on calibration trials only.
best = None
for band in (0, 5, 10, 15, 20, 30, 40, 60):
    L = np.array([path_len(paths[t], band) for t in train]); D = np.array([ref[t]['dist'] for t in train])
    k = (L @ D) / (L @ L); err = np.median(np.abs(k * L - D))
    if best is None or err < best[0]: best = (err, band, k)
_, band, k = best
stay = [t for t in train if ref[t]['p2'] / ref[t]['dur'] > 0.95]
cx, cy = np.median([np.median(paths[t]['x']) for t in stay]), np.median([np.median(paths[t]['y']) for t in stay])
def p2_time(p, R): return float(np.mean(np.hypot(p['x'] - cx, p['y'] - cy) < R) * (p['ts'][-1] - p['ts'][0]))
Rbest = min(range(30, 301, 10), key=lambda R: np.median([abs(p2_time(paths[t], R) - ref[t]['p2']) for t in train]))
A = np.array([[paths[t]['x'].mean(), paths[t]['y'].mean(), 1] for t in train])
mapx = np.linalg.lstsq(A, [ref[t]['x'] for t in train], rcond=None)[0]; mapy = np.linalg.lstsq(A, [ref[t]['y'] for t in train], rcond=None)[0]
print(f'calibrated on {len(train)} trials: deadband={band}px scale={k:.3f} cm/px pool_diameter~{2 * 485 * k:.0f}cm P2 centre=({cx:.0f},{cy:.0f}) radius={Rbest}px (~{Rbest * k:.0f}cm)')
rows = []
for t in sorted(ref):
    p = paths[t]; xm, ym = p['x'].mean(), p['y'].mean()
    rows.append(dict(test=t, animal=ref[t]['animal'], split='excluded' if t in EXCLUDE else ('calibration' if t % 2 else 'held_out'),
        found_pct=round(p['found'], 1), jumps_removed=p['jumps'], anymaze_tracked=ref[t]['trk'], anymaze_dist=ref[t]['dist'], tracker_dist=round(k * path_len(p, band), 1),
        anymaze_p2_s=ref[t]['p2'], tracker_p2_s=round(p2_time(p, Rbest), 1), anymaze_x=ref[t]['x'], tracker_x=round(float(mapx @ [xm, ym, 1]), 1), anymaze_y=ref[t]['y'], tracker_y=round(float(mapy @ [xm, ym, 1]), 1)))
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def stats(name, a, b, S):
    x = np.array([r[a] for r in S], float); y = np.array([r[b] for r in S], float); e = y - x
    print(f'  {name}: r={np.corrcoef(x, y)[0, 1]:.3f} median|err|={np.median(np.abs(e)):.1f} worst|err|={np.abs(e).max():.1f} bias={e.mean():+.1f}')
for label in ('calibration', 'held_out'):
    S = [r for r in rows if r['split'] == label]; print(f'{label} (n={len(S)})')
    stats('distance cm', 'anymaze_dist', 'tracker_dist', S); stats('P2 time s', 'anymaze_p2_s', 'tracker_p2_s', S)
    stats('avg x %', 'anymaze_x', 'tracker_x', S); stats('avg y %', 'anymaze_y', 'tracker_y', S)
S = [r for r in rows if r['split'] == 'held_out']
same = sum((r['anymaze_p2_s'] / ref[r['test']]['dur'] >= .9) == (r['tracker_p2_s'] / ref[r['test']]['dur'] >= .9) for r in S)
print(f'held-out stayer/leaver call agrees: {same}/{len(S)}')
print('found% min/median:', min(r['found_pct'] for r in rows), np.median([r['found_pct'] for r in rows]), ' jumps removed total:', sum(r['jumps_removed'] for r in rows))
print('\nall trials sorted by distance error')
for r in sorted(rows, key=lambda r: -abs(r['tracker_dist'] - r['anymaze_dist'])):
    print(f"t{r['test']:>2} a{r['animal']:>2} {r['split'][:5]} found={r['found_pct']} jumps={r['jumps_removed']} dist {r['anymaze_dist']:7.1f}->{r['tracker_dist']:7.1f} P2 {r['anymaze_p2_s']:5.1f}->{r['tracker_p2_s']:5.1f} anymaze_trk={r['anymaze_tracked']}")
