"""Builds updated AnyMaze files from the originals and the camera tracks.
Values change only on the trials in REPLACE. Every other row keeps its AnyMaze values, and tracker readings go in appended columns.
Usage: build_updated_anymaze.py <Check.zip> <audit.csv> <tracking_pilot folder> <out folder> <scratch folder>"""
import contextlib, csv, glob, io, os, re, runpy, sys, zipfile
import numpy as np
from scipy.signal import medfilt
ZIP, AUDIT, P, OUT, SCR = sys.argv[1:]
Z = zipfile.ZipFile(ZIP)
RAWDIR = os.path.join(SCR, 'anymaze_raw'); Z.extractall(RAWDIR); RAW = lambda d: os.path.join(RAWDIR, 'Check', f'KAcd{d}.csv')
def load(script, *args, out):
    argv, sys.argv = sys.argv, [script, *args, out]
    with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path(os.path.join(P, script))
    sys.argv = argv; return g
# Reuse the analysis code so every parameter is the one the published results used.
D6 = load('compare_d6.py', os.path.join(P, 'tracks_d6'), RAW(6), out=os.path.join(SCR, 'rerun_d6.csv'))
D7 = load('d7_match.py', os.path.join(P, 'tracks_d7'), os.path.join(P, 'd7_segments.csv'), RAW(7), out=os.path.join(SCR, 'rerun_d7.csv'))
D8 = load('compare.py', os.path.join(P, 'tracks'), RAW(8), out=os.path.join(SCR, 'rerun_d8.csv'))
AUD = {(int(r['day']), int(r['test'])): r for r in csv.DictReader(open(AUDIT, encoding='utf-8', newline=''))}
TR = {d: {int(r['test']): r for r in csv.DictReader(open(os.path.join(P, f'd{d}_tracker_vs_anymaze.csv'), newline=''))} for d in (1, 2, 3, 5, 6, 7, 8)}
# Median tracker-minus-AnyMaze time on unflagged trials that both systems ended before the cap.
OFFSET = {}
for d in (1, 2, 3, 5, 7):
    e = [float(r['tracker_s']) - float(r['anymaze_s']) for r in TR[d].values() if r['group'] != 'audit_flagged' and r['reached'] == 'True' and float(r['anymaze_s']) < 29.5 and float(r['tracker_s']) < 29.5]
    OFFSET[d] = round(float(np.median(e)), 2)
def d7_run(start):
    return next(r for r in D7['runs'] if abs(float(r['start']) - start) < .05)
def d7_measure(start, cap=30.0):
    """Time to platform (raw) and calibrated path, stopping at platform entry or the 30 s cap, whichever is first."""
    r = d7_run(start); p = D7['TR'][r['file']]; m = (p['t'] >= float(r['start'])) & (p['t'] <= float(r['end'])); t, x, y, a = p['t'][m], p['x'][m], p['y'][m], p['a'][m]
    big = np.where(a > 1000)[0]; i0 = 0
    if len(big) and t[big[0]] <= t[0] + 5:
        i0 = big[0]
        for b in big:
            if t[b] - t[i0] > 1.0: break
            i0 = b
        i0 += 1
    ok = np.where(~np.isnan(x))[0]; ok = ok[ok >= i0]; tt = t[ok[0]:]
    fx, fy = medfilt(np.interp(tt, t[ok], x[ok]), 3), medfilt(np.interp(tt, t[ok], y[ok]), 3)
    ins = np.where(np.hypot(fx - D7['PX'], fy - D7['PY']) < D7['R'])[0]; lat = float(tt[ins[0]] - tt[0]) if len(ins) else np.inf
    e = np.searchsorted(tt - tt[0], min(lat, cap), side='right'); ax, ay, s = fx[0], fy[0], 0.0
    for u, v in zip(fx[:e], fy[:e]):
        d = np.hypot(u - ax, v - ay)
        if d >= 20: s += d; ax, ay = u, v
    return lat, D7['k'] * s
