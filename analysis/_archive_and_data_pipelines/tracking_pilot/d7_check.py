"""Marked frames from the long d7 recordings. Usage: d7_check.py <track-folder> <out.jpg> <fileN|label|second> ..."""
import csv, os, subprocess, sys
import cv2
import numpy as np
V = {'file1': r'C:\Users\kobeq\Videos\2026-11-04 09-49-40.mp4', 'file2': r'C:\Users\kobeq\Videos\2026-11-04 10-44-54.mp4', 'file3': r'C:\Users\kobeq\Videos\2026-11-04 11-07-52.mp4'}
N = {'file1': 'file1_09-49-40.csv', 'file2': 'file2_10-44-54.csv', 'file3': 'file3_11-07-52.csv'}
tracks, out, *picks = sys.argv[1:]
cache = {}; tiles = []
for p in picks:
    f, label, sec = p.split('|'); sec = float(sec)
    if f not in cache: cache[f] = list(csv.DictReader(open(os.path.join(tracks, N[f]), newline='')))
    r = cache[f][int(round(sec * 10))]
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(sec), '-i', V[f], '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3).copy()
    if r['x_px']: cv2.drawMarker(img, (int(float(r['x_px'])), int(float(r['y_px']))), (0, 0, 255), cv2.MARKER_CROSS, 70, 4)
    img = cv2.resize(img[:, 340:1640], (390, 324))
    cv2.putText(img, label, (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    tiles.append(img)
while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 75])
