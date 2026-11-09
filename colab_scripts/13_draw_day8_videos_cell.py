# %% 8. Draw the videos on the original clips and save them to Drive. Finished videos are skipped on rerun.
import os, shutil, subprocess
from pathlib import Path
import cv2, numpy as np, pandas as pd
try:
    from google.colab import drive
    drive.mount("/content/drive")
except ImportError:
    pass

RUN_DIR = Path(os.environ.get("DRAW_RUN", "/content/drive/MyDrive/sp1DLC/Colab_Training_Runs/KAcheck_d6d8_20261107"))
CLIP_DIR = Path(os.environ.get("DRAW_CLIPS", "/content/drive/MyDrive/sp1DLC/d8_clips"))
TRACKS = RUN_DIR / "d8_tracks"
VIDEOS = Path(os.environ.get("DRAW_OUT", str(RUN_DIR / "d8_videos_cutoff03")))
DRAW_TMP = Path(os.environ.get("DRAW_TMP", "/content/draw_tmp"))
VIDEOS.mkdir(parents=True, exist_ok=True)
DRAW_TMP.mkdir(parents=True, exist_ok=True)
MIN_CONF, MAX_DIST, WIDTH = 0.3, 300, 1280  # hide a point below this confidence or this far (px) from the nose
LINKS = ["nose head_center neck spine_upper spine_mid spine_lower tail_base tail_quarter tail_mid tail_three_quarter tail_tip".split(),
         "left_ear head_center right_ear".split(), "left_shoulder spine_upper right_shoulder".split(), "left_hip spine_lower right_hip".split()]

tracks = sorted(TRACKS.glob("Test_*DLC*.h5"), key=lambda p: int(p.name.split("DLC")[0].split("_")[1]))
print("Tracked clips ready:", len(tracks))
for h5 in tracks:
    tag = h5.name.split("DLC")[0]
    final = VIDEOS / f"{tag}_labeled.mp4"
    if final.exists():
        continue
    df = pd.read_hdf(h5)
    df.columns = df.columns.droplevel(0)
    parts = list(df.columns.get_level_values(0).unique())
    xy = np.stack([df[p][["x", "y"]].values for p in parts], axis=1)
    conf = np.stack([df[p]["likelihood"].values for p in parts], axis=1)
    near = np.hypot(*(xy - xy[:, [parts.index("nose")]]).transpose(2, 0, 1)) <= MAX_DIST
    show = (conf >= MIN_CONF) & near
    colours = [tuple(int(c) for c in cv2.applyColorMap(np.uint8([[int(255 * i / (len(parts) - 1))]]), cv2.COLORMAP_JET)[0, 0]) for i in range(len(parts))]
    links = [(parts.index(a), parts.index(b)) for chain in LINKS for a, b in zip(chain, chain[1:])]
    local = DRAW_TMP / f"{tag}.mp4"
    shutil.copy2(CLIP_DIR / f"{tag.replace('_', ' ')}.mp4", local)
    cap = cv2.VideoCapture(str(local))
    W, H, fps = int(cap.get(3)), int(cap.get(4)), cap.get(5)
    s = WIDTH / W
    h = int(H * s) // 2 * 2
    tmp = DRAW_TMP / f"{tag}_labeled.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{WIDTH}x{h}", "-r", str(fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    k = 0
    while k < len(df):
        ok, f = cap.read()
        if not ok:
            break
        f = cv2.resize(f, (WIDTH, h), interpolation=cv2.INTER_AREA)
        p = (xy[k] * s).astype(int)
        for a, b in links:
            if show[k, a] and show[k, b]:
                cv2.line(f, tuple(int(v) for v in p[a]), tuple(int(v) for v in p[b]), (255, 255, 255), 1, cv2.LINE_AA)
        for j in np.where(show[k])[0]:
            cv2.circle(f, tuple(int(v) for v in p[j]), 3, colours[j], -1, cv2.LINE_AA)
        ff.stdin.write(f.tobytes())
        k += 1
    ff.stdin.close()
    assert ff.wait() == 0, f"ffmpeg failed on {tag}"
    cap.release()
    assert k == len(df), f"{tag}: drew {k} of {len(df)} frames"
    shutil.copy2(tmp, final)  # copied last, so an interrupted video is redrawn
    tmp.unlink()
    local.unlink()
    print(f"{tag}: {k} frames, {show.sum(axis=1).mean():.1f} of {len(parts)} points shown per frame", flush=True)
print("Videos in", VIDEOS, ":", len(list(VIDEOS.glob("*_labeled.mp4"))))
