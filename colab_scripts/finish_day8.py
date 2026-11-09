"""Tracks every Day 8 clip with the KA checking model and draws its video, saving both to Drive as each clip finishes.
Rerun any time: finished clips are skipped, and tracking already saved by the earlier notebook is reused."""
import importlib.util, os, shutil, subprocess, sys, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DRIVE = Path(os.environ.get("FINISH_DRIVE", "/content/drive/MyDrive/sp1DLC"))
NAME = "KAcheck_d6d8_20261107"
RUN = DRIVE / "Colab_Training_Runs" / NAME
CLIPS = Path(os.environ.get("FINISH_CLIPS", DRIVE / "d8_clips"))
TRACKS = Path(os.environ.get("FINISH_TRACKS", RUN / "d8_tracks"))
VIDEOS = Path(os.environ.get("FINISH_VIDEOS", RUN / "d8_videos_tail_base"))
WORK = Path(os.environ.get("FINISH_WORK", "/content/finish"))
SECONDS = os.environ.get("FINISH_SECONDS")  # testing only

if importlib.util.find_spec("deeplabcut") is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "deeplabcut==3.0.1"], check=True)
    print("DeepLabCut installed. The runtime restarts now: when it reconnects, run this same cell again.", flush=True)
    os.kill(os.getpid(), 9)
