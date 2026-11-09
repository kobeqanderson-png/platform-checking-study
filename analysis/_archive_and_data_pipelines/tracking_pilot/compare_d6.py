"""Estimates d6 release times, then compares tracker with AnyMaze.
Trials AnyMaze handled badly (audit retrack list) are kept out of calibration and scoring and reported separately.
Usage: compare_d6.py <track-folder> <KAcd6.csv> <out.csv>"""
import csv, glob, os, re, sys, collections
import numpy as np
from scipy.signal import medfilt
tracks, raw, out = sys.argv[1:]
AUDIT_FLAGGED = {3, 4, 10, 11, 13, 18, 22, 26, 30}   # d6 test numbers
SEG = 30.0
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan
ref = collections.defaultdict(lambda: dict(seg=[]))
for r in csv.DictReader(open(raw, encoding='latin-1', newline='')):
    q = ref[int(r['Animal'])]; q.update(test=int(r['Test']), trk=num(r['Tracked (%)']), reason=r['Reason ended'])
    q['seg'].append((num(r['Duration (s)']), num(r['Distance (cm)']), num(r['P2: SE : time (s)'])))
for q in ref.values():
    q['dur'], q['dist'], q['p2'] = [sum(s[i] for s in q['seg']) for i in range(3)]
T = {}
for f in glob.glob(os.path.join(tracks, 'rat*.csv')):
    rat = int(re.search(r'rat(\d+)', f).group(1)); rows = list(csv.DictReader(open(f, newline='')))
    T[rat] = dict(t=np.array([float(r['t_clip_s']) for r in rows]), xy=np.array([[num(r['x_px']), num(r['y_px'])] for r in rows]), a=np.array([num(r['area']) for r in rows]))
# Platform centre: median resting spot across clips, using frames with almost no movement.
rest = []
for p in T.values():
    ok = ~np.isnan(p['xy'][:, 0]); rest.append(np.nanmedian(p['xy'][ok], axis=0))
stayers = [np.median([p['xy'][~np.isnan(p['xy'][:, 0])][:, i] for _ in [0]], axis=1) for p in T.values() for i in [0]]
cand = np.array(rest); pc = np.median(cand, axis=0)
pc = np.median(cand[np.hypot(*(cand - pc).T) < 80], axis=0)
for rat, p in T.items():
    # Release = first frame after the hand blob (area over 1000; a rat alone peaks near 700) in the first 20 s.
    # With no hand blob, the clip started after placement, so use the first frame with a rat and mark it.
    early = np.where((p['t'] <= 20) & (p['a'] > 1000))[0]
    seen = np.where(~np.isnan(p['xy'][:, 0]) & (p['a'] <= 1000))[0]
    after = seen[seen > early[-1]] if len(early) else seen
    p['release'] = p['t'][after[0]]; p['hand_seen'] = bool(len(early))
def clean(p, t0, dur):
    keep = (p['t'] >= t0) & (p['t'] <= t0 + dur); ts = p['t'][keep] - t0; xy = p['xy'][keep]
    found = ~np.isnan(xy[:, 0]); good = np.where(found)[0]; last = good[0]
    for i in good[1:]:
        if np.hypot(*(xy[i] - xy[last])) > 83 * max(i - last, 1): found[i] = False
        else: last = i
    return ts, medfilt(np.interp(ts, ts[found], xy[found, 0]), 5), medfilt(np.interp(ts, ts[found], xy[found, 1]), 5), 100 * found.mean()
def plen(x, y, band):
    ax, ay, s = x[0], y[0], 0.0
    for a, b in zip(x, y):
        d = np.hypot(a - ax, b - ay)
        if d >= band: s += d; ax, ay = a, b
    return s
usable = sorted(r for r in T if T[r]['release'] is not None and ref[r]['test'] not in AUDIT_FLAGGED)
cal = usable[0::2]; hold = usable[1::2]
def L(r, b, shift=0): ts, x, y, _ = clean(T[r], T[r]['release'] + shift, ref[r]['dur']); return plen(x, y, b)
best = None
for b in (0, 5, 10, 15, 22, 30, 40, 60):
    l = np.array([L(r, b) for r in cal]); d = np.array([ref[r]['dist'] for r in cal]); k = (l @ d) / (l @ l); e = np.median(np.abs(k * l - d))
    if best is None or e < best[0]: best = (e, b, k)
_, band, k = best
def inP2(x, y, R): return np.hypot(x - pc[0], y - pc[1]) < R
def p2t(r, R, shift=0):
    ts, x, y, _ = clean(T[r], T[r]['release'] + shift, ref[r]['dur']); return float(inP2(x, y, R).mean() * ref[r]['dur'])
