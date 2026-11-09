"""Tail sweeps and VTE-like head scanning during the checking tests, from DeepLabCut keypoints.
Usage: python checking_kinematics.py      (writes checking_kinematics.csv and figures next to this script)

Same trials and 120 s windows as ../dlc_measures/checking_dlc_measures.py: KAC Day 6 and Day 8 from the final model
(KAcheck_d6d8_v3rot_20261108, 30 fps) and SP1 checking (10 fps). Everything is in body lengths, so cameras compare fairly.

Definitions
- Keypoints are used only where DLC likelihood >= 0.6; gaps up to 0.3 s are interpolated, longer gaps stay missing.
- Body length (BL): median neck-to-tail-base distance for that trial.
- Body axis: spine_mid -> neck (the front body). Lateral offset of a point = its signed perpendicular distance from that axis, in BL.
- Swimming: body (spine_mid) speed >= 1 BL/s for at least 0.5 s. Still: speed <= 0.25 BL/s for at least 0.5 s.
- Tail sweep amplitude: SD of the tail-base lateral offset while swimming, after removing a 1 s rolling median (so steady turns
  do not count as sweeps). Hip sweep: the same for the hip midpoint. Sweep rate: side-to-side crossings of that detrended
  tail-base offset per second of swimming, divided by 2 (full cycles per second, Hz).
- Noise floor: the same detrended tail-base offset SD while the rat is still (tail_jitter_still_BL); sweeps must clearly exceed it.
- Head yaw: angle of neck -> nose relative to the body axis. Head swing: a move of >= 25 degrees between turning points of the
  smoothed yaw (0.2 s median). VTE event: two consecutive opposite swings (left then right, or right then left) within 2 s
  while the rat is still. Head scanning rate: total absolute yaw change per second while still (degrees/s).
- Pre-departure VTE: VTE events in the 5 s before the rat first left the platform (rats that left only).
Trials with < 3 s swimming get no sweep values; trials with < 5 s still get no VTE values.
Caveats: SP1 is 10 fps, so its sweep rate is limited to <= 5 Hz and fast head swings can be missed; SP1 is not comparable to KAC
on rates. These measures have not been checked against video by eye.
"""
import csv, os, re
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs")
KAC = ROOT / "KAcheck_d6d8_v3rot_20261108"
AN = Path(r"C:\Users\kobeq\Documents\KAC database\analysis")
OUT = Path(__file__).resolve().parent
import sys
LK, SWIM, STILL, VTE_GAP = 0.6, 1.0, 0.25, 2.0
SWING = float(sys.argv[1]) if len(sys.argv) > 1 else 25.0   # head-swing threshold, degrees; run with 40 for the strict version

def ls(folder, prefix):
    return sorted(Path(folder) / f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(".h5") and "DLC" in f)

def load(h5, start, end, fps):
    d = pd.read_hdf(h5); d.columns = d.columns.droplevel(0)
    return d.iloc[int(round(start * fps)):int(round(end * fps))].reset_index(drop=True)

def pt(d, part, fps):
    xy = d[part][["x", "y"]].to_numpy(float).copy(); xy[d[part]["likelihood"].to_numpy() < LK] = np.nan
    return pd.DataFrame(xy).interpolate(limit=max(1, int(0.3 * fps)), limit_area="inside").to_numpy()

def runs(mask, n):
    out, s = [], None
    for i, v in enumerate(np.append(mask, False)):
        if v and s is None: s = i
        elif not v and s is not None:
            if i - s >= n: out.append((s, i))
            s = None
    return out

def keep(mask, n):
    m = np.zeros(len(mask), bool)
    for a, b in runs(mask, n): m[a:b] = True
    return m

def lateral(p, origin, u):  # signed perpendicular distance of p from the axis through origin along u
    v = p - origin; return u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]

def turning_points(y):
    """Indices of local turning points of y, ignoring NaN gaps."""
    idx = np.where(~np.isnan(y))[0]
    if len(idx) < 3: return []
    z = y[idx]; d = np.sign(np.diff(z)); d[d == 0] = 1
    tp = [0] + [i + 1 for i in range(len(d) - 1) if d[i] != d[i + 1]] + [len(z) - 1]
    return [idx[i] for i in tp]

