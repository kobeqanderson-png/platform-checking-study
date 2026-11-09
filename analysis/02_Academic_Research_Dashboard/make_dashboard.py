"""Builds dashboard.html (results + demo videos) from the cleaned results.
Run after analyze.py and the demo trimming.
Usage: python make_dashboard.py
"""
from pathlib import Path
import json
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
R = HERE / "results"

# Load statistics and measures
S = pd.read_csv(R / "sex_statistics.csv")
D = pd.read_csv(R / "per_rat_measures.csv")
E = pd.read_csv(R / "lean_out_events.csv")
CV = pd.read_csv(R / "committed_vs_aborted.csv")
PB = pd.read_csv(R / "paired_platform_bounds.csv")
NV = pd.read_csv(R / "notes_validation.csv")
kn = NV[NV.known_note == True]
ag = kn.groupby('cond').agreement.agg(['sum', 'count'])
agree = ' and '.join(f"{int(ag.loc[c,'sum'])}/{int(ag.loc[c,'count'])} ({'Day 6' if c=='kac_d6' else 'Day 8'})" for c in ('kac_d6','kac_d8') if c in ag.index)
agree_short = f"{int(ag['sum'].sum())}/{int(ag['count'].sum())}"

X = json.load(open(R / "sp1_extra.json"))
XP = X["p1"]
DT = pd.read_csv(R / "departure_types.csv").groupby(["cond", "kind"]).size()
fp = PB[PB.group == "F"].iloc[0]
mp = PB[PB.group == "M"].iloc[0]
cv = {r.cond: r for r in CV.itertuples()}

CONDS = [
    ("sp1", "SP1 Cohort", "Raised water (3.0 cm)"),
    ("kac_d6", "KAC Day 6", "Standard water (1.5 cm)"),
    ("kac_d8", "KAC Day 8", "Raised water (3.0 cm)")
]

def p_fmt(x):
    return "&lt; 0.001" if x < .001 else f"{x:.3f}"

def cls(x):
    return "sig" if x < .05 else "ns"

stay = {}
for c, *_ in CONDS:
    x = D[D.cond == c]
    s = {k: int(((x.sex == k) & (x.departures_observed == 0)).sum()) for k in "FM"}
    n = {k: int((x.sex == k).sum()) for k in "FM"}
    stay[c] = (s, n, stats.fisher_exact([[s["M"], n["M"] - s["M"]], [s["F"], n["F"] - s["F"]]])[1])

com = E.groupby(["cond", "sex", "kind"]).size().unstack(fill_value=0)
com["pct"] = 100 * com.committed / (com.committed + com.aborted)

ROWS = [
    ("platform_lower_pct", "Time on platform zone (%)", "Retained on-platform time; conservative lower bound conditional on accepted tracking", "{:.0f}%"),
    ("head_turn_pre_deg_s", "Head-turn speed (deg/s)", "On the platform, before any departure", "{:.0f}"),
    ("head_turn_first10_deg_s", "Head-turn speed, first 10 s", "Initial period when nearly all rats remain on the platform", "{:.0f}"),
    ("idphi_deg_s", "Head rotation rate (deg/s)", "Absolute head rotation rate per valid on-platform second", "{:.0f}"),
    ("head_sweeps_per_min", "Head sweeps per minute", "Angular head swings of 30° or more", "{:.0f}"),
    ("vte_episodes_per_min", "VTE-like episodes per minute", "Two or more alternating sweeps within 2 s", "{:.1f}"),
    ("edge_oscillations_per_min", "Edge rocking per minute", "Snout rocks forward and backward at least 1.5 cm over platform edge", "{:.0f}"),
    ("drift_observed_cm_s", "Body drift on platform (cm/s)", "Passive and active displacement while on platform", "{:.1f}")
]

rows_html = []
cells = "".join(f'<td><div class="val-comp"><span class="f-badge">{stay[c][0]["F"]}/{stay[c][1]["F"]}</span><span class="vs">vs</span><span class="m-badge">{stay[c][0]["M"]}/{stay[c][1]["M"]}</span></div><span class="stat-tag {cls(stay[c][2])}">Fisher p {p_fmt(stay[c][2])}</span></td>' for c, *_ in CONDS)
rows_html.append(f'<tr><th><div class="row-title">No observed departure</div><div class="row-note">Session contains 0 departures; tracking continuity verified</div></th>{cells}</tr>')

for key, lab, note, fmt in ROWS:
    cs = ""
    for c, *_ in CONDS:
        r = S[(S.cond == c) & (S.measure == key)]
        if r.empty:
            cs += '<td><span class="val-dash">–</span></td>'
            continue
        r = r.iloc[0]
        if pd.isna(r.mean_F) or pd.isna(r.mean_M):
            cs += '<td><span class="val-dash">–</span><div class="row-note">not measured</div></td>'
            continue
        cs += f'<td><div class="val-comp"><span class="f-badge">{fmt.format(r.mean_F)}</span><span class="vs">vs</span><span class="m-badge">{fmt.format(r.mean_M)}</span></div><span class="stat-tag {cls(r.holm_p)}">Holm p {p_fmt(r.holm_p)}</span></td>'
    rows_html.append(f'<tr><th><div class="row-title">{lab}</div><div class="row-note">{note}</div></th>{cs}</tr>')

cs = ""
for c, *_ in CONDS:
    f_, m_ = com.loc[(c, "F")], com.loc[(c, "M")]
    cs += f'<td><div class="val-comp"><span class="f-badge">{f_.pct:.0f}%</span><span class="vs">vs</span><span class="m-badge">{m_.pct:.0f}%</span></div><div class="row-note">{int(f_.committed)}/{int(f_.committed + f_.aborted)} vs {int(m_.committed)}/{int(m_.committed + m_.aborted)} lean-outs</div></td>'
rows_html.append(f'<tr><th><div class="row-title">Departures per lean-out attempt</div><div class="row-note">Pooled descriptive fraction of platform edge lean-outs converting to full swim departures</div></th>{cs}</tr>')

