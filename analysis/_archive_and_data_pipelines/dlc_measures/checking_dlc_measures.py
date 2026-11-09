"""Checking-test (probe) measures from DLC tracking, one row per rat, for KAC Day 6, KAC Day 8 and SP1 checking.
Method as d8_dlc_measures.py, generalised:
- Window: release to release + 120 s (SP1 clips are the 120 s trial itself).
- Pool: 172 cm across at the outer rim (KAC, confirmed); assumed the same for SP1 (not confirmed).
- Platform: where rats sit in the first 2 s after placement (median over rats); the zone radius is 0.165 pool radii
  (80 px at Day 8 scale, set from Day 8: stay-on rats never went beyond 74 px, swimmers went 200-600 px).
- Departure: out of the zone for at least 1 s. Wall time: beyond 0.85 of the rim radius.
- Body position: spine middle (head centre if unsure), confidence >= 0.3, interpolated, median-filtered over 0.3 s.
Rearing is not measured (not detectable from overhead).
"""
import csv, os, re
from pathlib import Path
import cv2, numpy as np, pandas as pd

ROOT = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs")
OUT = Path(__file__).resolve().parent
ZONE_R, WALL_R = 0.165, 0.85

def files(folder, prefix, suffix):
    """Lists files without glob: the Drive folder name contains [brackets], which glob treats as a pattern."""
    return sorted(Path(folder) / f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(suffix))

def tracks(sub, prefix):
    """First-model tracking files from every copy of its run folder, one per clip."""
    found = {}
    for d in KAC_DIRS:
        if (d / sub).exists():
            for p in files(d / sub, prefix, ".h5"):
                found.setdefault(p.name.split("DLC")[0], p)
    return [found[k] for k in sorted(found)]

def series(df, part, fps):
    xy = df[part][["x", "y"]].to_numpy(float).copy()
    xy[df[part]["likelihood"].to_numpy() < 0.3] = np.nan
    return pd.DataFrame(xy).interpolate(limit_direction="both").to_numpy().copy()  # writable under pandas copy-on-write

def body_of(df, fps):
    b = series(df, "spine_mid", fps)
    unsure = df["spine_mid"]["likelihood"].to_numpy() < 0.3
    b[unsure] = series(df, "head_center", fps)[unsure]
    return pd.DataFrame(b).rolling(max(3, int(fps * 0.3)), center=True, min_periods=1).median().to_numpy()

def runs(mask, n):
    out, s = [], None
    for i, v in enumerate(np.append(mask, False)):
        if v and s is None: s = i
        elif not v and s is not None:
            if i - s >= n: out.append((s, i))
            s = None
    return out