T1 = d7_measure(float(TR[7][1]['run_start_s'])); T30 = d7_measure(float(TR[7][30]['run_start_s'])); T20 = d7_measure(1116.8)
def d8_full(test, dur=120.0):
    rows = list(csv.DictReader(open(os.path.join(P, 'tracks', f'track_test{test:02d}.csv'), newline='')))
    ts = np.array([float(r['t_s']) for r in rows]); keep = ts <= dur; num = D8['num']; xy = np.array([[num(r['x_px']), num(r['y_px'])] for r in rows])[keep]; ts = ts[keep]
    f = ~np.isnan(xy[:, 0]); g = np.where(f)[0]; last = g[0]
    for i in g[1:]:
        if np.hypot(*(xy[i] - xy[last])) > 75 * max(i - last, 1): f[i] = False
        else: last = i
    p = dict(ts=ts, x=medfilt(np.interp(ts, ts[f], xy[f, 0]), 5), y=medfilt(np.interp(ts, ts[f], xy[f, 1]), 5))
    late = ts > float(D8['ref'][test]['dur'])
    return round(D8['k'] * D8['path_len'](p, D8['band']), 1), round(D8['p2_time'](p, D8['Rbest']), 1), 100 * f[late].mean() if late.any() else 100.0
T9 = d8_full(9)
def d6_segments(rat, dur):
    """Distance and P2 time per 30 s segment. The deadband anchor carries across segments so they sum to the trial total."""
    p = D6['T'][rat]; ts, x, y, _ = D6['clean'](p, p['release'], dur); ins = D6['inP2'](x, y, D6['R']); out = []; ax, ay = x[0], y[0]; tot = np.zeros(int(np.ceil(dur / 30)))
    for t, a, b in zip(ts, x, y):
        d = np.hypot(a - ax, b - ay)
        if d >= D6['band']: tot[min(int(t // 30), len(tot) - 1)] += d; ax, ay = a, b
    for i in range(len(tot)):
        m = (ts >= i * 30) & (ts < (i + 1) * 30) if i < len(tot) - 1 else ts >= i * 30; L = min(30.0, dur - i * 30)
        out.append((round(float(L), 1), round(float(D6['k'] * tot[i]), 2), round(float(ins[m].mean() * L), 1)))
    return out
s = lambda d, t: float(TR[d][t]['tracker_s']) - OFFSET[d]
PASS = 'AnyMaze stopped as the rat crossed the platform. Video shows it swim away and get guided on after the cap, so time set to cap and path measured to 30 s.'
# day, test: duration (None = keep), distance, reason.
REPLACE = {
    # Distances to 30 s below come from find_platform_pass_stops.py. Each stop was checked on video.
    (1, 92): (30.0, 837.3, PASS + ' Lab notes for rat 25: swam through the platform, never sat on it.'),
    (3, 39): (30.0, 599.7, 'AnyMaze duration disagrees with its own start time in the .szd database: the clock puts the end at 34.7 s after release and the rat settled at 33.3 s. Video checked.'),
    (1, 22): (20.0, float(TR[1][22]['tracker_cm']), 'AnyMaze duration disagrees with its own start time in the .szd database: the clock puts the end at 20.5 s after release and the rat settled at 20.0 s. Video checked.'),
    (2, 112): (19.4, 384.0, 'AnyMaze duration disagrees with its own start time in the .szd database: the clock puts the end at 19.9 s after release and the rat settled at 19.4 s. Video checked.'),
    (3, 25): (14.5, float(TR[3][25]['tracker_cm']), 'AnyMaze duration disagrees with its own start time in the .szd database: the clock puts the end at 14.2 s after release and the rat settled at 14.5 s. Video checked.'),
    (3, 51): (9.9, float(TR[3][51]['tracker_cm']), 'AnyMaze duration disagrees with its own start time in the .szd database: the clock puts the end at 10.5 s after release and the rat settled at 9.9 s. Video checked.'),
    (3, 74): (29.0, float(TR[3][74]['tracker_cm']), 'AnyMaze duration disagrees with its own start time in the .szd database: the clock puts the end at 29.2 s after release and the rat settled at 29.0 s. Video checked.'),
    (3, 59): (30.0, 753.3, 'AnyMaze started 23.7 s late by the .szd clock, so the rat only settled at 39.9 s and the clock puts the end at 39.4 s. Time set to cap and path measured to 30 s. Video checked.'),
    (3, 49): (None, float(TR[3][49]['tracker_cm']), 'Distance only: AnyMaze path has speed jumps. Time agrees within tracker error.'),
    (3, 97): (None, float(TR[3][97]['tracker_cm']), 'Distance only: AnyMaze implies 60 cm/s with tracking gaps. Time agrees. Other 3 trials for this rat agree within 0.4 s.'),
    (3, 78): (round(s(3, 78), 1), float(TR[3][78]['tracker_cm']), 'AnyMaze ended at 20.1 s with the rat swimming far from the platform (video at 20.1 s and 23 s). It arrives at 25.5 s.'),
    (5, 55): (round(s(5, 55), 1), float(TR[5][55]['tracker_cm']), 'AnyMaze ended at 0.2 s with the hand still holding the rat. Video shows a long swim to the platform.'),
    (5, 112): (round(s(5, 112), 1), float(TR[5][112]['tracker_cm']), 'AnyMaze ended at 0.9 s, rat still at the wall. Video shows it swimming to the platform.'),
    (5, 118): (None, float(TR[5][118]['tracker_cm']), 'Distance only: tracking gaps made AnyMaze under-read. Time agrees after offset.'),
    (7, 1): (30.0, round(T1[1], 1), 'AnyMaze ran past the 30 s cap to 37.7 s and picked up the hand. Rat still swimming at 30 s, so time set to cap and path measured to 30 s.'),
    (7, 20): (round(min(T20[0] - OFFSET[7], 30.0), 1) if np.isfinite(T20[0]) else 30.0, round(T20[1], 1), 'AnyMaze ended at 6.6 s while rat was swimming (video). Run was skipped by the aligner, then assigned by its position right after test 19.'),
    (7, 21): (None, float(TR[7][21]['tracker_cm']), 'Distance only: AnyMaze 6.5 cm is not possible for this swim. Time agrees after offset.'),
    (7, 23): (9.4, float(TR[7][23]['tracker_cm']), 'AnyMaze started 8.3 s before release by its own .szv start time, and it implies 95 cm/s. Its end falls 9.4 s after release, which matches the rat settling after the +1.6 s d7 camera offset.'),
    (7, 30): (30.0, round(T30[1], 1), 'AnyMaze ended at 19.9 s as the rat passed the platform. Video shows it swim away and still in the pool at 30 s, so time set to cap and path measured to 30 s.'),
    (7, 98): (round(s(7, 98), 1), float(TR[7][98]['tracker_cm']), 'AnyMaze ended at 0.4 s. Video shows the rat swimming at 6 s and 12 s.'),
    (7, 100): (round(s(7, 100), 1), float(TR[7][100]['tracker_cm']), 'The real swim was at 2218-2247 s in the recording, but AnyMaze test 100 only started near 2272 s, after that rat was out, so its 2.8 s and 248 cm do not describe the swim. Values measured from the swim on video.'),
    (8, 4): (None, float(TR[8][4]['tracker_dist']), 'AnyMaze tracked 64.0% of frames. Distance and P2 from camera; distance may over-read for a still rat.'),
    (8, 9): (120.0, T9[0], f'AnyMaze ended at 75.5 s (Pfound). Rat tracked in {T9[2]:.0f}% of frames to 120 s, so measured over the full probe.'),
    (8, 25): (None, float(TR[8][25]['tracker_dist']), 'AnyMaze tracked 74.9% of frames. Distance and P2 from camera; distance may over-read for a still rat.'),
}
# d4: the save time of each test gives the true end of the trial. See d4_clock_check.py.
CM = {d: {int(r['test']): r for r in csv.DictReader(open(os.path.join(P, f'd{d}_clock_match.csv'), newline=''))} for d in (1, 2, 3, 7)}
D4T = {int(r['test']): r for r in csv.DictReader(open(os.path.join(P, 'd4_tracker_vs_anymaze.csv'), newline=''))}
D4C = {int(r['test']): r for r in csv.DictReader(open(os.path.join(P, 'd4_clock_check.csv'), newline=''))}
for x in (2, 12, 18, 23, 25, 62, 72, 98, 99, 120):
    c = D4C[x]; REPLACE[(4, x)] = (float(c['new_s']), float(c['path_to_end_cm']), f"AnyMaze duration {c['anymaze_s']} s disagrees with its own save time, which puts the end at {c['end_by_save_s']} s after release. The rat settled on the platform at {c['settle_s']} s (capped at 30 s). Video checked.")
REPLACE[(4, 41)] = (float(D4C[41]['new_s']), float(D4C[41]['path_to_end_cm']), 'AnyMaze has tracking gaps and 108 cm for this swim. Save time and settle time both put the end near 10.6 s. Video checked.')
REPLACE[(4, 97)] = (float(D4C[97]['new_s']), float(D4C[97]['path_to_end_cm']), 'Lab notes: tracking seemed to stop mid-trial on rat 27 trial 1, and AnyMaze has only 87 cm. Save time and settle time both put the end near 16.5 s. Video checked.')
P2_8 = {4: float(TR[8][4]['tracker_p2_s']), 9: T9[1], 25: float(TR[8][25]['tracker_p2_s'])}
D6_REPLACE = {3: 'AnyMaze tracked 26.3% of frames. Video shows the rat on the platform at 30 s and 90 s.', 18: 'AnyMaze tracked 27.5% of frames. Video shows the rat on the platform at 30 s and 90 s.',
              22: 'AnyMaze tracked 42.9% of frames. Video shows the rat on the platform at 30 s and 90 s.', 4: 'AnyMaze ended at 4.6 s (Pfound) and missed the probe. Video shows the rat in the pool at 40 s and 100 s, so 120 s rebuilt from camera.'}
# Metadata columns are kept on replaced rows. All other measurements are blanked because they came from the bad AnyMaze path.
META = {'Test', 'Animal', 'Stage', 'Trial', 'Apparatus', 'Reason ended', 'Date', 'Day of week', 'Time', 'Time of day', 'User', 'Test notes', 'Recorded video file', 'Segment of test', 'Weight (g)', 'Sex', 'Treatment', 'Group', 'Strain', 'Age'}
NEW = ['Retrack status', 'Retrack time (s)', 'Retrack distance (cm)', 'Retrack P2 time (s)', 'Retrack match confidence', 'Retrack note']
# Outcome of the review of trials that could not be settled automatically. Tracker readings on MISMATCH runs are blanked because the run is not this trial.
GROUPS = [
    ('keep_anymaze', 'Tracker run was interrupted, so it gives no reading. AnyMaze shows a normal capped swim.', [(1, 38), (1, 78), (2, 40), (2, 58), (2, 77), (2, 117), (5, 46), (5, 63), (5, 76), (7, 42)]),
    ('keep_anymaze', 'Tracker marked a pass near the platform. The rat settled on it much later, matching AnyMaze.', [(1, 55), (3, 1), (3, 12), (3, 16), (3, 82), (3, 103), (3, 112)]),
    ('keep_anymaze', 'This tracker run does not fit this trial (likely misaligned). AnyMaze is internally consistent. Tracker readings removed.', [(1, 39), (1, 105), (1, 110), (1, 112), (2, 110), (2, 111), (2, 112), (3, 92)]),
    ('keep_anymaze', 'Time agrees at the cap. Tracker distance over the first 30 s is within 17% of AnyMaze, not enough to overrule it.', [(1, 106), (3, 73)]),
    ('keep_anymaze', 'Short swim is real. The time gap is under 2.5 s, which fits tracker release lag.', [(2, 115), (3, 114), (5, 47), (5, 83), (5, 115), (7, 99)]),
    ('keep_anymaze', 'Probe rat stayed on the platform or agrees on P2 time. No change justified.', [(6, 11), (6, 30), (8, 22)]),
    ('keep_anymaze', 'AnyMaze ended at 23.9 s with the rat swimming on video, but rat 13 has 3 recording runs for 4 trials and lab notes say it left the platform after finding it, so this match is not reliable. Tracker readings removed.', [(3, 740)]),
    ('no_video', 'No footage for this trial, so it cannot be verified.', [(1, 104), (5, 21), (5, 29)]),
    ('keep_anymaze', 'Tracker and save time agree with AnyMaze time closely enough. No change justified.', [(4, 34), (4, 50), (4, 110), (4, 116)]),
    ('keep_anymaze', 'This trial has no separate recording run: it merges with test 9, so the video cannot check it. Tracker readings removed.', [(4, 10)]),
    ('excluded', 'AnyMaze ended at 6.8 s with the rat swimming, but the recording stops 12.6 s into the trial, so no true value exists. Latency is at least about 11 s. Measurements blanked.', [(5, 53)]),
]
VERDICT = {k: (v, why) for v, why, keys in GROUPS for k in keys}
MISMATCH = set(GROUPS[2][2]) | {(3, 74)}
# Lab notes: d4 rats 13-15 were logged as 14-16 and rat 16 as 13 in AnyMaze. The test order 14, 15, 16, 13 matches.
D4_IDS = {'14': '13', '15': '14', '16': '15', '13': '16'}
ELEVEN = 'Rat 12 as AnyMaze says. The video file says 11 because the AnyMaze list still had a slot for rat 11, which died before d1.'
NOTE_EXTRA = {**{(1, x): ELEVEN for x in range(69, 73)}, **{(2, x): ELEVEN for x in range(69, 73)}, **{(3, x): ELEVEN for x in range(68, 72)}, (6, 18): ELEVEN,
              (3, 89): 'Lab notes: start E messed up, tracking failure on rat 25. AnyMaze and tracker times agree.', **{(4, x): 'IMPORTANT: lab notes for d4 say rat 10 dived under water while swimming and had a nose bleed. The trial was not recorded, so this applies to all 4 trials.' for x in range(65, 69)}, **{(3, x): 'Lab notes confirm one trial was missed for this rat on d3, so it has 3 trials.' for x in (37, 38, 39, 100, 101, 102)}, (6, 11): 'AnyMaze started about 20 s after release by the .szd clock, so its 113.5 s covers a later window. The rat stayed on the platform either way.', (8, 20): 'AnyMaze started about 10 s after release by the .szd clock. The rat stayed on the platform, so P2 time is not affected.', (5, 87): 'AnyMaze ended at 25.4 s with the rat away from the platform, but distances do not fit, so the match is doubtful. Values kept.'}
def agrees(d, tr):
    """True when a flagged trial's tracker reading matches AnyMaze: time within 2 s after offset and distance within 25%, or for probes distance within 15% and P2 within 7 s."""
    if not tr: return False
    if d in (6, 8):
        a, b = float(tr['anymaze_dist']), float(tr['tracker_dist'])
        return abs(a - b) <= .15 * a and abs(float(tr['anymaze_p2_s']) - float(tr['tracker_p2_s'])) <= 7
    if tr['reached'] != 'True' or float(tr['tracker_s']) >= 29.5 or float(tr['anymaze_s']) >= 29.5: return False
    return abs(float(tr['tracker_s']) - OFFSET[d] - float(tr['anymaze_s'])) <= 2 and abs(float(tr['tracker_cm']) - float(tr['anymaze_cm'])) <= .25 * max(float(tr['anymaze_cm']), 1)
os.makedirs(OUT, exist_ok=True); CHANGES = []; REVIEW = []; COUNT = {}
fmt = lambda v, n=2: '' if v is None else f'{v:.{n}f}'
for d in range(1, 9):
    text = Z.read(f'Check/KAcd{d}.csv').decode('latin-1'); rows = list(csv.reader(io.StringIO(text, newline='')))
    H = rows[0]; assert all(len(r) == len(H) for r in rows[1:])
    ci = {n: H.index(n) for n in ('Test', 'Animal', 'Duration (s)', 'Distance (cm)', 'Mean speed (cm/s)')}
    p2i = H.index('P2: SE : time (s)') if d in (6, 8) else None
    segi = H.index('Segment of test') if 'Segment of test' in H else None
    keep = {i for i, n in enumerate(H) if n in META}; out = [H + NEW]; status = {}
    for r in rows[1:]:
        t = int(r[ci['Test']]); rat = r[ci['Animal']]; tr = TR.get(d, {}).get(t); cm = CM.get(d, {}).get(t); clock_ok = bool(cm and abs(float(cm['lag_s'])) < 3.5)
        if cm and (not clock_ok or cm['old_match_agrees'] != 'True'): tr = None   # The start time shows the earlier block match used a different run.
        a = AUD.get((d, t), {}); row = list(r); ext = dict.fromkeys(NEW, ''); verdict = a.get('verdict', 'ok')
        ext['Retrack status'] = 'tracked_unchanged' if tr else 'not_tracked'
        if tr: ext['Retrack match confidence'] = tr.get('match_confidence', 'not_scored')
        if tr and d in (1, 2, 3, 5, 7):
            reached = tr['reached'] == 'True'; ts = tr['tracker_s']
            if ts not in ('', 'nan') and (reached or float(ts) >= 30):
                ext['Retrack time (s)'] = ts if reached else ''   # A run that ended without reaching the platform gives no real time.
                if reached and float(ts) < 29.5: ext['Retrack distance (cm)'] = tr['tracker_cm']   # Distances on capped trials run past 30 s, so they are withheld.
        if cm:
            ext['Retrack time (s)'] = cm['settle_s'] if clock_ok else ''; ext['Retrack match confidence'] = 'clock_match' if clock_ok else 'no_matching_run'
            if clock_ok: ext['Retrack status'] = 'tracked_unchanged'
            if not tr: ext['Retrack distance (cm)'] = ''
        if d == 8 and tr:
            ext['Retrack time (s)'] = r[ci['Duration (s)']]; ext['Retrack distance (cm)'] = tr['tracker_dist']; ext['Retrack P2 time (s)'] = tr['tracker_p2_s']; ext['Retrack match confidence'] = 'one_clip_per_test'
        if d == 6 and tr:
            ext['Retrack match confidence'] = 'one_clip_per_test'
            q = 120.0 if t in D6_REPLACE else float(tr['anymaze_dur']); seg = d6_segments(int(rat), q); i = ['0 - 30 secs.', '30 - 60 secs.', '60 - 90 secs.', '90 - 120 secs.'].index(r[segi])
            ext['Retrack time (s)'], ext['Retrack distance (cm)'], ext['Retrack P2 time (s)'] = seg[i]
            if t in D6_REPLACE:
                for j in range(len(row)):
                    if j not in keep: row[j] = ''
                row[ci['Duration (s)']], row[ci['Distance (cm)']], row[p2i] = fmt(seg[i][0], 1), fmt(seg[i][1]), fmt(seg[i][2], 1); row[ci['Mean speed (cm/s)']] = fmt(seg[i][1] / seg[i][0])
                ext['Retrack status'] = 'replaced'; ext['Retrack note'] = D6_REPLACE[t]
                CHANGES.append(dict(day=d, test=t, rat=rat, segment=r[segi], old_duration_s=r[ci['Duration (s)']], new_duration_s=row[ci['Duration (s)']], old_distance_cm=r[ci['Distance (cm)']], new_distance_cm=row[ci['Distance (cm)']], old_p2_s=r[p2i], new_p2_s=row[p2i], raw_tracker_time_s='', day_time_offset_s='', reason=D6_REPLACE[t]))
        if d == 4 and t in D4T:
            q = D4T[t]; ext['Retrack status'] = 'tracked_unchanged'; ext['Retrack match confidence'] = 'save_timestamp'
            if t not in (6, 10) and q['reached'] == 'True' and 0 < float(q['tracker_s']) < 29.5: ext['Retrack time (s)'] = q['tracker_s']; ext['Retrack distance (cm)'] = q['tracker_cm']
        if (d, t) in REPLACE:
            nd, ndist, why = REPLACE[(d, t)]; old = list(r)
            for j in range(len(row)):
                if j not in keep: row[j] = ''
            dur = nd if nd is not None else float(r[ci['Duration (s)']])
            row[ci['Duration (s)']] = fmt(dur, 1); row[ci['Distance (cm)']] = fmt(ndist); row[ci['Mean speed (cm/s)']] = fmt(ndist / dur)
            if d == 8: row[p2i] = fmt(P2_8[t], 1)
            ext['Retrack status'] = 'replaced'; ext['Retrack note'] = why
            if tr is None and t == 20: ext['Retrack time (s)'] = fmt(T20[0], 1) if np.isfinite(T20[0]) else ''; ext['Retrack match confidence'] = 'assigned_by_position'; ext['Retrack distance (cm)'] = fmt(T20[1], 1)
            if d == 7 and t == 1: ext['Retrack time (s)'] = ''; ext['Retrack distance (cm)'] = fmt(T1[1], 1)
            CHANGES.append(dict(day=d, test=t, rat=rat, segment='', old_duration_s=old[ci['Duration (s)']], new_duration_s=row[ci['Duration (s)']], old_distance_cm=old[ci['Distance (cm)']], new_distance_cm=row[ci['Distance (cm)']], old_p2_s=old[p2i] if p2i is not None else '', new_p2_s=row[p2i] if p2i is not None else '', raw_tracker_time_s=(tr or {}).get('tracker_s', ''), day_time_offset_s=OFFSET.get(d, '') if nd not in (None, 30.0, 120.0) else '', reason=why))
        if ext['Retrack status'] != 'replaced' and t in status:   # Later d6 segment rows take their test's status.
            ext['Retrack status'], ext['Retrack note'] = status[t]
        elif ext['Retrack status'] != 'replaced':
            issues = []
            if verdict != 'ok' and agrees(d, tr): ext['Retrack status'] = 'flag_not_confirmed'; ext['Retrack note'] = f"audit flag ({a.get('flags', '')}) not confirmed: tracker agrees with AnyMaze"
            elif verdict != 'ok': issues.append(f"audit {verdict}: {a.get('flags', '')}" + ('' if tr or clock_ok or d == 4 else '; not on video'))
            if tr and d in OFFSET and tr['tracker_s'] not in ('', 'nan') and tr['reached'] == 'True' and abs(float(tr['tracker_s']) - OFFSET[d] - min(float(tr['anymaze_s']), 30)) > 5: issues.append(f"time disagrees: AnyMaze {tr['anymaze_s']} s, tracker {tr['tracker_s']} s")
            if tr and d in OFFSET and tr['reached'] != 'True': issues.append(f"tracker run ended without a platform arrival (AnyMaze {tr['anymaze_s']} s)")
            if issues:
                v, why = VERDICT.get((d, t), ('keep_anymaze', 'The start-time clock supports AnyMaze here. The earlier tracker reading was a pass near the platform.')); ext['Retrack status'] = v; ext['Retrack note'] = why
                if (d, t) in MISMATCH: ext['Retrack time (s)'] = ext['Retrack distance (cm)'] = ''
                if v == 'excluded':
                    ext['Retrack time (s)'] = ext['Retrack distance (cm)'] = ''
                    row = [c if j in keep else '' for j, c in enumerate(r)]
                    CHANGES.append(dict(day=d, test=t, rat=rat, segment='', old_duration_s=r[ci['Duration (s)']], new_duration_s='', old_distance_cm=r[ci['Distance (cm)']], new_distance_cm='', old_p2_s='', new_p2_s='', raw_tracker_time_s='', day_time_offset_s='', reason=why))
                REVIEW.append(dict(day=d, test=t, rat=rat, anymaze_duration_s=tr['anymaze_dur'] if d == 6 and tr else r[ci['Duration (s)']], anymaze_distance_cm=tr['anymaze_dist'] if d == 6 and tr else r[ci['Distance (cm)']], tracker_time_s=(tr or {}).get('tracker_s', ''), tracker_distance_cm=(tr or {}).get('tracker_cm', (tr or {}).get('tracker_dist', '')), match_confidence=(tr or {}).get('match_confidence', ''), issue=' | '.join(issues), verdict=v, verdict_reason=why))
        if d == 4 and rat in D4_IDS and 73 <= t <= 88:
            row[ci['Animal']] = D4_IDS[rat]; ext['Retrack status'] = 'relabeled'; ext['Retrack note'] = f'AnyMaze logged this rat as {rat}. Lab notes and test order show it was rat {D4_IDS[rat]}.'
            if t % 4 == 1: CHANGES.append(dict(day=d, test=t, rat=D4_IDS[rat], segment='', old_duration_s='', new_duration_s='', old_distance_cm='', new_distance_cm='', old_p2_s='', new_p2_s='', raw_tracker_time_s='', day_time_offset_s='', reason=ext['Retrack note'] + f' Applies to tests {t} to {t + 3}.', old_animal=rat, new_animal=D4_IDS[rat]))
        if (d, t) in NOTE_EXTRA: ext['Retrack note'] = (ext['Retrack note'] + ' | ' if ext['Retrack note'] else '') + NOTE_EXTRA[(d, t)]
        status.setdefault(t, (ext['Retrack status'], ext['Retrack note']))
        out.append(row + [ext[n] for n in NEW])
        # Test 4 on d6 stopped inside its first segment, so the other 3 segments are new rows.
        if d == 6 and t == 4:
            for i, lab in ((1, '30 - 60 secs.'), (2, '60 - 90 secs.'), (3, '90 - 120 secs.')):
                seg = d6_segments(4, 120.0)[i]; add = [c if j in keep else '' for j, c in enumerate(r)]; add[segi] = lab
                add[ci['Duration (s)']], add[ci['Distance (cm)']], add[p2i] = fmt(seg[0], 1), fmt(seg[1]), fmt(seg[2], 1); add[ci['Mean speed (cm/s)']] = fmt(seg[1] / seg[0])
                out.append(add + ['replaced', fmt(seg[0], 1), fmt(seg[1]), fmt(seg[2], 1), 'one_clip_per_test', 'Row added: ' + D6_REPLACE[4]])
                CHANGES.append(dict(day=d, test=4, rat=rat, segment=lab, old_duration_s='', new_duration_s=fmt(seg[0], 1), old_distance_cm='', new_distance_cm=fmt(seg[1]), old_p2_s='', new_p2_s=fmt(seg[2], 1), raw_tracker_time_s='', day_time_offset_s='', reason='Row added: ' + D6_REPLACE[4]))
    with open(os.path.join(OUT, f'KAcd{d}.csv'), 'w', encoding='latin-1', newline='') as f:
        csv.writer(f, lineterminator='\r\n').writerows(out)
    COUNT[d] = {k: sum(1 for x in out[1:] if x[-6] == k) for k in ('replaced', 'relabeled', 'keep_anymaze', 'no_video', 'excluded', 'flag_not_confirmed', 'tracked_unchanged', 'not_tracked')}
for name, data in (('changes.csv', CHANGES), ('review_list.csv', REVIEW)):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()) + (['old_animal', 'new_animal'] if name == 'changes.csv' else []), restval=''); w.writeheader(); w.writerows(data)
print('weight/sex example:', [(n, c) for n, c in zip(H, rows[1]) if n in ('Weight (g)', 'Sex')])
print('time offsets:', OFFSET); print('d7 t1', T1, 'd7 t20', T20, 'd8 t9', T9)
print('rows by status:', COUNT); print('change rows', len(CHANGES), 'trials', len({(c['day'], c['test']) for c in CHANGES}), 'review', len(REVIEW))
for c in CHANGES: print(c['day'], c['test'], 'rat' + c['rat'], c['segment'], c['old_duration_s'], '->', c['new_duration_s'], '|', c['old_distance_cm'], '->', c['new_distance_cm'], '|', c['old_p2_s'], '->', c['new_p2_s'])
