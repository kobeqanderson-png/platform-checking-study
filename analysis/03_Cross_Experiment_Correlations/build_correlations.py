"""
build_correlations.py
Cross-experiment correlation analysis: Water maze × EPM, Open Field, NOR/Object Location
KAC cohort, rats 1-32 (1-16 Male, 17-32 Female)

Data sources:
  - Water maze: analysis/dlc_cleaned/results/per_rat_measures.csv (kac_d6)
  - Latency: analysis/updated_anymaze/analysis/results/rat_day_means.csv
  - Probe: analysis/updated_anymaze/analysis/results/probe_by_rat.csv
  - EPM: media_1794191505579_1e82d798.xlsx (analysis sheet, 15 cols)
  - Open Field: media_1794191505578_89bf44ab.xlsx (ofpen raw(in) sheet)
  - NOR (Feb 2026 cohort): media_1794191505574_739a02ce.xlsx (raw sheet)
  - KAOFam (Nov 2025 OF/NOR): media_1794191505578_aae7b18b.xlsx (KAOFam sheet)

Outputs:
  results/merged_per_rat.csv
  results/cross_experiment_correlations.csv
  figures/corr_heatmap.png  (+ _male.png, _female.png)
  figures/scatter_*.png
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── paths ────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE, "results")
FIGURES_DIR = os.path.join(BASE, "figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

ANALYSIS_ROOT = os.path.join(BASE, "..")
DLC_RESULTS   = os.path.join(ANALYSIS_ROOT, "dlc_cleaned", "results")
ANYMAZE       = os.path.join(ANALYSIS_ROOT, "updated_anymaze", "analysis", "results")
UPLOADED      = r"C:\Users\kobeq\.gemini\antigravity\brain\cf6ca52b-0db8-4d61-b4b8-30feb15441ad\.user_uploaded"

NOR_FILE    = os.path.join(UPLOADED, "media_1794191505574_739a02ce.xlsx")
KAOFAM_FILE = os.path.join(UPLOADED, "media_1794191505578_aae7b18b.xlsx")
OF_FILE     = os.path.join(UPLOADED, "media_1794191505578_89bf44ab.xlsx")
EPM_FILE    = os.path.join(UPLOADED, "media_1794191505579_1e82d798.xlsx")

SEX_MAP = {r: "M" if r <= 16 else "F" for r in range(1, 33)}


def _safe_float(val):
    try:
        f = float(val)
        return f if np.isfinite(f) else np.nan
    except Exception:
        return np.nan


# ── 1. Water maze per-rat measures (kac_d6) ──────────────────────────────────
print("Loading water maze per-rat measures…")
wm = pd.read_csv(os.path.join(DLC_RESULTS, "per_rat_measures.csv"))
wm_d6 = wm[wm["cond"] == "kac_d6"].copy()
wm_d6["rat"] = wm_d6["rat"].astype(int)
wm_cols = [
    "rat", "sex",
    "platform_lower_pct", "departures_observed",
    "head_turn_pre_deg_s", "head_sweeps_per_min", "vte_episodes_per_min",
    "distance_observed_cm", "speed_observed_cm_s",
]
wm_d6 = wm_d6[[c for c in wm_cols if c in wm_d6.columns]].copy()
wm_d6 = wm_d6.rename(columns={"sex": "sex_wm"})
print(f"  Water maze d6: {len(wm_d6)} rows, rats: {sorted(wm_d6['rat'].tolist())}")

# ── 2. Water maze latency (days 1-5) ─────────────────────────────────────────
print("Loading latency data…")
lat_path = os.path.join(ANYMAZE, "rat_day_means.csv")
if os.path.exists(lat_path):
    lat = pd.read_csv(lat_path)
    lat5 = lat[lat["day"] <= 5]
    mean_lat = lat5.groupby("rat")["lat"].mean().reset_index()
    mean_lat.columns = ["rat", "mean_latency_d1_5"]
    mean_lat["rat"] = mean_lat["rat"].astype(int)
    print(f"  Latency: {len(mean_lat)} rats")
else:
    print("  latency file not found, skipping")
    mean_lat = pd.DataFrame(columns=["rat", "mean_latency_d1_5"])

# ── 3. Probe data ─────────────────────────────────────────────────────────────
print("Loading probe data…")
probe_path = os.path.join(ANYMAZE, "probe_by_rat.csv")
probe_d6 = None
if os.path.exists(probe_path):
    probe = pd.read_csv(probe_path)
    p6 = probe[probe["day"] == 6].copy()
    if len(p6) >= 5:
        p6 = p6[["rat", "pct", "dist"]].rename(
            columns={"pct": "probe_pct_on_platform", "dist": "probe_dist_cm"}
        )
        p6["rat"] = p6["rat"].astype(int)
        probe_d6 = p6
        print(f"  Probe d6: {len(probe_d6)} rats")
    else:
        print("  Probe d6 insufficient data, skipping")
else:
    print("  probe_by_rat.csv not found, skipping")

# ── 4. EPM data ───────────────────────────────────────────────────────────────
print("Loading EPM data (1e82d798)…")
"""
EPM analysis sheet structure (0-indexed rows):
  Row 0: zone group headers ("Closed Arm Zone (CAZ)", "Open Arm Zone (OAZ)", "Center", "Ratio Time")
  Row 1: Males section col headers ("Males", "CAZ : entries", "CAZ : time (s)", ...)
  Rows 2..17: Male data (animal_id in col 0)
  Rows 18-20: Mean/SEM/blank
  Row 21: Females zone group headers
  Row 22: Females col headers ("Females", ...)
  Rows 23..37: Female data
  Rows 38+: Mean/SEM/t-test

