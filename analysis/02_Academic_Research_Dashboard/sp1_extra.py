"""SP1 additions: (1) the trained-platform (P1) test, (2) tail sweeping while swimming, (3) a swimming-tail demo.
P1 for SP1 is assumed to be in the quadrant opposite the checking platform (as in KAC): the checking platform mirrored through the
pool centre. SP1 video is 10 fps, so tail movements faster than about 5 sweeps per second cannot be resolved.
Reads cache/sp1_*.npz (from analyze.py). Writes results/sp1_p1.csv, results/sp1_swim_tail*.csv, figures/10_sp1_*.png, demos/swim_tail_sp1.mp4.
Usage: python sp1_extra.py
"""
import glob, json, shutil, subprocess
from pathlib import Path
import numpy as np, pandas as pd, cv2
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent; RES = HERE / "results"; FIG = HERE / "figures"; DEM = HERE / "demos"
C = {"F": "#2a78d6", "M": "#eb6834"}; INK, INK2, P1C = "#1d1d1b", "#6b6a66", "#7a3fb0"
plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "savefig.facecolor": "white"})
def pt(p): return "p < 0.001" if p < .001 else f"p = {p:.3f}"
Z = []
for f in sorted(glob.glob(str(HERE / "cache" / "sp1_rat*.npz"))):
    z = dict(np.load(f)); Z.append({k: (v.item() if v.ndim == 0 else v) for k, v in z.items()})
cx, cy, R = Z[0]["pool"]; fps = int(Z[0]["fps"]); cm = 86 / R
plat = np.median([z["platform"] for z in Z], axis=0)
P1_FRAC = -(plat - [cx, cy]) / R                       # opposite quadrant: mirrored through the pool centre
P1 = np.array([cx, cy]) + P1_FRAC * R
print(f"SP1 checking platform {((plat - [cx, cy]) / R).round(3)} pool radii; assumed P1 {P1_FRAC.round(3)}; {np.linalg.norm(plat - P1) * cm:.0f} cm apart")
sex = lambda r: "M" if r <= 16 else "F"

# ---------- 1. P1 test, same method as advanced/p1_check.py ----------
rot = lambda v, a: np.array([v[0] * np.cos(a) - v[1] * np.sin(a), v[0] * np.sin(a) + v[1] * np.cos(a)])
spots = {n: np.array([cx, cy]) + rot(P1_FRAC, a) * R for n, a in (("trained", 0), ("rot90", np.pi / 2), ("rot180", np.pi), ("rot270", 3 * np.pi / 2))}
rows = []
for z in Z:
    b = z["body"]; off = (~z["inside"].astype(bool)) & z["valid"].astype(bool) & np.isfinite(b).all(1)
    if off.sum() < fps: continue
    rows.append(dict(rat=int(z["rat"]), sex=sex(int(z["rat"])), off_s=off.sum() / fps,
                     **{f"pct_off_time_within20_{k}": 100 * np.mean(np.linalg.norm(b[off] - v, axis=1) * cm <= 20) for k, v in spots.items()},
                     **{f"closest_{k}_cm": np.nanmin(np.linalg.norm(b[off] - v, axis=1)) * cm for k, v in spots.items()}))
P = pd.DataFrame(rows); P.round(2).to_csv(RES / "sp1_p1.csv", index=False)
ctrl = P[[f"pct_off_time_within20_{k}" for k in ("rot90", "rot180", "rot270")]].mean(axis=1)
p1 = dict(n=len(P), n_female=int((P.sex == "F").sum()), trained_mean=P.pct_off_time_within20_trained.mean(), control_mean=ctrl.mean(),
          trained_median=P.pct_off_time_within20_trained.median(), control_median=ctrl.median(), wilcoxon_p=stats.wilcoxon(P.pct_off_time_within20_trained, ctrl).pvalue,
          closest_trained_median=P.closest_trained_cm.median(), closest_control_median=P[["closest_rot90_cm", "closest_rot180_cm", "closest_rot270_cm"]].mean(axis=1).median(),
          closest_p=stats.wilcoxon(P.closest_trained_cm, P[["closest_rot90_cm", "closest_rot180_cm", "closest_rot270_cm"]].mean(axis=1)).pvalue, P1_frac=P1_FRAC.tolist())