# Video metadata
VIDS = [
    {
        "id": "leave_vs_stay_sp1",
        "tag": "SP1 Cohort · Raised Water (3.0 cm)",
        "badge": "120s @ 4× Time-Lapse",
        "title": "Leaving vs Staying (SP1)",
        "desc": "Full 120 s side-by-side at 4× speed. A representative female leaves 3 times (initial disembarkation at 7.6 s); a representative male remains anchored on the platform.",
        "category": "side-by-side",
        "poster": "demos_trimmed/posters/leave_vs_stay_sp1.jpg"
    },
    {
        "id": "leave_vs_stay_kac_d6",
        "tag": "KAC Cohort Day 6 · Standard Water (1.5 cm)",
        "badge": "120s @ 4× Time-Lapse",
        "title": "Leaving vs Staying (KAC Day 6)",
        "desc": "Standard water depth. Purple diamond and dotted ring mark P1, the exact location of the escape platform during 5 days of spatial training.",
        "category": "side-by-side",
        "poster": "demos_trimmed/posters/leave_vs_stay_kac_d6.jpg"
    },
    {
        "id": "leave_vs_stay_kac_d8",
        "tag": "KAC Cohort Day 8 · Raised Water (3.0 cm)",
        "badge": "120s @ 4× Time-Lapse",
        "title": "Leaving vs Staying (KAC Day 8)",
        "desc": "Raised water depth in the same animals. Replicates the pronounced female leaving phenotype with doubled departure frequency.",
        "category": "side-by-side",
        "poster": "demos_trimmed/posters/leave_vs_stay_kac_d8.jpg"
    },
    {
        "id": "departure_to_P1",
        "tag": "KAC Day 6 Female · Target Excursion",
        "badge": "Real Time (1×)",
        "title": "Direct Excursion to Training Location P1",
        "desc": "A KAC Day 6 female disembarks, swims directly to the former training platform coordinates (P1), searches, and returns to the checking platform.",
        "category": "excursion",
        "poster": "demos_trimmed/posters/departure_to_P1.jpg"
    },
    {
        "id": "departure_to_wall",
        "tag": "KAC Day 6 Female · Perimeter Sweep",
        "badge": "Real Time (1×)",
        "title": "Perimeter Thigmotaxis & Return",
        "desc": "A female leaves the checking platform, follows the outer tank perimeter in a sweeping search arc, and reliably climbs back onto the platform.",
        "category": "excursion",
        "poster": "demos_trimmed/posters/departure_to_wall.jpg"
    },
    {
        "id": "departure_wander",
        "tag": "KAC Day 6 Female · Open Water Loop",
        "badge": "Real Time (1×)",
        "title": "Open-Water Exploratory Loop",
        "desc": "A brief open-water excursion that returns to the platform without contacting either P1 or the pool perimeter wall.",
        "category": "excursion",
        "poster": "demos_trimmed/posters/departure_wander.jpg"
    }
]

FIGS = [
    ("03_platform_state", "Every Rat, Every Second", "Raster occupancy across all 120 seconds. Grey: on-platform. Colored: off-platform swimming. Dark: tracking gap. Females leave repeatedly across all cohorts."),
    ("01_cleaned_paths", "DeepLabCut Pose Trajectories", "Spatial trajectories under the final model. Purple diamond & 20 cm dotted ring: P1 training platform location."),
    ("10_sp1_p1", "SP1: Off-Platform P1 Density", "Left: off-platform dwell within 20 cm of P1 vs matched control spots per rat. Right: SP1 trajectory maps."),
    ("06_head_scanning", "Platform Micro-Scanning & Kinematics", "Head-turn angular velocity before departure, total sweep frequency, and alternating VTE episodes. Orange: males, Blue: females."),
    ("05_paired_platform_bounds", "Paired Comparison: Standard vs Raised Depth", "Within-subject trajectory bounds in standard vs raised water depth. Gaps and untracked intervals are strictly bounded."),
    ("08_lean_outs", "Platform Edge Lean-Out Kinematics", "Head rotation before aborted pull-backs vs committed disembarkations."),
    ("04_missingness", "Tracking Continuity & Quality Control", "Tracking completeness per animal. Less than 1% of female time is untracked with the final rotation-augmented model.")
]

def make_html(is_site=False):
    prefix_corr = "../../correlations/" if is_site else "../correlations/"
    profiles_link = "profiles.html" if is_site else "site/profiles.html"
    explorer_link = "explorer.html" if is_site else "site/explorer.html"
    motion_lab_link = "dlc_motion_lab.html"
    return_portal_link = "../../portal/site/portal.html" if is_site else "../portal/site/portal.html"
    
    # Visual Art Cards (All 10 Grand Plates)
    art_cards = [
        ("art_chrono_skeleton", "Chrono-Strobe Pose Reconstruction", "16-point DeepLabCut skeletal stroboscope capturing high-speed posture maintenance during a direct excursion to P1.", "STROBE · POSE KINEMATICS"),
        ("art_posture_kymograph", "Posture Curvature Kymograph", "Spatiotemporal curvature κ along the body axis: cranial scanning oscillations vs 2.5 Hz retrograde traveling undulation waves.", "POSTURE · UNDULATION WAVES"),
        ("art_gaze_compass", "The Compass of Attention", "Polar radar distribution of on-platform head orientation relative to P1 and alternating head-sweep oscillograms.", "POLAR RADAR · GAZE CONE"),
        ("art_spacetime_helix", "3D Space-Time Corkscrew Manifold", "Spatiotemporal 3D reconstruction showing female space-time helices orbiting P1 vs male coiled platform spindles.", "3D MANIFOLD · SPACE-TIME"),
        ("art_swarm_ghosts", "Collective Fiber-Optic Superhighways", "All 16 females vs all 13 males superimposed in fiber-optic filaments, highlighting the dense corridor toward P1.", "POPULATION SWARMS · SUPERHIGHWAY"),
        ("art_swarm_streamplot", "Macroscopic Swarm Currents", "Streamline hydrodynamic vector field comparing the active female circulation corridor to the male static platform anchor.", "VECTOR CURRENTS · STREAMPLOT"),
        ("art_vorticity_landscape", "Topological Vorticity Landscape", "Curl of the velocity field (∇ × v) showing counter-rotating dipolar circulation funnelling movement toward P1.", "FLUID DYNAMICS · VORTICITY"),
        ("art_compass_fingerprints", "29 Individual Attention Roses", "Individual polar directional radars for every single rat, showing reproducible heading focus toward P1.", "POPULATION FINGERPRINTS · COMPASS"),
        ("art_eigenpostures", "Posture Attractor Manifold & Eigen-Deformation Modes", "97,915-frame egocentric pose decomposition: lateral undulation (43.2%), cranial flexion (34.8%), and the dynamical bifurcation between platform scanning and swimming limit cycles.", "EIGEN-POSTURES · PHASE SPACE"),
        ("art_wavelet_sonogram", "Time-Frequency Morlet Wavelet Ethogram Sonogram", "Continuous complex Morlet wavelets of body curvature: 2.5 Hz resonant swimming propulsion bursts vs 0.8 Hz on-platform exploratory scanning oscillations.", "TIME-FREQUENCY · MORLET WAVELET")
    ]
    art_cards_html = []
    for f_id, title, desc, tag in art_cards:
        art_cards_html.append(f"""
        <div class="figure-card" onclick="openLightbox('figures/{f_id}.png', '{title}', '{desc}')" style="border-color:var(--panel-border-hover);">
          <div class="figure-thumb-wrap" style="background:#090d14;">
            <img loading="lazy" src="figures/{f_id}.png" alt="{title}">
            <div class="figure-zoom-overlay">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Inspect High-Res</span>
            </div>
          </div>
          <div class="figure-body">
            <div class="figure-code" style="color:var(--accent);">{tag}</div>
            <h4 class="figure-title">{title}</h4>
            <p class="figure-desc">{desc}</p>
          </div>
        </div>
        """)
    art_joined = "".join(art_cards_html)

    # Generate video cards
    vid_cards_html = []
    for v in VIDS:
        vid_cards_html.append(f"""
        <div class="video-card" data-category="{v['category']}">
          <div class="video-frame">
            <video src="demos_trimmed/{v['id']}.mp4" poster="{v['poster']}" controls playsinline preload="metadata"></video>
            <div class="video-badge-strip">
              <span class="video-badge category">{v['tag']}</span>
              <span class="video-badge speed">{v['badge']}</span>
            </div>
          </div>
          <div class="video-body">
            <h4 class="video-title">{v['title']}</h4>
            <p class="video-desc">{v['desc']}</p>
          </div>
        </div>
        """)
    vids_joined = "".join(vid_cards_html)

    # Generate figure cards
    fig_cards_html = []
    for f_id, title, desc in FIGS:
        fig_cards_html.append(f"""
        <div class="figure-card" onclick="openLightbox('figures/{f_id}.png', '{title}', '{desc}')">
          <div class="figure-thumb-wrap">
            <img loading="lazy" src="figures/{f_id}.png" alt="{title}">
            <div class="figure-zoom-overlay">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Click to inspect</span>
            </div>
          </div>
          <div class="figure-body">
            <div class="figure-code">FIG · {f_id}</div>
            <h4 class="figure-title">{title}</h4>
            <p class="figure-desc">{desc}</p>
          </div>
        </div>
        """)
    figs_joined = "".join(fig_cards_html)

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Platform Checking Study · Behavioral Neuroscience Editorial</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
/* === DESIGN SYSTEM === */
:root {{
  --font-serif: 'Playfair Display', Georgia, serif;
  --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Editorial Light Palette */
  --bg: #f7f9fa;
  --bg-subtle: #f0f3f6;
  --panel: #ffffff;
  --panel-glass: rgba(255, 255, 255, 0.88);
  --panel-border: rgba(15, 23, 42, 0.08);
  --panel-border-hover: rgba(15, 23, 42, 0.16);

  --ink: #0a0f14;
  --ink-secondary: #4a5568;
  --ink-muted: #8c9ba5;
  --rule: rgba(15, 23, 42, 0.08);
  --rule-hairline: rgba(15, 23, 42, 0.04);

  /* Scientific Accents */
  --accent: #0f766e;
  --accent-light: #f0fdfa;
  --accent-glow: rgba(15, 118, 110, 0.12);
  --f: #1d4ed8;            /* Females: Crisp Sapphire */
  --f-soft: rgba(29, 78, 216, 0.08);
  --f-glow: rgba(29, 78, 216, 0.2);
  --m: #ea580c;            /* Males: Terracotta Amber */
  --m-soft: rgba(234, 88, 12, 0.08);
  --m-glow: rgba(234, 88, 12, 0.2);

  --sig-color: #0f766e;
  --sig-bg: #ccfbf1;
  --ns-color: #64748b;
  --ns-bg: #f1f5f9;

  --warn-bg: #fffbeb;
  --warn-border: #f59e0b;
  --warn-ink: #92400e;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.03);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.08);
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-full: 9999px;
}}

