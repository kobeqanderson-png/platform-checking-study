"""Tracks every clip for one probe day with the KA checking model and draws its video, saving both to Drive as each
clip finishes. Usage in Colab:  %run /content/drive/MyDrive/sp1DLC/finish_videos.py 6   (or 8)
Rerun any time: finished clips are skipped, and tracking already saved is reused."""
import importlib.util, os, re, shutil, subprocess, sys, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DAY = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FINISH_DAY", "8")).lower()
DRIVE = Path(os.environ.get("FINISH_DRIVE", "/content/drive/MyDrive/DLC output[sp1--kac1.5cm-3.0cm]"))
KA = dict(name=os.environ.get("FINISH_KA_NAME", "KAcheck_d6d8_20261107"), zip="MobileDLC_KAcheck_d6d8_20261107/KAcheck_d6d8_20261107.zip",
          model="KAcheck_d6d820261107-trainset85shuffle1", shuffle=1, snapshot="snapshot-best-400.pt")
# Each day's clips share one camera position, so one crop and overlay fit them all (pool fitted on every clip).
SETUP = {
    "8": dict(KA, clips="d8_clips", pattern="Test *.mp4", crop=(477, 30, 970), pool=(962, 515, 485), fill=(190, 194, 192),
              bar=(900, 970, 270, 940), out="d8"),  # Day 8 has a timestamp bar that crosses the pool
    "6": dict(KA, clips="d6_clips", pattern="Day06_*.mp4", crop=(211, 0, 1080), pool=(751, 510, 533), fill=(196, 209, 204), bar=None, out="d6"),
    # sp1 (older 640x480 camera): the all-worklists model with unlabeled points ignored, which learned from 1,278 sp1 frames.
    # Clips sit in one subfolder per day; the model reads them as they are.
    # "sp1" is the sp1 checking test only (the priority); "sp1all" adds the training days for later.
    "sp1": dict(name="sp1DLC_allworklists_20261106", zip="MobileDLC_AllWorklists_20261106/sp1DLC_allworklists_20261106.zip",
                run="allworklists_20261106", model="sp1DLC_allworklists20261106-trainset95shuffle2", shuffle=2,
                snapshot="snapshot-best-190.pt", clips="sp1_clips", pattern="sp1_check/Test *.mp4", crop=None, out="sp1"),
}
SETUP["sp1all"] = dict(SETUP["sp1"], pattern="*/Test *.mp4")
SETUP = SETUP[DAY]
NAME = SETUP["name"]
RUN = DRIVE / "Colab_Training_Runs" / SETUP.get("run", NAME)
CLIPS = Path(os.environ.get("FINISH_CLIPS", DRIVE / SETUP["clips"]))
TRACKS = Path(os.environ.get("FINISH_TRACKS", RUN / f"{SETUP['out']}_tracks"))
VIDEOS = Path(os.environ.get("FINISH_VIDEOS", RUN / f"{SETUP['out']}_videos_final"))
# Release-to-removal window per probe clip: before release the experimenter's head and glove are at the pool edge.
WINDOWS = Path(os.environ.get("FINISH_WINDOWS", DRIVE / "clip_windows.csv"))
WORK = Path(os.environ.get("FINISH_WORK", f"/content/finish_{SETUP['out']}"))
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
    project = Path("/content/finish_model") / NAME
    if not (project / "config.yaml").exists():
        with zipfile.ZipFile(DRIVE / SETUP["zip"]) as z:
            z.extractall(project.parent)
        model = f"dlc-models-pytorch/iteration-0/{SETUP['model']}"
        shutil.copytree(RUN / "training-datasets", project / "training-datasets", dirs_exist_ok=True)
        for f in ("train/pytorch_config.yaml", f"train/{SETUP['snapshot']}", "test/pose_cfg.yaml"):
            (project / model / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RUN / model / f, project / model / f)
    cfg = yaml.safe_load((project / "config.yaml").read_text())
    cfg["project_path"] = str(project)
    (project / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    CONFIG = str(project / "config.yaml")

CROP = SETUP["crop"]
X0, Y0, SIDE = CROP or (0, 0, 0)
MIN_CONF, MAX_DIST_1080, WIDTH = 0.3, 300, 1280  # the stray-point distance is for 1080p and scales with frame width
NOT_DRAWN = {"tail_quarter", "tail_mid", "tail_three_quarter", "tail_tip"}  # tail base is the last tail point kept
LINKS = ["nose head_center neck spine_upper spine_mid spine_lower tail_base".split(),
         "left_ear head_center right_ear".split(), "left_shoulder spine_upper right_shoulder".split(), "left_hip spine_lower right_hip".split()]
for d in (TRACKS, VIDEOS, WORK):
    d.mkdir(parents=True, exist_ok=True)
limit = ["-t", SECONDS] if SECONDS else []
if CROP:
    PX, PY, PR = SETUP["pool"]
    FILL = SETUP["fill"]  # water colour, BGR
    overlay = np.dstack([np.full((SIDE, SIDE, 3), FILL, np.uint8), np.full((SIDE, SIDE), 255, np.uint8)])
    cv2.circle(overlay, (PX - X0, PY - Y0), int(PR * 1.01), (0, 0, 0, 0), -1)
    if SETUP["bar"]:
        y0, y1, x0, x1 = SETUP["bar"]
        overlay[max(0, y0 - Y0):y1 - Y0, max(0, x0 - X0):x1 - X0] = (*FILL, 255)
    mask_png = WORK / "mask.png"
    cv2.imwrite(str(mask_png), overlay)
# Clips in day subfolders (sp1) get the folder in their name, since every day has a "Test 1".
tag_of = lambda clip: (f"{clip.parent.name}_" if clip.parent != CLIPS else "") + clip.stem.replace(" ", "_")


def prepare(clip):
    """Copies a clip off Drive, cropped and filled where the day needs it, as the version the model reads."""
    out = WORK / (tag_of(clip) + ".mp4")
    if not out.exists():
        tmp = out.with_suffix(".part.mp4")
        if CROP:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *limit, "-i", str(clip), "-i", str(mask_png), "-filter_complex", f"[0:v]crop={SIDE}:{SIDE}:{X0}:{Y0}[v];[v][1:v]overlay",
                            "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", "-pix_fmt", "yuv420p", str(tmp)], check=True)
        elif SECONDS:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *limit, "-i", str(clip), "-an", "-c:v", "libx264", "-crf", "16", str(tmp)], check=True)
        else:
            shutil.copy2(clip, tmp)
        tmp.replace(out)
    return out


