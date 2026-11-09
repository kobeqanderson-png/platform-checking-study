"""Historical: found the platform-pass stops whose 30 s values are now written into build_updated_anymaze.py. Video paths and d5 file names have changed since, so it will not rerun as is.
Finds trials where AnyMaze ended near a platform pass but the rat only settled much later, then renders frames."""
import csv, glob, os, re, subprocess
import numpy as np, cv2
from scipy.signal import medfilt
S = r'C:\Users\kobeq\AppData\Local\Temp\claude\fdae4b1b893f2873\2a043bed-5bb3-49ad-9a74-7abc4ecbcc1b\scratchpad'
P = r'C:\Users\kobeq\Videos\check_audit\tracking_pilot'; CR = r'C:\Users\kobeq\OneDrive\Pictures\Camera Roll'; CP = r'C:\Users\kobeq\Documents\checking protocol'
VID = {1: sorted(glob.glob(CR + r'\d1 videos\*.mp4')), 2: sorted(glob.glob(CR + r'\d2 videos\*.mp4')), 3: sorted(glob.glob(CP + r'\d3 videos\*.mp4')), 5: sorted(glob.glob(CP + r'\d5 videos\*.mp4')), 7: [r'C:\Users\kobeq\Videos\2026-11-04 09-49-40.mp4', r'C:\Users\kobeq\Videos\2026-11-04 10-44-54.mp4', r'C:\Users\kobeq\Videos\2026-11-04 11-07-52.mp4']}
POOL = {1: [(633, 367, 374), (632, 368, 370)], 2: [(641, 369, 379), (637, 367, 376)], 3: [(641, 370, 378)], 5: [(833, 566, 591), (999, 502, 711), (999, 502, 711), (833, 566, 591)], 7: [(930, 551, 511), (989, 553, 510), (989, 552, 510)]}
PLAT = {1: (151, -183), 2: (141, -182), 3: (142, -187), 5: (121, -174), 7: (119, -167)}; OFF = {1: -.1, 2: .05, 3: .1, 5: 1.3, 7: 1.75}; K = {1: .158, 2: .156, 3: .165, 5: .159, 7: .158}
DONE = {(3, 49), (3, 74), (3, 78), (3, 97), (5, 53), (5, 55), (5, 112), (5, 118), (7, 1), (7, 20), (7, 21), (7, 23), (7, 30), (7, 98), (7, 100)}
TR = {}
def track(d, n):
    if (d, n) not in TR:
        R = list(csv.DictReader(open(sorted(glob.glob(os.path.join(P, f'tracks_d{d}', f'file{n}_*.csv')))[0], newline='')))
        TR[d, n] = (np.array([float(q['t_s']) for q in R]), np.array([float(q['x_px'] or np.nan) for q in R]), np.array([float(q['y_px'] or np.nan) for q in R]))
    return TR[d, n]
def info(d, r):
    n = int(re.search(r'\d+', r['file']).group()); t, xp, yp = track(d, n); cx, cy, pr = POOL[d][n - 1]; s = 510 / pr; rel = float(r['release_s']); st = float(r['run_start_s'])
    x, y = (xp - cx) * s - PLAT[d][0], (yp - cy) * s - PLAT[d][1]; idx = np.where(~np.isnan(x) & (t >= st - .05))[0]; b = idx[0]
    for i in idx[1:]:
        if t[i] - t[b] > 4: break
        b = i
    end = float(t[b]); m = (t >= rel) & (t <= end) & ~np.isnan(x); tt, D = t[m] - rel, np.hypot(x[m], y[m]); settle = None
    for i in range(len(tt)):
        w = (tt >= tt[i]) & (tt <= tt[i] + 2)
        if tt[-1] >= tt[i] + 2 and D[w].max() < 70: settle = float(tt[i]); break
    near = np.where(D < 70)[0]; L = 0.0; m30 = tt <= 30; fx, fy = medfilt(x[m][m30], 3), medfilt(y[m][m30], 3); ax, ay = fx[0], fy[0]
    for u, v in zip(fx, fy):
        q = np.hypot(u - ax, v - ay)
        if q >= 20: L += q; ax, ay = u, v
    return dict(run=end - rel, settle=settle, first=float(tt[near[0]]) if len(near) else None, cm30=K[d] * L)
HIT = []
for d in VID:
    for r in csv.DictReader(open(os.path.join(P, f'd{d}_tracker_vs_anymaze.csv'), newline='')):
        if not r['release_s'] or (d, int(r['test'])) in DONE: continue
        am = float(r['anymaze_s'])
        if am >= 29: continue
        k = info(d, r); am2 = am + OFF[d]
        if k['run'] < am2 + 8: continue
        if k['settle'] is None or k['settle'] - am2 > 6:
            HIT.append((d, int(r['test']), r['rat'], r.get('match_confidence', '-'), am, float(r['anymaze_cm']), k['first'], k['settle'], round(k['run'], 1), round(k['cm30'], 1), r))
print('candidates', len(HIT))
for h in HIT: print(f"d{h[0]} t{h[1]} rat{h[2]} conf={h[3]} AM {h[4]}s {h[5]}cm first_near {h[6]} settle {h[7]} run {h[8]} path_to_30s {h[9]}cm")
tiles = []
for h in HIT[:14]:
    d, tn, r = h[0], h[1], h[10]; n = int(re.search(r'\d+', r['file']).group()); t, x, y = track(d, n); rel = float(r['release_s']); cx, cy, pr = POOL[d][n - 1]; s = pr / 510; px, py = PLAT[d]; am = h[4] + OFF[d]
    for lab, sec in (('AMend', am), ('+6', am + 6), ('settle', h[7] if h[7] else h[8] - 1)):
        tm = rel + sec; q = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', f'{tm:.2f}', '-i', VID[d][n - 1], '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
        w, hh = map(int, subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', VID[d][n - 1]]).decode().strip().split(','))
        if not q: continue
        img = np.frombuffer(q, np.uint8).reshape(hh, w, 3).copy(); cv2.circle(img, (int(cx + px * s), int(cy + py * s)), int(60 * s), (0, 200, 255), 2)
        m = (t >= tm - 4) & (t <= tm) & ~np.isnan(x); pts = np.c_[x[m], y[m]].astype(int)
        if len(pts) > 1: cv2.polylines(img, [pts], False, (0, 170, 0), 2)
        a = int(pr * 1.05); c = cv2.resize(img[max(cy - a, 0):cy + a, max(cx - a, 0):cx + a], (230, 230)); cv2.putText(c, f"d{d} t{tn} {lab} {sec:.1f}", (3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2); tiles.append(c)
while len(tiles) % 6: tiles.append(np.zeros((230, 230, 3), np.uint8))
if tiles: cv2.imwrite(os.path.join(S, 'sweep_sheet.jpg'), np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 70])