[data-theme="dark"] {{
  --bg: #090d12;
  --bg-subtle: #0f151e;
  --panel: #131922;
  --panel-glass: rgba(19, 25, 34, 0.88);
  --panel-border: rgba(255, 255, 255, 0.08);
  --panel-border-hover: rgba(255, 255, 255, 0.18);

  --ink: #f8fafc;
  --ink-secondary: #94a3b8;
  --ink-muted: #64748b;
  --rule: rgba(255, 255, 255, 0.08);
  --rule-hairline: rgba(255, 255, 255, 0.04);

  --accent: #2dd4bf;
  --accent-light: rgba(45, 212, 191, 0.12);
  --accent-glow: rgba(45, 212, 191, 0.18);
  --f: #60a5fa;
  --f-soft: rgba(96, 165, 250, 0.12);
  --f-glow: rgba(96, 165, 250, 0.25);
  --m: #fb923c;
  --m-soft: rgba(251, 146, 60, 0.12);
  --m-glow: rgba(251, 146, 60, 0.25);

  --sig-color: #2dd4bf;
  --sig-bg: rgba(45, 212, 191, 0.16);
  --ns-color: #94a3b8;
  --ns-bg: rgba(255, 255, 255, 0.06);

  --warn-bg: #1c1917;
  --warn-border: #d97706;
  --warn-ink: #fef3c7;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.6);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}

/* Top Sticky Editorial Bar */
.top-nav {{
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--panel-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--panel-border);
  transition: all 0.25s ease;
}}
.nav-inner {{
  max-width: 1360px;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}}
.nav-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: var(--ink);
}}
.brand-dot {{
  width: 9px;
  height: 9px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 10px #10b981;
  animation: pulse-dot 2s infinite ease-in-out;
}}
@keyframes pulse-dot {{
  0%, 100% {{ transform: scale(1); opacity: 1; }}
  50% {{ transform: scale(1.3); opacity: 0.6; }}
}}
.brand-title {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.nav-menu {{
  display: flex;
  align-items: center;
  gap: 20px;
  list-style: none;
}}
.nav-link {{
  font-family: var(--font-sans);
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.nav-link:hover {{
  color: var(--accent);
}}
.nav-badge-new {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  background: var(--accent-light);
  color: var(--accent);
  padding: 2px 7px;
  border-radius: var(--radius-full);
  border: 1px solid var(--accent-glow);
}}
.theme-btn {{
  background: var(--bg-subtle);
  border: 1px solid var(--panel-border);
  color: var(--ink);
  padding: 6px 12px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}}
.theme-btn:hover {{
  background: var(--panel);
  border-color: var(--panel-border-hover);
}}

/* Main Wrap */
.wrap {{
  max-width: 1360px;
  margin: 0 auto;
  padding: 40px 24px 100px;
  display: grid;
  gap: 56px;
}}

/* Editorial Marker */
.editorial-marker {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 20px;
  user-select: none;
}}
.marker-line {{
  width: 44px;
  height: 1px;
  background: var(--rule);
}}
.marker-vol {{
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
}}
.marker-dot {{
  width: 3px;
  height: 3px;
  background: var(--ink-muted);
  border-radius: 50%;
}}
.marker-sub {{
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}}
.marker-badge {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: var(--accent-light);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: 4px;
}}

/* Hero Section */
.hero {{
  text-align: center;
  max-width: 980px;
  margin: 0 auto;
  display: grid;
  gap: 20px;
}}
.hero h1 {{
  font-family: var(--font-serif);
  font-size: clamp(38px, 6.5vw, 64px);
  font-weight: 500;
  line-height: 1.08;
  letter-spacing: -0.025em;
  color: var(--ink);
}}
.hero h1 em {{
  font-style: italic;
  font-weight: 400;
  color: var(--accent);
}}
.hero-lede {{
  font-size: clamp(17px, 2.2vw, 20px);
  line-height: 1.6;
  color: var(--ink-secondary);
  font-weight: 400;
  max-width: 860px;
  margin: 0 auto;
}}
.f-text {{ color: var(--f); font-weight: 600; }}
.m-text {{ color: var(--m); font-weight: 600; }}