def trial(d, fps, first_departure=None):
    P = {k: pt(d, k, fps) for k in ("nose", "neck", "spine_mid", "tail_base", "left_hip", "right_hip")}
    L = np.nanmedian(np.linalg.norm(P["neck"] - P["tail_base"], axis=1))
    w = max(3, int(0.3 * fps)) | 1
    body = pd.DataFrame(P["spine_mid"]).rolling(w, center=True, min_periods=1).median().to_numpy()
    spd = np.r_[np.nan, np.linalg.norm(np.diff(body, axis=0), axis=1) * fps / L]
    spd = pd.Series(spd).rolling(w, center=True, min_periods=1).median().to_numpy()
    swim, still = keep(spd >= SWIM, int(0.5 * fps)), keep(spd <= STILL, int(0.5 * fps))
    ax = P["neck"] - P["spine_mid"]; u = ax / np.linalg.norm(ax, axis=1, keepdims=True)
    tail = lateral(P["tail_base"], P["spine_mid"], u) / L; hip = lateral((P["left_hip"] + P["right_hip"]) / 2, P["spine_mid"], u) / L
    det = lambda x: x - pd.Series(x).rolling(int(fps), center=True, min_periods=1).median().to_numpy()
    tail_d, hip_d = det(tail), det(hip)
    r = dict(body_length_px=L, swim_s=swim.sum() / fps, still_s=still.sum() / fps,
             pct_frames_keypoints_ok=100 * np.mean(~np.isnan(tail) & ~np.isnan(hip)),
             tail_jitter_still_BL=np.nanstd(tail_d[still]) if still.sum() > fps else np.nan)  # noise floor: same measure while not swimming
    # Rhythm check: average spectrum of the detrended tail-base offset over 2 s pieces of swimming (and of stillness).
    # A real stroke shows a peak; jitter is flat. Peak prominence = peak power / median power, 2 Hz to Nyquist (slower drift excluded).
    from scipy.signal import welch
    for name, mask in (("swim", swim), ("still", still)):
        segs = [tail_d[a + k:a + k + 2 * fps] for a, b in runs(mask, 2 * fps) for k in range(0, b - a - 2 * fps + 1, fps)]
        segs = [x for x in segs if not np.isnan(x).any()]
        if len(segs) >= 2:
            f, pw = welch(np.vstack(segs), fs=fps, nperseg=2 * fps, axis=1); pw = pw.mean(axis=0); band = f >= 2
            r[f"tail_peak_hz_{name}"] = f[band][np.argmax(pw[band])]; r[f"tail_peak_prominence_{name}"] = pw[band].max() / np.median(pw[band])
    if r["swim_s"] >= 3:
        ts = tail_d[swim & ~np.isnan(tail_d)]
        r["tail_sweep_amp_BL"] = np.std(ts); r["hip_sweep_amp_BL"] = np.nanstd(hip_d[swim])
        crossings = sum(((np.sign(tail_d[a:b][~np.isnan(tail_d[a:b])])[1:] * np.sign(tail_d[a:b][~np.isnan(tail_d[a:b])])[:-1]) < 0).sum() for a, b in runs(swim, int(0.5 * fps)))
        r["tail_sweep_rate_hz"] = crossings / 2 / r["swim_s"]
        ok = swim & ~np.isnan(tail_d) & ~np.isnan(hip_d); r["tail_hip_r"] = np.corrcoef(tail_d[ok], hip_d[ok])[0, 1] if ok.sum() > 10 else np.nan
    # head yaw relative to body axis
    hd = P["nose"] - P["neck"]; yaw = np.degrees(np.arctan2(u[:, 0] * hd[:, 1] - u[:, 1] * hd[:, 0], (u * hd).sum(axis=1)))
    yaw = pd.Series(yaw).rolling(max(3, int(0.2 * fps)) | 1, center=True, min_periods=1).median().to_numpy()
    def vte(mask):
        y = np.where(mask, yaw, np.nan); ev, tps = 0, turning_points(y)
        sw = [(tps[i], tps[i + 1], y[tps[i + 1]] - y[tps[i]]) for i in range(len(tps) - 1)
              if abs(y[tps[i + 1]] - y[tps[i]]) >= SWING and mask[tps[i]:tps[i + 1] + 1].all()]
        i = 0
        while i < len(sw) - 1:
            (a0, b0, d0), (a1, b1, d1) = sw[i], sw[i + 1]
            if np.sign(d0) != np.sign(d1) and a1 == b0 and (b1 - a0) / fps <= VTE_GAP: ev += 1; i += 2
            else: i += 1
        return ev
    if r["still_s"] >= 5:
        r["vte_events_per_min_still"] = vte(still) / (r["still_s"] / 60)
        dy = np.abs(np.diff(yaw)); r["head_scan_deg_per_s_still"] = np.nansum(dy[still[1:]]) / r["still_s"]
    if first_departure is not None and not pd.isna(first_departure) and first_departure >= 5:
        a = int((first_departure - 5) * fps); m = np.zeros(len(yaw), bool); m[a:int(first_departure * fps)] = True
        r["vte_events_5s_before_leaving"] = vte(m & (spd <= 0.5))
    return r