def pool_from(video):
    cap = cv2.VideoCapture(str(video)); n = int(cap.get(7)); fr = []
    for i in np.linspace(0, n - 1, 15).astype(int):
        cap.set(1, int(i)); ok, f = cap.read()
        if ok: fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    g = np.median(np.stack(fr), axis=0).astype(np.uint8)
    _, b = cv2.threshold(cv2.GaussianBlur(g, (9, 9), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # SP1's grey video needs an automatic threshold
    k = max(5, g.shape[1] // 60) | 1
    b = cv2.morphologyEx(cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((k, k), np.uint8)), cv2.MORPH_CLOSE, np.ones((2 * k + 1, 2 * k + 1), np.uint8))
    pts = max(cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0, :].astype(float)
    H, W = g.shape
    pts = pts[(pts[:, 0] > 3) & (pts[:, 0] < W - 4) & (pts[:, 1] > 3) & (pts[:, 1] < H - 4)]
    a, c, e = np.linalg.lstsq(np.c_[2 * pts, np.ones(len(pts))], (pts ** 2).sum(axis=1), rcond=None)[0]
    return float(a), float(c), float(np.sqrt(e + a ** 2 + c ** 2))

def measure(trials, pool, fps, label, p2=None):
    """trials: {rat: (test, df_window)}; returns per-rat rows."""
    cx, cy, R = pool
    cm = 86 / R
    bodies = {r: body_of(df, fps) for r, (t, df) in trials.items()}
    px, py = np.median([np.median(b[: 2 * fps], axis=0) for b in bodies.values()], axis=0)
    zone = ZONE_R * R
    print(f"{label}: {len(trials)} rats | pool ({cx:.0f},{cy:.0f}) r {R:.0f}px | platform ({px:.0f},{py:.0f}) = {np.hypot(px - cx, py - cy) / R:.2f} radii from centre | zone {zone:.0f}px")
    rows = []
    for rat, (test, df) in sorted(trials.items()):
        b = bodies[rat]
        d = np.hypot(b[:, 0] - px, b[:, 1] - py)
        inside = d <= zone
        out = runs(~inside, fps)
        wall = np.hypot(b[:, 0] - cx, b[:, 1] - cy) > WALL_R * R
        step = np.hypot(*np.diff(b, axis=0).T)
        rows.append({"rat": rat, "test": test, "seconds_tracked": round(len(df) / fps, 1),
                     "pct_time_on_platform_zone": round(inside.mean() * 100, 1), "departures": len(out),
                     "first_departure_s": round(out[0][0] / fps, 1) if out else "",
                     "pct_time_at_wall": round(wall.mean() * 100, 1),
                     **({"pct_time_in_anymaze_size_P2_zone": round(float((np.hypot(b[:, 0] - p2[0], b[:, 1] - p2[1]) <= p2[2]).mean() * 100), 1)} if p2 else {}),
                     "swim_path_off_platform_cm": round(float(np.nansum(step[~inside[1:]])) * cm, 1),
                     "mean_distance_from_platform_cm": round(float(d.mean()) * cm, 1),
                     "pct_frames_body_unsure": round(float((df["spine_mid"]["likelihood"] < 0.3).mean() * 100), 1)})
    return pd.DataFrame(rows)

def load(h5, start, end, fps):
    df = pd.read_hdf(h5); df.columns = df.columns.droplevel(0)
    return df.iloc[int(round(start * fps)): int(round(end * fps))].reset_index(drop=True)

def check(m, notes, label):
    n = pd.DataFrame(notes, columns=["rat", "notes_stayed_on", "notes_departures", "notes_first_departure_s", "notes_text"])
    c = m.merge(n, on="rat", how="left")
    c["dlc_stayed_on"] = np.where(c.departures == 0, "SOP", "LP")
    has = c.notes_stayed_on.isin(["SOP", "LP"])
    agree = (c.notes_stayed_on == c.dlc_stayed_on)[has]
    print(f"  {label} vs notes: stayed on vs left agrees on {agree.sum()} of {has.sum()} rats with notes")
    bad = c[has & (c.notes_stayed_on != c.dlc_stayed_on)]
    if len(bad):
        print(bad[["rat", "notes_stayed_on", "departures", "first_departure_s", "notes_text"]].to_string(index=False))
    return c[["rat", "sex", "notes_stayed_on", "dlc_stayed_on", "notes_departures", "departures", "notes_first_departure_s", "first_departure_s", "notes_text"]]

KAC_DIRS = [ROOT / "KAcheck_d6d8_v3rot_20261108"]  # FINAL KAC model: all 197 labels + rotation augmentation; one model for both days
sex = lambda r: "M" if r <= 16 else "F"

# ---- KAC Day 8 (raised water, 3 cm)
man = {int(r["test"]): r for r in csv.DictReader(open(r"C:\Users\kobeq\Videos\checkd8\trials\clip_manifest.csv"))}
t8 = {}
for h5 in tracks("d8_tracks", "Test_"):
    test = int(h5.name.split("DLC")[0].split("_")[1]); r = man[test]; s = float(r["release_offset_in_clip_s"])
    t8[int(r["animal"])] = (test, load(h5, s, s + 120, 30))
m8 = measure(t8, (962, 515, 485), 30, "KAC Day 8 (3 cm)", p2=(861, 689, 40))  # AnyMaze P2 zone as fitted to AnyMaze P2 times
m8.insert(1, "sex", m8.rat.map(sex)); m8.insert(2, "condition", "raised water 3 cm")
NOTES8 = [(1,"SOP",0,"","R 27 s"),(2,"SOP",0,"",""),(3,"LP","","","left platform"),(4,"SOP",0,"","R 55 s"),(5,"SOP",0,"",""),(6,"SOP",0,"",""),(7,"SOP",0,"","R 42 s"),(8,"SOP",0,"",""),
          (9,"SOP",0,"",""),(10,"SOP",0,"","R 13 s"),(12,"SOP",0,"","R 29 s"),(13,"LP",1,65,"left 65 s, back 87 s"),(14,"SOP",0,"",""),(15,"SOP",0,"",""),(16,"SOP",0,"",""),
          (17,"LP","","","left and returned"),(18,"LP",6,10,"left 6 times"),(20,"LP",1,95,"left 95 s"),(21,"LP",1,0,"left immediately"),(22,"LP",1,"","left; found platform"),
          (23,"LP",1,49,"left 49 s, 78 s"),(24,"LP",1,73,"left 73 s"),(25,"LP",7,5,"left x7"),(26,"SOP",0,"",""),(27,"LP",1,90,"left 90 s"),(28,"LP",5,7,"left x5 (?)"),
          (29,"LP",1,0,"left right away"),(30,"LP",3,0,"left x3"),(31,"LP",3,0,"left x3"),(32,"LP",4,0,"left x4")]
m8.to_csv(OUT / "kac_d8_dlc_measures.csv", index=False)
check(m8, NOTES8, "Day 8").to_csv(OUT / "kac_d8_notes_vs_dlc.csv", index=False)

# ---- KAC Day 6 (standard water 1.5 cm, the control)
rel = {int(r["rat"]): float(r["release_clip_s"]) for r in csv.DictReader(open(r"C:\Users\kobeq\Documents\KAC database\analysis\tracking_pilot\d6_tracker_vs_anymaze.csv"))}
t6 = {}
for h5 in tracks("d6_tracks", "Day06_"):
    rat = int(re.search(r"Rat(\d+)", h5.name).group(1))
    t6[rat] = (rat, load(h5, rel[rat], rel[rat] + 120, 30))
DAY6_READY = len(t6) == 29
if not DAY6_READY:
    print(f"KAC Day 6: only {len(t6)} of 29 tracked so far, so its measures are skipped until the run finishes")
else:
    m6 = measure(t6, (751, 510, 533), 30, "KAC Day 6 (1.5 cm, control)")
    m6.insert(1, "sex", m6.rat.map(sex)); m6.insert(2, "condition", "standard water 1.5 cm (control)")
# Typed from the Day 6 notebook page. Rats 10, 12-16 and 25 have no Day 6 note; rat 9's line is blank.
NOTES6 = [(2,"SOP",0,"","R 60 s, stayed on"),(3,"SOP",0,"","R 1:30, stayed on"),(4,"LP","",40,"jumped off ~40 s, small lap, got back on"),(5,"SOP",0,"","R 1:37, stayed on"),
          (6,"SOP",0,"","R 36 s, stayed on"),(7,"SOP",0,"","R halfway, stayed on"),(8,"SOP",0,"","submerging front half, R 1:22, stayed on"),
          (17,"LP",3,30,"R 20 s, left 30 s (x3), thigmotaxis"),(18,"LP","",10,"jumped off ~10 s"),(20,"SOP",0,"","R 15 s, submerging, stayed on"),
          (21,"LP","",0,"left/slipped immediately, found ~1:40"),(22,"LP","",87,"R 30 s, leaped off 87 s"),(23,"LP","",100,"R 51 s, left 100 s"),(24,"LP","",13,"left 13 s, R 71 s"),
          (26,"LP","",100,"R 40 s, off 100 s, jump for ledge"),(27,"","","","R 57 s"),(28,"LP",2,57,"R 45 s, off 57 s (2x)"),(29,"SOP",0,"","R 40 s, stayed on"),
          (30,"LP",5,20,"R 11 s, off 20 s (5x), jump for ledge"),(31,"LP",2,30,"off 30 s (2x)"),(32,"LP",2,60,"R 40 s, off 60 s (2x)")]
if DAY6_READY:
    m6.to_csv(OUT / "kac_d6_dlc_measures.csv", index=False)
    check(m6, NOTES6, "Day 6").to_csv(OUT / "kac_d6_notes_vs_dlc.csv", index=False)

# ---- SP1 checking (raised water, no control). AnyMaze provides the test-to-rat mapping.
# This legacy generator is not gap-aware; current analysis is in ../dlc_cleaned/.
sp1 = ROOT / "sp1" / "sp1_tracks"
clips = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\sp1_clips\sp1_check")
sp1_map_table = pd.read_csv(OUT / "sp1_checking_dlc_vs_anymaze.csv")
sp1_map = dict(zip(sp1_map_table.Test.astype(int), sp1_map_table.animal.str.replace("rat", "", regex=False).astype(int)))
assert set(sp1_map) == set(range(1, 33)) and set(sp1_map.values()) == set(range(1, 33))
ts = {}
for h5 in files(sp1, "sp1_check_Test_", ".h5"):
    test = int(h5.name.split("DLC")[0].split("_")[-1])
    ts[sp1_map[test]] = (test, load(h5, 0, 120, 10))
pool = pool_from(files(clips, "Test ", ".mp4")[0])
ms = measure(ts, pool, 10, "SP1 checking")
ms.insert(1, "sex", ms.rat.map(sex)); ms.insert(2, "condition", "raised water (SP1, no control)")
ms.to_csv(OUT / "sp1_checking_dlc_measures.csv", index=False)
print("written:", [p.name for p in sorted(OUT.glob("*_dlc_measures.csv"))])