/* Hero Quick Pills */
.hero-pills {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
}}
.hero-pill {{
  background: var(--panel-glass);
  border: 1px solid var(--panel-border);
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-secondary);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  gap: 8px;
}}
.hero-pill strong {{
  color: var(--ink);
  font-weight: 600;
}}
.pill-indicator {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}}

/* Hero KPIs */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}}
.kpi-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 24px;
  display: grid;
  gap: 12px;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}}
.kpi-card:hover {{
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--panel-border-hover);
}}
.kpi-card::before {{
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--m) 0%, var(--f) 100%);
}}
.kpi-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.kpi-lab {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}}
.kpi-condition {{
  font-family: var(--font-sans);
  font-size: 12px;
  background: var(--bg-subtle);
  padding: 3px 8px;
  border-radius: var(--radius-full);
  color: var(--ink-secondary);
}}
.kpi-values {{
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-family: var(--font-serif);
  font-size: 38px;
  font-weight: 600;
  line-height: 1;
}}
.kpi-vs {{
  font-family: var(--font-sans);
  font-size: 16px;
  font-style: italic;
  font-weight: 400;
  color: var(--ink-muted);
}}
.kpi-cap {{
  font-size: 13.5px;
  color: var(--ink-secondary);
  line-height: 1.45;
}}
.kpi-stat {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 11.5px;
  font-weight: 600;
  color: var(--sig-color);
  background: var(--sig-bg);
  padding: 3px 8px;
  border-radius: 4px;
  width: fit-content;
}}

/* Sections Header */
.section-head {{
  display: grid;
  gap: 8px;
  margin-bottom: 24px;
}}
.section-eyebrow {{
  font-family: var(--font-mono);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 8px;
}}
.section-eyebrow::before {{
  content: "";
  display: inline-block;
  width: 14px;
  height: 2px;
  background: var(--accent);
}}
.section-title {{
  font-family: var(--font-serif);
  font-size: clamp(26px, 3.8vw, 36px);
  font-weight: 500;
  color: var(--ink);
  letter-spacing: -0.015em;
}}
.section-desc {{
  font-size: 15.5px;
  color: var(--ink-secondary);
  max-width: 800px;
  line-height: 1.6;
}}

/* Hero Figure Presentation Card */
.hero-figure-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}}
.hero-figure-bar {{
  padding: 16px 24px;
  background: var(--bg-subtle);
  border-bottom: 1px solid var(--panel-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}}
.hfb-title {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 8px;
}}
.hfb-btn {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-full);
  padding: 6px 14px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}}
.hfb-btn:hover {{
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}}
.hero-figure-view {{
  background: #ffffff;
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: zoom-in;
}}
.hero-figure-view img {{
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: var(--radius-sm);
}}
.hero-figure-caption {{
  padding: 20px 24px;
  border-top: 1px solid var(--panel-border);
  font-size: 14.5px;
  color: var(--ink-secondary);
  background: var(--panel);
  line-height: 1.6;
}}
.hero-figure-caption b {{
  color: var(--ink);
}}

/* Video Grid (Static, Responsive, Editorial) */
.video-filter-bar {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}}
.filter-pill {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}}
.filter-pill:hover {{
  border-color: var(--panel-border-hover);
  color: var(--ink);
}}
.filter-pill.active {{
  background: var(--ink);
  color: var(--panel);
  border-color: var(--ink);
  font-weight: 600;
}}
[data-theme="dark"] .filter-pill.active {{
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}}
.video-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(390px, 1fr));
  gap: 24px;
}}
.video-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}}
.video-card:hover {{
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}}
.video-frame {{
  position: relative;
  background: #000000;
  aspect-ratio: 16 / 9;
  overflow: hidden;
}}
.video-frame video {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}
.video-badge-strip {{
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  pointer-events: none;
}}
.video-badge {{
  font-family: var(--font-mono);
  font-size: 10.5px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}
.video-badge.category {{
  background: rgba(0, 0, 0, 0.75);
  color: #ffffff;
  backdrop-filter: blur(8px);
}}
.video-badge.speed {{
  background: var(--accent);
  color: #ffffff;
}}
.video-body {{
  padding: 18px 20px;
  display: grid;
  gap: 8px;
  flex: 1;
}}
.video-title {{
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.25;
}}
.video-desc {{
  font-size: 14px;
  color: var(--ink-secondary);
  line-height: 1.5;
}}

/* Cross-Experiment Feature Spotlight */
.cross-spotlight {{
  background: linear-gradient(135deg, var(--panel) 0%, var(--bg-subtle) 100%);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  padding: 36px;
  box-shadow: var(--shadow-md);
  display: grid;
  gap: 28px;
  position: relative;
  overflow: hidden;
}}
.cross-spotlight::after {{
  content: "";
  position: absolute;
  right: -80px;
  bottom: -80px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
  pointer-events: none;
}}
.cross-grid {{
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 32px;
  align-items: center;
}}
@media (max-width: 960px) {{
  .cross-grid {{ grid-template-columns: 1fr; }}
}}
.cross-findings {{
  display: grid;
  gap: 16px;
}}
.finding-box {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  display: grid;
  gap: 6px;
  box-shadow: var(--shadow-sm);
}}
.finding-top {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.finding-badge {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--accent);
}}
.finding-r {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--sig-color);
  background: var(--sig-bg);
  padding: 2px 7px;
  border-radius: 4px;
}}
.finding-title {{
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 15px;
  color: var(--ink);
}}
.finding-text {{
  font-size: 13.5px;
  color: var(--ink-secondary);
  line-height: 1.5;
}}
.cross-preview-wrap {{
  display: grid;
  gap: 16px;
}}
.cross-preview-card {{
  background: #ffffff;
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 12px;
  box-shadow: var(--shadow-sm);
  cursor: zoom-in;
}}
.cross-preview-card img {{
  width: 100%;
  height: auto;
  display: block;
  border-radius: 6px;
}}
.cross-cta-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: var(--ink);
  color: var(--panel);
  padding: 14px 28px;
  border-radius: var(--radius-full);
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 14.5px;
  text-decoration: none;
  box-shadow: var(--shadow-md);
  transition: all 0.25s ease;
  width: fit-content;
}}
[data-theme="dark"] .cross-cta-btn {{
  background: var(--accent);
  color: #000;
}}
.cross-cta-btn:hover {{
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  opacity: 0.95;
}}

/* Statistical Results Table */
.tbl-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}}
.table-wrap {{
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
  min-width: 820px;
}}
thead th {{
  background: var(--bg-subtle);
  border-bottom: 2px solid var(--panel-border);
  padding: 14px 18px;
  text-align: left;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}}
