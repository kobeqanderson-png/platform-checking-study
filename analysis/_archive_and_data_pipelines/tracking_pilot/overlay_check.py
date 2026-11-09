"""Draws tracked positions on sampled frames so a person can verify them.
Usage: overlay_check.py <clip-folder> <clip_manifest.csv> <track-folder> <out.jpg> <test:second> [<test:second> ...]"""
import csv, os, subprocess, sys
import cv2
import numpy as np
clips, manifest, tracks, out, *picks = sys.argv[1:]
M = {r['test']: r for r in csv.DictReader(open(manifest, newline=''))}
tiles = []
for p in picks:
    test, sec = p.split(':'); sec = float(sec)
    off = float(M[test]['release_offset_in_clip_s'])
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(sec + off), '-i', os.path.join(clips, f'Test {test}.mp4'),
                          '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3).copy()
    rows = list(csv.DictReader(open(os.path.join(tracks, f'track_test{int(test):02d}.csv'), newline='')))
    r = min(rows, key=lambda x: abs(float(x['t_s']) - sec))
    if r['x_px']:
        c = (int(float(r['x_px'])), int(float(r['y_px'])))
        cv2.drawMarker(img, c, (0, 0, 255), cv2.MARKER_CROSS, 60, 4)
        label = f"t{test} {sec:.0f}s area={r['area_px']}"
    else:
        label = f"t{test} {sec:.0f}s NOT FOUND"
    cv2.putText(img, label, (260, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
    tiles.append(cv2.resize(img[:, 260:1660], (560, 432)))
while len(tiles) % 3: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 75])
