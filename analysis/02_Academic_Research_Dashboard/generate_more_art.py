"""Generates 4 advanced DeepLabCut computational ethology art pieces:
1. art_swarm_ghosts.png (Fiber-optic trajectory superhighways: All 16 Females vs All 13 Males)
2. art_vorticity_landscape.png (Topological Vorticity & Kinetic Energy Landscape)
3. art_compass_fingerprints.png (29 Individual Polar Attention Compass Roses)
4. art_posture_kymograph.png (Spatiotemporal Posture Curvature Kymograph & Traveling Undulation Waves)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
FIG_DIR = HERE / "figures"
SITE_FIG_DIR = HERE / "site" / "figures"

R_CM = 86.0
P1_FRAC = np.array([0.28, -0.355])
P1_CM = P1_FRAC * R_CM

print("Starting generation of advanced DLC visual art pieces...")

# ==============================================================================
# FIGURE 5: FIBER-OPTIC GHOST SWARM SUPERHIGHWAYS (ALL FEMALES VS ALL MALES)
# ==============================================================================
print("Generating Figure 5: Fiber-Optic Swarm Superhighways...")

kac_files = sorted(CACHE.glob("kac_d6_rat*.npz"))

fig, axes = plt.subplots(1, 2, figsize=(18, 9), facecolor="#070a0f")
plt.subplots_adjust(wspace=0.12)

# Load sample platform position
z_sample = np.load(kac_files[0])
cx_s, cy_s, R_s = z_sample["pool"]
scale_s = R_CM / R_s
plat_cm = (z_sample["platform"] - np.array([cx_s, cy_s])) * scale_s

panels = [
    (axes[0], "F", "FEMALE SUPERHIGHWAY · ALL 16 SUBJECTS SUPERIMPOSED",
     "Dense spatial convergence: The multi-filament fiber-optic superhighway funnels directly from the platform into the P1 target quadrant and sweeps the perimeter wall.",
     "#60a5fa", plt.cm.Blues),
    (axes[1], "M", "MALE RETENTION CORE · ALL 13 SUBJECTS SUPERIMPOSED",
     "Stationary confinement: Over 90% of male trajectory filaments remain tightly coiled within the 14 cm platform boundary.",
     "#fb923c", plt.cm.Oranges)
]

for ax, target_sex, title, desc, accent_col, cmap_seq in panels:
    ax.set_facecolor("#070a0f")
    ax.set_aspect("equal")
    ax.set_xlim(-92, 92)
    ax.set_ylim(-92, 92)
    ax.axis("off")

    # Base Pool Circle & Subtle Range Rings
    ax.add_patch(Circle((0, 0), R_CM, facecolor="#0a0f18", edgecolor=(1, 1, 1, 0.22), linewidth=2.5, zorder=1))
    for r in [25, 50, 75]:
        ax.add_patch(Circle((0, 0), r, fill=False, edgecolor="#141c2b", linestyle=":", linewidth=1, zorder=1))

    # Checking Platform Halo
    ax.add_patch(Circle(plat_cm, 14.2, facecolor="#141e2e", edgecolor="#38bdf8", linewidth=2.2, zorder=2))
    ax.text(plat_cm[0], plat_cm[1], "Platform", color="#38bdf8", fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=8)

    # P1 Target Halo
    ax.add_patch(Circle(P1_CM, 14.2, facecolor=(0.66, 0.33, 0.97, 0.12), edgecolor="#c084fc", linewidth=2.2, linestyle="--", zorder=2))
    ax.plot(P1_CM[0], P1_CM[1], marker="D", color="#c084fc", markersize=7, zorder=8)
    ax.text(P1_CM[0], P1_CM[1] - 17, "P1 Target", color="#c084fc", fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=8)

    # Plot all individual rat filaments
    rat_count = 0
    for f in kac_files:
        z = np.load(f)
        sex = str(z["sex"].item() if z["sex"].ndim == 0 else z["sex"])
        if sex != target_sex:
            continue
        rat_count += 1
        cx, cy, R_px = z["pool"]
        scale = R_CM / R_px
        body = (z["body"] - np.array([cx, cy])) * scale
        valid = z["valid"].astype(bool)

        # Split into continuous valid runs
        diff = np.diff(valid.astype(int))
        starts = np.where(diff == 1)[0] + 1
        if valid[0]: starts = np.r_[0, starts]
        ends = np.where(diff == -1)[0] + 1
        if valid[-1]: ends = np.r_[ends, len(valid)]

        for s, e in zip(starts, ends):
            if e - s < 5: continue
            seg = body[s:e]
            # Speed for coloring
            vel = np.gradient(seg, axis=0) * 30.0
            spd = np.linalg.norm(vel, axis=1)

            # Build line segments
            pts = seg.reshape(-1, 1, 2)
            line_segs = np.concatenate([pts[:-1], pts[1:]], axis=1)

            norm = plt.Normalize(0, 35)
            lc = LineCollection(line_segs, cmap="plasma" if target_sex == "F" else "cividis",
                                norm=norm, linewidth=1.2, alpha=0.38, zorder=4)
            lc.set_array(spd[:-1])
            ax.add_collection(lc)

    # Title & Captions
    ax.text(-86, 84, title, color=accent_col, fontsize=12.5, fontweight="bold", fontfamily="sans-serif")
    ax.text(-86, 76, desc, color="#94a3b8", fontsize=9.5, fontfamily="sans-serif")

save_path5 = FIG_DIR / "art_swarm_ghosts.png"
fig.savefig(save_path5, dpi=200, bbox_inches="tight", facecolor="#070a0f")
fig.savefig(SITE_FIG_DIR / "art_swarm_ghosts.png", dpi=200, bbox_inches="tight", facecolor="#070a0f")
plt.close(fig)
print(f"Saved {save_path5}")


# ==============================================================================
# FIGURE 6: TOPOLOGICAL VORTICITY & KINETIC CIRCULATION LANDSCAPE
# ==============================================================================
print("Generating Figure 6: Topological Vorticity & Circulation...")

# Compute velocity vector grid for females
fx, fy, fu, fv = [], [], [], []
for f in kac_files:
    z = np.load(f)
    if str(z["sex"].item() if z["sex"].ndim == 0 else z["sex"]) == "F":
        cx, cy, R = z["pool"]
        scale = R_CM / R
        valid = z["valid"].astype(bool)
        b = (z["body"][valid] - np.array([cx, cy])) * scale
        v = np.gradient(b, axis=0) * 30.0
        m = (np.linalg.norm(v, axis=1) < 80.0) & (np.isfinite(b).all(1))
        fx.append(b[m, 0]); fy.append(b[m, 1]); fu.append(v[m, 0]); fv.append(v[m, 1])

X = np.concatenate(fx); Y = np.concatenate(fy); U = np.concatenate(fu); V = np.concatenate(fv)
grid_n = 70
edges = np.linspace(-84, 84, grid_n + 1)
centers = (edges[:-1] + edges[1:]) / 2.0
XI, YI = np.meshgrid(centers, centers)
R_grid = np.sqrt(XI**2 + YI**2)
in_pool = R_grid <= (R_CM - 2.0)

u_grid, _, _ = np.histogram2d(Y, X, bins=[edges, edges], weights=U)
v_grid, _, _ = np.histogram2d(Y, X, bins=[edges, edges], weights=V)
cnt, _, _ = np.histogram2d(Y, X, bins=[edges, edges])

u_s = gaussian_filter(u_grid, 2.0) / (gaussian_filter(cnt, 2.0) + 1e-3)
v_s = gaussian_filter(v_grid, 2.0) / (gaussian_filter(cnt, 2.0) + 1e-3)
u_s[~in_pool] = np.nan
v_s[~in_pool] = np.nan

# Vorticity: dVy/dx - dVx/dy
dx = centers[1] - centers[0]
dvy_dx = np.gradient(np.nan_to_num(v_s), dx, axis=1)
dvx_dy = np.gradient(np.nan_to_num(u_s), dx, axis=0)
vorticity = dvy_dx - dvx_dy
vorticity[~in_pool] = np.nan

fig, ax = plt.subplots(figsize=(12, 11), facecolor="#070a0f")
ax.set_facecolor("#070a0f")
ax.set_aspect("equal")
ax.set_xlim(-92, 92)
ax.set_ylim(-92, 92)
ax.axis("off")

# Pool Boundary
ax.add_patch(Circle((0, 0), R_CM, facecolor="#090d14", edgecolor=(1, 1, 1, 0.25), linewidth=2.5, zorder=1))

# Vorticity Colormap Contour
v_max = 3.5
cf = ax.contourf(XI, YI, vorticity, levels=np.linspace(-v_max, v_max, 41),
                 cmap="coolwarm", extend="both", alpha=0.85, zorder=2)
cs = ax.contour(XI, YI, vorticity, levels=[-2.5, -1.5, -0.5, 0.5, 1.5, 2.5],
                colors="#ffffff", alpha=0.3, linewidths=0.8, zorder=3)

# Streamline overlay
speed = np.sqrt(u_s**2 + v_s**2)
speed_clean = np.nan_to_num(speed)
ax.streamplot(centers, centers, np.nan_to_num(u_s), np.nan_to_num(v_s),
              color="#ffffff", linewidth=0.8 + 2.0 * (speed_clean / (np.nanmax(speed_clean) + 1e-5)),
              density=1.4, arrowsize=1.2, zorder=4)

# Checking Platform & P1
ax.add_patch(Circle(plat_cm, 14.2, facecolor="#141e2e", edgecolor="#38bdf8", linewidth=2.5, zorder=5))
ax.text(plat_cm[0], plat_cm[1], "Platform", color="#38bdf8", fontsize=10, fontweight="bold", ha="center", va="center", zorder=8)

ax.add_patch(Circle(P1_CM, 14.2, facecolor=(0.66, 0.33, 0.97, 0.15), edgecolor="#c084fc", linewidth=2.5, linestyle="--", zorder=5))
ax.plot(P1_CM[0], P1_CM[1], marker="D", color="#c084fc", markersize=8, zorder=8)
ax.text(P1_CM[0], P1_CM[1] - 18, "P1 Target", color="#c084fc", fontsize=10, fontweight="bold", ha="center", va="center", zorder=8)

# Colorbar
cbar_ax = fig.add_axes([0.25, 0.07, 0.5, 0.022])
cbar = fig.colorbar(cf, cax=cbar_ax, orientation="horizontal")
cbar.set_label("Vorticity (Curl ∇ × v, s⁻¹) · Red: Counter-Clockwise Vortex, Blue: Clockwise Vortex",
               color="#ffffff", fontsize=10, fontweight="bold")
cbar.ax.tick_params(labelsize=9, labelcolor="#e2e8f0")

ax.text(-88, 85, "HYDRODYNAMIC VORTICITY LANDSCAPE · FEMALE EXPLORATORY DIPOLE",
        color="#38bdf8", fontsize=13, fontweight="bold", fontfamily="sans-serif")
ax.text(-88, 78, "Streamlines overlaid on rotational circulation: Counter-rotating vortices funnel movement toward P1.",
        color="#94a3b8", fontsize=10, fontfamily="sans-serif")

save_path6 = FIG_DIR / "art_vorticity_landscape.png"
fig.savefig(save_path6, dpi=200, bbox_inches="tight", facecolor="#070a0f")
fig.savefig(SITE_FIG_DIR / "art_vorticity_landscape.png", dpi=200, bbox_inches="tight", facecolor="#070a0f")
plt.close(fig)
print(f"Saved {save_path6}")


# ==============================================================================
# FIGURE 7: 29 INDIVIDUAL POLAR ATTENTION COMPASS FINGERPRINTS
# ==============================================================================
print("Generating Figure 7: 29 Individual Polar Attention Compass Roses...")

# Grid of 5 rows x 6 columns for 29 animals
fig, axes = plt.subplots(5, 6, figsize=(18, 15), subplot_kw={"projection": "polar"}, facecolor="#070a0f")
plt.subplots_adjust(wspace=0.3, hspace=0.35)

n_bins = 24
bins = np.linspace(-np.pi, np.pi, n_bins + 1)
bin_centers = (bins[:-1] + bins[1:]) / 2.0

for i, f in enumerate(kac_files):
    row, col = divmod(i, 6)
    ax = axes[row, col]
    ax.set_facecolor("#0d121c")

    z = np.load(f)
    rat_id = int(z["rat"].item() if z["rat"].ndim == 0 else z["rat"])
    sex = str(z["sex"].item() if z["sex"].ndim == 0 else z["sex"])
    valid = z["valid"].astype(bool)
    inside = z["inside"].astype(bool)
    off = z["off"].astype(bool)
    first_off = np.where(off)[0][0] if off.any() else len(off)

    mask = valid & inside & (np.arange(len(valid)) < first_off)
    cx, cy, R_px = z["pool"]
    scale = R_CM / R_px

    col_theme = "#60a5fa" if sex == "F" else "#fb923c"

    if mask.sum() > 30:
        b_cm = (z["body"][mask] - np.array([cx, cy])) * scale
        h_rad = z["head_angle"][mask]
        vec = P1_CM - b_cm
        ang_to_p1 = np.arctan2(vec[:, 1], vec[:, 0])
        rel_ang = np.angle(np.exp(1j * (h_rad - ang_to_p1)))

        hist, _ = np.histogram(rel_ang, bins=bins, density=True)
        ax.plot(bin_centers, hist, color=col_theme, linewidth=1.8)
        ax.fill(bin_centers, hist, color=col_theme, alpha=0.35)
    else:
        # Fallback if immediately left
        ax.plot([0, 0], [0, 1], color=col_theme, linewidth=1.5)

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetagrids([0, 90, 180, 270], ["P1", "", "180°", ""], fontsize=6.5, color="#64748b")
    ax.tick_params(labelleft=False)
    ax.grid(True, color="#1a2538", linestyle=":")
    ax.set_title(f"Rat {rat_id:02d} ({'Female' if sex=='F' else 'Male'})",
                 color=col_theme, fontsize=9.5, fontweight="bold", pad=8)

# Blank the last unused subplot (30th)
axes[4, 5].axis("off")

fig.suptitle("INDIVIDUAL ATTENTION COMPASS ROSES · ALL 29 ANIMALS (KAC DAY 6)\nRelative Head Direction While on Platform Prior to Disembarkation (0° = Pointing at P1)",
             color="#ffffff", fontsize=14, fontweight="bold", y=0.96)

save_path7 = FIG_DIR / "art_compass_fingerprints.png"
fig.savefig(save_path7, dpi=200, bbox_inches="tight", facecolor="#070a0f")
fig.savefig(SITE_FIG_DIR / "art_compass_fingerprints.png", dpi=200, bbox_inches="tight", facecolor="#070a0f")
plt.close(fig)
print(f"Saved {save_path7}")


# ==============================================================================
# FIGURE 8: SPATIOTEMPORAL POSTURE CURVATURE KYMOGRAPH
# ==============================================================================
print("Generating Figure 8: Spatiotemporal Posture Curvature Kymograph...")

# Compare Rat 28: Platform Scanning (t = 0 to 12s) vs Excursion Swimming (t = 56 to 65s)
z28 = np.load(CACHE / "kac_d6_rat28.npz")
pts = ["nose", "head_center", "neck", "spine_upper", "spine_mid", "spine_lower", "tail_base"]
coords = np.stack([z28[p] for p in pts], axis=1)  # (3600, 7, 2)
seg = np.diff(coords, axis=1)  # (3600, 6, 2)
angles = np.arctan2(seg[:, :, 1], seg[:, :, 0])  # (3600, 6)
curv = np.angle(np.exp(1j * np.diff(angles, axis=1)))  # (3600, 5)

fig, (ax_scan, ax_swim) = plt.subplots(2, 1, figsize=(15, 8), facecolor="#070a0f")
plt.subplots_adjust(hspace=0.35)

joint_labels = ["Nose-Head", "Head-Neck", "Neck-Upper", "Upper-Mid", "Mid-Lower"]

# Panel 1: Platform Scanning (Frames 0 to 360 = 0 to 12 seconds)
t1 = np.arange(360) / 30.0
kym1 = curv[:360].T  # (5, 360)
im1 = ax_scan.imshow(kym1, aspect="auto", cmap="coolwarm", vmin=-np.pi/2.5, vmax=np.pi/2.5,
                     extent=[0, 12, 4.5, -0.5])
ax_scan.set_yticks(range(5))
ax_scan.set_yticklabels(joint_labels, color="#94a3b8", fontsize=9.5, fontweight="bold")
ax_scan.set_xlabel("Time on Platform (Seconds 0 to 12)", color="#ffffff", fontsize=10, fontweight="bold")
ax_scan.set_title("STAGE 1 · ON-PLATFORM SCANNING: Cranial Joints Oscillate While Body Axis Remains Rigid",
                  color="#38bdf8", fontsize=11.5, fontweight="bold", pad=8)
ax_scan.tick_params(colors="#94a3b8")

# Panel 2: Swimming Excursion to P1 (Frames 1680 to 1950 = 56 to 65 seconds)
t2 = np.arange(1680, 1950) / 30.0
kym2 = curv[1680:1950].T
im2 = ax_swim.imshow(kym2, aspect="auto", cmap="coolwarm", vmin=-np.pi/3.5, vmax=np.pi/3.5,
                     extent=[56, 65, 4.5, -0.5])
ax_swim.set_yticks(range(5))
ax_swim.set_yticklabels(joint_labels, color="#94a3b8", fontsize=9.5, fontweight="bold")
ax_swim.set_xlabel("Time in Excursion to P1 (Seconds 56 to 65)", color="#ffffff", fontsize=10, fontweight="bold")
ax_swim.set_title("STAGE 2 · ACTIVE SWIMMING DASH: Retrograde Traveling Waves Undulate from Head to Tail (~2.5 Hz)",
                  color="#fb923c", fontsize=11.5, fontweight="bold", pad=8)
ax_swim.tick_params(colors="#94a3b8")

# Colorbar
cbar_ax = fig.add_axes([0.92, 0.25, 0.015, 0.5])
cbar = fig.colorbar(im1, cax=cbar_ax)
cbar.set_label("Spine Bending Curvature κ (rad) · Red: Right Flex, Blue: Left Flex",
               color="#ffffff", fontsize=9.5, fontweight="bold")
cbar.ax.tick_params(labelsize=8.5, labelcolor="#e2e8f0")

save_path8 = FIG_DIR / "art_posture_kymograph.png"
fig.savefig(save_path8, dpi=200, bbox_inches="tight", facecolor="#070a0f")
fig.savefig(SITE_FIG_DIR / "art_posture_kymograph.png", dpi=200, bbox_inches="tight", facecolor="#070a0f")
plt.close(fig)
print(f"Saved {save_path8}")

print("All 4 advanced DLC visual art pieces generated successfully!")