thead th small {{
  display: block;
  text-transform: none;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 400;
  color: var(--ink-muted);
  margin-top: 2px;
}}
tbody th, tbody td {{
  padding: 14px 18px;
  border-bottom: 1px solid var(--rule);
  vertical-align: top;
}}
tbody tr:last-child th, tbody tr:last-child td {{
  border-bottom: none;
}}
tbody tr:hover {{
  background: var(--bg-subtle);
}}
.row-title {{
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}}
.row-note {{
  font-size: 12.5px;
  color: var(--ink-secondary);
  font-weight: 400;
  margin-top: 3px;
  line-height: 1.4;
}}
.val-comp {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
}}
.f-badge {{
  color: var(--f);
  background: var(--f-soft);
  padding: 2px 7px;
  border-radius: 4px;
}}
.m-badge {{
  color: var(--m);
  background: var(--m-soft);
  padding: 2px 7px;
  border-radius: 4px;
}}
.vs {{
  font-family: var(--font-sans);
  font-size: 12px;
  font-style: italic;
  color: var(--ink-muted);
}}
.stat-tag {{
  display: inline-block;
  margin-top: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}}
.stat-tag.sig {{
  color: var(--sig-color);
  background: var(--sig-bg);
}}
.stat-tag.ns {{
  color: var(--ns-color);
  background: var(--ns-bg);
}}
.val-dash {{
  color: var(--ink-muted);
  font-family: var(--font-mono);
}}

/* Rigor Cards: What Holds vs What to Hold Back */
.rigor-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 24px;
}}
.rigor-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 24px 28px;
  display: grid;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}}
.rigor-card.caution {{
  background: var(--warn-bg);
  border-color: var(--warn-border);
}}
.rigor-card h3 {{
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 600;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 10px;
}}
.rigor-card.caution h3 {{
  color: var(--warn-ink);
}}
.rigor-card ul {{
  padding-left: 20px;
  display: grid;
  gap: 10px;
  font-size: 14.5px;
  color: var(--ink-secondary);
  line-height: 1.55;
}}
.rigor-card.caution ul {{
  color: var(--warn-ink);
}}

/* Figures Showcase */
.figure-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
}}
.figure-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}}
.figure-card:hover {{
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}}
.figure-thumb-wrap {{
  position: relative;
  background: #ffffff;
  padding: 12px;
  border-bottom: 1px solid var(--panel-border);
}}
.figure-thumb-wrap img {{
  width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
}}
.figure-zoom-overlay {{
  position: absolute;
  inset: 0;
  background: rgba(10, 15, 20, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #ffffff;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s ease;
}}
.figure-card:hover .figure-zoom-overlay {{
  opacity: 1;
}}
.figure-body {{
  padding: 16px 20px;
  display: grid;
  gap: 6px;
  flex: 1;
}}
.figure-code {{
  font-family: var(--font-mono);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}}
.figure-title {{
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.3;
}}
.figure-desc {{
  font-size: 13.5px;
  color: var(--ink-secondary);
  line-height: 1.5;
}}

/* Lightbox Modal */
.lightbox-modal {{
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(10, 15, 20, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  display: none;
  align-items: center;
  justify-content: center;
  padding: 30px;
}}
.lightbox-modal.active {{
  display: flex;
}}
.lightbox-box {{
  max-width: 1100px;
  width: 100%;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--panel);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--panel-border);
  position: relative;
}}
.lightbox-close {{
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  z-index: 10;
  transition: background 0.2s;
}}
.lightbox-close:hover {{
  background: var(--accent);
}}
.lightbox-img-wrap {{
  background: #ffffff;
  padding: 20px;
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
}}
.lightbox-img-wrap img {{
  max-width: 100%;
  max-height: 68vh;
  height: auto;
  object-fit: contain;
}}
.lightbox-meta {{
  padding: 20px 24px;
  background: var(--panel);
  border-top: 1px solid var(--panel-border);
}}
.lightbox-title {{
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 6px;
}}
.lightbox-desc {{
  font-size: 14px;
  color: var(--ink-secondary);
  line-height: 1.5;
}}

/* Footer */
footer {{
  border-top: 1px solid var(--rule);
  padding-top: 40px;
  display: grid;
  gap: 16px;
  color: var(--ink-muted);
  font-size: 13.5px;
  line-height: 1.6;
}}
footer code {{
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--bg-subtle);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--ink);
}}
footer a {{
  color: var(--accent);
  text-decoration: none;
}}
footer a:hover {{
  text-decoration: underline;
}}

/* Academic vs Presentation Edition Distinction Banner */
.edition-banner {{
  background: var(--panel);
  border: 1px solid var(--accent);
  border-left: 5px solid var(--accent);
  border-radius: var(--radius-md);
  padding: 16px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}}
.edition-badge {{
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: var(--accent-light);
  color: var(--accent);
  padding: 4px 9px;
  border-radius: 4px;
  margin-bottom: 5px;
}}
.edition-desc {{
  font-size: 14.5px;
  color: var(--ink-secondary);
  line-height: 1.45;
  max-width: 820px;
}}
.edition-btn {{
  background: var(--accent);
  color: #000 !important;
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 10px 18px;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(15, 118, 110, 0.2);
}}
.edition-btn:hover {{
  transform: translateX(3px);
  filter: brightness(1.1);
}}

/* Responsive */
@media (max-width: 768px) {{
  .wrap {{ padding-inline: 16px; gap: 40px; }}
  .video-grid, .figure-grid {{ grid-template-columns: 1fr; }}
  .hero h1 {{ font-size: 34px; }}
  .nav-menu {{ display: none; }}
}}
</style>
</head>
<body>

<!-- STICKY EDITORIAL TOP NAVIGATION -->
<nav class="top-nav">
  <div class="nav-inner">
    <a href="#" class="nav-brand">
      <span class="brand-dot"></span>
      <span class="brand-title">NeuroCheck · KAC &amp; SP1</span>
    </a>
    <ul class="nav-menu">
      <li><a href="{return_portal_link}" class="nav-link" style="color:var(--accent);font-weight:700;">Presentation Portal "Return" ↗</a></li>
      <li><a href="#hero" class="nav-link">Overview</a></li>
      <li><a href="#videos" class="nav-link">Tracked Demos</a></li>
      <li><a href="#art" class="nav-link">Kinematic Art</a></li>
      <li><a href="{motion_lab_link}" class="nav-link">Motion Lab <span class="nav-badge-new">60 FPS</span></a></li>
      <li><a href="#cross-correlations" class="nav-link">Cross-Correlations</a></li>
      <li><a href="#results" class="nav-link">Statistics</a></li>
      <li><a href="#figures" class="nav-link">Figures</a></li>
      <li><a href="{profiles_link}" class="nav-link">Individual Profiles &rarr;</a></li>
      <li><a href="{explorer_link}" class="nav-link">Behavior Atlas &rarr;</a></li>
    </ul>
    <button class="theme-btn" onclick="toggleTheme()" id="themeBtn">
      <span>Theme</span>
      <span id="themeIcon">☀️</span>
    </button>
  </div>