Columns (0-indexed):
  0  = animal_id
  1  = CAZ_entries
  2  = CAZ_time_s
  3  = CAZ_distance_m
  4  = NaN
  5  = OAZ_entries
  6  = OAZ_time_s
  7  = OAZ_distance_m
  8  = NaN
  9  = Center_entries
  13 = RatioTime
"""
epm_raw = pd.read_excel(EPM_FILE, sheet_name="analysis", header=None)
epm_records = []
sex = None
for idx, row in epm_raw.iterrows():
    v0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
    v0_lo = v0.lower()
    # detect sex section
    if v0_lo in ("males", "male"):
        sex = "M"; continue
    if v0_lo in ("females", "female"):
        sex = "F"; continue
    # skip non-data rows
    skip_vals = {"sex", "mean", "sem", "nan", "", "ttest", "closed arm zone (caz)", "open arm zone (oaz)"}
    if v0_lo in skip_vals or v0_lo.startswith("closed") or v0_lo.startswith("open arm"):
        continue
    try:
        rat_id = int(float(v0))
    except (ValueError, TypeError):
        continue
    if sex is None:
        sex = "M" if rat_id <= 16 else "F"
    # col 13 = RatioTime (OAZ_time / (CAZ_time + OAZ_time + Center_time))
    # Note: col 14 is 'Mex' (some multiplier), not ratio time for some rows
    epm_records.append({
        "rat":              rat_id,
        "sex_epm":          sex if sex else ("M" if rat_id <= 16 else "F"),
        "epm_caz_entries":  _safe_float(row.iloc[1]),
        "epm_caz_time_s":   _safe_float(row.iloc[2]),
        "epm_caz_dist_m":   _safe_float(row.iloc[3]),
        "epm_oaz_entries":  _safe_float(row.iloc[5]),
        "epm_oaz_time_s":   _safe_float(row.iloc[6]),
        "epm_oaz_dist_m":   _safe_float(row.iloc[7]),
        "epm_center_entries": _safe_float(row.iloc[9]),
        "epm_ratio_time":   _safe_float(row.iloc[13]),
    })

epm_df = pd.DataFrame(epm_records)
print(f"  EPM: {len(epm_df)} rats  |  cols: {[c for c in epm_df.columns if c != 'rat']}")
print(f"  EPM sample:\n{epm_df.head(5)[['rat','sex_epm','epm_oaz_time_s','epm_ratio_time']].to_string()}")

# ── 5. Open Field data ────────────────────────────────────────────────────────
print("\nLoading Open Field data (89bf44ab)…")
"""
ofpen raw(in) sheet:
  Row 0 = headers, rows 1+ = data
  Col 1  = Animal (rat_id)
  Col 3  = Distance (m)
  Col 8  = Mean speed (m/s)
  Col 23 = WZ : entries
  Col 26 = WZ : time (s)
  Col 121 = CZ : entries
  Col 124 = CZ : time (s)
