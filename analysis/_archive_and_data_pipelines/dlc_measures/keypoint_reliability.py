"""How usable each body point is while rats swim (final KAC model), for tail-sweep and head-scanning (VTE-type) measures.
Swimming = body more than 0.165 pool radii from the platform. Reports per point: median confidence and % frames >= 0.6,
plus how stable two body lengths are (a steady length means the points sit consistently on the body)."""
import os
from pathlib import Path
import numpy as np, pandas as pd

RUN = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs\KAcheck_d6d8_v3rot_20261108")
PARTS = ["nose", "head_center", "left_ear", "right_ear", "neck", "spine_mid", "spine_lower", "left_hip", "right_hip", "tail_base"]

def body_of(df):
    xy = df["spine_mid"][["x", "y"]].to_numpy(float).copy()
    xy[df["spine_mid"]["likelihood"].to_numpy() < 0.3] = np.nan
    xy = pd.DataFrame(xy).interpolate(limit_direction="both").to_numpy().copy()
    return pd.DataFrame(xy).rolling(9, center=True, min_periods=1).median().to_numpy()

rows, lengths = [], {"hip_width": [], "spine_mid_to_tail_base": []}
for sub, pool, plat in (("d6_tracks", (751, 510, 533), (642, 697)), ("d8_tracks", (962, 515, 485), (859, 689))):
    for name in sorted(os.listdir(RUN / sub)):
        if not name.endswith(".h5"):
            continue
        df = pd.read_hdf(RUN / sub / name); df.columns = df.columns.droplevel(0)
        b = body_of(df)
        swim = np.hypot(b[:, 0] - plat[0], b[:, 1] - plat[1]) > 0.165 * pool[2]
        if swim.sum() < 60:
            continue
        for p in PARTS:
            l = df[p]["likelihood"].to_numpy()[swim]
            rows.append((sub[:2], p, np.median(l), (l >= 0.6).mean() * 100))
        ok = lambda p: df[p]["likelihood"].to_numpy() >= 0.6
        xy = lambda p: df[p][["x", "y"]].to_numpy()
        for key, (a, c) in (("hip_width", ("left_hip", "right_hip")), ("spine_mid_to_tail_base", ("spine_mid", "tail_base"))):
            m = swim & ok(a) & ok(c)
            if m.sum() > 30:
                d = np.hypot(*(xy(a) - xy(c))[m].T)
                lengths[key].append(np.std(d) / np.mean(d))
r = pd.DataFrame(rows, columns=["day", "part", "median_conf", "pct_conf_ge_06"])
print("Rats that swam at least 2 s:", r.groupby("day").size().div(len(PARTS)).astype(int).to_dict())
print(r.groupby("part")[["median_conf", "pct_conf_ge_06"]].median().reindex(PARTS).round(2).to_string())
for k, v in lengths.items():
    print(f"{k}: frame-to-frame variation (coefficient of variation) median {np.median(v):.2f} across rats (lower = steadier)")
