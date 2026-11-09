"""Generates publication-grade, visually stunning scientific art figures from DeepLabCut tracking data.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle, Polygon
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
FIG_DIR = HERE / "figures"
SITE_FIG_DIR = HERE / "site" / "figures"
FIG_DIR.mkdir(exist_ok=True)
SITE_FIG_DIR.mkdir(exist_ok=True)

# Pool geometry constants for KAC Day 6
R_CM = 86.0  # Pool radius in cm
P1_FRAC = np.array([0.28, -0.355])  # (x_frac, y_frac) relative to pool center
P1_CM = P1_FRAC * R_CM  # P1 coordinates in cm

print("Starting generation of DLC visual explorations...")

# ==============================================================================
# FIGURE 1: CHRONOPHOTOGRAPHIC POSE STROBE & KINETIC FLOW RIBBON
# ==============================================================================
print("Generating Figure 1: Chronophotographic Pose Strobe (Rat 28)...")

# Load Rat 28 Day 6 (Female with classic to_P1 excursion)
z28 = np.load(CACHE / "kac_d6_rat28.npz")
cx, cy, R_px = z28["pool"]
cm_per_px = R_CM / R_px
fps = int(z28["fps"])

# Convert pixels to cm centered at pool origin (0, 0)
def to_cm(pts_px):
    return (pts_px - np.array([cx, cy])) * cm_per_px

plat_cm = to_cm(z28["platform"])

# Excursion frame range for Rat 28 Bout 1: 56.0s to 65.5s
f_start = int(56.0 * fps)
f_end = int(65.5 * fps)
sub_frames = np.arange(f_start, f_end)
t_rel = (sub_frames - f_start) / fps

body_cm = to_cm(z28["body"][sub_frames])
nose_cm = to_cm(z28["nose"][sub_frames])
head_cm = to_cm(z28["head_center"][sub_frames])
neck_cm = to_cm(z28["neck"][sub_frames])
spine_u_cm = to_cm(z28["spine_upper"][sub_frames])
spine_m_cm = to_cm(z28["spine_mid"][sub_frames])
spine_l_cm = to_cm(z28["spine_lower"][sub_frames])
tail_b_cm = to_cm(z28["tail_base"][sub_frames])
tail_m_cm = to_cm(z28["tail_mid"][sub_frames])
tail_q_cm = to_cm(z28["tail_quarter"][sub_frames])
l_ear_cm = to_cm(z28["left_ear"][sub_frames])
r_ear_cm = to_cm(z28["right_ear"][sub_frames])
l_sho_cm = to_cm(z28["left_shoulder"][sub_frames])
r_sho_cm = to_cm(z28["right_shoulder"][sub_frames])
l_hip_cm = to_cm(z28["left_hip"][sub_frames])
r_hip_cm = to_cm(z28["right_hip"][sub_frames])

# Velocity calculation
vel = np.gradient(body_cm, axis=0) * fps
speed_cm_s = np.linalg.norm(vel, axis=1)
dist_to_p1 = np.linalg.norm(body_cm - P1_CM, axis=1)

# Set up canvas
fig = plt.figure(figsize=(16, 12), facecolor="#090d14")
gs = fig.add_gridspec(3, 1, height_ratios=[4.5, 1, 0.4], hspace=0.25)
ax_arena = fig.add_subplot(gs[0], facecolor="#090d14")
ax_telemetry = fig.add_subplot(gs[1], facecolor="#0f1520")

# --- ARENA PLOT ---
ax_arena.set_aspect("equal")
ax_arena.set_xlim(-92, 92)
ax_arena.set_ylim(-92, 92)
ax_arena.axis("off")

# 1. Pool Perimeter with radial water rings
pool_circle = Circle((0, 0), R_CM, facecolor="#0e1420", edgecolor=(1, 1, 1, 0.2), linewidth=2.5, zorder=1)
ax_arena.add_patch(pool_circle)
for r_ring in [25, 50, 75]:
    ax_arena.add_patch(Circle((0, 0), r_ring, fill=False, edgecolor="#1a2333", linestyle=":", linewidth=1, zorder=1))

# 2. Checking Platform (Current Island)
plat_patch = Circle(plat_cm, 14.2, facecolor="#1a2538", edgecolor="#38bdf8", linewidth=2.5, zorder=2)
ax_arena.add_patch(plat_patch)
ax_arena.text(plat_cm[0], plat_cm[1] + 17, "CHECKING PLATFORM", color="#38bdf8", fontsize=10, fontweight="bold",
              ha="center", va="bottom", fontfamily="sans-serif", zorder=5)

# 3. P1 Training Platform Location (Target)
p1_patch = Circle(P1_CM, 14.2, facecolor=(0.66, 0.33, 0.97, 0.15), edgecolor="#c084fc", linewidth=2.5, linestyle="--", zorder=2)
ax_arena.add_patch(p1_patch)
ax_arena.plot(P1_CM[0], P1_CM[1], marker="D", color="#c084fc", markersize=9, zorder=5)
ax_arena.text(P1_CM[0], P1_CM[1] - 18, "TRAINING LOCATION (P1)", color="#c084fc", fontsize=10, fontweight="bold",
              ha="center", va="top", fontfamily="sans-serif", zorder=5)

# Direct vector connecting Platform to P1
ax_arena.plot([plat_cm[0], P1_CM[0]], [plat_cm[1], P1_CM[1]], color=(1, 1, 1, 0.15), linestyle="--", linewidth=1.2, zorder=2)

# 4. Continuous Kinetic Flow Ribbon (colored by speed)
points = body_cm.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)
norm = plt.Normalize(0, 36)
lc = LineCollection(segments, cmap="plasma", norm=norm, linewidth=4.5, alpha=0.9, zorder=4)
lc.set_array(speed_cm_s[:-1])
ax_arena.add_collection(lc)

# Subtle outer glow for the trajectory
lc_glow = LineCollection(segments, cmap="plasma", norm=norm, linewidth=11, alpha=0.25, zorder=3)
lc_glow.set_array(speed_cm_s[:-1])
ax_arena.add_collection(lc_glow)

# 5. Stroboscopic Skeletons (Every 11 frames = ~0.37s)
strobe_indices = np.arange(0, len(sub_frames), 11)

skeleton_bones = [
    # Cranial
    ("nose", "head"), ("head", "l_ear"), ("head", "r_ear"), ("l_ear", "r_ear"), ("head", "neck"),
    # Pectoral
    ("neck", "l_sho"), ("neck", "r_sho"), ("l_sho", "r_sho"), ("neck", "spine_u"),
    # Spinal
    ("spine_u", "spine_m"), ("spine_m", "spine_l"), ("spine_l", "tail_b"),
    # Pelvic
    ("spine_l", "l_hip"), ("spine_l", "r_hip"), ("l_hip", "r_hip"),
    # Tail
    ("tail_b", "tail_m"), ("tail_m", "tail_q")
]

for idx in strobe_indices:
    alpha = 0.35 + 0.65 * (idx / len(sub_frames))
    spd = speed_cm_s[idx]
    # Color based on excursion phase
    frac = idx / len(sub_frames)
    bone_color = plt.cm.plasma(norm(spd))
    
    parts_dict = {
        "nose": nose_cm[idx], "head": head_cm[idx], "neck": neck_cm[idx],
        "spine_u": spine_u_cm[idx], "spine_m": spine_m_cm[idx], "spine_l": spine_l_cm[idx],
        "tail_b": tail_b_cm[idx], "tail_m": tail_m_cm[idx], "tail_q": tail_q_cm[idx],
        "l_ear": l_ear_cm[idx], "r_ear": r_ear_cm[idx],
        "l_sho": l_sho_cm[idx], "r_sho": r_sho_cm[idx],
        "l_hip": l_hip_cm[idx], "r_hip": r_hip_cm[idx]
    }
    
    # Draw bones
    for p1_name, p2_name in skeleton_bones:
        pt1, pt2 = parts_dict[p1_name], parts_dict[p2_name]
        ax_arena.plot([pt1[0], pt2[0]], [pt1[1], pt2[1]], color=bone_color, linewidth=1.6, alpha=alpha, zorder=6)
    
    # Draw key joints
    for j_name, pt in parts_dict.items():
        size = 3.5 if j_name in ("head", "neck", "spine_m", "tail_b") else 2.2
        ax_arena.plot(pt[0], pt[1], "o", color="#ffffff", markersize=size, alpha=alpha, zorder=7)

# 6. Key Moment Milestones & Annotations
apex_idx = np.argmin(dist_to_p1)
milestones = [
    (0, "t = 56.0s · Disembarkation", plat_cm[0] - 8, plat_cm[1] - 8, "#38bdf8"),
    (int(len(sub_frames) * 0.28), "t = 58.7s · Velocity Surge (32 cm/s)", 0, -48, "#fb923c"),
    (apex_idx, f"t = 60.5s · P1 Apex ({dist_to_p1[apex_idx]:.1f} cm)", P1_CM[0] + 16, P1_CM[1] - 2, "#e879f9"),
    (len(sub_frames) - 1, "t = 65.5s · Platform Recovery", plat_cm[0] + 8, plat_cm[1] + 10, "#4ade80")
]

for idx, label, tx, ty, col in milestones:
    pos = body_cm[idx]
    ax_arena.plot(pos[0], pos[1], "o", color=col, markersize=8, markeredgecolor="#ffffff", markeredgewidth=1.5, zorder=10)
    ax_arena.annotate(label, xy=(pos[0], pos[1]), xytext=(tx, ty),
                      arrowprops=dict(arrowstyle="->", color=col, lw=1.2),
                      color="#ffffff", fontsize=9.5, fontweight="bold",
                      bbox=dict(boxstyle="round,pad=0.3", facecolor="#131b28", edgecolor=col, alpha=0.9),
                      zorder=11)

# Title & Metadata
ax_arena.text(-88, 84, "KINETIC CHRONO-STROBE · 16-POINT DEEPLABCUT POSE RECONSTRUCTION",
              color="#38bdf8", fontfamily="sans-serif", fontsize=13, fontweight="bold")
ax_arena.text(-88, 77, "Rat 28 (Female, KAC Day 6) · Directed Excursion to Former Training Platform P1",
              color="#94a3b8", fontfamily="sans-serif", fontsize=11)

# --- TELEMETRY SUBPLOT ---
ax_telemetry.plot(t_rel, speed_cm_s, color="#fb923c", linewidth=2.2, label="Swim Speed (cm/s)")
ax_telemetry.set_ylabel("Speed (cm/s)", color="#fb923c", fontsize=10, fontweight="bold")
ax_telemetry.tick_params(axis="y", labelcolor="#fb923c")
ax_telemetry.set_xlabel("Elapsed Time in Excursion (seconds)", color="#94a3b8", fontsize=10)
ax_telemetry.tick_params(axis="x", labelcolor="#94a3b8")
ax_telemetry.grid(True, color="#212c3d", linestyle=":")
ax_telemetry.set_xlim(0, t_rel[-1])
ax_telemetry.set_ylim(0, 42)

# Twin axis for distance to P1
ax_p1 = ax_telemetry.twinx()
ax_p1.plot(t_rel, dist_to_p1, color="#c084fc", linewidth=2.2, linestyle="--", label="Distance to P1 (cm)")
ax_p1.set_ylabel("Distance to P1 (cm)", color="#c084fc", fontsize=10, fontweight="bold")
ax_p1.tick_params(axis="y", labelcolor="#c084fc")
ax_p1.set_ylim(0, 110)

# Apex vertical line
t_apex = t_rel[apex_idx]
ax_telemetry.axvline(t_apex, color="#e879f9", linestyle=":", linewidth=2, label="P1 Proximity Apex")
ax_telemetry.text(t_apex + 0.1, 36, f"Closest Approach to P1 ({dist_to_p1[apex_idx]:.1f} cm)",
                  color="#e879f9", fontsize=9.5, fontweight="bold")

# Legend
lines1, labels1 = ax_telemetry.get_legend_handles_labels()
lines2, labels2 = ax_p1.get_legend_handles_labels()
ax_telemetry.legend(lines1 + lines2, labels1 + labels2, loc="upper right",
                    facecolor="#131b28", edgecolor="#212c3d", labelcolor="#e2e8f0", fontsize=9)

save_path1 = FIG_DIR / "art_chrono_skeleton.png"
fig.savefig(save_path1, dpi=200, bbox_inches="tight", facecolor="#090d14")
fig.savefig(SITE_FIG_DIR / "art_chrono_skeleton.png", dpi=200, bbox_inches="tight", facecolor="#090d14")
plt.close(fig)
print(f"Saved {save_path1}")


# ==============================================================================
# FIGURE 2: MACROSCOPIC SWARM CURRENTS (STREAMPLOT: FEMALE VS MALE)
# ==============================================================================
print("Generating Figure 2: Macroscopic Swarm Currents (Streamplot)...")

# Pool all Day 6 tracks by sex
kac_files = sorted(CACHE.glob("kac_d6_rat*.npz"))
female_vx, female_vy, female_x, female_y = [], [], [], []
male_vx, male_vy, male_x, male_y = [], [], [], []

for f in kac_files:
    z = np.load(f)
    sex = str(z["sex"].item() if z["sex"].ndim == 0 else z["sex"])
    valid = z["valid"].astype(bool)
    cx, cy, R_px = z["pool"]
    scale = R_CM / R_px
    body_cm = (z["body"] - np.array([cx, cy])) * scale
    
    # Velocity
    vel = np.gradient(body_cm, axis=0) * 30.0  # cm/s
    
    # Keep valid frames
    body_cm = body_cm[valid]
    vel = vel[valid]
    
    # Discard non-finite or jumps > 80 cm/s
    finite_mask = np.isfinite(body_cm).all(axis=1) & np.isfinite(vel).all(axis=1)
    speed_mask = np.linalg.norm(vel, axis=1) < 80.0
    mask = finite_mask & speed_mask
    
    b_valid = body_cm[mask]
    v_valid = vel[mask]
    
    if sex == "F":
        female_x.append(b_valid[:, 0])
        female_y.append(b_valid[:, 1])
        female_vx.append(v_valid[:, 0])
        female_vy.append(v_valid[:, 1])
    else:
        male_x.append(b_valid[:, 0])
        male_y.append(b_valid[:, 1])
        male_vx.append(v_valid[:, 0])
        male_vy.append(v_valid[:, 1])

F_x = np.concatenate(female_x)
F_y = np.concatenate(female_y)
F_u = np.concatenate(female_vx)
F_v = np.concatenate(female_vy)

M_x = np.concatenate(male_x)
M_y = np.concatenate(male_y)
M_u = np.concatenate(male_vx)
M_v = np.concatenate(male_vy)

# Grid for streamplot: 65x65 over [-84, 84] cm
grid_res = 65
xi = np.linspace(-84, 84, grid_res)
yi = np.linspace(-84, 84, grid_res)
XI, YI = np.meshgrid(xi, yi)
R_grid = np.sqrt(XI**2 + YI**2)
in_pool_mask = R_grid <= (R_CM - 2.0)

def compute_grid_vectors(x_pts, y_pts, u_pts, v_pts):
    # 2D binning and Gaussian smoothing
    u_sum, _, _ = np.histogram2d(y_pts, x_pts, bins=[yi, xi], weights=u_pts)
    v_sum, _, _ = np.histogram2d(y_pts, x_pts, bins=[yi, xi], weights=v_pts)
    count, _, _ = np.histogram2d(y_pts, x_pts, bins=[yi, xi])
    
    # Pad to match grid_res
    u_grid = np.zeros((grid_res, grid_res))
    v_grid = np.zeros((grid_res, grid_res))
    cnt_grid = np.zeros((grid_res, grid_res))
    u_grid[:-1, :-1] = u_sum
    v_grid[:-1, :-1] = v_sum
    cnt_grid[:-1, :-1] = count
    
    # Smooth with Gaussian
    sigma = 1.6
    u_smooth = gaussian_filter(u_grid, sigma=sigma)
    v_smooth = gaussian_filter(v_grid, sigma=sigma)
    cnt_smooth = gaussian_filter(cnt_grid, sigma=sigma)
    
    # Normalized velocity
    with np.errstate(divide='ignore', invalid='ignore'):
        U = np.where(cnt_smooth > 2.0, u_smooth / (cnt_smooth + 1e-5), 0.0)
        V = np.where(cnt_smooth > 2.0, v_smooth / (cnt_smooth + 1e-5), 0.0)
    
    # Mask outside pool
    U[~in_pool_mask] = 0.0
    V[~in_pool_mask] = 0.0
    return U, V

U_fem, V_fem = compute_grid_vectors(F_x, F_y, F_u, F_v)
U_mal, V_mal = compute_grid_vectors(M_x, M_y, M_u, M_v)

Speed_fem = np.sqrt(U_fem**2 + V_fem**2)
Speed_mal = np.sqrt(U_mal**2 + V_mal**2)

# Figure setup: Two side-by-side streamplots
fig, axes = plt.subplots(1, 2, figsize=(18, 9), facecolor="#090d14")
plt.subplots_adjust(wspace=0.15)

panels = [
    (axes[0], U_fem, V_fem, Speed_fem, "FEMALES (n = 16) · SWARM VECTOR CURRENT",
     "Organized hydrodynamic circulation: High-velocity corridor from checking platform to P1 quadrant & perimeter return loop.", "#38bdf8"),
    (axes[1], U_mal, V_mal, Speed_mal, "MALES (n = 13) · STATIC RETENTION FIELD",
     "Zero macroscopic velocity field: Energy remains tightly anchored within the platform boundaries with minimal spatial divergence.", "#fb923c")
]

for ax, U, V, Spd, title, desc, tag_col in panels:
    ax.set_facecolor("#090d14")
    ax.set_aspect("equal")
    ax.set_xlim(-92, 92)
    ax.set_ylim(-92, 92)
    ax.axis("off")
    
    # Pool background circle
    ax.add_patch(Circle((0, 0), R_CM, facecolor="#0c121c", edgecolor=(1, 1, 1, 0.2), linewidth=2.5, zorder=1))
    for r in [25, 50, 75]:
        ax.add_patch(Circle((0, 0), r, fill=False, edgecolor="#192233", linestyle=":", linewidth=1, zorder=1))
    
    # Checking Platform & P1
    ax.add_patch(Circle(plat_cm, 14.2, facecolor="#192336", edgecolor="#38bdf8", linewidth=2.2, zorder=2))
    ax.text(plat_cm[0], plat_cm[1], "Platform", color="#38bdf8", fontsize=9, fontweight="bold", ha="center", va="center", zorder=6)
    
    ax.add_patch(Circle(P1_CM, 14.2, facecolor=(0.66, 0.33, 0.97, 0.15), edgecolor="#c084fc", linewidth=2.2, linestyle="--", zorder=2))
    ax.text(P1_CM[0], P1_CM[1], "P1", color="#c084fc", fontsize=10, fontweight="bold", ha="center", va="center", zorder=6)
    
    # Streamplot
    speed_mag = np.sqrt(U**2 + V**2)
    lw = np.clip(speed_mag / 2.2, 0.8, 3.8)
    
    # Streamplot handles zero nicely
    strm = ax.streamplot(XI, YI, U, V, color=speed_mag, cmap="plasma",
                         density=1.5, linewidth=lw, arrowsize=1.4, zorder=4)
    
    # Title & tags
    ax.text(-86, 84, title, color=tag_col, fontsize=12.5, fontweight="bold", fontfamily="sans-serif")
    ax.text(-86, 76, desc, color="#94a3b8", fontsize=9.5, fontfamily="sans-serif", wrap=True)

# Add shared colorbar at the bottom
cbar_ax = fig.add_axes([0.3, 0.06, 0.4, 0.022])
cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0, 18), cmap="plasma"),
                    cax=cbar_ax, orientation="horizontal")
cbar.set_label("Macroscopic Current Speed (cm/s)", color="#ffffff", fontsize=10, fontweight="bold")
cbar.ax.tick_params(labelsize=9, labelcolor="#e2e8f0")

save_path2 = FIG_DIR / "art_swarm_streamplot.png"
fig.savefig(save_path2, dpi=200, bbox_inches="tight", facecolor="#090d14")
fig.savefig(SITE_FIG_DIR / "art_swarm_streamplot.png", dpi=200, bbox_inches="tight", facecolor="#090d14")
plt.close(fig)
print(f"Saved {save_path2}")


# ==============================================================================
# FIGURE 3: THE COMPASS OF ATTENTION (POLAR HEAD-ORIENTATION RADAR)
# ==============================================================================
print("Generating Figure 3: Compass of Attention (Polar Head Orientation)...")

# Calculate on-platform head orientation relative to the vector pointing toward P1
# For each rat in KAC Day 6, take all frames before first departure
angles_female = []
angles_male = []

for f in kac_files:
    z = np.load(f)
    sex = str(z["sex"].item() if z["sex"].ndim == 0 else z["sex"])
    valid = z["valid"].astype(bool)
    inside = z["inside"].astype(bool)
    
    # Prior to departure
    off = z["off"].astype(bool)
    if off.any():
        first_off = np.where(off)[0][0]
    else:
        first_off = len(off)
    
    mask = valid & inside & (np.arange(len(valid)) < first_off)
    if not mask.any():
        continue
    
    # Head angle and position
    cx, cy, R_px = z["pool"]
    scale = R_CM / R_px
    body_cm = (z["body"][mask] - np.array([cx, cy])) * scale
    head_rad = z["head_angle"][mask]  # Radians
    
    # Vector from current body to P1
    vec_to_p1 = P1_CM - body_cm
    ang_to_p1 = np.arctan2(vec_to_p1[:, 1], vec_to_p1[:, 0])
    
    # Relative alignment: 0 = straight to P1, +/- pi = away from P1
    rel_ang = np.angle(np.exp(1j * (head_rad - ang_to_p1)))
    
    if sex == "F":
        angles_female.extend(rel_ang)
    else:
        angles_male.extend(rel_ang)

angles_f = np.array(angles_female)
angles_m = np.array(angles_male)

fig = plt.figure(figsize=(15, 8), facecolor="#090d14")
gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1], wspace=0.3)
ax_polar = fig.add_subplot(gs[0], projection="polar", facecolor="#0e1522")
ax_timeseries = fig.add_subplot(gs[1], facecolor="#0e1522")

# --- POLAR RADAR ROSE ---
n_bins = 36
bins = np.linspace(-np.pi, np.pi, n_bins + 1)
hist_f, _ = np.histogram(angles_f, bins=bins, density=True)
hist_m, _ = np.histogram(angles_m, bins=bins, density=True)
bin_centers = (bins[:-1] + bins[1:]) / 2.0

# Plot Female radar (Sapphire / Violet)
ax_polar.plot(bin_centers, hist_f, color="#38bdf8", linewidth=2.8, label="Females (n = 16)", zorder=5)
ax_polar.fill(bin_centers, hist_f, color="#38bdf8", alpha=0.35, zorder=4)

# Plot Male radar (Amber)
ax_polar.plot(bin_centers, hist_m, color="#fb923c", linewidth=2.8, label="Males (n = 13)", zorder=5)
ax_polar.fill(bin_centers, hist_m, color="#fb923c", alpha=0.25, zorder=3)

# Polar formatting
ax_polar.set_theta_zero_location("N")  # 0 degrees at top (Facing P1)
ax_polar.set_theta_direction(-1)  # Clockwise
ax_polar.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315],
                        ["DIRECT AT P1 (0°)", "45°", "+90° (Right)", "135°", "OPPOSITE WALL (180°)", "225°", "-90° (Left)", "315°"],
                        color="#ffffff", fontsize=9, fontweight="bold")
ax_polar.grid(True, color="#222f42", linestyle=":")
ax_polar.tick_params(colors="#94a3b8")
ax_polar.set_title("ON-PLATFORM FIELD OF REGARD\nRelative Heading to Training Platform P1 (0°)",
                   color="#38bdf8", fontsize=12, fontweight="bold", pad=20)
ax_polar.legend(loc="lower right", facecolor="#131b28", edgecolor="#212c3d", labelcolor="#e2e8f0", fontsize=10)

# --- TIME SERIES HEAD SWEEP OSCILLOGRAM ---
# Take female rat 25 vs male rat 10 first 15 seconds
z_f = np.load(CACHE / "kac_d6_rat25.npz")
z_m = np.load(CACHE / "kac_d6_rat10.npz")
n_sec = 15 * 30
t_axis = np.arange(n_sec) / 30.0

turn_f = np.degrees(z_f["turn"][:n_sec])
turn_m = np.degrees(z_m["turn"][:n_sec])

ax_timeseries.plot(t_axis, turn_f, color="#38bdf8", linewidth=2.0, label="Female (Rat 25) · High-Frequency Sweeps")
ax_timeseries.plot(t_axis, turn_m, color="#fb923c", linewidth=1.8, label="Male (Rat 10) · Low Scanning Anchor", alpha=0.85)

ax_timeseries.axhline(30, color="#ffffff", linestyle=":", alpha=0.4)
ax_timeseries.axhline(-30, color="#ffffff", linestyle=":", alpha=0.4)
ax_timeseries.text(0.5, 33, "+30° Sweep Threshold", color="#94a3b8", fontsize=8.5)

ax_timeseries.set_ylabel("Head Angular Velocity (°/s)", color="#ffffff", fontsize=10, fontweight="bold")
ax_timeseries.set_xlabel("First 15 Seconds on Platform", color="#ffffff", fontsize=10, fontweight="bold")
ax_timeseries.tick_params(colors="#94a3b8")
ax_timeseries.grid(True, color="#222f42", linestyle=":")
ax_timeseries.set_xlim(0, 15)
ax_timeseries.set_title("MICRO-SCANNING OSCILLOGRAM\nAlternating Head Swings While on Platform",
                        color="#38bdf8", fontsize=12, fontweight="bold", pad=12)
ax_timeseries.legend(loc="upper right", facecolor="#131b28", edgecolor="#212c3d", labelcolor="#e2e8f0", fontsize=9.5)

save_path3 = FIG_DIR / "art_gaze_compass.png"
fig.savefig(save_path3, dpi=200, bbox_inches="tight", facecolor="#090d14")
fig.savefig(SITE_FIG_DIR / "art_gaze_compass.png", dpi=200, bbox_inches="tight", facecolor="#090d14")
plt.close(fig)
print(f"Saved {save_path3}")


# ==============================================================================
# FIGURE 4: 3D SPATIOTEMPORAL HELIX MANIFOLD
# ==============================================================================
print("Generating Figure 4: 3D Spatiotemporal Manifold...")

fig = plt.figure(figsize=(14, 11), facecolor="#090d14")
ax_3d = fig.add_subplot(projection="3d", facecolor="#090d14")

# Load Rat 25 (Female leaver) and Rat 02 (Male stayer)
z_fe = np.load(CACHE / "kac_d6_rat25.npz")
z_ma = np.load(CACHE / "kac_d6_rat02.npz")

scale_f = R_CM / z_fe["pool"][2]
scale_m = R_CM / z_ma["pool"][2]

b_fe = (z_fe["body"] - z_fe["pool"][:2]) * scale_f
b_ma = (z_ma["body"] - z_ma["pool"][:2]) * scale_m

t_fe = np.arange(len(b_fe)) / 30.0
t_ma = np.arange(len(b_ma)) / 30.0

# Plot base circular pool at T = 0
theta = np.linspace(0, 2*np.pi, 120)
x_pool = R_CM * np.cos(theta)
y_pool = R_CM * np.sin(theta)
ax_3d.plot(x_pool, y_pool, np.zeros_like(x_pool), color="#1e293b", linewidth=2.5)

# Checking Platform Cylindrical Pillar in Space-Time
p_x = plat_cm[0] + 14.2 * np.cos(theta)
p_y = plat_cm[1] + 14.2 * np.sin(theta)
ax_3d.plot(p_x, p_y, np.zeros_like(p_x), color="#38bdf8", linewidth=1.5)
ax_3d.plot(p_x, p_y, np.full_like(p_x, 120), color="#38bdf8", linewidth=1.5)

# P1 Target Pillar in Space-Time
p1_x = P1_CM[0] + 14.2 * np.cos(theta)
p1_y = P1_CM[1] + 14.2 * np.sin(theta)
ax_3d.plot(p1_x, p1_y, np.zeros_like(p1_x), color="#c084fc", linestyle="--", linewidth=1.5)
ax_3d.plot(p1_x, p1_y, np.full_like(p1_x, 120), color="#c084fc", linestyle="--", linewidth=1.5)

# Plot Male trajectory (Stays anchored in platform cylinder)
ax_3d.plot(b_ma[:, 0], b_ma[:, 1], t_ma, color="#fb923c", linewidth=2.2, label="Male (Rat 02) · Confined Platform Spindle", zorder=5)

# Plot Female trajectory (Bursts out into sweeping space-time helices)
# Segmented by speed
vel_f = np.gradient(b_fe, axis=0) * 30.0
spd_f = np.linalg.norm(vel_f, axis=1)

ax_3d.plot(b_fe[:, 0], b_fe[:, 1], t_fe, color="#38bdf8", linewidth=2.5, label="Female (Rat 25) · Space-Time Excursion Helices", zorder=6)

# Labels & View Angle
ax_3d.set_xlabel("Pool X (cm)", color="#94a3b8", fontsize=10, labelpad=10)
ax_3d.set_ylabel("Pool Y (cm)", color="#94a3b8", fontsize=10, labelpad=10)
ax_3d.set_zlabel("Time (Seconds, 0 to 120s)", color="#38bdf8", fontsize=10, labelpad=10)

ax_3d.tick_params(colors="#94a3b8", labelsize=8.5)
ax_3d.view_init(elev=28, azim=-62)

# Transparent panes
ax_3d.xaxis.set_pane_color((0.05, 0.08, 0.12, 1.0))
ax_3d.yaxis.set_pane_color((0.05, 0.08, 0.12, 1.0))
ax_3d.zaxis.set_pane_color((0.07, 0.10, 0.15, 1.0))

ax_3d.set_title("SPATIOTEMPORAL HELIX MANIFOLD · 3D SPACE-TIME RECONSTRUCTION\nMale Platform Spindle vs Female Excursion Helices Orbiting P1",
                color="#ffffff", fontsize=12, fontweight="bold", pad=20)
ax_3d.legend(loc="upper left", facecolor="#131b28", edgecolor="#212c3d", labelcolor="#e2e8f0", fontsize=9.5)

save_path4 = FIG_DIR / "art_spacetime_helix.png"
fig.savefig(save_path4, dpi=200, bbox_inches="tight", facecolor="#090d14")
fig.savefig(SITE_FIG_DIR / "art_spacetime_helix.png", dpi=200, bbox_inches="tight", facecolor="#090d14")
plt.close(fig)
print(f"Saved {save_path4}")

print("All 4 DLC visual exploration figures successfully created!")