"""
of_raw = pd.read_excel(OF_FILE, sheet_name="ofpen raw(in)", header=None)
of_records = []
for idx, row in of_raw.iloc[1:].iterrows():
    try:
        rat_id = int(float(row.iloc[1]))
    except (ValueError, TypeError):
        continue
    of_records.append({
        "rat":              rat_id,
        "of_distance_m":    _safe_float(row.iloc[3]),
        "of_mean_speed_ms": _safe_float(row.iloc[8]),
        "of_wz_entries":    _safe_float(row.iloc[23]),
        "of_wz_time_s":     _safe_float(row.iloc[26]),
        "of_cz_entries":    _safe_float(row.iloc[121]),
        "of_cz_time_s":     _safe_float(row.iloc[124]),
    })
of_df = pd.DataFrame(of_records)
print(f"  Open Field: {len(of_df)} rats")

# ── 6. NOR / Object Location (Feb 2026 main cohort) ──────────────────────────
print("Loading NOR data (739a02ce, Feb 2026)…")
"""
raw sheet:
  Row 0 = headers, rows 1+ = data
  Col 1  = Animal (rat_id)
  Col 5  = Distance (cm)
  Col 10 = Mean speed (cm/s)
  Col 25 = Object Location : number investigations
  Col 26 = Object Location : time investigating (s)
  Col 34 = Object Location : latency to investigation (s)
  Col 44 = Object Area : time (s)
"""
nor_raw = pd.read_excel(NOR_FILE, sheet_name="raw", header=None)
nor_records = []
for idx, row in nor_raw.iloc[1:].iterrows():
    try:
        rat_id = int(float(row.iloc[1]))
    except (ValueError, TypeError):
        continue
    nor_records.append({
        "rat":                       rat_id,
        "nor_total_distance_cm":     _safe_float(row.iloc[5]),
        "nor_mean_speed_cms":        _safe_float(row.iloc[10]),
        "nor_obj_loc_n_invest":      _safe_float(row.iloc[25]),
        "nor_obj_loc_time_invest_s": _safe_float(row.iloc[26]),
        "nor_obj_loc_latency_s":     _safe_float(row.iloc[34]),
        "nor_obj_area_time_s":       _safe_float(row.iloc[44]),
    })
nor_df = pd.DataFrame(nor_records)
print(f"  NOR: {len(nor_df)} rats")

# ── 7. KAOFam (Nov 2025 OF/NOR session) ──────────────────────────────────────
print("Loading KAOFam data (aae7b18b, Nov 2025)…")
"""
KAOFam sheet (same column structure as NOR raw):
  Col 2  = Animal (rat_id), Col 1 = Test (anymaze test order)
  Col 5  = Distance (cm)
  Col 10 = Mean speed (cm/s)
  Col 25 = Object Location : number investigations
  Col 26 = Object Location : time investigating (s)
  Col 34 = Object Location : latency to investigation (s)
  Col 44 = Object Area : time (s)
