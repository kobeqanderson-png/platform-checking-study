"""Tracks the d6 clips (1440x1080, no overlay, pool slightly cropped at the top).
Analysis size is chosen so the pool has the same pixel radius as the d8 pilot, keeping the blob limits comparable.
Records the whole clip, because release times are estimated afterwards.
Usage: track_d6.py <clip-folder> <out-folder> [--rats 2,3]
Output per rat: t_clip_s, x_px, y_px (1440x1080 pixels; blank if rejected), area_px, largest_dark_px (analysis pixels)."""
import argparse, csv, glob, os, re, subprocess
import cv2
import numpy as np

SRC_W, W, H, FPS = 1440, 648, 486, 10
SCALE = SRC_W / W
DARK, MIN_AREA, MAX_AREA = 90, 150, 9000

def frames(path):
    p = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', path, '-vf', f'fps={FPS},scale={W}:{H},format=gray',
                          '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        yield np.frombuffer(b, np.uint8).reshape(H, W)
    p.stdout.close(); p.wait()

def find_pool(sample):
    med = np.median(np.stack(sample), axis=0).astype(np.uint8)
    _, b = cv2.threshold(med, 150, 255, cv2.THRESH_BINARY)
    b = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
    # Least-squares circle using only edge points away from the frame border, since the pool is cropped.
    keep = (pts[:, 0] > 3) & (pts[:, 0] < W - 4) & (pts[:, 1] > 3) & (pts[:, 1] < H - 4)
    x, y = pts[keep, 0], pts[keep, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    cx, cy, c = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)[0]
    return float(cx), float(cy), float(np.sqrt(c + cx ** 2 + cy ** 2))

def locate(gray, mask):
    d = ((gray < DARK) & mask).astype(np.uint8)
    d = cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, _, st, ce = cv2.connectedComponentsWithStats(d, connectivity=8)
    if n <= 1: return None, None, 0
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); a = int(st[i, cv2.CC_STAT_AREA])
    if not MIN_AREA <= a <= MAX_AREA: return None, None, a
    return round(ce[i][0] * SCALE, 1), round(ce[i][1] * SCALE, 1), a

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('clips'); ap.add_argument('out'); ap.add_argument('--rats', default='')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    want = {int(x) for x in a.rats.split(',') if x}
    for path in sorted(glob.glob(os.path.join(a.clips, '*.mp4'))):
        rat = int(re.search(r'Rat(\d+)', path).group(1))
        if want and rat not in want: continue
        sample = [f.copy() for k, f in enumerate(frames(path)) if k % 100 == 0]
        cx, cy, r = find_pool(sample)
        yy, xx = np.mgrid[:H, :W]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 < (0.93 * r) ** 2
        rows = []
        for k, f in enumerate(frames(path)):
            x, y, ar = locate(f, mask); rows.append((round(k / FPS, 2), x, y, ar))
        with open(os.path.join(a.out, f'rat{rat:02d}.csv'), 'w', newline='') as fh:
            w = csv.writer(fh); w.writerow(['t_clip_s', 'x_px', 'y_px', 'area']); w.writerows(rows)
        ok = sum(1 for q in rows if q[1] is not None)
        print(f'rat {rat:>2} pool=({cx*SCALE:.0f},{cy*SCALE:.0f},r{r*SCALE:.0f}) frames={len(rows)} found={100*ok/len(rows):.1f}%', flush=True)

if __name__ == '__main__':
    main()