def draw(clip, h5):
    """Draws the points on the original clip, hiding low-confidence and stray points."""
    tag = tag_of(clip)
    final = VIDEOS / f"{tag}_labeled.mp4"
    if final.exists():
        return
    df = pd.read_hdf(h5)
    df.columns = df.columns.droplevel(0)
    parts = list(df.columns.get_level_values(0).unique())
    xy = np.stack([df[p][["x", "y"]].values for p in parts], axis=1)
    conf = np.stack([df[p]["likelihood"].values for p in parts], axis=1)
    probe = cv2.VideoCapture(str(clip))
    W, H, fps = int(probe.get(3)), int(probe.get(4)), probe.get(5) or 30
    probe.release()
    show = conf >= MIN_CONF
    show[:, [i for i, p in enumerate(parts) if p in NOT_DRAWN]] = False
    # Stray points are judged from the middle of the confident points, so a wrong nose can't drag the check with it.
    centre = np.nanmedian(np.where(show[..., None], xy, np.nan), axis=1)
    show &= np.hypot(*(xy - centre[:, None]).transpose(2, 0, 1)) <= MAX_DIST_1080 * W / 1920 * 0.6
    show[show.sum(axis=1) < 5] = False  # an empty pool still gets a few false hits
    if tag in windows:
        start, end = windows[tag]
        t = np.arange(len(show)) / fps
        show[(t < start) | (t > end)] = False
    colours = [tuple(int(c) for c in cv2.applyColorMap(np.uint8([[int(255 * i / (len(parts) - 1))]]), cv2.COLORMAP_JET)[0, 0]) for i in range(len(parts))]
    links = [(parts.index(a), parts.index(b)) for chain in LINKS for a, b in zip(chain, chain[1:])]
    width = min(WIDTH, W)  # small videos are drawn at their own size
    s = width / W
    h = int(H * s) // 2 * 2
    tmp = WORK / f"{tag}_labeled.mp4"
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", *limit, "-i", str(clip), "-vf", f"scale={width}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    size, k = width * h * 3, 0
    while k < len(df):
        raw = dec.stdout.read(size)
        if len(raw) < size:
            break
        f = np.frombuffer(raw, np.uint8).reshape(h, width, 3).copy()
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
    print(f"  video saved: {tag} ({k} frames, {show.sum(axis=1).mean():.1f} points shown per frame)", flush=True)


def track(video, batch):
    while True:
        try:
            deeplabcut.analyze_videos(CONFIG, [str(video)], shuffle=SETUP["shuffle"], videotype="mp4", device=DEVICE, batch_size=batch, destfolder=str(WORK))
            return batch
        except RuntimeError as error:
            if "out of memory" not in str(error).lower() or batch <= 1:
                raise
            torch.cuda.empty_cache()
            batch //= 2
            print(f"  GPU memory full: batch size is now {batch}", flush=True)


windows = {}
if WINDOWS.exists():
    for line in WINDOWS.read_text().splitlines()[1:]:
        t, a, b = line.split(",")
        windows[t] = (float(a), float(b))
number = lambda p: (p.parent.name, int(re.findall(r"\d+", p.stem)[-1]))
clips = sorted(CLIPS.glob(SETUP["pattern"]), key=number)
only = os.environ.get("FINISH_ONLY")
if only:
    clips = [c for c in clips if only in (c.stem, tag_of(c))]
print(f"Day {DAY}: {len(clips)} clips | {DEVICE} {torch.cuda.get_device_name(0) if DEVICE == 'cuda' else ''} | {os.cpu_count()} CPUs", flush=True)
started, done, batch = time.time(), 0, 32 if DEVICE == "cuda" else 4
done_h5 = lambda clip: next(iter(TRACKS.glob(f"{tag_of(clip)}DLC*.h5")), None)
with ThreadPoolExecutor(max(2, (os.cpu_count() or 4) // 2)) as pool:
    jobs = []
    ready = {c: pool.submit(prepare, c) for c in clips if not done_h5(c)}
    for clip in clips:
        tag = tag_of(clip)
        h5 = done_h5(clip)
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
        jobs.append(pool.submit(draw, clip, h5))
        print(f"tracked {done}/{len(clips)} ({tag}); about {(time.time() - started) / done * (len(clips) - done) / 60:.0f} min left", flush=True)
    for job in jobs:
        job.result()
print(f"ALL DONE in {(time.time() - started) / 60:.0f} min. Videos: {VIDEOS}  Tracking: {TRACKS}", flush=True)