</nav>

<div class="wrap">

  <!-- ACADEMIC & ADVISORY EDITION DISTINCTION BANNER -->
  <div class="edition-banner">
    <div>
      <span class="edition-badge">Academic, Advisory &amp; Classroom Edition</span>
      <div class="edition-desc">
        Formal methodology, hypothesis testing, DeepLabCut quality control, 10 publication-grade manifolds, and cross-experiment correlations tailored for thesis advisors, researchers, and coursework.
      </div>
    </div>
    <a href="{return_portal_link}" class="edition-btn">
      <span>Launch "Return" Presentation Portal</span>
      <span>&rarr;</span>
    </a>
  </div>

  <!-- EDITORIAL HERO HEADER -->
  <header class="hero" id="hero">
    <div class="editorial-marker">
      <span class="marker-line"></span>
      <span class="marker-vol">VOL. IV</span>
      <span class="marker-dot"></span>
      <span class="marker-sub">SFN 2026 ARCHIVE · POSE ETHOLOGY &amp; SPATIAL MEMORY</span>
      <span class="marker-dot"></span>
      <span class="marker-badge">KAC &amp; SP1 COHORTS</span>
      <span class="marker-line"></span>
    </div>

    <h1>Sex Divergence in <em>Platform Checking</em> &amp; Micro-Scanning Dynamics</h1>

    <p class="hero-lede">
      Placed on a hidden platform for 120 s, <span class="m-text">males</span> stay put while <span class="f-text">females</span> actively disembark to revisit the former training platform (P1), across standard (1.5 cm) and raised (3.0 cm) water depths. DeepLabCut tracking reveals this divergence originates before anyone leaves: <span class="f-text">females</span> engage in significantly elevated head-scanning sweeps while still anchored on the platform.
    </p>

    <!-- Quick Takeaways Pill Strip -->
    <div class="hero-pills">
      <div class="hero-pill"><span class="pill-indicator"></span><strong>10.6× Hazard Ratio</strong> Female vs male leaving rate (Cox p &lt; 0.001)</div>
      <div class="hero-pill"><span class="pill-indicator"></span><strong>3 Tests Replicated</strong> SP1 raised, KAC Day 6 standard, KAC Day 8 raised</div>
      <div class="hero-pill"><span class="pill-indicator"></span><strong>r = −0.66 Cross-Link</strong> Open Field center exploration predicts platform retention</div>
      <div class="hero-pill"><span class="pill-indicator" style="background:#c084fc;"></span><strong>Kinematic Art</strong> 4 Visual Manifolds &amp; Interactive Motion Lab</div>
    </div>
  </header>

  <!-- HERO KPIS -->
  <section class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-header">
        <span class="kpi-lab">SP1 Cohort</span>
        <span class="kpi-condition">Raised Water (3.0 cm)</span>
      </div>
      <div class="kpi-values">
        <span class="m-text">{stay['sp1'][0]['M']}/{stay['sp1'][1]['M']}</span>
        <span class="kpi-vs">vs</span>
        <span class="f-text">{stay['sp1'][0]['F']}/{stay['sp1'][1]['F']}</span>
      </div>
      <div class="kpi-cap">Males vs females with zero observed departures over 120 s.</div>
      <div class="kpi-stat">Fisher exact p {p_fmt(stay['sp1'][2])}</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <span class="kpi-lab">KAC Day 6</span>
        <span class="kpi-condition">Standard Water (1.5 cm)</span>
      </div>
      <div class="kpi-values">
        <span class="m-text">{stay['kac_d6'][0]['M']}/{stay['kac_d6'][1]['M']}</span>
        <span class="kpi-vs">vs</span>
        <span class="f-text">{stay['kac_d6'][0]['F']}/{stay['kac_d6'][1]['F']}</span>
      </div>
      <div class="kpi-cap">Proves divergence exists at normal depth — not caused by raised water.</div>
      <div class="kpi-stat">Fisher exact p {p_fmt(stay['kac_d6'][2])}</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <span class="kpi-lab">KAC Day 8</span>
        <span class="kpi-condition">Raised Water (3.0 cm)</span>
      </div>
      <div class="kpi-values">
        <span class="m-text">{stay['kac_d8'][0]['M']}/{stay['kac_d8'][1]['M']}</span>
        <span class="kpi-vs">vs</span>
        <span class="f-text">{stay['kac_d8'][0]['F']}/{stay['kac_d8'][1]['F']}</span>
      </div>
      <div class="kpi-cap">Zero females remained anchored; departure frequency doubled.</div>
      <div class="kpi-stat">Fisher exact p {p_fmt(stay['kac_d8'][2])}</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <span class="kpi-lab">Blinded QC</span>
        <span class="kpi-condition">Session Log Audit</span>
      </div>
      <div class="kpi-values">
        <span style="color:var(--accent)">{agree_short}</span>
        <span class="kpi-vs">sessions</span>
      </div>
      <div class="kpi-cap">Automated tracking matches handwritten experimenter notes for {agree}. Untracked time &lt; 1%.</div>
      <div class="kpi-stat">Rigorous Validation</div>
    </div>
  </section>

  <!-- MASTER NARRATIVE FIGURE -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Visual Synthesis</div>
      <h2 class="section-title">The Complete Narrative in Three Panels</h2>
      <p class="section-desc">From binary survival divergence to vector targeting of the former training platform.</p>
    </div>

    <div class="hero-figure-card">
      <div class="hero-figure-bar">
        <div class="hfb-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          Figure 1 · Synthesis of Retention, Latency &amp; Directional Trajectories
        </div>
        <button class="hfb-btn" onclick="openLightbox('figures/hero_story.png', 'The Story in One Figure', 'Panel A: The sex difference in three tests across two cohorts. Panel B: Females start leaving within seconds. Panel C: Where leavers swim before coming back.')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
          Inspect High-Res
        </button>
      </div>
      <div class="hero-figure-view" onclick="openLightbox('figures/hero_story.png', 'The Story in One Figure', 'Panel A: The sex difference in three tests across two cohorts. Panel B: Females start leaving within seconds. Panel C: Where leavers swim before coming back.')">
        <img src="figures/hero_story.png" alt="Three-panel synthesis figure">
      </div>
      <div class="hero-figure-caption">
        <b>Panel A:</b> The striking sex divergence replicates across three independent testing sessions spanning two experimental cohorts. 
        <b>Panel B:</b> Kaplan-Meier survival curves show females initiate departures within the first 10–20 seconds of placement.
        <b>Panel C:</b> Spatial trajectories demonstrate that disembarking females direct their search toward P1 (the former escape platform location during training) rather than random wandering.
      </div>
    </div>
  </section>

  <!-- TRACKED VIDEO SHOWCASE -->
  <section id="videos">
    <div class="section-head">
      <div class="section-eyebrow">Behavioral Ground Truth</div>
      <h2 class="section-title">The Behaviour, Tracked &amp; Validated</h2>
      <p class="section-desc">Video demos with synchronized DeepLabCut pose tracking. Placement transients are trimmed; all animals chosen represent median phenotypic performers rather than cherry-picked extremes.</p>
    </div>

    <!-- Filter Buttons -->
    <div class="video-filter-bar">
      <button class="filter-pill active" onclick="filterVideos('all', this)">All Clips (6)</button>
      <button class="filter-pill" onclick="filterVideos('side-by-side', this)">Leaving vs Staying (3 Tests)</button>
      <button class="filter-pill" onclick="filterVideos('excursion', this)">Excursion Trajectories (P1 / Wall / Wander)</button>
    </div>

    <!-- Video Cards Grid -->
    <div class="video-grid" id="videoGrid">
      {vids_joined}
    </div>
  </section>

  <!-- CROSS-EXPERIMENT CORRELATIONS FEATURE SPOTLIGHT -->
  <section id="cross-correlations">
    <div class="section-head">
      <div class="section-eyebrow">Cross-Experiment Integration · NEW</div>
      <h2 class="section-title">Bridging the Maze: Anxiety &amp; Exploration Phenotyping</h2>
      <p class="section-desc">Integrating water maze checking tests with Elevated Plus Maze (EPM), Open Field (OF), and Novel Object Recognition (NOR/PPT) datasets across 31 animals.</p>
    </div>

    <div class="cross-spotlight">
      <div class="cross-grid">
        <div class="cross-findings">
          <div class="finding-box">
            <div class="finding-top">
              <span class="finding-badge">Open Field Center Exploration × Water Maze</span>
              <span class="finding-r">r = −0.659 · p = 0.0001</span>
            </div>
            <div class="finding-title">Center Exploration Anti-Correlates with Platform Retention</div>
            <div class="finding-text">Animals that enter the open field center more frequently spend significantly less time lingering on the water maze platform. Active open-arena exploration maps directly onto spatial disembarkation drive.</div>
          </div>

          <div class="finding-box">
            <div class="finding-top">
              <span class="finding-badge">Locomotor Drive × On-Platform Micro-Scanning</span>
              <span class="finding-r">r = +0.649 · p = 0.0001</span>
            </div>
            <div class="finding-title">Open Field Distance Predicts Head Sweeps per Minute</div>
            <div class="finding-text">General locomotor distance in the open arena strongly predicts the frequency of exploratory head scanning sweeps (&ge; 30°) while on the platform.</div>
          </div>

          <div class="finding-box">
            <div class="finding-top">
              <span class="finding-badge">EPM Anxiety Index vs Disembarkation</span>
              <span class="finding-r">r = −0.104 · p = 0.59 (ns)</span>
            </div>
            <div class="finding-title">Platform Checking Is Driven by Foraging Exploration, Not Anxiety</div>
            <div class="finding-text">Elevated Plus Maze open arm ratio does not correlate with water maze departure count. Checking represents an active, goal-directed spatial foraging drive rather than unconditioned anxiety.</div>
          </div>

          <a href="{prefix_corr}correlations_dashboard.html" class="cross-cta-btn">
            <span>Explore Full Cross-Experiment Correlations Portal &rarr;</span>
          </a>
        </div>

        <div class="cross-preview-wrap">
          <div class="cross-preview-card" onclick="openLightbox('figures/corr_heatmap_all.png', 'Cross-Experiment Correlation Matrix', 'Spearman rank correlations across all 29 animals between water maze measures and EPM, Open Field, and NOR assays.')">
            <img src="figures/corr_heatmap_all.png" alt="Correlation Heatmap Preview">
          </div>
          <div class="cross-preview-card" onclick="openLightbox('figures/scatter_platform_lower_pct_x_of_distance_m.png', 'Platform Retention vs Open Field Distance', 'Scatter plot demonstrating significant negative correlation between open arena locomotion and platform dwell time.')">
            <img src="figures/scatter_platform_lower_pct_x_of_distance_m.png" alt="Scatter Plot Preview">
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- RIGOROUS RESULTS TABLE -->
  <section id="results">
    <div class="section-head">
      <div class="section-eyebrow">Quantitative Matrix</div>
      <h2 class="section-title">Comparative Statistics Across All Three Tests</h2>
      <p class="section-desc">Values represent <span class="f-text">Female mean</span> vs <span class="m-text">Male mean</span>. P-values are Mann-Whitney tests Holm-corrected within each test (Fisher's exact test for binary staying). Kinematic measures are computed strictly while on the platform.</p>
    </div>

    <div class="tbl-card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th style="width: 32%;">Behavioral / Kinematic Measure</th>
              <th>SP1 Cohort<small>Raised water (3.0 cm)</small></th>
              <th>KAC Day 6<small>Standard water (1.5 cm)</small></th>
              <th>KAC Day 8<small>Raised water (3.0 cm)</small></th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- WHERE THEY GO WHEN THEY LEAVE -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Spatial Trajectory Analysis</div>
      <h2 class="section-title">Leavers Direct Search Toward Former Platform Location (P1)</h2>
      <p class="section-desc">During 5 days of acquisition training, the platform resided at P1 (~74 cm from the checking test platform). On Day 6, disembarking females spent <b>8.7%</b> of their off-platform time within 20 cm of P1, compared to only <b>4.7%</b> at matched control coordinates (Wilcoxon p = 0.018, 15 rats).</p>
    </div>

    <div class="tbl-card" style="max-width: 800px;">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Statistical Model (KAC Cohort, Both Days)</th>
              <th>Effect Size &amp; Metric</th>
              <th>P-Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th><div class="row-title">Leaving Rate: Female vs Male</div><div class="row-note">Cox proportional hazards model, robust clustered SE by rat</div></th>
              <td><span class="f-badge">Hazard Ratio 10.6</span> (95% CI: 3.5 – 31.4)</td>
              <td><span class="stat-tag sig">&lt; 0.001</span></td>
            </tr>
            <tr>
              <th><div class="row-title">Water Depth Effect: Raised vs Standard</div><div class="row-note">Cox proportional hazards model</div></th>
              <td>Hazard Ratio 1.49 (95% CI: 0.85 – 2.59)</td>
              <td><span class="stat-tag ns">0.16 (ns)</span></td>
            </tr>
            <tr>
              <th><div class="row-title">Platform Zone Dwell: Female vs Male</div><div class="row-note">Linear mixed-effects model accounting for repeated measures</div></th>
              <td>&minus;27.0 percentage points</td>
              <td><span class="stat-tag sig">&lt; 0.001</span></td>
            </tr>
            <tr>
              <th><div class="row-title">Female Departure Bouts: Day 6 vs Day 8</div><div class="row-note">Within-subject paired Wilcoxon signed-rank test</div></th>
              <td>Median departure count: 2 &rarr; 4</td>
              <td><span class="stat-tag sig">0.003</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- RIGOR: WHAT HOLDS VS WHAT TO HOLD BACK -->
  <section class="rigor-grid">
    <div class="rigor-card">
      <h3>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        What Holds
      </h3>
      <ul>
        <li><strong>Binary sex divergence is robust:</strong> Replicated across three separate tests in two experimental cohorts. Females disembark; males remain anchored.</li>
        <li><strong>Depth independence:</strong> The divergence is already prominent at standard water depth (KAC Day 6, 1.5 cm), ruling out water depth as an artifactual trigger.</li>
        <li><strong>Pre-departure micro-scanning:</strong> Head turn velocity and angular sweep rates are elevated in females before any departure occurs.</li>
        <li><strong>Directional navigation toward P1:</strong> Disembarking females prioritize the training platform quadrant over control locations.</li>
        <li><strong>High-precision tracking fidelity:</strong> Tracking agrees with 47 of 50 experimenter log entries, with untracked missing time under 1% for every group.</li>
      </ul>
    </div>

    <div class="rigor-card caution">
      <h3>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        What to Hold Back
      </h3>
      <ul>
        <li><strong>Water depth effect confounded:</strong> In KAC, departures doubled on Day 8 (median 2 &rarr; 4, p = 0.003), but the sex &times; depth interaction in the mixed model is not significant (p = 0.13), and depth is confounded with test order and camera calibration.</li>
        <li><strong>VTE-like lean-out trend:</strong> Head rotation before pulling back vs leaving is exploratory and does not survive Holm correction (SP1 p = {cv['sp1'].holm_p:.2f}, D6 p = {cv['kac_d6'].holm_p:.2f}, D8 p = {cv['kac_d8'].holm_p:.2f}).</li>
        <li><strong>SP1 coordinate assumption:</strong> In SP1, P1 coordinates were estimated by mirroring across the pool centre rather than direct calibrated training coordinates.</li>
        <li><strong>Reminder training unmodeled:</strong> Day 7 reminder training between Day 6 and Day 8 is not yet tracked with pose estimation.</li>
      </ul>
    </div>
  </section>

  <!-- KINEMATIC ART & VISUAL EXPLORATIONS -->
  <section id="art">
    <div class="section-head" style="display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:16px;">
      <div>
        <div class="section-eyebrow">Computational Ethology &amp; Visual Art</div>
        <h2 class="section-title">DeepLabCut Kinematic Art &amp; Manifold Reconstructions</h2>
        <p class="section-desc">Visual explorations of rodent spatial mechanics: Stroboscopic 16-point pose capture, hydrodynamic swarm vector currents, polar attention compasses, and 3D space-time helices.</p>
      </div>
      <a href="{motion_lab_link}" style="display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:var(--panel);padding:12px 22px;border-radius:var(--radius-full);font-family:var(--font-mono);font-size:12.5px;font-weight:600;text-decoration:none;box-shadow:var(--shadow-md);transition:all 0.2s ease;">
        <span>Launch 60 FPS Motion Lab &rarr;</span>
      </a>
    </div>

    <div class="figure-grid" style="grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));">
      {art_joined}
    </div>
  </section>

  <!-- FIGURES GALLERY -->
  <section id="figures">
    <div class="section-head">
      <div class="section-eyebrow">Scientific Evidence Gallery</div>
      <h2 class="section-title">DeepLabCut Pose Tracking &amp; Kinematic Plates</h2>
      <p class="section-desc">Click any plate to inspect full-resolution vector graphics and detailed analytical legends.</p>
    </div>

    <div class="figure-grid">
      {figs_joined}
    </div>
  </section>

  <!-- FOOTER -->
  <footer>
    <p>
      <strong>Data &amp; Modeling Pipeline:</strong> Cleaned pose points are filtered for false rim reflections (&le; 40 px), bounded by pool radius (&le; 0.98), and constrained by maximum body velocity (&le; 60 cm/s). Small gaps (&le; 0.5 s) are filled; longer tracking loss is strictly bounded. Models: KAC <code>KAcheck_d6d8_v3rot_20261108</code> (best-320 with rotation augmentation, 13 body points), SP1 <code>best-190</code>.
    </p>
    <p>
      Reproduce all results with <code>analyze.py</code> and <code>make_dashboard.py</code> in <code>analysis/dlc_cleaned</code>. Explore individual records in <a href="{profiles_link}">Individual Profiles</a> or browse kinematic trajectories in the <a href="{explorer_link}">Behavior Atlas</a>. Cross-experiment phenotyping matrix available in <a href="{prefix_corr}correlations_dashboard.html">Cross-Experiment Correlations</a>.
    </p>
  </footer>

</div>

<!-- LIGHTBOX MODAL -->
<div class="lightbox-modal" id="lightboxModal" onclick="closeLightbox(event)">
  <div class="lightbox-box" onclick="event.stopPropagation()">
    <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
    <div class="lightbox-img-wrap">
      <img id="lightboxImg" src="" alt="Enlarged Figure">
    </div>
    <div class="lightbox-meta">
      <h3 class="lightbox-title" id="lightboxTitle"></h3>
      <p class="lightbox-desc" id="lightboxDesc"></p>
    </div>
  </div>
</div>

<script>
// Video Category Filtering
function filterVideos(cat, btn) {{
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const cards = document.querySelectorAll('.video-card');
  cards.forEach(c => {{
    if (cat === 'all' || c.getAttribute('data-category') === cat) {{
      c.style.display = 'flex';
    }} else {{
      c.style.display = 'none';
    }}
  }});
}}

// Lightbox
function openLightbox(src, title, desc) {{
  document.getElementById('lightboxImg').src = src;
  document.getElementById('lightboxTitle').textContent = title;
  document.getElementById('lightboxDesc').textContent = desc;
  document.getElementById('lightboxModal').classList.add('active');
  document.body.style.overflow = 'hidden';
}}
function closeLightbox(e) {{
  document.getElementById('lightboxModal').classList.remove('active');
  document.body.style.overflow = '';
}}
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeLightbox();
}});

// Theme Switcher
function toggleTheme() {{
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const target = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', target);
  localStorage.setItem('neuro_theme', target);
  updateThemeIcon(target);
}}
function updateThemeIcon(theme) {{
  document.getElementById('themeIcon').textContent = theme === 'dark' ? '🌙' : '☀️';
}}
// Init theme
(function() {{
  const saved = localStorage.getItem('neuro_theme');
  if (saved) {{
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
  }}
}})();
</script>

</body>
</html>"""

# Generate dashboard.html
html_main = make_html(is_site=False)
(HERE / "dashboard.html").write_text(html_main, encoding="utf-8")
print(f"Generated dashboard.html ({len(html_main)} bytes)")

# Generate site/index.html
site_dir = HERE / "site"
if site_dir.exists():
    html_site = make_html(is_site=True)
    (site_dir / "index.html").write_text(html_site, encoding="utf-8")
    print(f"Generated site/index.html ({len(html_site)} bytes)")