import cv2, numpy as np, pandas as pd, torch, yaml
import deeplabcut

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CONFIG = os.environ.get("FINISH_CONFIG")
if not CONFIG:
    project = WORK / NAME
    if not (project / "config.yaml").exists():
        with zipfile.ZipFile(DRIVE / f"MobileDLC_{NAME}" / f"{NAME}.zip") as z:
            z.extractall(WORK)
        model = "dlc-models-pytorch/iteration-0/KAcheck_d6d820261107-trainset85shuffle1"
        shutil.copytree(RUN / "training-datasets", project / "training-datasets", dirs_exist_ok=True)
        (project / model / "train").mkdir(parents=True, exist_ok=True)
        for f in ("train/pytorch_config.yaml", "train/snapshot-best-400.pt", "test/pose_cfg.yaml"):
            (project / model / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RUN / model / f, project / model / f)
    cfg = yaml.safe_load((project / "config.yaml").read_text())
    cfg["project_path"] = str(project)
    (project / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    CONFIG = str(project / "config.yaml")

# All 30 clips share one camera position (checked: pool centre 962,515, radius 485), so one crop and overlay fit them all.
X0, Y0, SIDE = 477, 30, 970
FILL = (190, 194, 192)  # water colour, BGR
MIN_CONF, MAX_DIST, WIDTH = 0.3, 300, 1280
NOT_DRAWN = {"tail_quarter", "tail_mid", "tail_three_quarter", "tail_tip"}  # tail base is the last tail point kept
LINKS = ["nose head_center neck spine_upper spine_mid spine_lower tail_base".split(),
         "left_ear head_center right_ear".split(), "left_shoulder spine_upper right_shoulder".split(), "left_hip spine_lower right_hip".split()]
for d in (TRACKS, VIDEOS, WORK):
    d.mkdir(parents=True, exist_ok=True)
overlay = np.dstack([np.full((SIDE, SIDE, 3), FILL, np.uint8), np.full((SIDE, SIDE), 255, np.uint8)])
cv2.circle(overlay, (962 - X0, 515 - Y0), int(485 * 1.01), (0, 0, 0, 0), -1)
overlay[900 - Y0:970 - Y0, 270 - X0 if 270 > X0 else 0:940 - X0] = (*FILL, 255)  # the timestamp bar crosses the pool
mask_png = WORK / "mask.png"
cv2.imwrite(str(mask_png), overlay)
limit = ["-t", SECONDS] if SECONDS else []


def prepare(clip):
    """Copies a clip off Drive and writes the cropped, filled version the model reads."""
    out = WORK / (clip.stem.replace(" ", "_") + ".mp4")
    if not out.exists():
        tmp = out.with_suffix(".part.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *limit, "-i", str(clip), "-i", str(mask_png), "-filter_complex", f"[0:v]crop={SIDE}:{SIDE}:{X0}:{Y0}[v];[v][1:v]overlay",
                        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", "-pix_fmt", "yuv420p", str(tmp)], check=True)
        tmp.replace(out)
    return out


def draw(tag, h5):
    """Draws the points on the original clip, hiding low-confidence and stray points."""
    final = VIDEOS / f"{tag}_labeled.mp4"
    if final.exists():
        return
    df = pd.read_hdf(h5)
    df.columns = df.columns.droplevel(0)
    parts = list(df.columns.get_level_values(0).unique())
    xy = np.stack([df[p][["x", "y"]].values for p in parts], axis=1)
    conf = np.stack([df[p]["likelihood"].values for p in parts], axis=1)
    show = (conf >= MIN_CONF) & (np.hypot(*(xy - xy[:, [parts.index("nose")]]).transpose(2, 0, 1)) <= MAX_DIST)
    show[:, [i for i, p in enumerate(parts) if p in NOT_DRAWN]] = False
    colours = [tuple(int(c) for c in cv2.applyColorMap(np.uint8([[int(255 * i / (len(parts) - 1))]]), cv2.COLORMAP_JET)[0, 0]) for i in range(len(parts))]
    links = [(parts.index(a), parts.index(b)) for chain in LINKS for a, b in zip(chain, chain[1:])]
    s, h = WIDTH / 1920, 720
    tmp = WORK / f"{tag}_labeled.mp4"
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", *limit, "-i", str(CLIPS / f"{tag.replace('_', ' ')}.mp4"), "-vf", f"scale={WIDTH}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{WIDTH}x{h}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    size, k = WIDTH * h * 3, 0
    while k < len(df):
        raw = dec.stdout.read(size)
        if len(raw) < size:
            break
        f = np.frombuffer(raw, np.uint8).reshape(h, WIDTH, 3).copy()
        p = (xy[k] * s).astype(int).tolist()
        for a, b in links:
            if show[k, a] and show[k, b]:
                cv2.line(f, p[a], p[b], (255, 255, 255), 1, cv2.LINE_AA)
        for j in np.flatnonzero(show[k]):
            cv2.circle(f, p[j], 3, colours[j], -1, cv2.LINE_AA)
        enc.stdin.write(f.tobytes())
        k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close()
    assert enc.wait() == 0, f"ffmpeg failed on {tag}"
    shutil.copy2(tmp, final)
    tmp.unlink()
    print(f"  video saved: {tag} ({k} frames, {show.sum(axis=1).mean():.1f} of {len(parts)} points shown per frame)", flush=True)


def track(video, batch):
    while True:
        try:
            deeplabcut.analyze_videos(CONFIG, [str(video)], shuffle=1, videotype="mp4", device=DEVICE, batch_size=batch, destfolder=str(WORK))
            return batch
        except RuntimeError as error:
            if "out of memory" not in str(error).lower() or batch <= 1:
                raise
            torch.cuda.empty_cache()
            batch //= 2
            print(f"  GPU memory full: batch size is now {batch}", flush=True)


clips = sorted(CLIPS.glob("Test *.mp4"), key=lambda p: int(p.stem.split()[-1]))
only = os.environ.get("FINISH_ONLY")
if only:
    clips = [c for c in clips if c.stem == only]
print(f"{len(clips)} clips | {DEVICE} {torch.cuda.get_device_name(0) if DEVICE == 'cuda' else ''} | {os.cpu_count()} CPUs", flush=True)
started, done, batch = time.time(), 0, 32 if DEVICE == "cuda" else 4
done_h5 = lambda tag: next(iter(TRACKS.glob(f"{tag}DLC*.h5")), None)
with ThreadPoolExecutor(max(2, (os.cpu_count() or 4) // 2)) as pool:
    jobs = []
    ready = {c: pool.submit(prepare, c) for c in clips if not done_h5(c.stem.replace(" ", "_"))}
    for clip in clips:
        tag = clip.stem.replace(" ", "_")
        h5 = done_h5(tag)
        if h5 is None:
            video = ready[clip].result()
            batch = track(video, batch)
            raw = next(WORK.glob(f"{tag}DLC*.h5"))
            df = pd.read_hdf(raw)
            df.loc[:, df.columns.get_level_values(-1) == "x"] += X0  # back to full-frame coordinates
            df.loc[:, df.columns.get_level_values(-1) == "y"] += Y0
            h5 = TRACKS / raw.name
            df.to_hdf(h5, key="df_with_missing", mode="w")
            for f in [*WORK.glob(f"{tag}DLC*"), video]:
                f.unlink()
        done += 1
        jobs.append(pool.submit(draw, tag, h5))
        rate = (time.time() - started) / done
        print(f"tracked {done}/{len(clips)} ({tag}); about {rate * (len(clips) - done) / 60:.0f} min left", flush=True)
    for job in jobs:
        job.result()
print(f"ALL DONE in {(time.time() - started) / 60:.0f} min. Videos: {VIDEOS}  Tracking: {TRACKS}", flush=True)
