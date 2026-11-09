"""Elevates correlations_dashboard.html with the editorial scientific design system.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
html_file = HERE / "correlations_dashboard.html"
orig_text = html_file.read_text(encoding="utf-8")

script_idx = orig_text.find("<script>")
script_content = orig_text[script_idx:]

new_head_and_body = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Cross-Experiment Correlations · Water Maze × Exploration &amp; Anxiety</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
/* === EDITORIAL DESIGN SYSTEM === */
:root {
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

  /* Scientific Accents */
  --accent: #0f766e;
  --accent-light: #f0fdfa;
  --accent-glow: rgba(15, 118, 110, 0.12);
  --f: #1d4ed8;            /* Females: Crisp Sapphire */
  --f-soft: rgba(29, 78, 216, 0.08);
  --m: #ea580c;            /* Males: Terracotta Amber */
  --m-soft: rgba(234, 88, 12, 0.08);

  --sig-color: #0f766e;
  --sig-bg: #ccfbf1;
  --ns-color: #64748b;
  --ns-bg: #f1f5f9;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.03);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.08);
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-full: 9999px;
}

[data-theme="dark"] {
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

  --accent: #2dd4bf;
  --accent-light: rgba(45, 212, 191, 0.12);
  --accent-glow: rgba(45, 212, 191, 0.18);
  --f: #60a5fa;
  --f-soft: rgba(96, 165, 250, 0.12);
  --m: #fb923c;
  --m-soft: rgba(251, 146, 60, 0.12);

  --sig-color: #2dd4bf;
  --sig-bg: rgba(45, 212, 191, 0.16);
  --ns-color: #94a3b8;
  --ns-bg: rgba(255, 255, 255, 0.06);

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.6);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

/* Top Sticky Editorial Nav */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--panel-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--panel-border);
}
.nav-inner {
  max-width: 1360px;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--ink);
}
.brand-dot {
  width: 9px;
  height: 9px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 10px #10b981;
}
.brand-title {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.nav-menu {
  display: flex;
  align-items: center;
  gap: 20px;
  list-style: none;
}
.nav-link {
  font-family: var(--font-sans);
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
}
.nav-link:hover {
  color: var(--accent);
}
.theme-btn {
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
}

/* Wrap */
.wrap {
  max-width: 1360px;
  margin: 0 auto;
  padding: 40px 24px 100px;
  display: grid;
  gap: 52px;
}

/* Editorial Marker */
.editorial-marker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 20px;
  user-select: none;
}
.marker-line { width: 44px; height: 1px; background: var(--rule); }
.marker-vol { font-family: var(--font-serif); font-style: italic; font-size: 13px; font-weight: 500; color: var(--ink); }
.marker-dot { width: 3px; height: 3px; background: var(--ink-muted); border-radius: 50%; }
.marker-sub { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--ink-secondary); }
.marker-badge {
  font-family: var(--font-mono); font-size: 10px; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; background: var(--accent-light); color: var(--accent); padding: 2px 8px; border-radius: 4px;
}

/* Header */
.hero {
  text-align: center;
  max-width: 960px;
  margin: 0 auto;
  display: grid;
  gap: 18px;
}
.hero h1 {
  font-family: var(--font-serif);
  font-size: clamp(34px, 5.5vw, 56px);
  font-weight: 500;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.hero h1 em {
  font-style: italic;
  color: var(--accent);
}
.hero-lede {
  font-size: clamp(16px, 2vw, 19px);
  color: var(--ink-secondary);
  line-height: 1.6;
}
.f-text { color: var(--f); font-weight: 600; }
.m-text { color: var(--m); font-weight: 600; }

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}
.kpi-card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 22px 24px;
  display: grid;
  gap: 8px;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}
.kpi-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: var(--accent);
}
.kpi-lab {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}
.kpi-val {
  font-family: var(--font-serif);
  font-size: 38px;
  font-weight: 600;
  line-height: 1;
  color: var(--ink);
}
.kpi-cap {
  font-size: 13px;
  color: var(--ink-secondary);
}

/* Section Heads */
.section-head {
  display: grid;
  gap: 8px;
  margin-bottom: 22px;
}
.section-eyebrow {
  font-family: var(--font-mono);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-eyebrow::before {
  content: "";
  display: inline-block;
  width: 14px;
  height: 2px;
  background: var(--accent);
}
.section-title {
  font-family: var(--font-serif);
  font-size: clamp(24px, 3.5vw, 32px);
  font-weight: 500;
  color: var(--ink);
}
.section-desc {
  font-size: 15px;
  color: var(--ink-secondary);
  max-width: 820px;
}

/* Two Card Layout */
.two-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 24px;
}
.editorial-card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 24px 28px;
  display: grid;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}
.editorial-card h3 {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
  color: var(--ink);
}
.editorial-card ul {
  padding-left: 20px;
  display: grid;
  gap: 10px;
  font-size: 14px;
  color: var(--ink-secondary);
  line-height: 1.55;
}
.editorial-card strong {
  color: var(--ink);
}
.sig-badge {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 6px;
}

/* Heatmap Section */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 8px;
}
.tab {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  background: var(--bg-subtle);
  color: var(--ink-secondary);
  cursor: pointer;
  border: 1px solid var(--panel-border);
  transition: all 0.2s ease;
}
.tab.active {
  background: var(--ink);
  color: var(--panel);
  border-color: var(--ink);
}
[data-theme="dark"] .tab.active {
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}
.tab-content {
  display: none;
  background: #ffffff;
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-sm);
}
.tab-content.active {
  display: block;
}
.tab-content img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 6px;
}
.tab-content figcaption {
  padding: 12px 6px 4px;
  font-size: 14px;
  color: var(--ink-secondary);
}

/* Scatter Grid */
.scatter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}
.scatter-fig {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}
.scatter-fig .img {
  background: #ffffff;
  padding: 10px;
  border-bottom: 1px solid var(--panel-border);
}
.scatter-fig img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
}
.scatter-fig figcaption {
  padding: 12px 16px;
  font-size: 13.5px;
  color: var(--ink-secondary);
  line-height: 1.45;
}
.scatter-fig figcaption b {
  color: var(--ink);
  display: block;
  margin-bottom: 2px;
}

/* Tables */
.tbl-card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.table-wrap-fixed {
  max-height: 540px;
  overflow-y: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
  min-width: 800px;
}
thead th {
  background: var(--bg-subtle);
  border-bottom: 2px solid var(--panel-border);
  padding: 12px 14px;
  text-align: left;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-secondary);
  cursor: pointer;
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 5;
}
thead th:hover {
  color: var(--accent);
}
.sort-arrow { margin-left: 4px; opacity: 0.4; font-size: 9px; }
thead th.sorted-asc .sort-arrow::after { content: "▲"; opacity: 1; }
thead th.sorted-desc .sort-arrow::after { content: "▼"; opacity: 1; }
thead th:not(.sorted-asc):not(.sorted-desc) .sort-arrow::after { content: "▲▼"; }

tbody th, tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--rule);
  font-size: 14px;
  white-space: nowrap;
}
tbody tr:hover {
  background: var(--bg-subtle);
}
.sex-m { color: var(--m); font-weight: 600; }
.sex-f { color: var(--f); font-weight: 600; }

/* Filter Controls */
.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.filter-row label {
  font-family: var(--font-mono);
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-secondary);
}
.filter-row select, .filter-row input {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 13px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  outline: none;
}
.filter-row select:focus, .filter-row input:focus {
  border-color: var(--accent);
}

/* Footer */
footer {
  border-top: 1px solid var(--rule);
  padding-top: 36px;
  font-size: 13.5px;
  color: var(--ink-muted);
  line-height: 1.6;
}
footer a { color: var(--accent); text-decoration: none; }
footer a:hover { text-decoration: underline; }
footer code { font-family: var(--font-mono); font-size: 12px; background: var(--bg-subtle); padding: 2px 6px; border-radius: 4px; }
</style>
</head>
<body>

<nav class="top-nav">
  <div class="nav-inner">
    <a href="../dlc_cleaned/dashboard.html" class="nav-brand">
      <span class="brand-dot"></span>
      <span class="brand-title">NeuroCheck · Correlations</span>
    </a>
    <ul class="nav-menu">
      <li><a href="../dlc_cleaned/dashboard.html" class="nav-link">&larr; Platform Checking Dashboard</a></li>
      <li><a href="../dlc_cleaned/site/index.html" class="nav-link">Behavior Atlas Site</a></li>
      <li><a href="../dlc_cleaned/site/profiles.html" class="nav-link">Individual Profiles</a></li>
    </ul>
    <button class="theme-btn" onclick="toggleTheme()" id="themeBtn">
      <span>Theme</span>
      <span id="themeIcon">☀️</span>
    </button>
  </div>
</nav>

<div class="wrap">

  <header class="hero">
    <div class="editorial-marker">
      <span class="marker-line"></span>
      <span class="marker-vol">VOL. IV</span>
      <span class="marker-dot"></span>
      <span class="marker-sub">CROSS-EXPERIMENT PHENOTYPING · SFN 2026 ARCHIVE</span>
      <span class="marker-dot"></span>
      <span class="marker-badge">KAC COHORT · 29 RATS</span>
      <span class="marker-line"></span>
    </div>

    <h1>Cross-Experiment Phenotyping: <em>Water Maze Checking</em> &times; Exploration Assays</h1>

    <p class="hero-lede">
      Water maze checking dynamics correlated with Elevated Plus Maze (EPM), Open Field (OF), and Novel Object Recognition (NOR/PPT) assays across the KAC cohort (n = 29, <span class="m-text">males 1–16</span>, <span class="f-text">females 17–32</span>). Water maze metrics are drawn from the Day 6 checking test (standard 1.5 cm depth).
    </p>
  </header>

  <!-- KPI STRIP -->
  <section class="kpi-grid">
    <div class="kpi-card">
      <span class="kpi-lab">Animals (n)</span>
      <div class="kpi-val" id="kpi-n">—</div>
      <div class="kpi-cap">With complete water maze + behavioral battery</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-lab">Significant Tests</span>
      <div class="kpi-val" id="kpi-sig">—</div>
      <div class="kpi-cap">p &lt; 0.05 Spearman r across all animals (420 total tests)</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-lab">Strongest Effect</span>
      <div class="kpi-val" id="kpi-r">—</div>
      <div class="kpi-cap">Open Field centre entries &times; % platform retention time</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-lab">EPM Dissociation</span>
      <div class="kpi-val" id="kpi-epm">—</div>
      <div class="kpi-cap">EPM open arm ratio does not correlate with departures (p &gt; 0.50)</div>
    </div>
  </section>

  <!-- TOP 5 & INTERPRETATION -->
  <section class="two-card-grid">
    <div class="editorial-card">
      <h3>Top 5 Ranked Correlations</h3>
      <ul id="top5-list"></ul>
    </div>
    <div class="editorial-card">
      <h3>Neurobehavioral Interpretation</h3>
      <ul>
        <li><strong>Open field locomotion cluster:</strong> Locomotor drive in the open field anti-correlates strongly with platform dwell (r &approx; &minus;0.65, p &lt; 0.001): more active rats depart the platform sooner and more frequently.</li>
        <li><strong>Center exploration mirrors disembarkation:</strong> Animals entering the open arena center spend significantly less time anchored (r = &minus;0.66). Active open-space boldness maps onto water maze disembarkation.</li>
        <li><strong>NOR object investigation:</strong> Investigation duration of the relocated object predicts platform departures (r = 0.54) and head scanning sweeps (r = 0.52).</li>
        <li><strong>Dissociation from anxiety:</strong> EPM open-arm ratio does not correlate with checking departures (r = &minus;0.10, p = 0.59), confirming checking is driven by spatial foraging exploration, not panic.</li>
      </ul>
    </div>
  </section>

  <!-- HEATMAP SECTION -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Correlation Matrices</div>
      <h2 class="section-title">Behavioral Battery &times; Water Maze Measures</h2>
      <p class="section-desc">Spearman rank correlation coefficients between anxiety/exploration assays (rows) and water maze Day 6 checking measures (columns).</p>
    </div>

    <div class="tabs">
      <div class="tab active" onclick="switchTab(event,'hm-all')">All Animals (n = 29)</div>
      <div class="tab" onclick="switchTab(event,'hm-male')">Males Only (n = 13)</div>
      <div class="tab" onclick="switchTab(event,'hm-female')">Females Only (n = 16)</div>
    </div>

    <div class="tab-content active" id="hm-all">
      <figure class="plate">
        <img src="figures/corr_heatmap_all.png" alt="Correlation heatmap – all animals" loading="lazy">
        <figcaption><b>All animals (n = 29):</b> Rows encompass EPM, Open Field, NOR-Feb, and KAOFam. Columns encompass Water Maze Day 6 checking, latency, and probe measures.</figcaption>
      </figure>
    </div>
    <div class="tab-content" id="hm-male">
      <figure class="plate">
        <img src="figures/corr_heatmap_male.png" alt="Correlation heatmap – males" loading="lazy">
        <figcaption><b>Males only (n = 13)</b></figcaption>
      </figure>
    </div>
    <div class="tab-content" id="hm-female">
      <figure class="plate">
        <img src="figures/corr_heatmap_female.png" alt="Correlation heatmap – females" loading="lazy">
        <figcaption><b>Females only (n = 16)</b></figcaption>
      </figure>
    </div>
  </section>

  <!-- SCATTER PLOTS -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Bivariate Relationships</div>
      <h2 class="section-title">Key Scatter Plots with Animal Annotations</h2>
      <p class="section-desc">Each point denotes an individual animal, color-coded by sex (<span class="m-text">&block; Male</span>, <span class="f-text">&block; Female</span>) with linear regression fit line.</p>
    </div>

    <div class="scatter-grid" id="scatter-grid"></div>
  </section>

  <!-- SIGNIFICANT CORRELATIONS TABLE -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Statistical Audit</div>
      <h2 class="section-title">All Statistically Significant Tests (p &lt; 0.05)</h2>
      <p class="section-desc">Ranked by effect magnitude |r|. Click column headers to sort.</p>
    </div>

    <div class="tbl-card">
      <div class="table-wrap table-wrap-fixed">
        <table id="sig-table">
          <thead>
            <tr>
              <th onclick="sortSigTable(0)" data-col="0">Assay Measure<span class="sort-arrow"></span></th>
              <th onclick="sortSigTable(1)" data-col="1">Water Maze Measure<span class="sort-arrow"></span></th>
              <th onclick="sortSigTable(2)" data-col="2">n<span class="sort-arrow"></span></th>
              <th onclick="sortSigTable(3)" data-col="3">Spearman r<span class="sort-arrow"></span></th>
              <th onclick="sortSigTable(4)" data-col="4">P-Value<span class="sort-arrow"></span></th>
              <th onclick="sortSigTable(5)" data-col="5">|r|<span class="sort-arrow"></span></th>
            </tr>
          </thead>
          <tbody id="sig-tbody"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- MERGED PER-RAT DATA TABLE -->
  <section>
    <div class="section-head">
      <div class="section-eyebrow">Raw Master Dataset</div>
      <h2 class="section-title">Per-Rat Integrated Records</h2>
      <p class="section-desc">Full 39-variable merged matrix across all 29 animals. Click column headers to sort; filter by sex or search by rat ID.</p>
    </div>

    <div class="filter-row">
      <label>Filter by Sex:</label>
      <select id="sex-filter" onchange="renderTable()">
        <option value="all">All Cohorts (29)</option>
        <option value="M">Males Only (13)</option>
        <option value="F">Females Only (16)</option>
      </select>
      <label>Search Record:</label>
      <input type="text" id="search-box" placeholder="e.g. rat ID or value..." oninput="renderTable()" style="width:180px">
    </div>

    <div class="tbl-card">
      <div class="table-wrap table-wrap-fixed">
        <table id="main-table">
          <thead id="main-thead"></thead>
          <tbody id="main-tbody"></tbody>
        </table>
      </div>
    </div>
  </section>

  <footer>
    <p>
      Cross-Experiment Integration Pipeline &middot; Compiled from <code>build_correlations.py</code> &middot; KAC Cohort &middot; Water Maze Day 6 Checking Tests &times; EPM &times; Open Field &times; NOR (Feb 2026) &times; KAOFam (Nov 2025).
    </p>
    <p style="margin-top:8px">
      Return to <a href="../dlc_cleaned/dashboard.html">Platform Checking Dashboard</a> or explore the <a href="../dlc_cleaned/site/index.html">Behavior Atlas</a>.
    </p>
  </footer>

</div>

<script>
// Theme Switcher Logic
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const target = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', target);
  localStorage.setItem('neuro_theme', target);
  updateThemeIcon(target);
}
function updateThemeIcon(theme) {
  document.getElementById('themeIcon').textContent = theme === 'dark' ? '🌙' : '☀️';
}
(function() {
  const saved = localStorage.getItem('neuro_theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
  }
})();
</script>
"""

final_html = new_head_and_body + script_content
html_file.write_text(final_html, encoding="utf-8")
print(f"Updated {html_file} ({len(final_html)} bytes)")
