"""Frames with the tracked position marked, for trials where tracker and AnyMaze disagree.
Usage: flagged_check.py <clip-folder> <track-folder> <out.jpg> <rat:clip_second> ..."""
import csv, os, subprocess, sys
import cv2
import numpy as np
clips, tracks, out, *picks = sys.argv[1:]
tiles = []
for p in picks:
    rat, sec = p.split(':'); rat = int(rat); sec = float(sec)
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(sec), '-i', os.path.join(clips, f'Day06_Checking_1p5cm_Rat{rat:02d}.mp4'),
                          '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(1080, 1440, 3).copy()
    rows = list(csv.DictReader(open(os.path.join(tracks, f'rat{rat:02d}.csv'), newline='')))
    r = min(rows, key=lambda x: abs(float(x['t_clip_s']) - sec))
    if r['x_px']: cv2.drawMarker(img, (int(float(r['x_px'])), int(float(r['y_px']))), (0, 0, 255), cv2.MARKER_CROSS, 70, 4)
    img = cv2.resize(img, (400, 300))
    cv2.putText(img, f'R{rat} clip {sec:.0f}s', (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    tiles.append(img)
while len(tiles) % 3: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 75])
