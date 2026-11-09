"""Matches d4 runs to AnyMaze trials by save timestamp and compares that with match_day.py's block matching.
A run is assigned to a test when the test's save time, corrected by a global clock offset, falls in or just after the run.
Usage: d4_match.py <tracking_pilot> <KAcd4.csv> <audit.csv> <scratch folder>"""
import contextlib, csv, io, os, runpy, sys
import numpy as np
P, RAW, AUDIT, SCR = sys.argv[1:]
out = os.path.join(SCR, 'd4_block.csv'); tracks = os.path.join(P, 'tracks_d4'); log = os.path.join(tracks, 'run.log')
argv = sys.argv; sys.argv = ['match_day.py', '4', tracks, log, RAW, AUDIT, out]; buf = io.StringIO()
with contextlib.redirect_stdout(buf): g = runpy.run_path(os.path.join(P, 'match_day.py'))
sys.argv = argv; print(buf.getvalue())
runs, R, k = g['runs'], g['R'], g['k']; M = [g['measure'](r, R) for r in runs]
BL = {int(r['test']): r for r in csv.DictReader(open(out, newline=''))}
A = {int(r['Test']): r for r in csv.DictReader(open(RAW, encoding='latin-1', newline=''))}
sec = lambda s: int(s[:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8]) - (14 * 3600 + 18 * 60 + 44)   # 09:18:44 local is 14:18:44 UTC
SAVE = {int(r['test']): sec(r['saved_utc']) for r in csv.DictReader(open(os.path.join(P, 'd4_szv_times.csv'), newline=''))}
Q = [float(BL[t]['release_s']) + float(BL[t]['anymaze_s']) - SAVE[t] for t in BL if BL[t]['release_s'] and BL[t]['reached'] == 'True' and float(BL[t]['anymaze_s']) < 29.5]
off = float(np.median(Q)); print(f'clock offset (video time minus save time): {off:+.1f} s, IQR {np.percentile(Q, 25):+.1f} to {np.percentile(Q, 75):+.1f}, n={len(Q)}')
rows = []
for t in sorted(A):
    E = SAVE[t] + off; d = float(A[t]['Duration (s)'])
    # The run whose release plus the AnyMaze duration lands closest to the corrected save time.
    best = min(range(len(runs)), key=lambda j: abs((M[j]['release'] if M[j] else runs[j]['start']) + d - E))
    r, m = runs[best], M[best]; res = (m['release'] if m else r['start']) + d - E
    lat = np.nan if not m or np.isnan(m['latency']) else m['latency']; b = BL.get(t)
    same = bool(b and b['release_s'] and m and abs(float(b['release_s']) - m['release']) < .5)
    rows.append(dict(test=t, rat_anymaze=A[t]['Animal'], run_start_s=round(r['start'], 1), run_end_s=round(r['end'], 1), release_s=round(m['release'], 1) if m else '', time_residual_s=round(res, 1), anymaze_s=d, tracker_s=round(min(30.0, lat), 1) if not np.isnan(lat) else 30.0, reached=not np.isnan(lat), anymaze_cm=float(A[t]['Distance (cm)']), tracker_cm=round(k * m['path'], 1) if m else '', block_match=b['release_s'] if b else '', methods_agree=same))
with open(os.path.join(P, 'd4_tracker_vs_anymaze.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
good = [r for r in rows if abs(r['time_residual_s']) <= 15]
print(f'matched within 15 s of save time: {len(good)}/{len(rows)}; methods agree on {sum(r["methods_agree"] for r in rows)}; duplicate runs: {len(rows) - len({r["run_start_s"] for r in rows})}')
print('poor timestamp fit:', [(r['test'], r['time_residual_s']) for r in rows if abs(r['time_residual_s']) > 15])
print('runs used twice:', sorted({r['run_start_s'] for r in rows if sum(x['run_start_s'] == r['run_start_s'] for x in rows) > 1}))
print('methods disagree:', [r['test'] for r in rows if not r['methods_agree']])
c = [r for r in good if r['anymaze_s'] < 29.5 and r['tracker_s'] < 29.5]; e = np.array([r['tracker_s'] - r['anymaze_s'] for r in c]); a, b = np.array([r['anymaze_s'] for r in c]), np.array([r['tracker_s'] for r in c])
print(f'time, trials both ended: n={len(c)} r={np.corrcoef(a, b)[0, 1]:.3f} median offset {np.median(e):+.2f}s med|err| {np.median(abs(e)):.2f}s; over 5 s: {[r["test"] for r in c if abs(r["tracker_s"] - r["anymaze_s"]) > 5]}')
print('capped by one system only:', [(r['test'], r['anymaze_s'], r['tracker_s']) for r in good if (r['anymaze_s'] >= 29.5) != (r['tracker_s'] >= 29.5)])
for t in (10, 34, 41, 50, 62, 97, 98, 110, 116, 120, 21):
    r = rows[t - 1]; print(f"t{t} rat{r['rat_anymaze']} AM {r['anymaze_s']}s {r['anymaze_cm']}cm trk {r['tracker_s']}s {r['tracker_cm']}cm reached={r['reached']} rel={r['release_s']} res={r['time_residual_s']} agree={r['methods_agree']}")
