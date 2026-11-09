"""Contact sheet: one frame just after each estimated release, for visual review.
Usage: release_sheet.py <clip-folder> <comparison.csv> <out.jpg> [seconds-after-release]"""
import csv, os, subprocess, sys
import cv2
import numpy as np
clips, comp, out = sys.argv[1:4]; after = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
tiles = []
for r in csv.DictReader(open(comp, newline='')):
    t = float(r['release_clip_s']) + after
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(t), '-i', os.path.join(clips, f"Day06_Checking_1p5cm_Rat{int(r['rat']):02d}.mp4"),
                          '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vf', 'scale=280:210', '-'], capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(210, 280, 3).copy()
    cv2.putText(img, f"R{r['rat']} {t:.1f}s", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    tiles.append(img)
while len(tiles) % 6: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 72])
