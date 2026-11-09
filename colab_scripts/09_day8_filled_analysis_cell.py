# Paste into the open training notebook after shuffle 2 has trained. Runs Day 8 clips with the fixed model,
# filling the timestamp bar and everything outside the pool with the water colour. Finished clips are skipped on rerun.
import shutil, subprocess
from pathlib import Path
from IPython.display import display
import cv2, numpy as np, pandas as pd, deeplabcut

IN = Path("/content/drive/MyDrive/sp1DLC/d8_clips")
SAVE = OUTPUT / "d8_filled_shuffle2"
TMP = Path("/content/d8_tmp")
SAVE.mkdir(parents=True, exist_ok=True)
TMP.mkdir(exist_ok=True)
BAR = (900, 970, 270, 940)  # y0, y1, x0, x1 of the timestamp bar in the 1920x1080 clips


def fit_fill(path):
    """Returns the mask of pixels to keep, the fill colour and the pool circle."""
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    for i in np.linspace(0, n - 1, 15).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if ok:
            frames.append(f)
    cap.release()
    colour = np.median(np.stack(frames), axis=0).astype(np.uint8)
    med = cv2.cvtColor(colour, cv2.COLOR_BGR2GRAY)
    _, b = cv2.threshold(med, 150, 255, cv2.THRESH_BINARY)
    b = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((31, 31), np.uint8))
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, np.ones((51, 51), np.uint8))
    cnts, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
    H, W = med.shape
    pts = pts[(pts[:, 0] > 3) & (pts[:, 0] < W - 4) & (pts[:, 1] > 3) & (pts[:, 1] < H - 4)]
    a, c, e = np.linalg.lstsq(np.c_[2 * pts, np.ones(len(pts))], (pts ** 2).sum(axis=1), rcond=None)[0]
    r = float(np.sqrt(e + a ** 2 + c ** 2))
    mask = np.zeros((H, W), np.uint8)
    cv2.circle(mask, (int(a), int(c)), int(r * 1.01), 255, -1)
    y0, y1, x0, x1 = BAR
    mask[y0:y1, x0:x1] = 0
    fill = np.median(colour[(mask > 0) & (med > 150)], axis=0).astype(np.uint8)
    return mask, fill, (a, c, r), n


def far_stats(df, limit=300):
    parts = list(df.columns.get_level_values(0).unique())
    far = sum((np.hypot(df[p]["x"] - df["nose"]["x"], df[p]["y"] - df["nose"]["y"]).values > limit).astype(int) for p in parts)
    nh = np.hypot(df["nose"]["x"] - df["head_center"]["x"], df["nose"]["y"] - df["head_center"]["y"]).values
    return {"frames": len(df), "pct_any_far": round((far > 0).mean() * 100, 1), "pct_5plus_far": round((far >= 5).mean() * 100, 1),
            "pct_nose_head_gt80": round((nh > 80).mean() * 100, 1), "tail_tip_pct_conf_gt_0.6": round((df["tail_tip"]["likelihood"] > 0.6).mean() * 100, 1)}


clips = sorted(IN.glob("*.mp4"), key=lambda p: int(p.stem.split()[-1]))
print("Clips visible in Drive:", len(clips), "of 30 (rerun this cell to pick up the rest)")
for clip in clips:
    tag = clip.stem.replace(" ", "_")
    done = SAVE / f"{tag}_summary.csv"
    if done.exists():
        continue
    mask, fill, circle, n = fit_fill(clip)
    filled = TMP / f"{tag}.mp4"
    cap = cv2.VideoCapture(str(clip))
    W, H, fps = int(cap.get(3)), int(cap.get(4)), cap.get(5)
    wr = cv2.VideoWriter(str(filled), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    while True:
        ok, f = cap.read()
        if not ok:
            break
        f[mask == 0] = fill
        wr.write(f)
    wr.release()
    cap.release()
    deeplabcut.analyze_videos(str(CONFIG), [str(filled)], shuffle=2, videotype="mp4", device="cuda", save_as_csv=True, destfolder=str(TMP))
    deeplabcut.create_labeled_video(str(CONFIG), [str(filled)], shuffle=2, videotype="mp4", pcutoff=0.2, dotsize=6, destfolder=str(TMP))
    h5 = next(TMP.glob(f"{tag}DLC*.h5"))
    df = pd.read_hdf(h5)
    df.columns = df.columns.droplevel(0)
    stats = {"clip": clip.stem, "pool_x": round(circle[0]), "pool_y": round(circle[1]), "pool_r": round(circle[2]), **far_stats(df)}
    labeled = sorted(TMP.glob(f"{tag}DLC*labeled*.mp4"))[-1]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(labeled), "-vf", "scale=960:-2", "-c:v", "libx264", "-crf", "27", "-pix_fmt", "yuv420p", str(SAVE / f"{tag}_labeled.mp4")], check=True)
    shutil.copy2(h5, SAVE / h5.name)
    shutil.copy2(h5.with_suffix(".csv"), SAVE / h5.with_suffix(".csv").name)
    pd.DataFrame([stats]).to_csv(done, index=False)  # written last, so an interrupted clip is redone
    for f in [*TMP.glob(f"{tag}DLC*"), TMP / f"{tag}.mp4"]:
        f.unlink()
    print(stats, flush=True)

table = pd.concat([pd.read_csv(f) for f in sorted(SAVE.glob("*_summary.csv"))]).sort_values("pct_5plus_far", ascending=False)
table.to_csv(SAVE / "ALL_CLIPS_SUMMARY.csv", index=False)
display(table)
print("Finished", len(table), "clips. Saved to", SAVE)