R = min(range(30, 301, 10), key=lambda c: np.median([abs(p2t(r, c) - ref[r]['p2']) for r in cal]))
print('releases:', {r: float(T[r]['release']) for r in sorted(T)})
print('no hand blob seen (clip may start after placement):', [r for r in sorted(T) if not T[r]['hand_seen']])
print(f'calibrated on {len(cal)}: deadband={band}px scale={k:.3f} cm/px implied outer pool diameter={2 * 533 * k:.0f}cm (d8 pilot gave ~172) platform=({pc[0]:.0f},{pc[1]:.0f}) P2 radius={R}px ~{R * k:.0f}cm')
rows = []
for r in sorted(T):
    p = T[r]
    if p['release'] is None: continue
    q = ref[r]; ts, x, y, fnd = clean(p, p['release'], q['dur']); ts2, x2, y2, _ = clean(p, p['release'], 120.0)
    group = 'audit_flagged' if q['test'] in AUDIT_FLAGGED else ('calibration' if r in cal else 'held_out')
    rows.append(dict(rat=r, test=q['test'], group=group, release_clip_s=round(float(p['release']), 1), found_pct=round(fnd, 1), anymaze_tracked=q['trk'], anymaze_reason=q['reason'], anymaze_dur=round(q['dur'], 1),
        anymaze_dist=round(q['dist'], 1), tracker_dist=round(k * plen(x, y, band), 1), anymaze_p2_s=round(q['p2'], 1), tracker_p2_s=round(float(inP2(x, y, R).mean() * q['dur']), 1),
        tracker_full120_dist=round(k * plen(x2, y2, band), 1), tracker_full120_p2_s=round(float(inP2(x2, y2, R).mean() * (ts2[-1] - ts2[0])), 1), clip_covers_120s=bool(ts2[-1] >= 119)))
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def stat(n, a, b, S):
    x = np.array([s[a] for s in S], float); y = np.array([s[b] for s in S], float); e = y - x
    print(f'  {n}: r={np.corrcoef(x, y)[0, 1]:.3f} median|err|={np.median(np.abs(e)):.1f} worst={np.abs(e).max():.1f} bias={e.mean():+.1f}')
for g in ('calibration', 'held_out'):
    S = [s for s in rows if s['group'] == g]; print(f'{g} n={len(S)}'); stat('distance', 'anymaze_dist', 'tracker_dist', S); stat('P2 s', 'anymaze_p2_s', 'tracker_p2_s', S)
S = [s for s in rows if s['group'] == 'held_out']
print('held-out stay/leave agrees:', sum((s['anymaze_p2_s'] / s['anymaze_dur'] >= .9) == (s['tracker_p2_s'] / s['anymaze_dur'] >= .9) for s in S), '/', len(S))
print('\nrelease-time sensitivity on scoring trials (shift s -> median |err| distance, P2):')
for sh in (-6, -4, -2, -1, 0, 1, 2, 4, 6):
    S2 = [r for r in usable if T[r]['release'] + sh >= 0]
    print(f"  {sh:+d}: {np.median([abs(k * L(r, band, sh) - ref[r]['dist']) for r in S2]):.1f} cm, {np.median([abs(p2t(r, R, sh) - ref[r]['p2']) for r in S2]):.1f} s")
print('\nper-30s segment agreement, P2 s, held-out: r and median err')
a, b = [], []
for r in hold:
    q = ref[r]; ts, x, y, _ = clean(T[r], T[r]['release'], q['dur']); ins = inP2(x, y, R)
    for i, s in enumerate(q['seg']):
        m = (ts >= i * SEG) & (ts < (i + 1) * SEG)
        if m.any(): a.append(s[2]); b.append(ins[m].mean() * s[0])
print(f'  n={len(a)} r={np.corrcoef(a, b)[0, 1]:.3f} median|err|={np.median(np.abs(np.array(a) - np.array(b))):.1f}s')
print('\ntable')
for s in sorted(rows, key=lambda s: (s['group'], s['test'])):
    print(f"{s['group'][:5]} rat{s['rat']:>2} t{s['test']:>2} rel={s['release_clip_s']:5.1f} found={s['found_pct']} anymz_trk={s['anymaze_tracked']} {s['anymaze_reason'][:6]} dur={s['anymaze_dur']} dist {s['anymaze_dist']:7.1f}->{s['tracker_dist']:7.1f} P2 {s['anymaze_p2_s']:5.1f}->{s['tracker_p2_s']:5.1f} | full120 {s['tracker_full120_dist']:7.1f} {s['tracker_full120_p2_s']:5.1f} cover={s['clip_covers_120s']}")