"""
kaofam_raw = pd.read_excel(KAOFAM_FILE, sheet_name="KAOFam", header=None)
kaofam_records = []
for idx, row in kaofam_raw.iloc[1:].iterrows():
    try:
        rat_id = int(float(row.iloc[2]))
    except (ValueError, TypeError):
        continue
    kaofam_records.append({
        "rat":                            rat_id,
        "kaofam_total_distance_cm":       _safe_float(row.iloc[5]),
        "kaofam_mean_speed_cms":          _safe_float(row.iloc[10]),
        "kaofam_obj_loc_n_invest":        _safe_float(row.iloc[25]),
        "kaofam_obj_loc_time_invest_s":   _safe_float(row.iloc[26]),
        "kaofam_obj_loc_latency_s":       _safe_float(row.iloc[34]),
        "kaofam_obj_area_time_s":         _safe_float(row.iloc[44]),
    })
kaofam_df = pd.DataFrame(kaofam_records)
print(f"  KAOFam: {len(kaofam_df)} rats")

# ── 8. Merge everything ───────────────────────────────────────────────────────
print("\nMerging all data sources…")
merged = wm_d6.copy()
merged = merged.merge(mean_lat, on="rat", how="left")
if probe_d6 is not None:
    merged = merged.merge(probe_d6, on="rat", how="left")
merged = merged.merge(epm_df.drop(columns=["sex_epm"], errors="ignore"), on="rat", how="left")
merged = merged.merge(of_df, on="rat", how="left")
merged = merged.merge(nor_df, on="rat", how="left")
merged = merged.merge(kaofam_df, on="rat", how="left")

# harmonise sex
if "sex_wm" in merged.columns:
    merged["sex"] = merged["sex_wm"].map({"M": "M", "F": "F"}).fillna(
        merged["rat"].map(SEX_MAP)
    )
else:
    merged["sex"] = merged["rat"].map(SEX_MAP)

print(f"  Merged table: {merged.shape[0]} rats × {merged.shape[1]} columns")
print(f"  Rats in merged: {sorted(merged['rat'].tolist())}")
merged.to_csv(os.path.join(RESULTS_DIR, "merged_per_rat.csv"), index=False)
print(f"  Saved merged_per_rat.csv")

# ── 9. Correlation analysis ───────────────────────────────────────────────────
print("\nComputing Spearman correlations…")

WM_MEASURES = [
    "platform_lower_pct",
    "departures_observed",
    "head_turn_pre_deg_s",
    "head_sweeps_per_min",
    "vte_episodes_per_min",
    "mean_latency_d1_5",
]
if probe_d6 is not None:
    WM_MEASURES.append("probe_pct_on_platform")

BEHAVIORAL_MEASURES = [
    # EPM
    "epm_oaz_time_s", "epm_ratio_time", "epm_oaz_entries",
    "epm_caz_time_s", "epm_center_entries",
    # Open Field
    "of_distance_m", "of_mean_speed_ms", "of_cz_time_s", "of_wz_time_s",
    "of_cz_entries",
    # NOR (Feb 2026)
    "nor_obj_loc_n_invest", "nor_obj_loc_time_invest_s",
    "nor_obj_loc_latency_s", "nor_obj_area_time_s",
    "nor_total_distance_cm",
    # KAOFam (Nov 2025)
    "kaofam_obj_loc_n_invest", "kaofam_obj_loc_time_invest_s",
    "kaofam_obj_loc_latency_s", "kaofam_obj_area_time_s",
    "kaofam_total_distance_cm",
]

WM_MEASURES        = [c for c in WM_MEASURES        if c in merged.columns]
BEHAVIORAL_MEASURES = [c for c in BEHAVIORAL_MEASURES if c in merged.columns]

corr_rows = []
for grp_label, subset in [("All",    merged),
                           ("Male",   merged[merged["sex"] == "M"]),
                           ("Female", merged[merged["sex"] == "F"])]:
    for bm in BEHAVIORAL_MEASURES:
        for wm_col in WM_MEASURES:
            pair = subset[[bm, wm_col]].dropna()
            if len(pair) < 5:
                continue
            r, p = stats.spearmanr(pair[bm], pair[wm_col])
            corr_rows.append({
                "group":       grp_label,
                "beh_measure": bm,
                "wm_measure":  wm_col,
                "n":           len(pair),
                "spearman_r":  round(r, 4),
                "p_value":     round(p, 5),
                "sig":         "**" if p < 0.01 else ("*" if p < 0.05 else ("†" if p < 0.1 else "")),
            })

corr_df = pd.DataFrame(corr_rows)
corr_df.to_csv(os.path.join(RESULTS_DIR, "cross_experiment_correlations.csv"), index=False)
print(f"  Saved cross_experiment_correlations.csv ({len(corr_df)} correlations)")

# Top 5 significant (All group, sorted by |r|)
sig_all = corr_df[(corr_df["group"] == "All") & (corr_df["p_value"] < 0.05)]
top5 = (sig_all.assign(abs_r=lambda x: x["spearman_r"].abs())
        .sort_values("abs_r", ascending=False)
        .head(5))
print(f"\nSignificant correlations (All animals, p<0.05): {len(sig_all)}")
print("Top 5:")
for _, row in top5.iterrows():
    print(f"  {row['beh_measure']} × {row['wm_measure']}: r={row['spearman_r']:.3f}, p={row['p_value']:.4f} {row['sig']}")

# ── 10. Heatmap figures ───────────────────────────────────────────────────────
BEH_LABELS = {
    "epm_oaz_time_s":           "EPM: Open arm time (s)",
    "epm_ratio_time":           "EPM: OAZ ratio time",
    "epm_oaz_entries":          "EPM: Open arm entries",
    "epm_caz_time_s":           "EPM: Closed arm time (s)",
    "epm_center_entries":       "EPM: Center entries",
    "of_distance_m":            "OF: Total distance (m)",
    "of_mean_speed_ms":         "OF: Mean speed (m/s)",
    "of_cz_time_s":             "OF: Center time (s)",
    "of_wz_time_s":             "OF: Wall time (s)",
    "of_cz_entries":            "OF: Center entries",
    "nor_obj_loc_n_invest":     "NOR-Feb: # investigations",
    "nor_obj_loc_time_invest_s":"NOR-Feb: Invest. time (s)",
    "nor_obj_loc_latency_s":    "NOR-Feb: Latency (s)",
    "nor_obj_area_time_s":      "NOR-Feb: Obj area time (s)",
    "nor_total_distance_cm":    "NOR-Feb: Distance (cm)",
    "kaofam_obj_loc_n_invest":  "KAOFam: # investigations",
    "kaofam_obj_loc_time_invest_s":"KAOFam: Invest. time (s)",
    "kaofam_obj_loc_latency_s": "KAOFam: Latency (s)",
    "kaofam_obj_area_time_s":   "KAOFam: Obj area time (s)",
    "kaofam_total_distance_cm": "KAOFam: Distance (cm)",
}
WM_LABELS = {
    "platform_lower_pct":     "% Platform\ntime",
    "departures_observed":    "Departures",
    "head_turn_pre_deg_s":    "Head turn\n(°/s)",
    "head_sweeps_per_min":    "Head sweeps\n/min",
    "vte_episodes_per_min":   "VTE/min",
    "mean_latency_d1_5":      "Latency\n(d1-5)",
    "probe_pct_on_platform":  "Probe %",
}


def make_heatmap(subset_df, grp_label, beh_measures, wm_measures):
    present_beh = [b for b in beh_measures if b in subset_df.columns]
    present_wm  = [w for w in wm_measures  if w in subset_df.columns]

    r_mat = pd.DataFrame(index=present_beh, columns=present_wm, dtype=float)
    p_mat = pd.DataFrame(index=present_beh, columns=present_wm, dtype=float)

    for bm in present_beh:
        for wm_col in present_wm:
            pair = subset_df[[bm, wm_col]].dropna()
            if len(pair) < 5:
                r_mat.loc[bm, wm_col] = np.nan
                p_mat.loc[bm, wm_col] = np.nan
            else:
                r, p = stats.spearmanr(pair[bm], pair[wm_col])
                r_mat.loc[bm, wm_col] = r
                p_mat.loc[bm, wm_col] = p

    r_mat.index   = [BEH_LABELS.get(i, i) for i in r_mat.index]
    p_mat.index   = r_mat.index
    r_mat.columns = [WM_LABELS.get(c, c) for c in r_mat.columns]
    p_mat.columns = r_mat.columns

    n_rows = len(r_mat)
    n_cols = len(r_mat.columns)
    fig_h = max(7, n_rows * 0.44 + 2.5)
    fig_w = max(8, n_cols * 1.6 + 3.5)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    sns.heatmap(
        r_mat.astype(float), ax=ax,
        cmap=cmap, center=0, vmin=-1, vmax=1,
        linewidths=0.4, linecolor="#cccccc",
        cbar_kws={"label": "Spearman r", "shrink": 0.75},
        annot=False,
    )
    for ri, bm in enumerate(r_mat.index):
        for ci, wm_col in enumerate(r_mat.columns):
            r_val = r_mat.iloc[ri, ci]
            p_val = p_mat.iloc[ri, ci]
            if pd.isna(r_val):
                continue
            sig_str = "**" if p_val < 0.01 else ("*" if p_val < 0.05 else ("†" if p_val < 0.1 else ""))
            txt  = f"{r_val:.2f}{sig_str}"
            fc   = "white" if abs(r_val) > 0.42 else "black"
            bold = "bold" if sig_str else "normal"
            ax.text(ci + 0.5, ri + 0.5, txt, ha="center", va="center",
                    fontsize=7.5, color=fc, fontweight=bold)

    ax.set_title(
        f"Cross-experiment Spearman correlations — {grp_label}  (n ≈ {len(subset_df)})\n"
        "* p<0.05  ** p<0.01  † p<0.10",
        fontsize=11, pad=10,
    )
    ax.set_xlabel("Water maze measures", fontsize=10)
    ax.set_ylabel("Anxiety & exploration measures", fontsize=10)
    ax.tick_params(axis="x", labelrotation=25, labelsize=8.5)
    ax.tick_params(axis="y", labelrotation=0,  labelsize=8.0)
    plt.tight_layout()

    out = os.path.join(FIGURES_DIR, f"corr_heatmap_{grp_label.lower()}.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {os.path.basename(out)}")
    return r_mat, p_mat


print("\nGenerating heatmaps…")
make_heatmap(merged,                      "All",    BEHAVIORAL_MEASURES, WM_MEASURES)
make_heatmap(merged[merged["sex"] == "M"],"Male",   BEHAVIORAL_MEASURES, WM_MEASURES)
make_heatmap(merged[merged["sex"] == "F"],"Female", BEHAVIORAL_MEASURES, WM_MEASURES)

import shutil
shutil.copy(os.path.join(FIGURES_DIR, "corr_heatmap_all.png"),
            os.path.join(FIGURES_DIR, "corr_heatmap.png"))
print("  Saved corr_heatmap.png (copy of All heatmap)")

# ── 11. Scatter plots ─────────────────────────────────────────────────────────
print("\nGenerating scatter plots…")

SCATTER_PAIRS = [
    ("platform_lower_pct",   "epm_ratio_time",             "% Platform time",        "EPM OAZ ratio time"),
    ("platform_lower_pct",   "of_distance_m",              "% Platform time",        "OF total distance (m)"),
    ("departures_observed",  "epm_ratio_time",             "Departures observed",    "EPM OAZ ratio time"),
    ("departures_observed",  "epm_oaz_time_s",             "Departures observed",    "EPM open arm time (s)"),
    ("departures_observed",  "of_distance_m",              "Departures observed",    "OF total distance (m)"),
    ("head_turn_pre_deg_s",  "epm_oaz_time_s",             "Head-turn speed (°/s)",  "EPM open arm time (s)"),
    ("head_turn_pre_deg_s",  "of_distance_m",              "Head-turn speed (°/s)",  "OF total distance (m)"),
    ("vte_episodes_per_min", "nor_obj_loc_time_invest_s",  "VTE/min",                "NOR invest. time (s)"),
    ("head_sweeps_per_min",  "nor_obj_loc_n_invest",       "Head sweeps/min",        "NOR # investigations"),
    ("mean_latency_d1_5",    "epm_ratio_time",             "Mean escape latency (s)","EPM OAZ ratio time"),
    ("platform_lower_pct",   "nor_obj_area_time_s",        "% Platform time",        "NOR obj area time (s)"),
    ("departures_observed",  "kaofam_obj_loc_time_invest_s","Departures observed",   "KAOFam invest. time (s)"),
]

SEX_COLORS = {"M": "#d9591f", "F": "#2a78d6"}

saved_scatters = []
for wm_col, bm_col, wm_lbl, bm_lbl in SCATTER_PAIRS:
    if wm_col not in merged.columns or bm_col not in merged.columns:
        print(f"  Skip {wm_col} × {bm_col} (missing)")
        continue
    pair = merged[[wm_col, bm_col, "sex", "rat"]].dropna()
    if len(pair) < 5:
        print(f"  Skip {wm_col} × {bm_col} (n={len(pair)} < 5)")
        continue

    r_val, p_val = stats.spearmanr(pair[wm_col], pair[bm_col])

    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    for sx, grp in pair.groupby("sex"):
        c = SEX_COLORS.get(sx, "#888")
        ax.scatter(grp[wm_col], grp[bm_col], c=c, s=52, alpha=0.78,
                   edgecolors="white", linewidths=0.5,
                   label="Male" if sx == "M" else "Female")
        for _, rw in grp.iterrows():
            ax.annotate(str(int(rw["rat"])), (rw[wm_col], rw[bm_col]),
                        fontsize=5.5, alpha=0.65, ha="center", va="bottom",
                        xytext=(0, 2), textcoords="offset points")

    # OLS line (all animals together)
    xs_all = pair[wm_col].astype(float)
    ys_all = pair[bm_col].astype(float)
    m, b, *_ = stats.linregress(xs_all, ys_all)
    xs = np.linspace(xs_all.min(), xs_all.max(), 100)
    ax.plot(xs, m * xs + b, color="#0f6b74", lw=1.5, alpha=0.7, linestyle="--")

    sig_str = "**" if p_val < 0.01 else ("*" if p_val < 0.05 else ("†" if p_val < 0.1 else "ns"))
    ax.set_title(f"Spearman r = {r_val:.3f},  p = {p_val:.4f} {sig_str}  (n={len(pair)})",
                 fontsize=9.5)
    ax.set_xlabel(wm_lbl, fontsize=10)
    ax.set_ylabel(bm_lbl, fontsize=10)
    patches = [mpatches.Patch(color=SEX_COLORS["M"], label="Male"),
               mpatches.Patch(color=SEX_COLORS["F"], label="Female")]
    ax.legend(handles=patches, fontsize=8, framealpha=0.7)
    plt.tight_layout()

    safe_name = f"{wm_col}_x_{bm_col}".replace("/", "_")[:70]
    out = os.path.join(FIGURES_DIR, f"scatter_{safe_name}.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  scatter_{safe_name}.png  r={r_val:.3f} p={p_val:.4f} {sig_str}")
    saved_scatters.append(os.path.basename(out))

# ── 12. Summary printout ──────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
sig_all = corr_df[(corr_df["group"] == "All") & (corr_df["p_value"] < 0.05)]
print(f"Significant correlations (All group, p<0.05): {len(sig_all)}")
top_all = (sig_all.assign(abs_r=lambda x: x["spearman_r"].abs())
           .sort_values("abs_r", ascending=False))
print(top_all[["beh_measure", "wm_measure", "n", "spearman_r", "p_value", "sig"]]
      .to_string(index=False))

print(f"\nOutputs:")
print(f"  {os.path.join(RESULTS_DIR, 'merged_per_rat.csv')}")
print(f"  {os.path.join(RESULTS_DIR, 'cross_experiment_correlations.csv')}")
print(f"  {FIGURES_DIR}/corr_heatmap*.png")
print(f"  {FIGURES_DIR}/scatter_*.png")
print("Done.")