print("P1:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in p1.items()})

# ---------- 2. Tail sweeping while swimming ----------
def ang(v): return np.arctan2(v[:, 1], v[:, 0])
def runs(m):
    out, s = [], None
    for i, v in enumerate(np.append(m, False)):
        if v and s is None: s = i
        elif not v and s is not None: out.append((s, i)); s = None
    return out
TR, EX, TC = [], {}, []
for z in Z:
    b = z["body"]; ok = z["valid"].astype(bool) & np.isfinite(b).all(1)
    swim = (~z["inside"].astype(bool)) & ok
    if swim.sum() < 3 * fps: continue
    tip = np.where((z["tail_tip_lk"] >= .5)[:, None], z["tail_tip"], z["tail_mid"])
    tail_ok = ((z["tail_tip_lk"] >= .5) | (z["tail_mid_lk"] >= .5)) & (z["tail_base_lk"] >= .5) & swim
    phi = np.degrees(np.angle(np.exp(1j * (ang(tip - z["tail_base"]) - ang(z["tail_base"] - z["head_center"])))))   # tail relative to body axis, signed
    phi[~tail_ok] = np.nan
    v = np.r_[[[np.nan, np.nan]], np.diff(b, axis=0)] * fps * cm
    speed = np.hypot(*v.T); head = np.where(speed > 5, ang(np.nan_to_num(v)), np.nan)   # swim direction, only while moving
    turn = np.r_[np.nan, np.angle(np.exp(1j * np.diff(head)))] * fps * 180 / np.pi   # signed change in swim direction, deg/s (wrapped, NaN-safe)
    turn[np.abs(turn) > 720] = np.nan
    dphi = np.r_[np.nan, np.diff(phi)] * fps
    m = tail_ok & np.isfinite(dphi)
    # sweeps: swings of >= 20 deg between turning points, within continuous tracked swimming
    sweeps, amps = 0, []
    for a, e in runs(tail_ok):
        x = phi[a:e]
        if len(x) < 3: continue
        tp = [0] + [i for i in range(1, len(x) - 1) if (x[i] - x[i - 1]) * (x[i + 1] - x[i]) < 0] + [len(x) - 1]
        sw = [abs(x[j] - x[i]) for i, j in zip(tp[:-1], tp[1:]) if abs(x[j] - x[i]) >= 20]; sweeps += len(sw); amps += sw
    rud = np.isfinite(phi) & np.isfinite(turn)
    r_rudder = stats.spearmanr(phi[rud], turn[rud])[0] if rud.sum() >= 3 * fps else np.nan     # tail to one side while turning: rudder
    vig_ok = m & np.isfinite(speed)
    r_speed = stats.spearmanr(np.abs(dphi[vig_ok]), speed[vig_ok])[0] if vig_ok.sum() >= 3 * fps else np.nan
    # last 3 s before climbing back on vs the rest of the swim
    back = [e for a, e in runs(~z["inside"].astype(bool)) if e < len(b) and e - a >= fps]
    near = np.zeros(len(b), bool)
    for e in back: near[max(0, e - 3 * fps):e] = True
    vn, vr = np.nanmean(np.abs(dphi[m & near])) if (m & near).sum() >= fps else np.nan, np.nanmean(np.abs(dphi[m & ~near])) if (m & ~near).sum() >= fps else np.nan
    TR.append(dict(rat=int(z["rat"]), sex=sex(int(z["rat"])), swim_s=swim.sum() / fps, tail_tracked_pct=100 * tail_ok.sum() / swim.sum(),
                   sweeps_per_s=sweeps / max(tail_ok.sum() / fps, 1e-9), sweep_amplitude_deg=np.median(amps) if amps else np.nan,
                   tail_vigour_deg_s=np.nanmean(np.abs(dphi[m])), rudder_r=r_rudder, vigour_speed_r=r_speed,
                   vigour_last3s_before_return=vn, vigour_rest_of_swim=vr, returns=len(back)))
    EX[int(z["rat"])] = dict(phi=phi, turn=turn, speed=speed, swim=swim, z=z, tip=tip, tail_ok=tail_ok)
T = pd.DataFrame(TR).sort_values(["sex", "rat"]); T.round(3).to_csv(RES / "sp1_swim_tail_per_rat.csv", index=False)
F = T[T.sex == "F"]
res = dict(n_swimmers=len(T), n_female=len(F), n_male=int((T.sex == "M").sum()),
           female_sweeps_per_s=F.sweeps_per_s.mean(), female_amp=F.sweep_amplitude_deg.median(), female_tracked=F.tail_tracked_pct.mean(),
           rudder_r_mean=T.rudder_r.mean(), rudder_p=stats.wilcoxon(T.rudder_r.dropna()).pvalue, rudder_n=int(T.rudder_r.notna().sum()),
           speed_r_mean=T.vigour_speed_r.mean(), speed_p=stats.wilcoxon(T.vigour_speed_r.dropna()).pvalue)
pr = T.dropna(subset=["vigour_last3s_before_return", "vigour_rest_of_swim"])
if len(pr) >= 5:
    res.update(return_n=len(pr), return_last3=pr.vigour_last3s_before_return.mean(), return_rest=pr.vigour_rest_of_swim.mean(),
               return_p=stats.wilcoxon(pr.vigour_last3s_before_return, pr.vigour_rest_of_swim).pvalue)
print("swim tail:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})
json.dump(dict(p1=p1, swim_tail=res), open(RES / "sp1_extra.json", "w"), indent=1, default=float)

# ---------- figures ----------
fig, axs = plt.subplots(1, 2, figsize=(9, 3.8))
x = np.r_[P.pct_off_time_within20_trained.values]; c = ctrl.values
for t, cc, s in zip(x, c, P.sex): axs[0].plot([0, 1], [cc, t], "-o", color=C[s], ms=4, lw=1, alpha=.8)
axs[0].plot([0, 1], [c.mean(), x.mean()], "-o", color=INK, lw=2.2, ms=7); axs[0].set_xticks([0, 1]); axs[0].set_xticklabels(["Control spots\n(mean of 3)", "P1\n(trained, assumed)"]); axs[0].set_xlim(-.3, 1.3)
axs[0].set_ylabel("Off-platform time within 20 cm (%)"); axs[0].set_title(f"SP1 leavers near P1 ({pt(p1['wilcoxon_p'])}, n = {p1['n']})", fontsize=10.5)
th = np.linspace(0, 2 * np.pi, 200); ax = axs[1]
ax.plot(np.cos(th), np.sin(th), color=INK2, lw=.8)
for z in Z:
    b = (z["body"] - [cx, cy]) / R; ax.plot(b[:, 0], b[:, 1], color=C[sex(int(z["rat"]))], lw=.5, alpha=.45)
pp = (plat - [cx, cy]) / R; ax.add_patch(plt.Circle(pp, .165, fill=False, ls="--", color=INK, lw=.8))
ax.add_patch(plt.Circle(P1_FRAC, 20 / 86, fill=False, ls=":", color=P1C, lw=1)); ax.plot(*P1_FRAC, "D", color=P1C, ms=5)
ax.set_aspect("equal"); ax.set_ylim(1.05, -1.05); ax.set_xlim(-1.05, 1.05); ax.axis("off"); ax.set_title("SP1 paths; purple: P1 (opposite quadrant)", fontsize=10.5)
fig.tight_layout(); fig.savefig(FIG / "10_sp1_p1.png", dpi=220, bbox_inches="tight"); plt.close(fig)

ex = F.sort_values("swim_s").iloc[len(F) // 2]; e = EX[int(ex.rat)]   # a typical female for swim time
seg = max(runs(e["swim"] & np.isfinite(e["phi"])), key=lambda r: r[1] - r[0]); a, b_ = seg[0], min(seg[1], seg[0] + 20 * fps)
fig, axs = plt.subplots(1, 3, figsize=(13, 3.6), gridspec_kw=dict(width_ratios=[2.2, 1, 1]))
t = np.arange(a, b_) / fps; axs[0].plot(t, e["phi"][a:b_], color=C["F"], lw=1.4, label="Tail angle (deg, + = right)")
axs[0].plot(t, np.clip(e["turn"][a:b_], -180, 180) / 2, color=INK2, lw=1, label="Turning (deg/s ÷ 2)"); axs[0].axhline(0, color=INK2, lw=.5)
axs[0].set_xlabel("Time from release (s)"); axs[0].legend(fontsize=8, loc="upper left"); axs[0].set_title(f"SP1 female rat {int(ex.rat)}: one swim", fontsize=10.5)
for s in "FM":
    q = T[T.sex == s]; axs[1].scatter(np.full(len(q), 0 if s == "F" else 1) + np.random.default_rng(1).uniform(-.15, .15, len(q)), q.rudder_r, color=C[s], s=22, edgecolor=INK, lw=.4)
axs[1].axhline(0, color=INK2, lw=.6); axs[1].set_xticks([0, 1]); axs[1].set_xticklabels(["Females", "Males"]); axs[1].set_ylabel("Tail angle vs turning (r)")
axs[1].set_title(f"Tail as a rudder? ({pt(res['rudder_p'])})", fontsize=10.5)
if "return_p" in res:
    for _, r in pr.iterrows(): axs[2].plot([0, 1], [r.vigour_rest_of_swim, r.vigour_last3s_before_return], "-o", color=C[r.sex], ms=4, lw=1, alpha=.8)
    axs[2].set_xticks([0, 1]); axs[2].set_xticklabels(["Rest of swim", "Last 3 s before\nclimbing back on"]); axs[2].set_xlim(-.3, 1.3)
    axs[2].set_ylabel("Tail vigour (deg/s)"); axs[2].set_title(f"Finding the platform ({pt(res['return_p'])}, n = {res['return_n']})", fontsize=10.5)
fig.tight_layout(); fig.savefig(FIG / "11_sp1_swim_tail.png", dpi=220, bbox_inches="tight"); plt.close(fig)

# ---------- demo: the same swim, camera following the rat, real speed ----------
z = e["z"]; cap = cv2.VideoCapture(str(z["video"])); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(z["start"] * fps)) + a)
W, side = 520, int(.9 * R); tmp = DEM / "tmp_swim.mp4"; vw = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), fps / 2, (W, W + 40)); trail = []   # half speed
for i in range(a, b_):
    ok, f = cap.read()
    if not ok: break
    c0 = z["body"][i] if np.isfinite(z["body"][i]).all() else (trail[-1][1] if trail else plat)
    x0, y0 = c0 - side / 2; s_ = W / side
    crop = cv2.warpAffine(f, np.array([[s_, 0, -x0 * s_], [0, s_, -y0 * s_]]), (W, W), borderMode=cv2.BORDER_REPLICATE)
    P_ = lambda p: tuple(np.rint((np.asarray(p) - [x0, y0]) * s_).astype(int))
    if np.isfinite(z["body"][i]).all(): trail.append((i, z["body"][i]))
    trail = [(k, p) for k, p in trail if k >= i - 2 * fps]
    if len(trail) > 1: cv2.polylines(crop, [np.array([P_(p) for _, p in trail], np.int32)], False, (214, 120, 42), 2, cv2.LINE_AA)
    parts = ["tail_base", "tail_quarter", "tail_mid", "tail_three_quarter", "tail_tip"]
    pts = [P_(z[p][i]) for p in parts if np.isfinite(z[p][i]).all() and z[p + "_lk"][i] >= .5]
    if len(pts) > 1: cv2.polylines(crop, [np.array(pts, np.int32)], False, (0, 215, 255), 4, cv2.LINE_AA)
    for p in ("nose", "head_center"):
        if np.isfinite(z[p][i]).all(): cv2.circle(crop, P_(z[p][i]), 4, (255, 255, 255), -1, cv2.LINE_AA)
    txt = f"tail {e['phi'][i]:+4.0f} deg" if np.isfinite(e["phi"][i]) else "tail: not tracked"
    cv2.putText(crop, txt, (12, W - 14), 0, .6, (0, 0, 0), 4, cv2.LINE_AA); cv2.putText(crop, txt, (12, W - 14), 0, .6, (255, 255, 255), 1, cv2.LINE_AA)
    bar = np.full((40, W, 3), 255, np.uint8)
    cv2.putText(bar, f"SP1 female rat {int(ex.rat)} swimming, half speed, t = {i / fps:5.1f} s. Yellow: tail", (8, 26), 0, .45, (30, 30, 30), 1, cv2.LINE_AA)
    vw.write(np.vstack([crop, bar]))
vw.release()
subprocess.run([shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-i", str(tmp), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart", str(DEM / "swim_tail_sp1.mp4")], check=True); tmp.unlink()
print("demo rat", int(ex.rat), "seconds", round((b_ - a) / fps, 1), "from", round(a / fps, 1))
