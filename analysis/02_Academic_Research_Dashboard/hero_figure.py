"""One poster figure: (A) never left, by sex, in three tests; (B) % still on the platform over 120 s; (C) where departures went. Reads results/ (run analyze.py and departure_demos.py first).
Writes figures/hero_story.png (300 dpi) and figures/hero_story.svg (editable). Usage: python hero_figure.py
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent; RES = HERE / "results"; FIG = HERE / "figures"
F_, M_, INK, INK2, P1C = "#2a78d6", "#eb6834", "#1d1d1b", "#6b6a66", "#7a3fb0"
plt.rcParams.update({"font.family": "Arial", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK2,
                     "axes.titlesize": 14, "axes.titleweight": "bold", "legend.frameon": False, "savefig.facecolor": "white"})
D = pd.read_csv(RES / "per_rat_measures.csv")
TESTS = [("sp1", "SP1", "raised water"), ("kac_d6", "KAC Day 6", "standard water"), ("kac_d8", "KAC Day 8", "raised water")]
def ptxt(p): return "p < 0.001" if p < .001 else f"p = {p:.3f}"

fig = plt.figure(figsize=(17, 11)); gs = fig.add_gridspec(2, 6, height_ratios=[1, 1], hspace=.5, wspace=.6)

# A: never left
ax = fig.add_subplot(gs[0, :3]); w = .36
for j, (c, name, sub) in enumerate(TESTS):
    x = D[D.cond == c]; k = {s: int(((x.sex == s) & (x.departures_observed == 0)).sum()) for s in "MF"}; n = {s: int((x.sex == s).sum()) for s in "MF"}
    p = stats.fisher_exact([[k["M"], n["M"] - k["M"]], [k["F"], n["F"] - k["F"]]])[1]
    for i, (s, col) in enumerate((("M", M_), ("F", F_))):
        v = 100 * k[s] / n[s]; ax.bar(j + (i - .5) * w, v, w * .92, color=col, edgecolor=INK, lw=.6)
        ax.text(j + (i - .5) * w, v + 2, f"{k[s]}/{n[s]}", ha="center", va="bottom", fontsize=12, weight="bold")
    ax.plot([j - w / 2, j - w / 2, j + w / 2, j + w / 2], [100, 104, 104, 100], color=INK, lw=1); ax.text(j, 106, ptxt(p), ha="center", fontsize=11)
ax.set_xticks(range(3)); ax.set_xticklabels([f"{n}\n{s}" for _, n, s in TESTS]); ax.set_ylim(0, 118); ax.set_ylabel("Rats that never left the platform (%)")
ax.bar(0, 0, color=M_, label="Males"); ax.bar(0, 0, color=F_, label="Females"); ax.legend(loc="upper right", ncol=2, bbox_to_anchor=(1, 1.02))
ax.set_title("A   Males stay, females leave: three tests, two cohorts", loc="left")

# B: still on the platform over time
for j, (c, name, sub) in enumerate(TESTS):
    ax = fig.add_subplot(gs[0, 3 + j])
    for s, col, lab in (("M", M_, "Males"), ("F", F_, "Females")):
        x = D[(D.cond == c) & (D.sex == s)]; t = np.where(x.departures_observed == 0, np.inf, x.first_departure_s.fillna(x.first_off_lower_s))   # onset inside a short gap: earliest possible time
        t = np.sort(np.where(np.isfinite(t), t, 121)); tt = np.r_[0, t[t <= 120], 120]; yy = np.r_[100, 100 * (1 - np.arange(1, (t <= 120).sum() + 1) / len(t)), 100 * (t > 120).mean()]
        ax.step(tt, yy, where="post", color=col, lw=2.6, label=lab)
    ax.set_xlim(0, 120); ax.set_ylim(0, 103); ax.set_xticks([0, 60, 120]); ax.set_xlabel("Seconds")
    ax.set_title(f"{name}\n{sub}", fontsize=12)
    if j == 0: ax.set_ylabel("Still on the platform (%)"); ax.text(0, 1.2, "B   How fast they leave", transform=ax.transAxes, fontsize=14, weight="bold")
    else: ax.set_yticklabels([])

# C: where departures went
ax = fig.add_subplot(gs[1, 1:5]); T = pd.read_csv(RES / "departure_types.csv")
order = [("to_P1", "Toward P1 (trained spot)", P1C), ("P1_and_wall", "P1 and the wall", "#b9a3d1"), ("to_wall", "Along the wall", "#8a8f94"), ("wander", "Loop in open water", "#d4d6d8")]
for j, (c, name, sub) in enumerate(TESTS):
    x = T[T.cond == c]; n = len(x); left = 0
    for k, lab, col in order:
        v = 100 * (x.kind == k).mean(); ax.barh(j, v, left=left, color=col, edgecolor="white", lw=1.5, label=lab if j == 0 else None)
        if v >= 8: ax.text(left + v / 2, j, f"{v:.0f}%", ha="center", va="center", fontsize=11, color="white" if k in ("to_P1", "to_wall") else INK)
        left += v
    ax.text(101, j, f"n = {n}", va="center", fontsize=11, color=INK2)
ax.set_yticks(range(3)); ax.set_yticklabels([f"{n}\n{s}" for _, n, s in TESTS], fontsize=11); ax.invert_yaxis(); ax.set_xlim(0, 112); ax.set_xlabel("Departures that returned (%)")
ax.legend(loc="upper center", bbox_to_anchor=(.5, -.18), ncol=2, fontsize=11); ax.spines["left"].set_visible(False)
ax.set_title("C   Where leavers go before returning", loc="left")
ax.text(0, -.6, "P1 = where the platform was during training (SP1: assumed opposite quadrant). Some swims pass P1 by chance:\nagainst control spots, leavers favour P1 on KAC Day 6 (p = 0.018) but not significantly in SP1 (p = 0.16).", transform=ax.get_xaxis_transform(), fontsize=10, color=INK2, va="top")

fig.savefig(FIG / "hero_story.png", dpi=300, bbox_inches="tight"); fig.savefig(FIG / "hero_story.svg", bbox_inches="tight"); print("saved")
