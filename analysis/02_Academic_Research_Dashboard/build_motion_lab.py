"""Generates dlc_motion_lab.html with all 10 grand art plates, 3D WebGL Space-Time Manifold,
live posture phase space canvas (PC1 vs PC2), multi-rat swarm simulation, dual ghost mode,
live posture curvature oscilloscope, and interactive audio sonification.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

def generate_motion_lab_html(is_site=False):
    prefix_back = "dashboard.html" if not is_site else "index.html"
    profiles_link = "site/profiles.html" if not is_site else "profiles.html"
    explorer_link = "site/explorer.html" if not is_site else "explorer.html"
    corr_link = "../correlations/correlations_dashboard.html" if not is_site else "../../correlations/correlations_dashboard.html"
    return_portal_link = "../../portal/site/portal.html" if is_site else "../portal/site/portal.html"
    json_path = "dlc_motion_data.json"
    json_payload = (HERE / "dlc_motion_data.json").read_text(encoding="utf-8")

    # All 10 Grand Art Plates
    art_plates = [
        ("art_chrono_skeleton", "PLATE 01 · STROBOSCOPIC POSE RECONSTRUCTION", "Kinetic Chrono-Strobe: 16-Point Pose Ribbon",
         "Harold Edgerton stroboscopic aesthetic meets AI pose estimation. Follows Rat 28 (Female) disembarking at 56s, surging at 32 cm/s directly along the bearing to P1 (closest approach 6.8 cm), looping, and climbing back onto the platform."),
        ("art_posture_kymograph", "PLATE 02 · POSTURE CURVATURE KYMOGRAPH", "Spatiotemporal Body Curvature & Traveling Waves",
         "Kymograph of instantaneous curvature κ across 5 body joints from snout to tail. Contrasts on-platform scanning (cranial oscillations while trunk remains rigid) against swimming (2.5 Hz retrograde traveling undulation waves)."),
        ("art_gaze_compass", "PLATE 03 · POLAR GAZE RADAR & OSCILLOGRAM", "The Compass of Attention: Directional Tuning to P1",
         "Polar radar distribution of on-platform head orientation relative to P1 (0° = pointing straight at P1). Females display a sharp, focused lobe oriented toward the training platform prior to disembarking."),
        ("art_spacetime_helix", "PLATE 04 · 3D SPACE-TIME MANIFOLD", "Spatiotemporal Helix Manifold: Male Pillar vs Female Corkscrew",
         "Isometric 3D space-time manifold (Pool X, Y on floor, Time 0 to 120s vertical). Male paths remain wound tightly inside the platform cylinder. Female paths burst out into sweeping corkscrews orbiting P1."),
        ("art_swarm_ghosts", "PLATE 05 · COLLECTIVE TRAJECTORY FILAMENTS", "Fiber-Optic Superhighways: All 16 Females vs All 13 Males",
         "Every single individual rat's path superimposed in semi-transparent fiber-optic filaments. Females concentrate into a dense superhighway funneling straight through P1; males form a tight, static retention core on the platform."),
        ("art_swarm_streamplot", "PLATE 06 · MACROSCOPIC SWARM CURRENTS", "Streamline Vector Fields: Female Vortex vs Male Quiescence",
         "2D velocity vector fields interpolated across 100,000+ frames demonstrate macroscopic spatial organization: A prominent vector conduit connects the checking platform to the learned platform quadrant."),
        ("art_vorticity_landscape", "PLATE 07 · HYDRODYNAMIC VORTICITY", "Topological Vorticity & Rotational Circulation Dipole",
         "Curl of the female velocity field (∇ × v). Reveals counter-rotating dipolar circulation: an exit vortex steering out to P1 and a return vortex sweeping the outer pool perimeter back to the platform."),
        ("art_compass_fingerprints", "PLATE 08 · POPULATION FINGERPRINTS", "29 Individual Attention Compass Roses (KAC Day 6)",
         "Polar directional radar for all 29 individual rats. Highlights the individual animal reproducibility: almost every female displays an elongated directional petal pointing toward P1, while males are isotropic."),
        ("art_eigenpostures", "PLATE 09 · POSTURE MANIFOLD & EIGEN-DEFORMATION MODES", "97,915-Frame Egocentric Skeletal Decomposition",
         "Decomposition of egocentric 13-point pose vectors reveals a low-dimensional postural space with two discrete dynamical attractors: rigid on-platform scanning vs resonant swimming undulation."),
        ("art_wavelet_sonogram", "PLATE 10 · TIME-FREQUENCY MORLET WAVELET ETHOGRAM", "Continuous Wavelet Spectrogram: 2.5 Hz Propulsion vs 0.8 Hz Scanning",
         "Continuous complex Morlet wavelets reveal the exact temporal architecture of behavioral transitions: sudden bursts of 2.5 Hz resonant undulation during swimming vs stationary low-frequency cranial oscillations.")
    ]

    art_cards_html = []
    for f_id, tag, title, desc in art_plates:
        art_cards_html.append(f"""
        <div class="art-card" onclick="openLightbox('figures/{f_id}.png', '{title}', '{desc}')">
          <div class="art-thumb-wrap">
            <img src="figures/{f_id}.png" alt="{title}" loading="lazy">
            <div class="art-zoom-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              Inspect High-Res
            </div>
          </div>
          <div class="art-body">
            <div class="art-tag">{tag}</div>
            <h3 class="art-title">{title}</h3>
            <p class="art-desc">{desc}</p>
          </div>
        </div>
        """)
    art_joined = "".join(art_cards_html)

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>The DeepLabCut Motion Lab · Interactive Pose Dynamics &amp; Kinematic Art</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<!-- Three.js & OrbitControls: Local bundle with CDN fallback -->
<script src="js/three.min.js"></script>
<script src="js/OrbitControls.js"></script>
<script>
if (typeof THREE === 'undefined') {{
  const s1 = document.createElement('script');
  s1.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  document.head.appendChild(s1);
  const s2 = document.createElement('script');
  s2.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';
  document.head.appendChild(s2);
}}
</script>

<style>
:root {{
  --font-serif: 'Playfair Display', Georgia, serif;
  --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Obsidian Dark (Default for Visual Motion Lab) */
  --bg: #070a0f;
  --bg-subtle: #0d121a;
  --panel: #111722;
  --panel-glass: rgba(17, 23, 34, 0.88);
  --panel-border: rgba(255, 255, 255, 0.08);
  --panel-border-hover: rgba(255, 255, 255, 0.2);

  --ink: #f8fafc;
  --ink-secondary: #94a3b8;
  --ink-muted: #64748b;
  --rule: rgba(255, 255, 255, 0.08);

  --accent: #2dd4bf;
  --accent-light: rgba(45, 212, 191, 0.12);
  --accent-glow: rgba(45, 212, 191, 0.25);
  --f: #60a5fa;
  --f-soft: rgba(96, 165, 250, 0.12);
  --m: #fb923c;
  --m-soft: rgba(251, 146, 60, 0.12);
  --p1-color: #c084fc;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.7);

  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-full: 9999px;
}}

[data-theme="light"] {{
  --bg: #f8fafc;
  --bg-subtle: #f0f3f6;
  --panel: #ffffff;
  --panel-glass: rgba(255, 255, 255, 0.88);
  --panel-border: rgba(15, 23, 42, 0.08);
  --panel-border-hover: rgba(15, 23, 42, 0.18);

  --ink: #0a0f14;
  --ink-secondary: #4a5568;
  --ink-muted: #8c9ba5;
  --rule: rgba(15, 23, 42, 0.08);

  --accent: #0f766e;
  --accent-light: #f0fdfa;
  --accent-glow: rgba(15, 118, 110, 0.15);
  --f: #1d4ed8;
  --f-soft: rgba(29, 78, 216, 0.08);
  --m: #ea580c;
  --m-soft: rgba(234, 88, 12, 0.08);
  --p1-color: #7e22ce;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.1);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

/* Top Sticky Editorial Nav */
.top-nav {{
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--panel-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--panel-border);
}}
.nav-inner {{
  max-width: 1400px;
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
  gap: 10px;
  text-decoration: none;
  color: var(--ink);
}}
.brand-dot {{
  width: 9px;
  height: 9px;
  background: var(--accent);
  border-radius: 50%;
  box-shadow: 0 0 12px var(--accent);
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
}}
.nav-link:hover {{
  color: var(--accent);
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
}}

/* Wrap */
.wrap {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 24px 100px;
  display: grid;
  gap: 64px;
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
.marker-line {{ width: 44px; height: 1px; background: var(--rule); }}
.marker-vol {{ font-family: var(--font-serif); font-style: italic; font-size: 13px; font-weight: 500; color: var(--ink); }}
.marker-dot {{ width: 3px; height: 3px; background: var(--ink-muted); border-radius: 50%; }}
.marker-sub {{ font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--ink-secondary); }}
.marker-badge {{
  font-family: var(--font-mono); font-size: 10px; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; background: var(--accent-light); color: var(--accent); padding: 2px 8px; border-radius: 4px;
}}

/* Header */
.hero {{
  text-align: center;
  max-width: 1040px;
  margin: 0 auto;
  display: grid;
  gap: 18px;
}}
.hero h1 {{
  font-family: var(--font-serif);
  font-size: clamp(34px, 5.5vw, 56px);
  font-weight: 500;
  line-height: 1.1;
  letter-spacing: -0.02em;
}}
.hero h1 em {{
  font-style: italic;
  color: var(--accent);
}}
.hero-lede {{
  font-size: clamp(16px, 2vw, 19px);
  color: var(--ink-secondary);
  line-height: 1.6;
}}

/* Section Titles */
.section-head {{
  margin-bottom: 28px;
  display: grid;
  gap: 6px;
}}
.section-eyebrow {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
}}
.section-title {{
  font-family: var(--font-serif);
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--ink);
}}
.section-desc {{
  font-size: 15px;
  color: var(--ink-secondary);
  max-width: 820px;
}}

/* ART GALLERY GRID (10 Plates) */
.art-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 28px;
}}
@media (max-width: 980px) {{
  .art-grid {{ grid-template-columns: 1fr; }}
}}
.art-card {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  cursor: pointer;
}}
.art-card:hover {{
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--panel-border-hover);
}}
.art-thumb-wrap {{
  position: relative;
  background: #090d14;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.art-thumb-wrap img {{
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.3s ease;
}}
.art-card:hover .art-thumb-wrap img {{
  transform: scale(1.02);
}}
.art-zoom-badge {{
  position: absolute;
  top: 14px;
  right: 14px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 6px 12px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.art-card:hover .art-zoom-badge {{
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}}
.art-body {{
  padding: 22px 26px;
  display: grid;
  gap: 8px;
  flex: 1;
}}
.art-tag {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}}
.art-title {{
  font-family: var(--font-serif);
  font-size: 21px;
  font-weight: 600;
  color: var(--ink);
}}
.art-desc {{
  font-size: 14px;
  color: var(--ink-secondary);
  line-height: 1.55;
}}

/* INTERACTIVE MOTION LAB PLAYER */
.lab-container {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: var(--shadow-lg);
  display: grid;
  gap: 28px;
}}
.lab-topbar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 20px;
}}
.rat-select-wrap {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}}
.rat-select-label {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}}
.rat-pill {{
  background: var(--bg-subtle);
  border: 1px solid var(--panel-border);
  color: var(--ink);
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-family: var(--font-sans);
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}}
.rat-pill:hover {{
  border-color: var(--panel-border-hover);
}}
.rat-pill.active {{
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}}
.view-switch-bar {{
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-subtle);
  padding: 4px;
  border-radius: var(--radius-full);
  border: 1px solid var(--panel-border);
}}
.view-tab {{
  background: transparent;
  border: none;
  color: var(--ink-secondary);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}}
.view-tab.active {{
  background: var(--panel);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--panel-border);
}}

.rat-story-banner {{
  font-size: 14px;
  color: var(--ink-secondary);
  background: var(--bg-subtle);
  padding: 12px 18px;
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}}

/* Player Stage */
.lab-stage {{
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 28px;
  align-items: start;
}}
@media (max-width: 1080px) {{
  .lab-stage {{ grid-template-columns: 1fr; }}
}}
.canvas-wrap {{
  background: #090d14;
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  position: relative;
  aspect-ratio: 1 / 1;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
  box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.8);
}}
#motionCanvas {{
  width: 100%;
  height: 100%;
  display: block;
}}
#webglContainer {{
  width: 100%;
  height: 100%;
  display: none;
  position: absolute;
  inset: 0;
}}
.canvas-overlay-tip {{
  position: absolute;
  bottom: 12px;
  left: 14px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  pointer-events: none;
}}

/* Live Telemetry Sidebar */
.telemetry-sidebar {{
  display: grid;
  gap: 14px;
}}
.telemetry-card {{
  background: var(--bg-subtle);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 16px 18px;
  display: grid;
  gap: 6px;
}}
.tel-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.tel-lab {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}}
.tel-val {{
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
  color: var(--ink);
}}
.tel-sub {{
  font-size: 12px;
  color: var(--ink-muted);
}}
.status-pill {{
  display: inline-block;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  background: var(--accent-light);
  color: var(--accent);
}}

/* Oscilloscope & Phase Boxes */
.oscilloscope-box {{
  background: var(--bg-subtle);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  display: grid;
  gap: 8px;
}}
#oscilloscopeCanvas {{
  width: 100%;
  height: 56px;
  background: #090d14;
  border-radius: 6px;
  display: block;
}}
#phaseCanvas {{
  width: 100%;
  height: 96px;
  background: #090d14;
  border-radius: 6px;
  display: block;
}}

/* Controls Bar */
.controls-bar {{
  background: var(--bg-subtle);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 18px 24px;
  display: grid;
  gap: 14px;
}}
.timeline-row {{
  display: flex;
  align-items: center;
  gap: 16px;
}}
.time-display {{
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
  min-width: 90px;
}}
.scrub-slider {{
  flex: 1;
  accent-color: var(--accent);
  cursor: pointer;
  height: 6px;
}}
.buttons-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
}}
.play-btn-group {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.ctrl-btn {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  color: var(--ink);
  padding: 8px 18px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.ctrl-btn:hover {{
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}}
.speed-group {{
  display: flex;
  align-items: center;
  gap: 6px;
}}
.speed-btn {{
  background: var(--panel);
  border: 1px solid var(--panel-border);
  color: var(--ink-secondary);
  padding: 4px 10px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}}
.speed-btn.active {{
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}}
.toggle-group {{
  display: flex;
  align-items: center;
  gap: 14px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-secondary);
  flex-wrap: wrap;
}}
.toggle-label {{
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}}

/* Lightbox Modal */
.lightbox-modal {{
  position: fixed; inset: 0; z-index: 999;
  background: rgba(7, 10, 15, 0.94);
  backdrop-filter: blur(16px);
  display: none; align-items: center; justify-content: center; padding: 30px;
}}
.lightbox-modal.active {{ display: flex; }}
.lightbox-box {{
  max-width: 1200px; width: 100%; max-height: 92vh;
  display: flex; flex-direction: column; background: var(--panel);
  border-radius: var(--radius-lg); overflow: hidden; border: 1px solid var(--panel-border);
  position: relative;
}}
.lightbox-close {{
  position: absolute; top: 16px; right: 16px; width: 38px; height: 38px;
  border-radius: 50%; background: rgba(0,0,0,0.6); color: #fff; border: none;
  cursor: pointer; font-size: 20px; z-index: 10; display: flex; align-items: center; justify-content: center;
}}
.lightbox-close:hover {{ background: var(--accent); color: #000; }}
.lightbox-img-wrap {{
  background: #090d14; padding: 20px; flex: 1; overflow: auto;
  display: flex; align-items: center; justify-content: center;
}}
.lightbox-img-wrap img {{
  max-width: 100%; max-height: 72vh; object-fit: contain;
}}
.lightbox-meta {{
  padding: 20px 24px; background: var(--panel); border-top: 1px solid var(--panel-border);
}}
.lightbox-title {{ font-family: var(--font-serif); font-size: 22px; font-weight: 600; color: var(--ink); margin-bottom: 6px; }}
.lightbox-desc {{ font-size: 14px; color: var(--ink-secondary); line-height: 1.5; }}

footer {{
  border-top: 1px solid var(--rule);
  padding-top: 36px;
  font-size: 13.5px;
  color: var(--ink-muted);
  line-height: 1.6;
}}
footer a {{ color: var(--accent); text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}

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
  margin-bottom: 24px;
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
  font-size: 14px;
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
</style>
</head>
<body>

<nav class="top-nav">
  <div class="nav-inner">
    <a href="{prefix_back}" class="nav-brand">
      <span class="brand-dot"></span>
      <span class="brand-title">NeuroCheck · Motion Lab</span>
    </a>
    <ul class="nav-menu">
      <li><a href="{return_portal_link}" class="nav-link" style="color:var(--accent);font-weight:700;">Presentation Portal "Return" ↗</a></li>
      <li><a href="{prefix_back}" class="nav-link">&larr; Platform Checking Dashboard</a></li>
      <li><a href="{explorer_link}" class="nav-link">Behavior Atlas</a></li>
      <li><a href="{profiles_link}" class="nav-link">Individual Profiles</a></li>
      <li><a href="{corr_link}" class="nav-link">Cross-Correlations</a></li>
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
      <span class="edition-badge">Academic &amp; Advisory Pose Stage</span>
      <div class="edition-desc">
        Real-time 60 FPS skeletal kinematics, 3D space-time cylinder, and posture attractor phase dynamics for formal research demonstration.
      </div>
    </div>
    <a href="{return_portal_link}" class="edition-btn">
      <span>Launch "Return" Presentation Portal</span>
      <span>&rarr;</span>
    </a>
  </div>

  <header class="hero">
    <div class="editorial-marker">
      <span class="marker-line"></span>
      <span class="marker-vol">VOL. V</span>
      <span class="marker-dot"></span>
      <span class="marker-sub">SPECIAL FEATURE · COMPUTATIONAL ETHOLOGY &amp; KINEMATIC ART</span>
      <span class="marker-dot"></span>
      <span class="marker-badge">10 ART MANIFOLDS · 60 FPS 3D POSE STAGE</span>
      <span class="marker-line"></span>
    </div>

    <h1>The DeepLabCut Motion Lab: <em>Kinematic Manifolds &amp; Pose Dynamics</em></h1>

    <p class="hero-lede">
      Explore the complete micro-structure of rodent spatial behavior. Featuring stroboscopic 16-point pose reconstructions, 3D space-time helices, eigen-posture manifolds, hydrodynamic swarm vector currents, polar attention compasses, continuous Morlet wavelet sonograms, and an interactive 60 FPS WebGL motion stage.
    </p>
  </header>

  <!-- GRAND SCIENTIFIC ART GALLERY (10 PLATES) -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Publication Art Portfolio · 10 Grand Plates</div>
      <h2 class="section-title">DeepLabCut Kinematic Art &amp; Manifold Reconstructions</h2>
      <p class="section-desc">Click any plate to inspect full high-resolution rendering, detailed anatomical traces, and analytical legends.</p>
    </div>

    <div class="art-grid">
      {art_joined}
    </div>
  </section>

  <!-- INTERACTIVE POSE & MOTION LAB -->
  <section id="player">
    <div class="section-head">
      <div class="section-eyebrow">Interactive 60 FPS Canvas &amp; 3D WebGL Player</div>
      <h2 class="section-title">The Real-Time DeepLabCut Motion Stage</h2>
      <p class="section-desc">Choose a representative animal, scrub through the 120-second session, switch between 2D arena and 3D space-time cylinder, toggle Swarm Simulation mode, and inspect live posture phase trajectories and audio sonification.</p>
    </div>

    <div class="lab-container">
      <!-- Top Animal Selector & View Switcher -->
      <div class="lab-topbar">
        <div class="rat-select-wrap">
          <span class="rat-select-label">Primary Subject:</span>
          <button class="rat-pill active" onclick="loadRat('rat28', this)">Rat 28 (Female · P1 Run)</button>
          <button class="rat-pill" onclick="loadRat('rat25', this)">Rat 25 (Female · 4 Excursions)</button>
          <button class="rat-pill" onclick="loadRat('rat17', this)">Rat 17 (Female · Bimodal)</button>
          <button class="rat-pill" onclick="loadRat('rat14', this)">Rat 14 (Male · Super-Scanner)</button>
          <button class="rat-pill" onclick="loadRat('rat02', this)">Rat 02 (Male · Anchored)</button>
        </div>

        <div class="view-switch-bar">
          <button class="view-tab active" id="tab2D" onclick="switchView('2d')">2D Arena View</button>
          <button class="view-tab" id="tab3D" onclick="switchView('3d')">3D Space-Time Orbit 🪐</button>
        </div>
      </div>

      <div class="rat-story-banner" id="ratStory">
        Loading motion telemetry data...
      </div>

      <!-- Main Stage -->
      <div class="lab-stage">
        <!-- Canvas Stage -->
        <div class="canvas-wrap">
          <canvas id="motionCanvas" width="700" height="700"></canvas>
          <div id="webglContainer"></div>
          <div class="canvas-overlay-tip" id="stageTip">2D Top-Down View · 60 FPS Kinematics</div>
        </div>

        <!-- Telemetry Gauges -->
        <div class="telemetry-sidebar">
          <div class="telemetry-card">
            <div class="tel-header">
              <span class="tel-lab">Behavioral State</span>
              <span class="status-pill" id="telState">INITIALIZING</span>
            </div>
            <div class="tel-val" id="telPlatform">Platform Zone</div>
            <div class="tel-sub" id="telSubState">Checking platform retention</div>
          </div>

          <div class="telemetry-card">
            <div class="tel-header">
              <span class="tel-lab">Swim Speed</span>
              <span class="tel-lab" style="color:var(--m)">cm/s</span>
            </div>
            <div class="tel-val" id="telSpeed">0.0</div>
            <div class="tel-sub">Instantaneous velocity</div>
          </div>

          <div class="telemetry-card">
            <div class="tel-header">
              <span class="tel-lab">Distance to P1 Target</span>
              <span class="tel-lab" style="color:var(--p1-color)">cm</span>
            </div>
            <div class="tel-val" id="telDistP1">74.2</div>
            <div class="tel-sub">&le; 20 cm = P1 Catchment Zone</div>
          </div>

          <!-- Real-Time Posture Waveform -->
          <div class="oscilloscope-box">
            <div class="tel-header">
              <span class="tel-lab">Posture Waveform (Curvature)</span>
              <span class="tel-lab" style="color:var(--accent)">LIVE</span>
            </div>
            <canvas id="oscilloscopeCanvas" width="300" height="56"></canvas>
            <div class="tel-sub">Traveling undulation wave along spine</div>
          </div>

          <!-- Real-Time Posture Phase Space (PC1 vs PC2) -->
          <div class="oscilloscope-box">
            <div class="tel-header">
              <span class="tel-lab">Posture Phase Space (PC1 vs PC2)</span>
              <span class="tel-lab" style="color:var(--f)">LIVE ATTRACTOR</span>
            </div>
            <canvas id="phaseCanvas" width="300" height="96"></canvas>
            <div class="tel-sub" id="telPhaseSub">Scanning Attractor vs Swim Orbit</div>
          </div>
        </div>
      </div>

      <!-- Controls & Scrubber -->
      <div class="controls-bar">
        <div class="timeline-row">
          <span class="time-display" id="timeDisplay">00:00.0 / 02:00</span>
          <input type="range" class="scrub-slider" id="scrubber" min="0" max="1800" value="0" step="1">
        </div>

        <div class="buttons-row">
          <div class="play-btn-group">
            <button class="ctrl-btn" id="playBtn" onclick="togglePlay()">
              <span id="playIcon">▶ Play</span>
            </button>
            <button class="ctrl-btn" onclick="resetPlay()">⏮ Reset</button>
          </div>

          <div class="speed-group">
            <span style="font-family:var(--font-mono);font-size:11px;color:var(--ink-secondary);margin-right:4px">RATE:</span>
            <button class="speed-btn" onclick="setSpeed(0.5, this)">0.5×</button>
            <button class="speed-btn active" onclick="setSpeed(1.0, this)">1×</button>
            <button class="speed-btn" onclick="setSpeed(2.0, this)">2×</button>
            <button class="speed-btn" onclick="setSpeed(4.0, this)">4×</button>
            <button class="speed-btn" onclick="setSpeed(8.0, this)">8×</button>
          </div>

          <div class="toggle-group">
            <label class="toggle-label"><input type="checkbox" id="chkGhost" checked> Dual Ghost (vs Male 02)</label>
            <label class="toggle-label"><input type="checkbox" id="chkSwarm" onchange="toggleSwarm(this)"> 🌊 Swarm (5 Rats)</label>
            <label class="toggle-label"><input type="checkbox" id="chkSkeleton" checked> Skeleton</label>
            <label class="toggle-label"><input type="checkbox" id="chkTrail" checked> Trail</label>
            <label class="toggle-label"><input type="checkbox" id="chkGaze" checked> Gaze Cone</label>
            <label class="toggle-label"><input type="checkbox" id="chkSound" onchange="toggleAudio(this)"> 🔊 Sound</label>
          </div>
        </div>
      </div>
    </div>
  </section>

  <footer>
    <p>
      The DeepLabCut Motion Lab &middot; Developed for the SFN 2026 Platform Checking Archive &middot; 
      Built from rotation-augmented DeepLabCut models (<code>KAcheck_d6d8_v3rot_20261108</code>).
    </p>
    <p style="margin-top:8px">
      Return to <a href="{prefix_back}">Platform Checking Dashboard</a>, explore <a href="{profiles_link}">Individual Profiles</a>, or browse the <a href="{explorer_link}">Behavior Atlas</a>.
    </p>
  </footer>

</div>

<!-- LIGHTBOX MODAL -->
<div class="lightbox-modal" id="lightboxModal" onclick="closeLightbox(event)">
  <div class="lightbox-box" onclick="event.stopPropagation()">
    <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
    <div class="lightbox-img-wrap">
      <img id="lightboxImg" src="" alt="Enlarged Art Plate">
    </div>
    <div class="lightbox-meta">
      <h3 class="lightbox-title" id="lightboxTitle"></h3>
      <p class="lightbox-desc" id="lightboxDesc"></p>
    </div>
  </div>
</div>

<!-- Embedded Motion Data Payload (Guarantees local file:/// compatibility with ZERO CORS errors) -->
<script id="motionDataPayload" type="application/json">
{json_payload}
</script>

<script>
// --- GLOBAL STATE ---
let motionData = null;
let currentRatKey = "rat28";
let currentFrame = 0;
let isPlaying = false;
let playSpeed = 1.0;
let lastAnimTime = 0;
let currentView = "2d"; // "2d" or "3d"
let isSwarmMode = false;

const canvas = document.getElementById("motionCanvas");
const ctx = canvas.getContext("2d");
const oscCanvas = document.getElementById("oscilloscopeCanvas");
const oscCtx = oscCanvas.getContext("2d");
const phaseCanvas = document.getElementById("phaseCanvas");
const phaseCtx = phaseCanvas.getContext("2d");
const webglContainer = document.getElementById("webglContainer");
const POOL_RADIUS_CM = 86.0;

// Three.js 3D Space-Time State
let scene3D, camera3D, renderer3D, controls3D;
let splineMesh3D = null, ghostSplineMesh3D = null;
let markerSphere3D = null, timePlane3D = null;
let isThreeInitialized = false;

// Web Audio Sonification
let audioCtx = null;
let oscNode = null;
let gainNode = null;
let isAudioEnabled = false;

function initAudio() {{
  if (!audioCtx) {{
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext();
    oscNode = audioCtx.createOscillator();
    gainNode = audioCtx.createGain();
    oscNode.type = "sine";
    gainNode.gain.value = 0;
    oscNode.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    oscNode.start();
  }}
}}

function toggleAudio(cb) {{
  isAudioEnabled = cb.checked;
  if (isAudioEnabled) {{
    initAudio();
    if (audioCtx.state === "suspended") audioCtx.resume();
  }} else if (gainNode) {{
    gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
  }}
}}

function updateAudio(spd) {{
  if (!isAudioEnabled || !gainNode || !oscNode) return;
  if (!isPlaying) {{
    gainNode.gain.setTargetAtTime(0, audioCtx.currentTime, 0.05);
    return;
  }}
  const freq = 220 + Math.min(spd, 40) * 11;
  oscNode.frequency.setTargetAtTime(freq, audioCtx.currentTime, 0.05);
  gainNode.gain.setTargetAtTime(0.08, audioCtx.currentTime, 0.05);
}}

// Parse Embedded Motion Data
(function() {{
  try {{
    const el = document.getElementById("motionDataPayload");
    if (el && el.textContent.trim().length > 100) {{
      motionData = JSON.parse(el.textContent);
      initApp();
      return;
    }}
  }} catch (e) {{
    console.warn("Error parsing embedded payload, falling back to fetch:", e);
  }}

  // Fallback to fetch if embedded payload missing
  fetch("{json_path}")
    .then(r => r.json())
    .then(data => {{
      motionData = data;
      initApp();
    }})
    .catch(err => {{
      console.error("Error loading motion data:", err);
      document.getElementById("ratStory").textContent = "Failed to load kinematic dataset.";
    }});
}})();

function initApp() {{
  loadRat("rat28", document.querySelector(".rat-pill.active"));
  requestAnimationFrame(renderLoop);
}}

function loadRat(key, btn) {{
  if (!motionData || !motionData[key]) return;
  currentRatKey = key;
  currentFrame = 0;
  
  document.querySelectorAll(".rat-pill").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  
  const d = motionData[key];
  document.getElementById("ratStory").innerHTML = `<strong>${{d.label}}:</strong> ${{d.story}}`;
  document.getElementById("scrubber").max = d.n_frames - 1;
  document.getElementById("scrubber").value = 0;
  updateTelemetry(0);
  if (currentView === "3d" && isThreeInitialized) update3DTrajectory();
}}

function togglePlay() {{
  isPlaying = !isPlaying;
  document.getElementById("playIcon").textContent = isPlaying ? "⏸ Pause" : "▶ Play";
}}

function resetPlay() {{
  currentFrame = 0;
  isPlaying = false;
  document.getElementById("playIcon").textContent = "▶ Play";
  document.getElementById("scrubber").value = 0;
  updateTelemetry(0);
}}

function setSpeed(spd, btn) {{
  playSpeed = spd;
  document.querySelectorAll(".speed-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}}

function toggleSwarm(cb) {{
  isSwarmMode = cb.checked;
}}

document.getElementById("scrubber").addEventListener("input", e => {{
  currentFrame = parseInt(e.target.value);
  updateTelemetry(currentFrame);
}});

document.addEventListener("keydown", e => {{
  if (e.code === "Space" && e.target.tagName !== "INPUT") {{
    e.preventDefault();
    togglePlay();
  }}
}});

// --- VIEW SWITCHING (2D vs 3D) ---
function switchView(view) {{
  currentView = view;
  const tab2D = document.getElementById("tab2D");
  const tab3D = document.getElementById("tab3D");
  const tip = document.getElementById("stageTip");

  if (view === "2d") {{
    tab2D.classList.add("active");
    tab3D.classList.remove("active");
    canvas.style.display = "block";
    webglContainer.style.display = "none";
    tip.textContent = "2D Top-Down View · 60 FPS Kinematics";
  }} else {{
    tab3D.classList.add("active");
    tab2D.classList.remove("active");
    canvas.style.display = "none";
    webglContainer.style.display = "block";
    tip.textContent = "3D Space-Time Cylinder · Drag to Orbit, Scroll to Zoom";
    if (!isThreeInitialized) initThree3D();
    else update3DTrajectory();
  }}
}}

// --- THREE.JS 3D SPACE-TIME MANIFOLD ---
function initThree3D() {{
  if (typeof THREE === "undefined") {{
    console.warn("Three.js not loaded, cannot init 3D view");
    return;
  }}
  isThreeInitialized = true;
  const w = webglContainer.clientWidth || 700;
  const h = webglContainer.clientHeight || 700;

  scene3D = new THREE.Scene();
  scene3D.background = new THREE.Color(0x070a0f);

  camera3D = new THREE.PerspectiveCamera(45, w / h, 1, 2000);
  camera3D.position.set(160, 180, 260);

  renderer3D = new THREE.WebGLRenderer({{ antialias: true }});
  renderer3D.setSize(w, h);
  renderer3D.setPixelRatio(window.devicePixelRatio);
  webglContainer.appendChild(renderer3D.domElement);

  if (typeof THREE.OrbitControls !== "undefined") {{
    controls3D = new THREE.OrbitControls(camera3D, renderer3D.domElement);
    controls3D.enableDamping = true;
    controls3D.dampingFactor = 0.05;
    controls3D.target.set(0, 60, 0);
  }}

  // Ambient & Directional Lights
  const ambLight = new THREE.AmbientLight(0xffffff, 0.7);
  scene3D.add(ambLight);
  const dirLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
  dirLight.position.set(100, 200, 100);
  scene3D.add(dirLight);

  // 1. Water Maze Pool Cylinder (R=86cm, Height=120s)
  const poolGeo = new THREE.CylinderGeometry(POOL_RADIUS_CM, POOL_RADIUS_CM, 120, 48, 1, true);
  const poolMat = new THREE.MeshBasicMaterial({{
    color: 0x38bdf8,
    wireframe: true,
    transparent: true,
    opacity: 0.12
  }});
  const poolMesh = new THREE.Mesh(poolGeo, poolMat);
  poolMesh.position.set(0, 60, 0);
  scene3D.add(poolMesh);

  // Floor Grid Rings
  [25, 50, 75, 86].forEach(r => {{
    const ringGeo = new THREE.RingGeometry(r - 0.4, r + 0.4, 48);
    const ringMat = new THREE.MeshBasicMaterial({{ color: 0xffffff, transparent: true, opacity: 0.15, side: THREE.DoubleSide }});
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = 0;
    scene3D.add(ring);
  }});

  // 2. Checking Platform Column (Cylinder through time)
  const platGeo = new THREE.CylinderGeometry(14.2, 14.2, 120, 24, 1, false);
  const platMat = new THREE.MeshBasicMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.22, wireframe: true }});
  const platCol = new THREE.Mesh(platGeo, platMat);
  platCol.position.set(-17.6, 60, 30.2);
  scene3D.add(platCol);

  // 3. P1 Column
  const p1Geo = new THREE.CylinderGeometry(20.0, 20.0, 120, 24, 1, false);
  const p1Mat = new THREE.MeshBasicMaterial({{ color: 0xc084fc, transparent: true, opacity: 0.18, wireframe: true }});
  const p1Col = new THREE.Mesh(p1Geo, p1Mat);
  p1Col.position.set(24.1, 60, -30.5);
  scene3D.add(p1Col);

  // Current Time Slicing Disc
  const planeGeo = new THREE.CircleGeometry(POOL_RADIUS_CM, 48);
  const planeMat = new THREE.MeshBasicMaterial({{ color: 0x2dd4bf, transparent: true, opacity: 0.08, side: THREE.DoubleSide }});
  timePlane3D = new THREE.Mesh(planeGeo, planeMat);
  timePlane3D.rotation.x = Math.PI / 2;
  scene3D.add(timePlane3D);

  // Pulsing Marker Sphere
  const sphereGeo = new THREE.SphereGeometry(3.5, 16, 16);
  const sphereMat = new THREE.MeshBasicMaterial({{ color: 0x2dd4bf }});
  markerSphere3D = new THREE.Mesh(sphereGeo, sphereMat);
  scene3D.add(markerSphere3D);

  update3DTrajectory();
}}

function update3DTrajectory() {{
  if (!isThreeInitialized || !motionData || !motionData[currentRatKey]) return;
  const d = motionData[currentRatKey];

  if (splineMesh3D) scene3D.remove(splineMesh3D);
  if (ghostSplineMesh3D) scene3D.remove(ghostSplineMesh3D);

  // Create 3D points: X=neck[0], Y=time (0 to 120), Z=neck[1]
  const pts = [];
  const colors = [];
  const color1 = new THREE.Color(d.sex === "F" ? 0x38bdf8 : 0xfb923c);
  const colorFast = new THREE.Color(0xf43f5e);

  for (let i = 0; i < d.n_frames; i++) {{
    const pt = d.skeleton.neck[i];
    const tY = (i / d.n_frames) * 120;
    pts.push(new THREE.Vector3(pt[0], tY, pt[1]));
    
    const spd = d.speed[i] || 0;
    const c = color1.clone().lerp(colorFast, Math.min(spd / 35, 1.0));
    colors.push(c.r, c.g, c.b);
  }}

  const curveGeo = new THREE.BufferGeometry().setFromPoints(pts);
  curveGeo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  const curveMat = new THREE.LineBasicMaterial({{ vertexColors: true, linewidth: 2.5 }});
  splineMesh3D = new THREE.Line(curveGeo, curveMat);
  scene3D.add(splineMesh3D);

  // Ghost trajectory (Rat 02) if enabled
  if (document.getElementById("chkGhost").checked && motionData["rat02"]) {{
    const g = motionData["rat02"];
    const gPts = [];
    for (let i = 0; i < g.n_frames; i++) {{
      const pt = g.skeleton.neck[i];
      const tY = (i / g.n_frames) * 120;
      gPts.push(new THREE.Vector3(pt[0], tY, pt[1]));
    }}
    const gGeo = new THREE.BufferGeometry().setFromPoints(gPts);
    const gMat = new THREE.LineBasicMaterial({{ color: 0xea580c, transparent: true, opacity: 0.55 }});
    ghostSplineMesh3D = new THREE.Line(gGeo, gMat);
    scene3D.add(ghostSplineMesh3D);
  }}
}}

// --- RENDER LOOP ---
function renderLoop(timestamp) {{
  if (!lastAnimTime) lastAnimTime = timestamp;
  const delta = (timestamp - lastAnimTime) / 1000;
  lastAnimTime = timestamp;

  if (isPlaying && motionData && motionData[currentRatKey]) {{
    const d = motionData[currentRatKey];
    currentFrame += d.fps * delta * playSpeed;
    if (currentFrame >= d.n_frames) {{
      currentFrame = d.n_frames - 1;
      isPlaying = false;
      document.getElementById("playIcon").textContent = "▶ Play";
    }}
    document.getElementById("scrubber").value = Math.floor(currentFrame);
    updateTelemetry(Math.floor(currentFrame));
  }}

  if (currentView === "2d") {{
    drawCanvas();
  }} else if (isThreeInitialized) {{
    if (controls3D) controls3D.update();
    if (motionData && motionData[currentRatKey]) {{
      const d = motionData[currentRatKey];
      const fIdx = Math.min(Math.floor(currentFrame), d.n_frames - 1);
      const pt = d.skeleton.neck[fIdx];
      const tY = (fIdx / d.n_frames) * 120;
      if (markerSphere3D) markerSphere3D.position.set(pt[0], tY, pt[1]);
      if (timePlane3D) timePlane3D.position.y = tY;
    }}
    renderer3D.render(scene3D, camera3D);
  }}

  drawOscilloscope();
  drawPhaseSpace();
  requestAnimationFrame(renderLoop);
}}

function updateTelemetry(fIdx) {{
  if (!motionData || !motionData[currentRatKey]) return;
  const d = motionData[currentRatKey];
  fIdx = Math.min(fIdx, d.n_frames - 1);

  const tSec = fIdx / d.fps;
  const mins = Math.floor(tSec / 60);
  const secs = (tSec % 60).toFixed(1).padStart(4, "0");
  document.getElementById("timeDisplay").textContent = `0${{mins}}:${{secs}} / 02:00`;

  const spd = d.speed[fIdx];
  const trn = d.turn[fIdx];
  const isOff = d.off[fIdx] === 1;

  document.getElementById("telSpeed").textContent = spd.toFixed(1);

  updateAudio(spd);

  // Distance to P1
  const bodyPt = d.skeleton.neck[fIdx];
  const distP1 = Math.hypot(bodyPt[0] - d.p1[0], bodyPt[1] - d.p1[1]);
  document.getElementById("telDistP1").textContent = distP1.toFixed(1);

  // State
  const stateBadge = document.getElementById("telState");
  const platState = document.getElementById("telPlatform");
  const subState = document.getElementById("telSubState");

  if (!isOff) {{
    stateBadge.textContent = "ON PLATFORM";
    stateBadge.style.color = "#38bdf8";
    stateBadge.style.background = "rgba(56, 189, 248, 0.15)";
    platState.textContent = "Anchored Safe";
    subState.textContent = Math.abs(trn) >= 30 ? "Engaging in micro-scanning sweeps" : "Stationary posture";
  }} else if (distP1 <= 20) {{
    stateBadge.textContent = "AT P1 TARGET";
    stateBadge.style.color = "#c084fc";
    stateBadge.style.background = "rgba(192, 132, 252, 0.2)";
    platState.textContent = "Target Reached";
    subState.textContent = `< ${{distP1.toFixed(1)}} cm from former platform`;
  }} else {{
    stateBadge.textContent = "OFF-PLATFORM SWEEP";
    stateBadge.style.color = "#fb923c";
    stateBadge.style.background = "rgba(251, 146, 60, 0.15)";
    platState.textContent = "Active Excursion";
    subState.textContent = spd > 25 ? "High-velocity swim dash" : "Exploratory navigation";
  }}
}}

// --- LIVE POSTURE OSCILLOSCOPE ---
function drawOscilloscope() {{
  const ow = oscCanvas.width, oh = oscCanvas.height;
  oscCtx.clearRect(0, 0, ow, oh);

  if (!motionData || !motionData[currentRatKey]) return;
  const d = motionData[currentRatKey];
  const fIdx = Math.min(Math.floor(currentFrame), d.n_frames - 1);

  const pts = ["nose", "head_center", "neck", "spine_upper", "spine_mid", "spine_lower", "tail_base"];
  const segs = [];
  for (let i = 0; i < pts.length - 1; i++) {{
    const p1 = d.skeleton[pts[i]][fIdx];
    const p2 = d.skeleton[pts[i+1]][fIdx];
    segs.push(Math.atan2(p2[1] - p1[1], p2[0] - p1[0]));
  }}
  const curvs = [];
  for (let i = 0; i < segs.length - 1; i++) {{
    let diff = segs[i+1] - segs[i];
    while (diff > Math.PI) diff -= 2 * Math.PI;
    while (diff < -Math.PI) diff += 2 * Math.PI;
    curvs.push(diff);
  }}

  // Center line
  oscCtx.beginPath();
  oscCtx.moveTo(0, oh / 2);
  oscCtx.lineTo(ow, oh / 2);
  oscCtx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  oscCtx.stroke();

  // Draw waveform
  oscCtx.beginPath();
  const stepX = ow / (curvs.length + 1);
  oscCtx.moveTo(0, oh / 2);
  for (let i = 0; i < curvs.length; i++) {{
    const x = (i + 1) * stepX;
    const y = oh / 2 - curvs[i] * 28;
    oscCtx.lineTo(x, y);
  }}
  oscCtx.lineTo(ow, oh / 2);
  oscCtx.lineWidth = 2.2;
  oscCtx.strokeStyle = d.sex === "F" ? "#60a5fa" : "#fb923c";
  oscCtx.shadowColor = d.sex === "F" ? "#60a5fa" : "#fb923c";
  oscCtx.shadowBlur = 8;
  oscCtx.stroke();
  oscCtx.shadowBlur = 0;
}}

// --- LIVE POSTURE PHASE SPACE (PC1 vs PC2) ---
function drawPhaseSpace() {{
  const pw = phaseCanvas.width, ph = phaseCanvas.height;
  phaseCtx.clearRect(0, 0, pw, ph);

  if (!motionData || !motionData[currentRatKey] || !motionData[currentRatKey].pc1) return;
  const d = motionData[currentRatKey];
  const fIdx = Math.min(Math.floor(currentFrame), d.n_frames - 1);

  // Mapping from PC coords (-165 to 0) to phaseCanvas
  function toPhaseX(pc1) {{
    return ((pc1 - (-165)) / (0 - (-165))) * pw;
  }}
  function toPhaseY(pc2) {{
    return ph / 2 - (pc2 / 50.0) * (ph * 0.42);
  }}

  // 1. Attractor Basins Background
  // Scanning Basin at left (centered around -135, 0)
  phaseCtx.save();
  phaseCtx.beginPath();
  const bX = toPhaseX(-135);
  const bY = toPhaseY(0);
  phaseCtx.ellipse(bX, bY, 26, 20, 0, 0, Math.PI * 2);
  phaseCtx.fillStyle = "rgba(45, 212, 191, 0.12)";
  phaseCtx.fill();
  phaseCtx.strokeStyle = "rgba(45, 212, 191, 0.3)";
  phaseCtx.stroke();

  // Swim Orbit at right (centered around -75, 0)
  phaseCtx.beginPath();
  const sX = toPhaseX(-75);
  phaseCtx.ellipse(sX, bY, 44, 28, 0, 0, Math.PI * 2);
  phaseCtx.fillStyle = "rgba(244, 63, 94, 0.08)";
  phaseCtx.fill();
  phaseCtx.strokeStyle = "rgba(244, 63, 94, 0.25)";
  phaseCtx.stroke();
  phaseCtx.restore();

  // Labels
  phaseCtx.fillStyle = "rgba(255, 255, 255, 0.35)";
  phaseCtx.font = "9px var(--font-mono)";
  phaseCtx.textAlign = "center";
  phaseCtx.fillText("SCAN ATTRACTOR", bX, ph - 6);
  phaseCtx.fillText("SWIM LIMIT CYCLE", sX, ph - 6);

  // 2. Trajectory Tail (last 35 frames)
  const tailLen = 35;
  const startTail = Math.max(0, fIdx - tailLen);
  phaseCtx.beginPath();
  let first = true;
  for (let i = startTail; i <= fIdx; i++) {{
    const x = toPhaseX(d.pc1[i]);
    const y = toPhaseY(d.pc2[i]);
    if (first) {{ phaseCtx.moveTo(x, y); first = false; }}
    else {{ phaseCtx.lineTo(x, y); }}
  }}
  phaseCtx.strokeStyle = d.sex === "F" ? "rgba(96, 165, 250, 0.7)" : "rgba(251, 146, 60, 0.7)";
  phaseCtx.lineWidth = 1.8;
  phaseCtx.stroke();

  // 3. Current Point
  const curX = toPhaseX(d.pc1[fIdx]);
  const curY = toPhaseY(d.pc2[fIdx]);
  phaseCtx.beginPath();
  phaseCtx.arc(curX, curY, 4.5, 0, Math.PI * 2);
  phaseCtx.fillStyle = "#ffffff";
  phaseCtx.shadowColor = d.sex === "F" ? "#60a5fa" : "#fb923c";
  phaseCtx.shadowBlur = 10;
  phaseCtx.fill();
  phaseCtx.shadowBlur = 0;
}}

// --- CANVAS RENDERING (2D) ---
function drawCanvas() {{
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const cx = w / 2, cy = h / 2;
  const scale = (w * 0.44) / POOL_RADIUS_CM;

  function toScreen(cmX, cmY) {{
    return [cx + cmX * scale, cy + cmY * scale];
  }}

  // 1. Pool Background & Radial Grid
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, POOL_RADIUS_CM * scale, 0, Math.PI * 2);
  ctx.fillStyle = "#0b1018";
  ctx.fill();
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
  ctx.stroke();

  [25, 50, 75].forEach(rCm => {{
    ctx.beginPath();
    ctx.arc(cx, cy, rCm * scale, 0, Math.PI * 2);
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.setLineDash([4, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
  }});
  ctx.restore();

  if (!motionData) return;
  const d = motionData[currentRatKey];
  if (!d) return;
  const fIdx = Math.min(Math.floor(currentFrame), d.n_frames - 1);

  // 2. Checking Platform
  const [platX, platY] = toScreen(d.plat[0], d.plat[1]);
  const platR = 14.2 * scale;
  ctx.save();
  ctx.beginPath();
  ctx.arc(platX, platY, platR, 0, Math.PI * 2);
  ctx.fillStyle = "#141e2e";
  ctx.fill();
  ctx.lineWidth = 2.2;
  ctx.strokeStyle = "#38bdf8";
  ctx.shadowColor = "#38bdf8";
  ctx.shadowBlur = 12;
  ctx.stroke();
  ctx.restore();

  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 11px var(--font-mono)";
  ctx.textAlign = "center";
  ctx.fillText("PLATFORM", platX, platY + 4);

  // 3. P1 Former Training Location
  const [p1X, p1Y] = toScreen(d.p1[0], d.p1[1]);
  const p1CatchmentR = 20.0 * scale;
  ctx.save();
  ctx.beginPath();
  ctx.arc(p1X, p1Y, p1CatchmentR, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(168, 85, 247, 0.08)";
  ctx.fill();
  ctx.lineWidth = 1.8;
  ctx.strokeStyle = "#c084fc";
  ctx.setLineDash([5, 5]);
  ctx.stroke();

  // Diamond
  ctx.beginPath();
  ctx.moveTo(p1X, p1Y - 7);
  ctx.lineTo(p1X + 7, p1Y);
  ctx.lineTo(p1X, p1Y + 7);
  ctx.lineTo(p1X - 7, p1Y);
  ctx.closePath();
  ctx.fillStyle = "#c084fc";
  ctx.fill();
  ctx.restore();

  ctx.fillStyle = "#c084fc";
  ctx.font = "bold 11px var(--font-mono)";
  ctx.textAlign = "center";
  ctx.fillText("P1 TARGET", p1X, p1Y - 12);

  // SWARM SIMULATION MODE
  if (isSwarmMode) {{
    const swarmKeys = ["rat28", "rat25", "rat17", "rat14", "rat02"];
    const swarmColors = {{
      "rat28": "#38bdf8",
      "rat25": "#f43f5e",
      "rat17": "#2dd4bf",
      "rat14": "#fb923c",
      "rat02": "#ea580c"
    }};
    swarmKeys.forEach(sKey => {{
      const sRat = motionData[sKey];
      if (!sRat) return;
      const sIdx = Math.min(fIdx, sRat.n_frames - 1);
      drawRatOnCanvas(sRat, sIdx, swarmColors[sKey], 0.75, sRat.label.split(" ")[0] + " " + sRat.label.split(" ")[1]);
    }});
    return;
  }}

  // DUAL GHOST MODE (Rat 02)
  if (document.getElementById("chkGhost").checked && currentRatKey !== "rat02" && motionData["rat02"]) {{
    const ghost = motionData["rat02"];
    const gIdx = Math.min(fIdx, ghost.n_frames - 1);
    drawRatOnCanvas(ghost, gIdx, "#ea580c", 0.45, "Male Rat 02 (Anchor Ghost)");
  }}

  // PRIMARY SUBJECT
  const primaryColor = d.sex === "F" ? "#38bdf8" : "#fb923c";
  drawRatOnCanvas(d, fIdx, primaryColor, 1.0, null);
}}

function drawRatOnCanvas(d, fIdx, mainColor, alpha, labelText) {{
  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2;
  const scale = (w * 0.44) / POOL_RADIUS_CM;

  function toScreen(cmX, cmY) {{
    return [cx + cmX * scale, cy + cmY * scale];
  }}

  const doTrail = document.getElementById("chkTrail").checked;
  const doSkel = document.getElementById("chkSkeleton").checked;
  const doGaze = document.getElementById("chkGaze").checked;

  ctx.save();
  ctx.globalAlpha = alpha;

  // 1. Trail
  if (doTrail) {{
    const trailLen = 75;
    const startT = Math.max(0, fIdx - trailLen);
    for (let i = startT; i < fIdx; i++) {{
      const [x1, y1] = toScreen(d.skeleton.neck[i][0], d.skeleton.neck[i][1]);
      const [x2, y2] = toScreen(d.skeleton.neck[i+1][0], d.skeleton.neck[i+1][1]);
      const frac = (i - startT) / (fIdx - startT);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.lineWidth = 1.0 + frac * 2.5;
      ctx.strokeStyle = mainColor;
      ctx.globalAlpha = alpha * frac * 0.75;
      ctx.stroke();
    }}
    ctx.globalAlpha = alpha;
  }}

  // 2. Gaze Cone
  const nose = d.skeleton.nose[fIdx];
  const head = d.skeleton.head_center[fIdx];
  const [nx, ny] = toScreen(nose[0], nose[1]);
  const [hx, hy] = toScreen(head[0], head[1]);
  const gazeAngle = Math.atan2(ny - hy, nx - hx);

  if (doGaze) {{
    const coneLen = 65;
    const coneAngle = Math.PI / 6;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(nx, ny);
    ctx.arc(nx, ny, coneLen, gazeAngle - coneAngle, gazeAngle + coneAngle);
    ctx.closePath();
    const grad = ctx.createRadialGradient(nx, ny, 0, nx, ny, coneLen);
    grad.addColorStop(0, "rgba(255, 255, 255, 0.4)");
    grad.addColorStop(1, "rgba(255, 255, 255, 0.0)");
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.restore();
  }}

  // 3. 14-Point Skeleton
  if (doSkel) {{
    const skelEdges = [
      ["nose", "head_center"],
      ["head_center", "neck"],
      ["head_center", "left_ear"],
      ["head_center", "right_ear"],
      ["neck", "spine_upper"],
      ["neck", "left_shoulder"],
      ["neck", "right_shoulder"],
      ["spine_upper", "spine_mid"],
      ["spine_mid", "spine_lower"],
      ["spine_lower", "left_hip"],
      ["spine_lower", "right_hip"],
      ["spine_lower", "tail_base"]
    ];

    // Bones
    ctx.lineWidth = 2.2;
    ctx.strokeStyle = mainColor;
    ctx.shadowColor = mainColor;
    ctx.shadowBlur = 8;
    skelEdges.forEach(([p1Key, p2Key]) => {{
      const [x1, y1] = toScreen(d.skeleton[p1Key][fIdx][0], d.skeleton[p1Key][fIdx][1]);
      const [x2, y2] = toScreen(d.skeleton[p2Key][fIdx][0], d.skeleton[p2Key][fIdx][1]);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }});
    ctx.shadowBlur = 0;

    // Joints
    Object.keys(d.skeleton).forEach(k => {{
      const [jx, jy] = toScreen(d.skeleton[k][fIdx][0], d.skeleton[k][fIdx][1]);
      ctx.beginPath();
      ctx.arc(jx, jy, k === "nose" ? 4.2 : 2.5, 0, Math.PI * 2);
      ctx.fillStyle = k === "nose" ? "#ffffff" : mainColor;
      ctx.fill();
    }});
  }} else {{
    // Simple marker
    const [bx, by] = toScreen(d.skeleton.neck[fIdx][0], d.skeleton.neck[fIdx][1]);
    ctx.beginPath();
    ctx.arc(bx, by, 6.0, 0, Math.PI * 2);
    ctx.fillStyle = mainColor;
    ctx.fill();
  }}

  // Label
  if (labelText) {{
    const [lx, ly] = toScreen(d.skeleton.head_center[fIdx][0], d.skeleton.head_center[fIdx][1]);
    ctx.fillStyle = mainColor;
    ctx.font = "bold 10px var(--font-mono)";
    ctx.textAlign = "center";
    ctx.fillText(labelText, lx, ly - 14);
  }}

  ctx.restore();
}}

// --- LIGHTBOX MODAL ---
function openLightbox(src, title, desc) {{
  document.getElementById('lightboxImg').src = src;
  document.getElementById('lightboxTitle').textContent = title;
  document.getElementById('lightboxDesc').textContent = desc;
  document.getElementById('lightboxModal').classList.add('active');
  document.body.style.overflow = 'hidden';
}}
function closeLightbox() {{
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

# Generate dlc_motion_lab.html
html1 = generate_motion_lab_html(is_site=False)
(HERE / "dlc_motion_lab.html").write_text(html1, encoding="utf-8")
print(f"Generated {HERE / 'dlc_motion_lab.html'} ({len(html1)} bytes)")

# Generate site/dlc_motion_lab.html
site_dir = HERE / "site"
if site_dir.exists():
    html2 = generate_motion_lab_html(is_site=True)
    (site_dir / "dlc_motion_lab.html").write_text(html2, encoding="utf-8")
    print(f"Generated {site_dir / 'dlc_motion_lab.html'} ({len(html2)} bytes)")
