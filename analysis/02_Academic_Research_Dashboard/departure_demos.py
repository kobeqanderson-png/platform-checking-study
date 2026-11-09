"""Demo clips of single departures by where the rat went, then back onto the platform:
  to_P1      came within 20 cm of P1 (the trained platform location) and did not reach the wall
  to_wall    reached the wall (beyond 0.85 pool radii) and did not come within 20 cm of P1
  wander     neither: a loop in open water
Bouts come from ../advanced/bouts.csv (returned bouts only). Positions are the cleaned tracks in cache/. For each type the bout
closest to that type's median duration is shown (typical, not the most dramatic). KAC Day 6 is preferred: the training days and
Day 6 share the camera, so P1 is best placed there. Writes demos/departure_<type>.mp4 and results/departure_types.csv.
Usage: python departure_demos.py
"""
import glob, shutil, subprocess
from pathlib import Path
import numpy as np, pandas as pd, cv2

HERE = Path(__file__).resolve().parent; DEM = HERE / "demos"; AN = HERE.parent
P1_FRAC = {"kac_d6": (.28, -.355), "kac_d8": (.28, -.355), "sp1": (.4623, -.0624)}   # SP1: assumed opposite quadrant
COND = {("KAC", 6): "kac_d6", ("KAC", 8): "kac_d8", ("SP1", 6): "sp1"}
COL = {"Female": (214, 120, 42), "Male": (52, 104, 235)}; PURPLE = (176, 63, 122)
B = pd.read_csv(AN / "advanced" / "bouts.csv"); B = B[B.returned]
Z = {}
for f in glob.glob(str(HERE / "cache" / "*.npz")):
    z = dict(np.load(f)); z = {k: (v.item() if v.ndim == 0 else v) for k, v in z.items()}; Z[(z["cond"], int(z["rat"]))] = z
rows = []
for _, b in B.iterrows():
    cond = COND.get((b.cohort, int(b.day)))
    if cond is None or (cond, int(b.rat)) not in Z: continue
    z = Z[(cond, int(b.rat))]; fps = int(z["fps"]); cx, cy, R = z["pool"]; cm = 86 / R
    a, e = int(round(b.start_s * fps)), int(round((b.start_s + b.off_s) * fps))
    body = z["body"][a:e]; body = body[np.isfinite(body).all(1)]
    if len(body) < fps: continue
    p1 = np.array([cx, cy]) + np.array(P1_FRAC[cond]) * R
    near_p1 = np.min(np.linalg.norm(body - p1, axis=1)) * cm <= 20
    wall = bool(b.reached_wall)
    kind = "to_P1" if near_p1 and not wall else "to_wall" if wall and not near_p1 else "wander" if not (wall or near_p1) else "P1_and_wall"
    rows.append(dict(cond=cond, rat=int(b.rat), sex=b.sex, bout=int(b.bout), start_s=b.start_s, off_s=b.off_s, kind=kind,
                     max_dist_cm=b.max_dist_cm, settled=bool(z['inside'][max(0, a - 2 * fps):a].all()) if a >= 2 * fps else False, min_dist_to_p1_cm=np.min(np.linalg.norm(body - p1, axis=1)) * cm, a=a, e=e))
D = pd.DataFrame(rows); D.drop(columns=["a", "e"]).round(2).to_csv(HERE / "results" / "departure_types.csv", index=False)
print(D.groupby(["cond", "kind"]).size().unstack(fill_value=0).to_string())

def clip(r, name, label):
    z = Z[(r.cond, r.rat)]; fps = int(z["fps"]); cx, cy, R = z["pool"]
    a, e = max(0, r.a - 2 * fps), min(len(z["body"]), r.e + 2 * fps)
    step = 2 if (e - a) / fps > 25 else 1                       # long bouts at 2x so the clip stays short
    side = 2.1 * R; W = 560; s = W / side; x0, y0 = cx - side / 2, cy - side / 2
    P = lambda p: tuple(np.rint((np.asarray(p) - [x0, y0]) * s).astype(int))
    cap = cv2.VideoCapture(str(z["video"])); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(z["start"] * fps)) + a)
    tmp = DEM / "tmp_dep.mp4"; vw = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, W + 44)); trail = []
    p1 = np.array([cx, cy]) + np.array(P1_FRAC[z["cond"]]) * R
    for i in range(a, e):
        ok, f = cap.read()
        if not ok: break
        if (i - a) % step: continue
        crop = cv2.warpAffine(f, np.array([[s, 0, -x0 * s], [0, s, -y0 * s]]), (W, W))
        cv2.circle(crop, P(z["platform"]), round(.165 * R * s), (255, 255, 255), 1, cv2.LINE_AA)
        cv2.circle(crop, P((cx, cy)), round(.85 * R * s), (150, 150, 150), 1, cv2.LINE_AA)          # wall zone boundary
        cv2.circle(crop, P(p1), round(20 / 86 * R * s), PURPLE, 1, cv2.LINE_AA); cv2.drawMarker(crop, P(p1), PURPLE, cv2.MARKER_DIAMOND, 10, 2)
        cv2.putText(crop, "P1 (trained)" + (" - assumed" if z["cond"] == "sp1" else ""), (P(p1)[0] + 8, P(p1)[1] - 10), 0, .42, PURPLE, 1, cv2.LINE_AA)
        if np.isfinite(z["body"][i]).all(): trail.append(P(z["body"][i]))
        if len(trail) > 1: cv2.polylines(crop, [np.array(trail, np.int32)], False, COL[r.sex], 2, cv2.LINE_AA)
        if trail: cv2.circle(crop, trail[-1], 6, COL[r.sex], -1, cv2.LINE_AA)
        state = "ON PLATFORM" if z["inside"][i] else "OFF PLATFORM"
        cv2.putText(crop, state, (12, 28), 0, .6, (0, 0, 0), 4, cv2.LINE_AA); cv2.putText(crop, state, (12, 28), 0, .6, (255, 255, 255), 1, cv2.LINE_AA)
        bar = np.full((44, W, 3), 255, np.uint8)
        cv2.putText(bar, f"{label} | {r.cond.replace('kac_d', 'KAC Day ').replace('sp1', 'SP1')}, {r.sex.lower()} rat {r.rat} | t = {i / fps:5.1f} s{' | 2x' if step == 2 else ''}",
                    (8, 28), 0, .45, (30, 30, 30), 1, cv2.LINE_AA)
        vw.write(np.vstack([crop, bar]))
    vw.release()
    subprocess.run([shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-i", str(tmp), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart", str(DEM / f"departure_{name}.mp4")], check=True); tmp.unlink()
    print(name, r.cond, r.sex, "rat", r.rat, "bout", r.bout, f"{r.off_s:.1f} s off, max {r.max_dist_cm:.0f} cm")

LABEL = {"to_P1": "Out to P1 (trained spot) and back", "to_wall": "Out to the wall and back", "wander": "A loop in open water and back"}
for kind in ("to_P1", "to_wall", "wander"):
    pool = D[(D.kind == kind) & (D.cond == "kac_d6") & (D.sex == "Female") & D.settled]   # on the platform for the 2 s before leaving   # females: males rarely leave, and their hops are brief
    if pool.empty: pool = D[D.kind == kind]
    if pool.empty: print("no bout of type", kind); continue
    r = pool.iloc[(pool.off_s - pool.off_s.median()).abs().argsort().iloc[0]]
    clip(r, kind, LABEL[kind])
