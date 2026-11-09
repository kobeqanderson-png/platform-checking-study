"""Tracks a long, uncut pool recording at 10 Hz. Analysis size matches the pilot's pool radius (~242 px).
Usage: track_recording.py <video> <out.csv>
Output: t_s, x_px, y_px (source pixels; blank if rejected), area (analysis pixels; hand or arm shows as large)."""
import csv, json, subprocess, sys
import cv2
import numpy as np

video, out = sys.argv[1:3]
TARGET_R, FPS, DARK, MIN_AREA, MAX_AREA = 242, 10, 90, 150, 9000
info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'json', video]))
SW, SH, DUR = info['streams'][0]['width'], info['streams'][0]['height'], float(info['format']['duration'])

def grab(t, w, h):
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(t), '-i', video, '-frames:v', '1', '-vf', f'scale={w}:{h},format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w)

def fit(w, h):
    med = np.median(np.stack([grab(t, w, h) for t in np.linspace(5, DUR - 5, 25)]), axis=0).astype(np.uint8)
    _, b = cv2.threshold(med, 150, 255, cv2.THRESH_BINARY)
    b = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
    keep = (pts[:, 0] > 3) & (pts[:, 0] < w - 4) & (pts[:, 1] > 3) & (pts[:, 1] < h - 4)
    x, y = pts[keep, 0], pts[keep, 1]
    cx, cy, c = np.linalg.lstsq(np.c_[2 * x, 2 * y, np.ones(len(x))], x ** 2 + y ** 2, rcond=None)[0]
    return float(cx), float(cy), float(np.sqrt(c + cx ** 2 + cy ** 2))

# Keep the source aspect ratio: some recordings are 4:3, and squashing them would turn the pool into an oval.
H0 = int(960 * SH / SW) // 2 * 2
_, _, r0 = fit(960, H0)
f = TARGET_R / r0
W, H = int(960 * f) // 2 * 2, int(H0 * f) // 2 * 2
cx, cy, r = fit(W, H)
SCALE = SW / W
yy, xx = np.mgrid[:H, :W]
mask = (xx - cx) ** 2 + (yy - cy) ** 2 < (0.93 * r) ** 2
print(f'pool source px=({cx * SCALE:.0f},{cy * SCALE:.0f},r{r * SCALE:.0f}) analysis={W}x{H} duration={DUR:.0f}s', flush=True)

p = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', video, '-vf', f'fps={FPS},scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['t_s', 'x_px', 'y_px', 'area']); k = 0
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        g = np.frombuffer(b, np.uint8).reshape(H, W)
        d = ((g < DARK) & mask).astype(np.uint8)
        d = cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        n, _, st, ce = cv2.connectedComponentsWithStats(d, connectivity=8)
        x = y = ''; a = 0
        if n > 1:
            i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); a = int(st[i, cv2.CC_STAT_AREA])
            if MIN_AREA <= a <= MAX_AREA: x, y = round(ce[i][0] * SCALE, 1), round(ce[i][1] * SCALE, 1)
        w.writerow([round(k / FPS, 2), x, y, a]); k += 1
p.stdout.close(); p.wait()
print(f'done frames={k}', flush=True)
