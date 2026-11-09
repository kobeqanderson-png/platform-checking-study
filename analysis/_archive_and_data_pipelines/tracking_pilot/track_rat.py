"""Dark-blob rat tracker for the top-down pool videos.

Finds the largest dark region inside the detected pool, at a fixed sample rate.
Usage:
  track_rat.py <clip-folder> <clip_manifest.csv> <out-folder> [--tests 7,12] [--overlay]
Writes one CSV per test with: t_s (seconds since release), x_px, y_px, area_px (full-frame pixels).
"""
import argparse, csv, os, subprocess, sys
import cv2
import numpy as np

W, H, FPS = 960, 540, 10          # analysis size and sample rate
SCALE = 1920 / W
DARK = 90                         # grey level below which a pixel counts as rat
MIN_AREA, MAX_AREA = 150, 9000    # plausible rat blob area at analysis size

def read_frames(path, seek=0.0):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(seek), '-i', path,
           '-vf', f'fps={FPS},scale={W}:{H},format=gray', '-f', 'rawvideo', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = W * H
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(H, W)
    p.stdout.close(); p.wait()

def find_pool(frames):
    """Pool = large bright circle; estimated from the median of sampled frames."""
    med = np.median(np.stack(frames), axis=0).astype(np.uint8)
    _, bright = cv2.threshold(med, 150, 255, cv2.THRESH_BINARY)
    # Opening removes the on-screen labels and timestamp so they cannot stretch the circle.
    bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    m = cv2.moments(c)
    return m['m10'] / m['m00'], m['m01'] / m['m00'], float(np.sqrt(cv2.contourArea(c) / np.pi))

def locate(gray, mask):
    dark = ((gray < DARK) & mask).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, _, stats, cent = cv2.connectedComponentsWithStats(dark, connectivity=8)
    if n <= 1: return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    a = int(stats[i, cv2.CC_STAT_AREA])
    if not MIN_AREA <= a <= MAX_AREA: return None
    return float(cent[i][0]), float(cent[i][1]), a

def track(path, offset, swim):
    samples = []
    for k, f in enumerate(read_frames(path)):
        if k % 100 == 0: samples.append(f.copy())
    cx, cy, r = find_pool(samples)
    yy, xx = np.mgrid[:H, :W]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 < (0.93 * r) ** 2   # inset to drop the rim
    rows = []
    for k, f in enumerate(read_frames(path)):
        t = k / FPS - offset
        if t < 0 or t > swim: continue
        hit = locate(f, mask)
        rows.append((round(t, 2), *(np.round(np.array(hit[:2]) * SCALE, 1) if hit else (None, None)), int(hit[2] * SCALE ** 2) if hit else 0))
    return rows, (cx * SCALE, cy * SCALE, r * SCALE)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clips'); ap.add_argument('manifest'); ap.add_argument('out')
    ap.add_argument('--tests', default=''); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    want = set(a.tests.split(',')) if a.tests else None
    pools = []
    for m in csv.DictReader(open(a.manifest, newline='')):
        if want and m['test'] not in want: continue
        path = os.path.join(a.clips, f"Test {m['test']}.mp4")
        rows, pool = track(path, float(m['release_offset_in_clip_s']), float(m['swim_s']))
        with open(os.path.join(a.out, f"track_test{int(m['test']):02d}.csv"), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['t_s', 'x_px', 'y_px', 'area_px']); w.writerows(rows)
        found = sum(1 for r in rows if r[1] is not None)
        pools.append((m['test'], m['animal'], *[round(v, 1) for v in pool], len(rows), round(100 * found / max(len(rows), 1), 1)))
        print(f"test {m['test']:>2} a{m['animal']:>2} pool=({pool[0]:.0f},{pool[1]:.0f},r{pool[2]:.0f}) frames={len(rows)} found={pools[-1][-1]}%", flush=True)
    with open(os.path.join(a.out, 'run_summary.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['test', 'animal', 'pool_x', 'pool_y', 'pool_r', 'frames', 'found_pct']); w.writerows(pools)

if __name__ == '__main__':
    main()