rows = []
sex = lambda r: "Male" if r <= 16 else "Female"
# KAC Day 8: release offsets and test -> rat from the clip manifest
m8 = pd.read_csv(AN / "dlc_measures" / "kac_d8_dlc_measures.csv").set_index("rat")
man = {int(r["test"]): r for r in csv.DictReader(open(r"C:\Users\kobeq\Videos\checkd8\trials\clip_manifest.csv"))}
for h5 in ls(KAC / "d8_tracks", "Test_"):
    t = int(h5.name.split("DLC")[0].split("_")[1]); r = man[t]; s = float(r["release_offset_in_clip_s"]); rat = int(r["animal"])
    rows.append(dict(cohort="KAC", day=8, condition="raised water 3 cm", rat=rat, sex=sex(rat), fps=30, **trial(load(h5, s, s + 120, 30), 30, m8.first_departure_s.get(rat))))
# KAC Day 6: release times from the Day 6 tracker check
m6 = pd.read_csv(AN / "dlc_measures" / "kac_d6_dlc_measures.csv").set_index("rat")
rel = {int(r["rat"]): float(r["release_clip_s"]) for r in csv.DictReader(open(AN / "tracking_pilot" / "d6_tracker_vs_anymaze.csv"))}
for h5 in ls(KAC / "d6_tracks", "Day06_"):
    rat = int(re.search(r"Rat(\d+)", h5.name).group(1))
    rows.append(dict(cohort="KAC", day=6, condition="standard water 1.5 cm (control)", rat=rat, sex=sex(rat), fps=30, **trial(load(h5, rel[rat], rel[rat] + 120, 30), 30, m6.first_departure_s.get(rat))))
# SP1 checking: AnyMaze gives test -> rat; clips are the 120 s trial
mp = pd.read_csv(AN / "dlc_measures" / "sp1_checking_dlc_vs_anymaze.csv"); smap = dict(zip(mp.Test.astype(int), mp.animal.str.replace("rat", "", regex=False).astype(int)))
ms = pd.read_csv(AN / "dlc_measures" / "sp1_checking_dlc_measures.csv").set_index("rat")
for h5 in ls(ROOT / "sp1" / "sp1_tracks", "sp1_check_Test_"):
    t = int(h5.name.split("DLC")[0].split("_")[-1]); rat = smap[t]
    rows.append(dict(cohort="SP1", day=6, condition="raised water (no control)", rat=rat, sex=sex(rat), fps=10, **trial(load(h5, 0, 120, 10), 10, ms.first_departure_s.get(rat))))
K = pd.DataFrame(rows).sort_values(["cohort", "day", "rat"]).round(3)
K.to_csv(OUT / ("checking_kinematics.csv" if SWING == 25 else f"checking_kinematics_swing{SWING:.0f}.csv"), index=False)
print(K.groupby(["cohort", "day", "sex"]).agg(n=("rat", "size"), swim_s=("swim_s", "mean"), still_s=("still_s", "mean"), tail_amp=("tail_sweep_amp_BL", "mean"),
      tail_n=("tail_sweep_amp_BL", "count"), rate=("tail_sweep_rate_hz", "mean"), hip_amp=("hip_sweep_amp_BL", "mean"), tail_hip_r=("tail_hip_r", "mean"),
      vte=("vte_events_per_min_still", "mean"), scan=("head_scan_deg_per_s_still", "mean"), vte_pre=("vte_events_5s_before_leaving", "mean"),
      vte_pre_n=("vte_events_5s_before_leaving", "count"), kp_ok=("pct_frames_keypoints_ok", "mean"), jitter=("tail_jitter_still_BL", "mean")).round(2).to_string())
