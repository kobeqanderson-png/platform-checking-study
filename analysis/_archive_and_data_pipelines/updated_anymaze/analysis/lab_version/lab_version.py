"""Lab-meeting version: classic bar graphs, scatter plots, t-tests, two-way ANOVA and Fisher's exact test, plus an Excel workbook whose
means, SEMs and t-tests are live Excel formulas. Reads the per-rat tables made by ../analysis.py (training days) and the DLC
checking-test measures in dlc_measures (KAC Day 6 and Day 8 from the final v3rot model; SP1).
Usage: python lab_version.py <analysis results folder> <dlc_measures folder>"""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import BarChart, ScatterChart, Reference, Series
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.data_source import NumDataSource, NumRef
from openpyxl.chart.marker import Marker
from openpyxl.utils import get_column_letter as COL
RES, DLC = sys.argv[1:]; HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
RD = pd.read_csv(os.path.join(RES, 'rat_day_means.csv')); PB = pd.read_csv(os.path.join(RES, 'probe_by_rat.csv')); D8 = pd.read_csv(os.path.join(DLC, 'kac_d8_dlc_measures.csv')); D6 = pd.read_csv(os.path.join(DLC, 'kac_d6_dlc_measures.csv')); NV6 = pd.read_csv(os.path.join(DLC, 'kac_d6_notes_vs_dlc.csv')).rename(columns={'departures': 'dlc_departures', 'first_departure_s': 'dlc_first_departure_s'}); NV = pd.read_csv(os.path.join(DLC, 'kac_d8_notes_vs_dlc.csv')).rename(columns={'departures': 'dlc_departures', 'first_departure_s': 'dlc_first_departure_s'})
SEXES = ['Female', 'Male']; rats = RD.drop_duplicates('rat')[['rat', 'sex', 'batch']].assign(o=lambda x: x.sex.map({'Female': 0, 'Male': 1})).sort_values(['o', 'rat']).drop(columns='o').reset_index(drop=True)
W = lambda col: RD.pivot(index='rat', columns='day', values=col).reindex(rats.rat)
LAT, SPD = W('lat'), W('speed'); P6A = PB[PB.day == 6].set_index('rat').reindex(rats.rat); P8A = PB[PB.day == 8].set_index('rat').reindex(rats.rat); DL = D8.set_index('rat').reindex(rats.rat); DL6 = D6.set_index('rat').reindex(rats.rat)
# Checking tests use DLC video tracking (final model v3rot) for both days, as SP1 does. AnyMaze (P6A, P8A) is kept only as a cross-check. Rat 1 has no Day 6 clip.
mk = lambda d: pd.DataFrame({'pct': d.pct_time_on_platform_zone, 'stayed': d.departures.eq(0).where(d.departures.notna())})  # stayed = never left (0 departures), as in the notes
P6, P8 = mk(DL6), mk(DL)
assert DL.index.isin(D8.rat).all() and len(rats) == 30
F, M = (rats.sex == 'Female').values, (rats.sex == 'Male').values

# ---------- statistics (the same tests the workbook formulas reproduce, plus ANOVA and Fisher) ----------
def mixed_anova(Y, g):
    """Two-way mixed ANOVA: day (within) x sex (between), subjects nested in sex, Greenhouse-Geisser correction for the within terms."""
    n, k = Y.shape; GM = Y.mean(); ms = Y.mean(axis=1); md = Y.mean(0); out = {}
    ss_sex = k * sum((g == s).sum() * (Y[g == s].mean() - GM) ** 2 for s in np.unique(g)); ss_bs = k * ((ms - GM) ** 2).sum(); ss_sub = ss_bs - ss_sex
    ss_day = n * ((md - GM) ** 2).sum(); ss_int = sum((g == s).sum() * ((Y[g == s].mean(0) - Y[g == s].mean() - md + GM) ** 2).sum() for s in np.unique(g))
    ss_ws = ((Y - ms[:, None]) ** 2).sum(); ss_err = ss_ws - ss_day - ss_int; df_sub, df_err = n - 2, (k - 1) * (n - 2)
    R = np.vstack([Y[g == s] - Y[g == s].mean(0) for s in np.unique(g)]); S = R.T @ R / (n - 2); C = np.eye(k) - 1 / k; D = C @ S @ C; eps = np.trace(D) ** 2 / ((k - 1) * (D ** 2).sum())
    for name, ss, df, err, dfe, gg in (('Sex', ss_sex, 1, ss_sub, df_sub, 1), ('Day', ss_day, k - 1, ss_err, df_err, eps), ('Day x Sex', ss_int, k - 1, ss_err, df_err, eps)):
        Fv = (ss / df) / (err / dfe); out[name] = dict(F=Fv, df1=df * gg, df2=dfe * gg, p=stats.f.sf(Fv, df * gg, dfe * gg), eta_p2=ss / (ss + err))
    return out, eps
AN, EPS = mixed_anova(LAT[[1, 2, 3, 4, 5]].values, rats.sex.values); ANS, EPS_S = mixed_anova(SPD[[1, 2, 3, 4, 5]].values, rats.sex.values)
tt = lambda a, b: stats.ttest_ind(a, b, nan_policy='omit')   # Student t, equal variances: matches Excel TTEST(...,2,2)
T = {}
T['speed'] = tt(SPD[[1, 2, 3, 4, 5]].mean(axis=1)[F], SPD[[1, 2, 3, 4, 5]].mean(axis=1)[M]); T['rem'] = stats.ttest_rel(LAT[7], LAT[5])
T['p6'] = tt(P6.pct[F], P6.pct[M]); T['p8'] = tt(P8.pct[F], P8.pct[M]); T['dep'] = tt(DL.departures[F], DL.departures[M]); T['wall'] = tt(DL.pct_time_at_wall[F], DL.pct_time_at_wall[M]); T['dep6'] = tt(DL6.departures[F], DL6.departures[M]); T['wall6'] = tt(DL6.pct_time_at_wall[F], DL6.pct_time_at_wall[M])
st = lambda P, k: P.stayed[k].dropna().astype(bool)   # stayed yes/no for rats that were tested
fisher = lambda P: stats.fisher_exact([[int(st(P, F).sum()), int((~st(P, F)).sum())], [int(st(P, M).sum()), int((~st(P, M)).sum())]])
FS = lambda P: f"{int(st(P, M).sum())}/{len(st(P, M))} males vs {int(st(P, F).sum())}/{len(st(P, F))} females"
FI6, FI8 = fisher(P6), fisher(P8)

# ---------- SP1 cohort (separate study, checking test at raised water only, no standard-depth control) ----------
# Rat = AnyMaze "animal" column (tests 9-16 are rats 17-24 and tests 17-24 are rats 9-16). Sex from Documents/2025/data/Rat weights 12-30-24.xlsx
# (rats 1-16 male, 17-32 female), confirmed by the experimenter. No SP1 deaths or exclusions in SP1.xlsx (all 32 rats on days 1-6). Platform time, departures, wall from DLC; distance from AnyMaze
# (AnyMaze's platform zone logs false exits for rats sitting still, so its platform time is not used).
S1 = pd.read_csv(os.path.join(DLC, 'sp1_checking_dlc_vs_anymaze.csv')); S1['rat'] = S1.animal.str.extract(r'(\d+)', expand=False).astype(int)
S1['sex'] = np.where(S1.rat <= 16, 'Male', 'Female'); S1 = S1.assign(o=(S1.sex == 'Male').astype(int)).sort_values(['o', 'rat']).reset_index(drop=True)
S1['stayed'] = S1.departures == 0; SF, SM = (S1.sex == 'Female').values, (S1.sex == 'Male').values
TS = {c: tt(S1[c][SF], S1[c][SM]) for c in ('pct_time_on_platform_zone', 'departures', 'pct_time_at_wall', 'anymaze_distance_cm')}
FIS = stats.fisher_exact([[S1.stayed[SM].sum(), (~S1.stayed[SM]).sum()], [S1.stayed[SF].sum(), (~S1.stayed[SF]).sum()]])
BOTH = (P6.pct.notna() & P8.pct.notna()).values; R68 = stats.pearsonr(P6.pct[BOTH], P8.pct[BOTH]); WT = {'all': stats.ttest_rel(P8.pct[BOTH].values, P6.pct[BOTH].values), 'F': stats.ttest_rel(P8.pct[F & BOTH].values, P6.pct[F & BOTH].values), 'M': stats.ttest_rel(P8.pct[M & BOTH].values, P6.pct[M & BOTH].values)}; MW = {k: stats.mannwhitneyu(a[F], a[M], nan_policy='omit').pvalue for k, a in (('p6', P6.pct), ('p8', P8.pct), ('dep', DL.departures), ('wall', DL.pct_time_at_wall))}
v = NV.dropna(subset=['notes_first_departure_s', 'dlc_first_departure_s']); RV = stats.pearsonr(v.notes_first_departure_s, v.dlc_first_departure_s)
agree = lambda d: f"{int((d.notes_stayed_on.notna() & (d.notes_stayed_on == d.dlc_stayed_on)).sum())} of {int(d.notes_stayed_on.notna().sum())}"; AG6, AG8 = agree(NV6), agree(NV)
RAM = stats.pearsonr(P8A.pct, DL.pct_time_in_anymaze_size_P2_zone); DAM = (DL.pct_time_in_anymaze_size_P2_zone - P8A.pct).abs().max()   # Same-size zone, so a like-for-like check of AnyMaze P2 time.
pt = lambda p: 'p < 0.001' if p < .001 else f'p = {p:.3f}'; star = lambda p: '***' if p < .001 else '**' if p < .01 else '*' if p < .05 else 'n.s.'
print('ANOVA latency', {k: (round(x['F'], 2), round(x['df1'], 2), round(x['df2'], 2), round(x['p'], 4)) for k, x in AN.items()}, 'GG eps', round(EPS, 3))
print('ANOVA speed', {k: (round(x['F'], 2), round(x['p'], 4)) for k, x in ANS.items()}); print({k: round(v.pvalue, 4) for k, v in T.items()}, 'Fisher', round(FI6[1], 4), round(FI8[1], 5), 'r68', round(R68[0], 2), 'MW', {k: round(x, 4) for k, x in MW.items()}, 'notes vs DLC r', round(RV[0], 2), len(v))

# ---------- figures: classic bars with SEM, individual rats as dots ----------
C = {'Female': '#2a78d6', 'Male': '#eb6834'}; INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'Arial' if 'Arial' in {f.name for f in matplotlib.font_manager.fontManager.ttflist} else 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK, 'legend.frameon': False, 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'savefig.facecolor': 'white'})
RNG = np.random.default_rng(3); sem = lambda x: np.std(x, ddof=1) / np.sqrt(len(x))
def save(fig, n): fig.savefig(os.path.join(FIG, n), dpi=300, bbox_inches='tight'); plt.close(fig)
def bracket(ax, x1, x2, y, p):
    d = .025 * y   # Bracket height scales with the data, so it sits just above the bars whatever the units.
    ax.plot([x1, x1, x2, x2], [y, y + d, y + d, y], color=INK, lw=1); ax.text((x1 + x2) / 2, y + 1.3 * d, star(p), ha='center', va='bottom', fontsize=11)
def sexbars(ax, values, ylab, title, p=None, top=None):
    ns = []
    for i, s in enumerate(SEXES):
        x = np.asarray(values[F if s == 'Female' else M], float); x = x[~np.isnan(x)]; ns.append(len(x)); ax.bar(i, x.mean(), .62, yerr=sem(x), color=C[s], edgecolor=INK, lw=.8, capsize=6, error_kw=dict(lw=1.2, ecolor=INK))
        ax.scatter(i + RNG.uniform(-.17, .17, len(x)), x, s=16, color='white', edgecolor=INK, lw=.7, zorder=3)
    ax.set_xticks([0, 1]); ax.set_xticklabels([f'Female\n(n = {ns[0]})', f'Male\n(n = {ns[1]})']); ax.set_ylabel(ylab); ax.set_title(title)
    if p is not None: hi = max(np.nanmax(values), 0) * 1.04 if top is None else top; bracket(ax, 0, 1, hi, p); ax.set_ylim(0, hi * 1.13)
L6, L8 = 'Day 6 check: control\n(standard water, 1.5 cm)', 'Day 8 check\n(water raised, 3 cm)'  # Per the experimenter: 1.5 cm is the standard water level, so day 6 is the control; only day 8 is raised. Same rats both days.
fig, ax = plt.subplots(figsize=(7.5, 4.2)); days = [1, 2, 3, 4, 5, 7]; w = .38
for j, s in enumerate(SEXES):
    m = [LAT[d][F if s == 'Female' else M].mean() for d in days]; e = [sem(LAT[d][F if s == 'Female' else M]) for d in days]
    ax.bar(np.arange(len(days)) + (j - .5) * w, m, w, yerr=e, color=C[s], edgecolor=INK, lw=.8, capsize=4, error_kw=dict(lw=1.1, ecolor=INK), label=s)
ax.set_xticks(range(len(days))); ax.set_xticklabels(['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 7\n(reminder)']); ax.set_ylabel('Escape latency (s)'); ax.set_ylim(0, 30); ax.legend(loc='upper right', ncol=2)
ax.set_title('Escape latency fell across training days'); ax.text(0, -.24, f"Two-way ANOVA (days 1-5): Day {pt(AN['Day']['p'])}; Sex {pt(AN['Sex']['p'])}; Day x Sex {pt(AN['Day x Sex']['p'])}.  Mean ± SEM.", transform=ax.transAxes, fontsize=9, color=INK2)
save(fig, '5_latency_by_day.png')
fig, ax = plt.subplots(1, 2, figsize=(7.5, 4.2), sharey=True)
sexbars(ax[0], P6.pct.values, 'Time on platform (% of 120 s)', L6, T['p6'].pvalue, 103); sexbars(ax[1], P8.pct.values, '', L8, T['p8'].pvalue, 103); ax[1].set_ylabel('')
fig.text(.01, -.03, f"Unpaired t-test, females vs males: Day 6 {pt(T['p6'].pvalue)}, Day 8 {pt(T['p8'].pvalue)}.  Mean ± SEM; dots are individual rats.", fontsize=9, color=INK2); fig.tight_layout(); save(fig, '1_checking_time_on_platform.png')
fig, ax = plt.subplots(figsize=(5.5, 4.2)); w = .38
for j, s in enumerate(SEXES):
    k = F if s == 'Female' else M; ys = [100 * st(P6, k).mean(), 100 * st(P8, k).mean()]; b = ax.bar(np.arange(2) + (j - .5) * w, ys, w, color=C[s], edgecolor=INK, lw=.8, label=s)
    for xi, yi, c, nn in zip(np.arange(2) + (j - .5) * w, ys, (st(P6, k).sum(), st(P8, k).sum()), (len(st(P6, k)), len(st(P8, k)))): ax.text(xi, yi + 1.5, f'{int(c)}/{nn}', ha='center', va='bottom', fontsize=10)
ax.set_xticks([0, 1]); ax.set_xticklabels([L6, L8]); ax.set_ylabel('Rats that stayed on the platform (%)'); ax.set_ylim(0, 110); ax.legend(loc='upper left', bbox_to_anchor=(1, 1)); ax.set_title('Most males stayed; most females left')
ax.text(0, -.17, f"Fisher's exact test: Day 6 {pt(FI6[1])}, Day 8 {pt(FI8[1])}.  Stayed = never left the platform (0 departures), as in the handwritten notes.", transform=ax.transAxes, fontsize=9, color=INK2); save(fig, '2_checking_rats_that_stayed.png')
fig, ax = plt.subplots(2, 2, figsize=(7.5, 7.6))
for row, (d, D, kd, kw) in enumerate(((6, DL6, 'dep6', 'wall6'), (8, DL, 'dep', 'wall'))):
    lab = 'Day 6 (control, 1.5 cm)' if d == 6 else 'Day 8 (raised, 3 cm)'
    sexbars(ax[row, 0], D.departures.values, 'Times the rat left the platform', f'{lab}: departures', T[kd].pvalue); sexbars(ax[row, 1], D.pct_time_at_wall.values, 'Time at the pool wall (%)', f'{lab}: wall', T[kw].pvalue)
fig.text(.01, -.03, f"KAC checking tests, DeepLabCut video tracking (final model). Unpaired t-tests. Wall time depends on the tracking model: treat it as provisional.", fontsize=9, color=INK2); fig.tight_layout(); save(fig, '3_checking_departures_and_wall.png')
fig, ax = plt.subplots(figsize=(4.5, 4.2)); sexbars(ax, SPD[[1, 2, 3, 4, 5]].mean(axis=1).values, 'Swim speed (cm/s)', 'Females swam faster', T['speed'].pvalue)
ax.text(0, -.2, f"Average of days 1-5. Unpaired t-test {pt(T['speed'].pvalue)}.", transform=ax.transAxes, fontsize=9, color=INK2); save(fig, '6_swim_speed.png')
fig, ax = plt.subplots(figsize=(4.8, 4.2)); w = .38
for j, s in enumerate(SEXES):
    k = F if s == 'Female' else M; ax.bar(np.arange(2) + (j - .5) * w, [LAT[5][k].mean(), LAT[7][k].mean()], w, yerr=[sem(LAT[5][k]), sem(LAT[7][k])], color=C[s], edgecolor=INK, lw=.8, capsize=5, error_kw=dict(lw=1.1, ecolor=INK), label=s)
ax.set_xticks([0, 1]); ax.set_xticklabels(['Day 5\n(last training)', 'Day 7\n(reminder)']); ax.set_ylabel('Escape latency (s)'); ax.set_ylim(0, 30); ax.legend(loc='upper left', ncol=2); ax.set_title('No forgetting by the reminder day')
ax.text(0, -.22, f"Paired t-test, day 5 vs day 7 (all rats): {pt(T['rem'].pvalue)}.  Mean ± SEM.", transform=ax.transAxes, fontsize=9, color=INK2); save(fig, '7_reminder_day.png')
fig, ax = plt.subplots(1, 2, figsize=(9, 4.2))
for s in SEXES:
    k = F if s == 'Female' else M; ax[0].scatter(P6.pct[k], P8.pct[k], s=40, color=C[s], edgecolor=INK, lw=.6, label=s)
ax[0].plot([0, 100], [0, 100], color=INK2, lw=1, ls='--'); ax[0].set_xlabel('Day 6: time on platform (%)'); ax[0].set_ylabel('Day 8: time on platform (%)'); ax[0].legend(loc='lower right'); ax[0].set_title(f'Same rat, both checking tests (r = {R68[0]:.2f})')
ax[1].scatter(v.notes_first_departure_s, v.dlc_first_departure_s, s=40, color=INK2, edgecolor=INK, lw=.6); lim = [0, max(v.notes_first_departure_s.max(), v.dlc_first_departure_s.max()) + 10]; ax[1].plot(lim, lim, color=INK2, lw=1, ls='--')
ax[1].set_xlabel('First departure, experimenter notes (s)'); ax[1].set_ylabel('First departure, video tracking (s)'); ax[1].set_title(f'Video tracking matches the notes (r = {RV[0]:.3f}, n = {len(v)})'); fig.tight_layout(); save(fig, '4_checking_scatter_plots.png')

fig, ax = plt.subplots(1, 2, figsize=(7.5, 4.2))
for a, col, yl, ttl in ((ax[0], 'pct_time_on_platform_zone', 'Time on platform (% of 120 s)', 'SP1: time on platform'), (ax[1], 'departures', 'Times the rat left the platform', 'SP1: departures')):
    for i, (s, k) in enumerate((('Female', SF), ('Male', SM))):
        x = S1[col][k].to_numpy(float); a.bar(i, x.mean(), .62, yerr=sem(x), color=C[s], edgecolor=INK, lw=.8, capsize=6, error_kw=dict(lw=1.2, ecolor=INK))
        a.scatter(i + RNG.uniform(-.17, .17, len(x)), x, s=16, color='white', edgecolor=INK, lw=.7, zorder=3)
    a.set_xticks([0, 1]); a.set_xticklabels([f'Female\n(n = {SF.sum()})', f'Male\n(n = {SM.sum()})']); a.set_ylabel(yl); a.set_title(ttl)
    hi = 103 if 'pct' in col else S1[col].max() * 1.04; bracket(a, 0, 1, hi, TS[col].pvalue); a.set_ylim(0, hi * 1.13)
fig.text(.01, -.03, f"SP1 cohort, checking test at raised water (no standard-depth control). DeepLabCut tracking. Unpaired t-test: platform {pt(TS['pct_time_on_platform_zone'].pvalue)}, departures {pt(TS['departures'].pvalue)}.\nNever left the platform: {int(S1.stayed[SM].sum())}/{SM.sum()} males vs {int(S1.stayed[SF].sum())}/{SF.sum()} females, Fisher {pt(FIS[1])}.", fontsize=9, color=INK2); fig.tight_layout(); save(fig, '0_sp1_checking.png')

# ---------- Exploratory: VTE-like head scanning (../../../kinematics/checking_kinematics.py) ----------
# Head swings >= 25 or >= 40 degrees, left-right within 2 s, while the rat is still; events per minute of stillness.
# Head angle error vs hand labels on 36 held-out frames: median 5 degrees (kinematics/angle_validation.csv). Not checked against video by eye.
KD = os.path.join(DLC, '..', 'kinematics')
VT = {th: pd.read_csv(os.path.join(KD, 'checking_kinematics.csv' if th == 25 else f'checking_kinematics_swing{th}.csv')) for th in (25, 40)}
VK = {(th, d): VT[th].query("cohort == 'KAC' and day == @d").set_index('rat').vte_events_per_min_still.reindex(rats.rat) for th in (25, 40) for d in (6, 8)}
VS = {th: VT[th].query("cohort == 'SP1'").set_index('rat').vte_events_per_min_still for th in (25, 40)}
VB = {th: (VK[(th, 6)].notna() & VK[(th, 8)].notna()).values for th in (25, 40)}
TV = {th: dict(paired=stats.ttest_rel(VK[(th, 6)][VB[th]], VK[(th, 8)][VB[th]]), wil=stats.wilcoxon(VK[(th, 6)][VB[th]], VK[(th, 8)][VB[th]]).pvalue,
               s6=tt(VK[(th, 6)][F], VK[(th, 6)][M]), s8=tt(VK[(th, 8)][F], VK[(th, 8)][M]),
               sp1=tt(VS[th][VS[th].index > 16], VS[th][VS[th].index <= 16])) for th in (25, 40)}
fig, ax = plt.subplots(1, 2, figsize=(8, 4.2), sharey=False); w = .36
for a, th in zip(ax, (25, 40)):
    for j, s in enumerate(SEXES):
        k = F if s == 'Female' else M; ys = [VK[(th, 6)][k].dropna() for _ in (0,)] + [VK[(th, 8)][k].dropna()]
        a.bar(np.arange(2) + (j - .5) * w, [y.mean() for y in ys], w, yerr=[sem(y) for y in ys], color=C[s], edgecolor=INK, lw=.8, capsize=5, error_kw=dict(lw=1.1, ecolor=INK), label=s)
    a.set_xticks([0, 1]); a.set_xticklabels(['Day 6\ncontrol 1.5 cm', 'Day 8\nraised 3 cm']); a.set_ylabel('Head-scan events per minute still'); a.set_title(f'Head swings >= {th} degrees')
ax[0].legend(loc='upper right'); fig.tight_layout()
cap = [f"{th} deg: day 6 vs day 8, paired t-test {pt(TV[th]['paired'].pvalue)}; females vs males, day 6 {pt(TV[th]['s6'].pvalue)}, day 8 {pt(TV[th]['s8'].pvalue)}." for th in (25, 40)]
cap.append('EXPLORATORY. KAC, DeepLabCut head angle (median error 5 degrees vs hand labels). Test order is fixed and day 6 used a different camera,')
cap.append('so day 6 vs day 8 is not a pure water-depth effect.')
fig.text(.01, -.01, '\n'.join(cap), fontsize=8.5, color=INK2, va='top'); save(fig, '8_exploratory_head_scanning.png')

# ---------- Excel workbook ----------
wb = Workbook(); AR = 'Arial'; B = Font(name=AR, bold=True); N = Font(name=AR); H = Font(name=AR, bold=True, size=14); NOTE = Font(name=AR, italic=True, color='52514E', size=9); GREEN = Font(name=AR, color='008000')
HEAD = PatternFill('solid', fgColor='E8EEF7'); STAT = PatternFill('solid', fgColor='F4F4F2'); thin = Side(style='thin', color='BFBFBF')
def header(ws, row, names):
    for j, n in enumerate(names, 1): c = ws.cell(row, j, n); c.font = B; c.fill = HEAD; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); c.border = Border(bottom=thin)
def widths(ws, w):
    for j, x in enumerate(w, 1): ws.column_dimensions[COL(j)].width = x
def data_rows(ws, start, cols, fmt='0.0'):
    for i, r in enumerate(rats.itertuples()):
        ws.cell(start + i, 1, int(r.rat)).font = N; ws.cell(start + i, 2, r.sex).font = N
        for j, x in enumerate(cols(r.rat), 3):
            c = ws.cell(start + i, j, None if pd.isna(x) else (round(float(x), 2) if not isinstance(x, str) else x)); c.font = N; c.number_format = fmt
def stat_rows(ws, row0, first, last, c0, c1, fm, paired=False):
    """Mean, SEM, n for each sex, and a t-test p value, all as Excel formulas over the rat rows above."""
    fF, lF, fM, lM = first, first + 14, first + 15, last; labels = []
    for i, (lab, f) in enumerate((('Female mean', 'AVERAGE({c}{a}:{c}{b})'), ('Female SEM', 'STDEV({c}{a}:{c}{b})/SQRT(COUNT({c}{a}:{c}{b}))'), ('Male mean', 'AVERAGE({c}{a}:{c}{b})'), ('Male SEM', 'STDEV({c}{a}:{c}{b})/SQRT(COUNT({c}{a}:{c}{b}))'), ('t-test p (F vs M)', 'TTEST({c}{fF}:{c}{lF},{c}{fM}:{c}{lM},2,2)'))):
        r = row0 + i; ws.cell(r, 1, lab).font = B; ws.cell(r, 1).fill = STAT; ws.cell(r, 2).fill = STAT; labels.append(r)
        for j in range(c0, c1 + 1):
            c = COL(j); a, b = (fF, lF) if 'Female' in lab else (fM, lM); cell = ws.cell(r, j, '=' + f.format(c=c, a=a, b=b, fF=fF, lF=lF, fM=fM, lM=lM)); cell.font = N; cell.number_format = '0.000' if 'p' in lab else fm; cell.fill = STAT
    return labels
def bar_chart(ws, title, ytitle, cats, mean_rows, sem_rows, c0, c1, anchor, ymax=None, w=17, h=8.5):
    # Units go in the chart title: openpyxl axis titles overlap the tick labels in Excel. Legend on top keeps it clear of the category labels.
    ch = BarChart(); ch.type = 'col'; ch.grouping = 'clustered'; ch.title = f'{title} - {ytitle}'; ch.width, ch.height = w, h; ch.legend.position = 't'; ch.title.overlay = False; ch.legend.overlay = False
    for name, mr, sr, color in (('Female', mean_rows[0], sem_rows[0], '2A78D6'), ('Male', mean_rows[1], sem_rows[1], 'EB6834')):
        s = Series(Reference(ws, min_col=c0, max_col=c1, min_row=mr), title=name); s.graphicalProperties.solidFill = color; s.graphicalProperties.line.solidFill = '000000'
        rng = f"'{ws.title}'!${COL(c0)}${sr}:${COL(c1)}${sr}"; s.errBars = ErrorBars(errDir='y', errBarType='both', errValType='cust', noEndCap=False, plus=NumDataSource(NumRef(f=rng)), minus=NumDataSource(NumRef(f=rng))); ch.series.append(s)
    ch.set_categories(cats); ch.y_axis.scaling.min = 0
    if ymax: ch.y_axis.scaling.max = ymax
    ch.y_axis.majorGridlines = None; ch.x_axis.delete = False; ch.y_axis.delete = False; ws.add_chart(ch, anchor)
# Latency sheet
ws = wb.active; ws.title = 'Latency'; ws['A1'] = 'Escape latency per rat (seconds; mean of that day\'s trials; 30 s = did not find the platform)'; ws['A1'].font = H
header(ws, 3, ['Rat', 'Sex', 'Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 7 (reminder)']); data_rows(ws, 4, lambda r: [LAT.loc[r, d] for d in days])
SR = stat_rows(ws, 35, 4, 33, 3, 8, '0.0'); widths(ws, [18, 9, 9, 9, 9, 9, 9, 14])
ws['A41'] = 'Two-way ANOVA (days 1-5) is on the Statistics sheet. Per-day t-tests are uncorrected; use the ANOVA for the overall answer.'; ws['A41'].font = NOTE
bar_chart(ws, 'Escape latency by day (mean ± SEM)', 'Latency (s)', Reference(ws, min_col=3, max_col=8, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 3, 8, 'J3', 30)
# Swim speed sheet
ws = wb.create_sheet('Swim speed'); ws['A1'] = 'Swim speed per rat (cm/s; median of that day\'s trials)'; ws['A1'].font = H
header(ws, 3, ['Rat', 'Sex', 'Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Average days 1-5']); data_rows(ws, 4, lambda r: [SPD.loc[r, d] for d in [1, 2, 3, 4, 5]])
for i in range(30): c = ws.cell(4 + i, 8, f'=AVERAGE(C{4 + i}:G{4 + i})'); c.font = N; c.number_format = '0.0'
SR = stat_rows(ws, 35, 4, 33, 3, 8, '0.0'); widths(ws, [18, 9, 9, 9, 9, 9, 9, 16])
bar_chart(ws, 'Swim speed by day (mean ± SEM)', 'Speed (cm/s)', Reference(ws, min_col=3, max_col=8, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 3, 8, 'J3')
# Reminder sheet
ws = wb.create_sheet('Reminder'); ws['A1'] = 'Day 5 vs day 7 (reminder): escape latency per rat (s)'; ws['A1'].font = H
header(ws, 3, ['Rat', 'Sex', 'Day 5', 'Day 7', 'Change (7 - 5)']); data_rows(ws, 4, lambda r: [LAT.loc[r, 5], LAT.loc[r, 7]])
for i in range(30): c = ws.cell(4 + i, 5, f'=D{4 + i}-C{4 + i}'); c.font = N; c.number_format = '0.0'
SR = stat_rows(ws, 35, 4, 33, 3, 5, '0.0'); ws['A41'] = 'Paired t-test, day 5 vs day 7, all 30 rats'; ws['A41'].font = B; c = ws['C41']; c.value = '=TTEST(C4:C33,D4:D33,2,1)'; c.number_format = '0.000'; c.font = N
widths(ws, [24, 9, 10, 10, 15]); bar_chart(ws, 'Day 5 vs day 7 (mean ± SEM)', 'Latency (s)', Reference(ws, min_col=3, max_col=4, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 3, 4, 'G3', 30, 12)
# Probes sheet
ws = wb.create_sheet('Checking tests'); ws['A1'] = 'Checking tests (120 s, rat starts on the platform; day 6 = control at the standard 1.5 cm water level, day 8 = water raised to 3 cm; same rats): time on the platform and whether the rat stayed. DeepLabCut video tracking, final model; rat 1 has no Day 6 clip.'; ws['A1'].font = H
header(ws, 3, ['Rat', 'Sex', 'Day 6 control (1.5 cm): % time on platform', 'Day 8 raised (3 cm): % time on platform', 'Day 6: stayed?', 'Day 8: stayed?'])
data_rows(ws, 4, lambda r: [P6.pct[r], P8.pct[r]])
for i in range(30):
    for j, src in ((5, 'C'), (6, 'D')): t = 'Day 6 video tracking' if j == 5 else 'Day 8 video tracking'; c = ws.cell(4 + i, j, f"=IF('{t}'!D{4 + i}=\"\",\"\",IF('{t}'!D{4 + i}=0,\"Yes\",\"No\"))"); c.font = N; c.alignment = Alignment(horizontal='center')
SR = stat_rows(ws, 35, 4, 33, 3, 4, '0.0')
for i, (lab, f) in enumerate((('Females that stayed', 'COUNTIF({c}4:{c}18,"Yes")'), ('Males that stayed', 'COUNTIF({c}19:{c}33,"Yes")'))):
    ws.cell(41 + i, 1, lab).font = B
    for j, cc in ((5, 'E'), (6, 'F')): c = ws.cell(41 + i, j, '=' + f.format(c=cc)); c.font = N
ws['A44'] = "Fisher's exact test (stayed vs left, by sex)"; ws['A44'].font = B; ws['E44'] = round(FI6[1], 5); ws['F44'] = round(FI8[1], 5)
for c in ('E44', 'F44'): ws[c].font = Font(name=AR, color='0000FF'); ws[c].number_format = '0.0000'
ws['A45'] = 'Fisher p values are computed in Python (Excel has no Fisher test). Stayed = never left the platform (0 departures), as in the handwritten notes. Yes/No is read live from the departures column on the video tracking tab for that day. Water levels are from the experimenter.'; ws['A45'].font = NOTE
widths(ws, [24, 9, 16, 16, 12, 12]); bar_chart(ws, 'Time on platform during checking tests (mean ± SEM)', '% of 120 s', Reference(ws, min_col=3, max_col=4, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 3, 4, 'H3', 100, 13)
sc = ScatterChart(); sc.title = 'Each rat: day 6 % on platform (across) vs day 8 (up)'; sc.style = 13; sc.width, sc.height = 13, 8.5; sc.legend.position = 't'; sc.title.overlay = False; sc.legend.overlay = False
for name, a, b, color in (('Female', 4, 18, '2A78D6'), ('Male', 19, 33, 'EB6834')):
    s = Series(Reference(ws, min_col=4, min_row=a, max_row=b), Reference(ws, min_col=3, min_row=a, max_row=b), title=name); s.marker = Marker('circle', size=7); s.marker.graphicalProperties.solidFill = color; s.marker.graphicalProperties.line.solidFill = '000000'; s.graphicalProperties.line.noFill = True; sc.series.append(s)
sc.x_axis.scaling.min = sc.y_axis.scaling.min = 0; sc.x_axis.scaling.max = sc.y_axis.scaling.max = 100; sc.x_axis.delete = sc.y_axis.delete = False; ws.add_chart(sc, 'H22')
ws['A47'] = 'Day 6 control vs day 8 raised water, paired t-test p (same rats)'; ws['A47'].font = B
for i, (lab, a, b) in enumerate((('All rats', 4, 33), ('Females', 4, 18), ('Males', 19, 33)), 48):
    ws.cell(i, 1, lab).font = N; c = ws.cell(i, 3, f'=TTEST(C{a}:C{b},D{a}:D{b},2,1)'); c.number_format = '0.000'; c.font = N
ws['H40'] = 'Pearson r, day 6 vs day 8:'; ws['H40'].font = B; ws['K40'] = '=CORREL(C4:C33,D4:D33)'; ws['K40'].number_format = '0.00'; ws['K40'].font = N
# Video tracking sheets, one per KAC checking day
for d, D, NVd in ((6, DL6, NV6), (8, DL, NV)):
    lab = 'Day 6 checking test (control, standard water 1.5 cm)' if d == 6 else 'Day 8 checking test (water raised, 3 cm)'
    ws = wb.create_sheet(f'Day {d} video tracking'); ws['A1'] = f'{lab} measured by DeepLabCut video tracking (final model; 120 s from release)'; ws['A1'].font = H
    header(ws, 3, ['Rat', 'Sex', '% time on platform zone', 'Times left the platform', 'First departure (s)', '% time at the wall', '% frames body unsure'])
    data_rows(ws, 4, lambda r: [D.pct_time_on_platform_zone[r], D.departures[r], D.first_departure_s[r], D.pct_time_at_wall[r], D.pct_frames_body_unsure[r]])
    SR = stat_rows(ws, 35, 4, 33, 3, 6, '0.0'); widths(ws, [24, 9, 15, 15, 14, 14, 14])
    ws['A41'] = 'First departure is blank for rats that never left; its mean and t-test cover only rats that left (Excel skips blanks).' + (' Rat 1 has no Day 6 clip.' if d == 6 else ''); ws['A41'].font = NOTE
    ws['A42'] = 'Platform zone: 0.165 pool radii around the platform (80 px at Day 8 scale; stayers never moved beyond 74 px, swimmers went 200-600 px). Wall = beyond 0.85 of the rim radius; wall time depends on the tracking model, so treat it as provisional.'; ws['A42'].font = NOTE
    bar_chart(ws, f'Day {d}: times left the platform (mean ± SEM)', 'count', Reference(ws, min_col=4, max_col=4, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 4, 4, 'I3', None, 10)
    bar_chart(ws, f'Day {d}: % time at the wall (mean ± SEM)', '% of 120 s', Reference(ws, min_col=6, max_col=6, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 6, 6, 'I21', None, 10)
    ws = wb.create_sheet(f'Day {d} notes vs tracking'); ws['A1'] = f"Check: experimenter's handwritten day {d} notes vs video tracking"; ws['A1'].font = H
    cols = ['rat', 'sex', 'notes_stayed_on', 'dlc_stayed_on', 'notes_departures', 'dlc_departures', 'notes_first_departure_s', 'dlc_first_departure_s', 'notes_text']
    header(ws, 3, ['Rat', 'Sex', 'Notes: stayed?', 'Tracking: stayed?', 'Notes: departures', 'Tracking: departures', 'Notes: first departure (s)', 'Tracking: first departure (s)', 'Notes (typed)', 'Stayed agrees?'])
    NVs = NVd.assign(o=NVd.sex.map({'F': 0, 'M': 1})).sort_values(['o', 'rat'])
    for i, r in enumerate(NVs.itertuples()):
        for j, cname in enumerate(cols, 1):
            x = getattr(r, cname); c = ws.cell(4 + i, j, None if pd.isna(x) else (x.item() if hasattr(x, 'item') else x)); c.font = N; c.alignment = Alignment(wrap_text=(cname == 'notes_text'), vertical='top')
        c = ws.cell(4 + i, 10, f'=IF(C{4 + i}="","no note",IF(C{4 + i}=D{4 + i},"Yes","No"))'); c.font = N
    n = len(NVs); ws.cell(5 + n, 1, 'Stayed/left agreement (rats with a note)').font = B; ws.cell(5 + n, 10, f'=COUNTIF(J4:J{3 + n},"Yes")&" of "&(COUNTIF(J4:J{3 + n},"Yes")+COUNTIF(J4:J{3 + n},"No"))').font = N
    ws.cell(6 + n, 1, 'Pearson r, first departure (notes vs tracking)').font = B; c = ws.cell(6 + n, 8, f'=CORREL(G4:G{3 + n},H4:H{3 + n})'); c.number_format = '0.00'; c.font = N
    widths(ws, [12, 7, 12, 12, 12, 12, 14, 14, 48, 12])
# Statistics sheet
ws = wb.create_sheet('Statistics'); ws['A1'] = 'All statistical tests'; ws['A1'].font = H
header(ws, 3, ['Question', 'Test', 'Result', 'p value', 'Answer'])
rows = [('Day 6 control check (1.5 cm): time on platform by sex', 'Unpaired t-test', f"t({T['p6'].df:.0f}) = {T['p6'].statistic:.2f}", T['p6'].pvalue, 'Males stayed longer' if T['p6'].pvalue < .05 else 'No difference'),
        ('Day 8 raised-water check (3 cm): time on platform by sex', 'Unpaired t-test', f"t({T['p8'].df:.0f}) = {T['p8'].statistic:.2f}", T['p8'].pvalue, 'Males stayed longer' if T['p8'].pvalue < .05 else 'No difference'),
        ('Day 6: did more males stay?', "Fisher's exact test", FS(P6), FI6[1], 'Yes' if FI6[1] < .05 else 'No'),
        ('Day 8: did more males stay?', "Fisher's exact test", FS(P8), FI8[1], 'Yes' if FI8[1] < .05 else 'No'),
        ('Raising the water (day 6 control vs day 8): all rats', 'Paired t-test, % time on platform', f"t({WT['all'].df:.0f}) = {WT['all'].statistic:.2f}", WT['all'].pvalue, 'Changed' if WT['all'].pvalue < .05 else 'No change'),
        ('Raising the water: females', 'Paired t-test', f"t({WT['F'].df:.0f}) = {WT['F'].statistic:.2f}; {P6.pct[F].mean():.0f}% to {P8.pct[F].mean():.0f}%", WT['F'].pvalue, 'Changed' if WT['F'].pvalue < .05 else 'No change'),
        ('Raising the water: males', 'Paired t-test', f"t({WT['M'].df:.0f}) = {WT['M'].statistic:.2f}; {P6.pct[M].mean():.0f}% to {P8.pct[M].mean():.0f}%", WT['M'].pvalue, 'Changed' if WT['M'].pvalue < .05 else 'No change'),
        ('Day 8: departures by sex (video tracking)', 'Unpaired t-test', f"t(28) = {T['dep'].statistic:.2f}", T['dep'].pvalue, 'Females left more often' if T['dep'].pvalue < .05 else 'No difference'),
        ('Day 8: time at the wall by sex (video tracking; provisional)', 'Unpaired t-test', f"t(28) = {T['wall'].statistic:.2f}", T['wall'].pvalue, 'Females more at the wall' if T['wall'].pvalue < .05 else 'No difference'),
        ('Day 6: departures by sex (video tracking)', 'Unpaired t-test', f"t({T['dep6'].df:.0f}) = {T['dep6'].statistic:.2f}", T['dep6'].pvalue, 'Females left more often' if T['dep6'].pvalue < .05 else 'No difference'),
        ('Day 6: time at the wall by sex (video tracking; provisional)', 'Unpaired t-test', f"t({T['wall6'].df:.0f}) = {T['wall6'].statistic:.2f}", T['wall6'].pvalue, 'Females more at the wall' if T['wall6'].pvalue < .05 else 'No difference'),
        ('Did each rat behave the same on both checking tests?', 'Pearson correlation, day 6 vs day 8', f'r = {R68[0]:.2f}', R68[1], 'Yes, strongly' if R68[1] < .05 else 'No'),
        ('Does video tracking match the notes?', 'Pearson correlation, first departure time', f'r = {RV[0]:.2f}, n = {len(v)}', RV[1], 'Yes' if RV[1] < .05 else 'No'),
        ('Does video tracking match AnyMaze on day 8?', 'Pearson correlation, % time on platform (same zone size)', f'r = {RAM[0]:.3f}, largest gap {DAM:.0f} points', RAM[1], 'Yes' if RAM[1] < .05 else 'No'),
        ('Did latency fall across days 1-5?', 'Two-way mixed ANOVA, Day (within) x Sex (between), Greenhouse-Geisser corrected', f"F({AN['Day']['df1']:.1f}, {AN['Day']['df2']:.1f}) = {AN['Day']['F']:.2f}", AN['Day']['p'], 'Yes'),
        ('Did females and males differ in latency?', 'Same ANOVA, Sex main effect', f"F(1, {AN['Sex']['df2']:.0f}) = {AN['Sex']['F']:.2f}", AN['Sex']['p'], 'No' if AN['Sex']['p'] >= .05 else 'Yes'),
        ('Did the sexes learn at different rates?', 'Same ANOVA, Day x Sex', f"F({AN['Day x Sex']['df1']:.1f}, {AN['Day x Sex']['df2']:.1f}) = {AN['Day x Sex']['F']:.2f}", AN['Day x Sex']['p'], 'No' if AN['Day x Sex']['p'] >= .05 else 'Yes'),
        ('Did swim speed differ by sex?', 'Unpaired t-test, average speed days 1-5', f"t(28) = {T['speed'].statistic:.2f}", T['speed'].pvalue, 'Yes, females faster' if T['speed'].pvalue < .05 else 'No'),
        ('Was there forgetting by the reminder day?', 'Paired t-test, day 5 vs day 7', f"t(29) = {T['rem'].statistic:.2f}", T['rem'].pvalue, 'No' if T['rem'].pvalue >= .05 else 'Yes')]
rows = [('SP1: time on platform by sex', 'Unpaired t-test (DLC tracking)', f"t({len(S1) - 2}) = {TS['pct_time_on_platform_zone'].statistic:.2f}", TS['pct_time_on_platform_zone'].pvalue, 'Males stayed longer' if TS['pct_time_on_platform_zone'].pvalue < .05 else 'No difference'),
        ('SP1: did more males stay?', "Fisher's exact test", f"{int(S1.stayed[SM].sum())}/{SM.sum()} males vs {int(S1.stayed[SF].sum())}/{SF.sum()} females", FIS[1], 'Yes' if FIS[1] < .05 else 'No'),
        ('SP1: departures by sex', 'Unpaired t-test (DLC tracking)', f"t({len(S1) - 2}) = {TS['departures'].statistic:.2f}", TS['departures'].pvalue, 'Females left more often' if TS['departures'].pvalue < .05 else 'No difference'),
        ('SP1: time at the wall by sex', 'Unpaired t-test (DLC tracking)', f"t({len(S1) - 2}) = {TS['pct_time_at_wall'].statistic:.2f}", TS['pct_time_at_wall'].pvalue, 'Differs' if TS['pct_time_at_wall'].pvalue < .05 else 'No difference')] + rows
rows = rows + [(f'EXPLORATORY head scanning (>= {th} deg): day 6 vs day 8', 'Paired t-test, KAC', f"t({TV[th]['paired'].df:.0f}) = {TV[th]['paired'].statistic:.2f}", TV[th]['paired'].pvalue, 'Fewer on day 8 (order and camera also differ)' if TV[th]['paired'].pvalue < .05 and TV[th]['paired'].statistic > 0 else 'No clear change') for th in (25, 40)] + \
    [(f'EXPLORATORY head scanning (>= {th} deg): females vs males, day {d}', 'Unpaired t-test, KAC', f"t({TV[th][k].df:.0f}) = {TV[th][k].statistic:.2f}", TV[th][k].pvalue, 'Differs' if TV[th][k].pvalue < .05 else 'No difference') for th in (25, 40) for d, k in ((6, 's6'), (8, 's8'))]
for i, r in enumerate(rows):
    for j, x in enumerate(r, 1):
        c = ws.cell(4 + i, j, round(float(x), 5) if j == 4 else x); c.font = Font(name=AR, color='0000FF') if j == 4 else N; c.alignment = Alignment(wrap_text=True, vertical='top')
        if j == 4: c.number_format = '0.0000'
k = 5 + len(rows); notes = ['Blue values are computed in Python (scipy). The t-test and correlation values match the live Excel formulas on each data sheet.',
    f"ANOVA uses each rat's mean per day for days 1-5, 30 rats. Sphericity correction (Greenhouse-Geisser) epsilon = {EPS:.2f}. Partial eta squared: Day {AN['Day']['eta_p2']:.2f}, Sex {AN['Sex']['eta_p2']:.2f}, Day x Sex {AN['Day x Sex']['eta_p2']:.2f}.",
    f"Non-parametric check (Mann-Whitney) agrees: day 6 {pt(MW['p6'])}, day 8 {pt(MW['p8'])}, departures {pt(MW['dep'])}, wall time {pt(MW['wall'])}.",
    "t-tests are Student's two-tailed, equal variances (Excel TTEST type 2; paired = type 1). No correction for multiple tests; the checking-test results would survive one."]
for i, t in enumerate(notes): ws.cell(k + i, 1, t).font = NOTE
widths(ws, [42, 46, 26, 11, 26])
# SP1 sheet
ws = wb.create_sheet('SP1 checking'); ws['A1'] = 'SP1 cohort checking test (120 s, rat starts on the platform, raised water; no standard-depth control). Separate cohort from KAC.'; ws['A1'].font = H
header(ws, 3, ['Rat', 'Sex', '% time on platform (DLC)', 'Times left the platform (DLC)', '% time at the wall (DLC)', 'Distance swum (cm, AnyMaze)', 'Stayed?', 'AnyMaze test no.'])
for i, r in enumerate(S1.itertuples()):
    for j, x in enumerate((int(r.rat), r.sex, r.pct_time_on_platform_zone, int(r.departures), r.pct_time_at_wall, r.anymaze_distance_cm), 1): c = ws.cell(4 + i, j, x); c.font = N; c.number_format = '0.0' if j > 2 else 'General'
    c = ws.cell(4 + i, 7, f'=IF(D{4 + i}=0,"Yes","No")'); c.font = N; c.alignment = Alignment(horizontal='center'); ws.cell(4 + i, 8, int(r.Test)).font = N
nF = int(SF.sum()); last = 3 + len(S1); r0 = last + 2
for i, (lab, f) in enumerate((('Female mean', 'AVERAGE({c}4:{c}%d)' % (3 + nF)), ('Female SEM', 'STDEV({c}4:{c}%d)/SQRT(COUNT({c}4:{c}%d))' % (3 + nF, 3 + nF)), ('Male mean', 'AVERAGE({c}%d:{c}%d)' % (4 + nF, last)), ('Male SEM', 'STDEV({c}%d:{c}%d)/SQRT(COUNT({c}%d:{c}%d))' % (4 + nF, last, 4 + nF, last)), ('t-test p (F vs M)', 'TTEST({c}4:{c}%d,{c}%d:{c}%d,2,2)' % (3 + nF, 4 + nF, last)))):
    ws.cell(r0 + i, 1, lab).font = B; ws.cell(r0 + i, 1).fill = STAT; ws.cell(r0 + i, 2).fill = STAT
    for j in range(3, 7): c = ws.cell(r0 + i, j, '=' + f.format(c=COL(j))); c.font = N; c.number_format = '0.000' if 'p' in lab else '0.0'; c.fill = STAT
ws.cell(r0 + 6, 1, 'Females that stayed').font = B; ws.cell(r0 + 6, 7, '=COUNTIF(G4:G%d,"Yes")' % (3 + nF)).font = N
ws.cell(r0 + 7, 1, 'Males that stayed').font = B; ws.cell(r0 + 7, 7, '=COUNTIF(G%d:G%d,"Yes")' % (4 + nF, last)).font = N
ws.cell(r0 + 8, 1, "Fisher's exact test (stayed vs left, by sex)").font = B; c = ws.cell(r0 + 8, 7, round(FIS[1], 5)); c.font = Font(name=AR, color='0000FF'); c.number_format = '0.0000'
for i, t in enumerate(('Rat numbers come from AnyMaze (tests 9-16 are rats 17-24; tests 17-24 are rats 9-16). Sex: rats 1-16 male, 17-32 female (confirmed by the experimenter). All 32 rats were tested; SP1 records (Documents/2025/data/SP1.xlsx) show no deaths or exclusions.',
                       "Platform time, departures and wall time are from DLC video tracking. AnyMaze is used only for distance (r = 0.994 with DLC): its platform zone logged false exits for rats sitting still (e.g. rat 22: AnyMaze 22.5 s, video and DLC 120 s).",
                       'Pool size assumed 172 cm, as for KAC (not confirmed for SP1). Stayed = never left the platform (0 departures), as in the handwritten notes.')): ws.cell(r0 + 10 + i, 1, t).font = NOTE
widths(ws, [22, 9, 15, 15, 14, 15, 10, 10]); bar_chart(ws, 'SP1: time on platform (mean ± SEM)', '% of 120 s', Reference(ws, min_col=3, max_col=3, min_row=3), (r0, r0 + 2), (r0 + 1, r0 + 3), 3, 3, 'J3', 100, 10)
bar_chart(ws, 'SP1: times left the platform (mean ± SEM)', 'count', Reference(ws, min_col=4, max_col=4, min_row=3), (r0, r0 + 2), (r0 + 1, r0 + 3), 4, 4, 'J21', None, 10)
# Exploratory head-scanning sheet
ws = wb.create_sheet('Exploratory head scanning'); ws['A1'] = 'EXPLORATORY: VTE-like head scanning during the KAC checking tests (head swings left-right within 2 s while still; events per minute still)'; ws['A1'].font = H
header(ws, 3, ['Rat', 'Sex', 'Day 6, swings >= 25 deg', 'Day 8, swings >= 25 deg', 'Day 6, swings >= 40 deg', 'Day 8, swings >= 40 deg'])
data_rows(ws, 4, lambda r: [VK[(25, 6)][r], VK[(25, 8)][r], VK[(40, 6)][r], VK[(40, 8)][r]], '0.00')
SR = stat_rows(ws, 35, 4, 33, 3, 6, '0.00'); widths(ws, [30, 9, 14, 14, 14, 14])
ws['A41'] = 'Day 6 vs day 8, paired t-test p (same rats)'; ws['A41'].font = B
for i, (lab, a, b) in enumerate((('All rats', 4, 33), ('Females', 4, 18), ('Males', 19, 33)), 42):
    ws.cell(i, 1, lab).font = N
    for col, (c6, c8) in ((3, ('C', 'D')), (5, ('E', 'F'))): c = ws.cell(i, col, f'=TTEST({c6}{a}:{c6}{b},{c8}{a}:{c8}{b},2,1)'); c.number_format = '0.000'; c.font = N
for i, t in enumerate(("How it is measured: head angle = nose direction relative to the body axis (spine middle to neck), from DeepLabCut (final KAC model). A swing is a move of at least 25 (or 40) degrees between turning points; an event is a left-then-right (or right-then-left) pair within 2 s while the rat is still (body moving under 0.25 body lengths per second).",
                       "Check against hand labels (36 held-out frames): head angle median error 5 degrees, worst 10% 13 degrees, r = 0.85. The 40-degree column is the stricter version, less affected by tracking noise. Not checked against video by eye.",
                       "Day 6 and day 8 differ in more than water depth: the test order is fixed (rats may scan less on their second checking test) and day 6 used a different camera. Do not present day 6 vs day 8 as a water-depth effect.",
                       f"Counts are skewed, so a Wilcoxon signed-rank check is also reported: 25 deg p = {TV[25]['wil']:.3f}, 40 deg p = {TV[40]['wil']:.3f}. Rat 1 has no Day 6 clip. SP1 (10 fps, so fast swings can be missed): females vs males, 25 deg {pt(TV[25]['sp1'].pvalue)}, 40 deg {pt(TV[40]['sp1'].pvalue)}.",
                       "Tail sweeps (hips and tail base vs the body axis) were also tried and are not reported: the hand-label check showed the tracking error (0.044 body lengths) is as large as the sweeps themselves.")): ws.cell(46 + i, 1, t).font = NOTE
bar_chart(ws, 'Head-scan events per minute still (mean ± SEM)', 'events/min', Reference(ws, min_col=3, max_col=6, min_row=3), (SR[0], SR[2]), (SR[1], SR[3]), 3, 6, 'H3', None, 16)
# Summary sheet (first tab)
ws = wb.create_sheet('Summary', 0); ws['A1'] = 'Water maze checking tests: SP1 and KAC cohorts (summary)'; ws['A1'].font = Font(name=AR, bold=True, size=16)
lines = [('Checking tests (main result)', None),
         (f"1. KAC cohort, both checking tests (day 6 control at the standard 1.5 cm water level; day 8 water raised to 3 cm), males stayed on the platform and females left. Day 6: {P6.pct[M].mean():.0f}% vs {P6.pct[F].mean():.0f}% of the time ({pt(T['p6'].pvalue)}). Day 8: {P8.pct[M].mean():.0f}% vs {P8.pct[F].mean():.0f}% ({pt(T['p8'].pvalue)}). Raising the water from day 6 to day 8: females {P6.pct[F].mean():.0f}% to {P8.pct[F].mean():.0f}% ({pt(WT['F'].pvalue)}), males {P6.pct[M].mean():.0f}% to {P8.pct[M].mean():.0f}% ({pt(WT['M'].pvalue)}), paired t-tests." + (' So the sex difference is already there at standard depth; raising the water did not significantly add to it.' if WT['all'].pvalue >= .05 else ''), None),
         (f"2. Video tracking, both days: females left the platform {DL6.departures[F].mean():.1f} times on average on day 6 and {DL.departures[F].mean():.1f} on day 8; males {DL6.departures[M].mean():.1f} and {DL.departures[M].mean():.1f} (day 6 {pt(T['dep6'].pvalue)}, day 8 {pt(T['dep'].pvalue)}). Wall time depends on the tracking model, so it is shown as provisional.", None),
         (f"3. Each rat behaved the same way on both checking tests (r = {R68[0]:.2f}), and the video tracking matched the experimenter's notes (stayed or left agreed for {AG6} rats with notes on day 6 and {AG8} on day 8; first-departure times r = {RV[0]:.2f}) and AnyMaze's day 8 platform time (r = {RAM[0]:.3f}).", None),
         (f"4. Design: the earlier SP1 cohort (a separate cohort) had its checking test at raised water only, with no standard-depth control: males stayed {S1.pct_time_on_platform_zone[SM].mean():.0f}% of the time vs females {S1.pct_time_on_platform_zone[SF].mean():.0f}% ({pt(TS['pct_time_on_platform_zone'].pvalue)}); {int(S1.stayed[SM].sum())}/{SM.sum()} males vs {int(S1.stayed[SF].sum())}/{SF.sum()} females stayed (Fisher {pt(FIS[1])}). KAC was run to add the standard-depth control (points 1-3).", None),
         ('', None), ('Training days (background)', None),
         (f"5. All rats learned. Escape latency fell from {LAT[1].mean():.1f} s on day 1 to {LAT[5].mean():.1f} s on day 5 (ANOVA, {pt(AN['Day']['p'])}).", None),
         (f"6. Females and males learned equally well (no sex difference, {pt(AN['Sex']['p'])}; no difference in learning rate, {pt(AN['Day x Sex']['p'])}). Females swam faster ({SPD[[1, 2, 3, 4, 5]].mean(axis=1)[F].mean():.1f} vs {SPD[[1, 2, 3, 4, 5]].mean(axis=1)[M].mean():.1f} cm/s, {pt(T['speed'].pvalue)}).", None),
         (f"7. No forgetting by the reminder day: {LAT[5].mean():.1f} s on day 5, {LAT[7].mean():.1f} s on day 7 ({pt(T['rem'].pvalue)}).", None),
         ('', None), ('Exploratory (not for the poster without more checks)', None),
         (f"8. Head scanning (VTE-like) while still on the platform: KAC rats made fewer head swings on day 8 than day 6 ({pt(TV[25]['paired'].pvalue)}; stricter 40-degree version {pt(TV[40]['paired'].pvalue)}), but test order and camera also changed, so this is not a water-depth effect. No sex difference at the stricter threshold. Tail sweeps could not be measured: tracking error is as large as the sweeps.", None),
         ('', None), ('How to read this workbook', None),
         ('Each sheet lists every rat, then the female and male means, SEMs and t-test with live Excel formulas: click a cell to see the calculation.', None),
         ('Blue numbers were calculated in Python (the ANOVA and Fisher tests, which Excel cannot do). Green cells on this sheet link to the data sheets.', None),
         ('Data: training days use AnyMaze exports corrected against overhead video (see updated_anymaze/README.md). Checking tests (SP1 and KAC) use DeepLabCut video tracking; KAC uses the final v3rot model for both days. KAC: 30 rats, 15 per sex (rats 11 and 19 died); rat 1 has no Day 6 clip. Testing batch had no effect.', None),
         ('Bar graphs show mean ± SEM; dots are individual rats. Picture files for slides are in the figures folder next to this workbook.', None)]
for i, (t, _) in enumerate(lines, 3):
    c = ws.cell(i, 1, t); c.font = B if t in ('Checking tests (main result)', 'Training days (background)', 'Exploratory (not for the poster without more checks)', 'How to read this workbook') else N; c.alignment = Alignment(wrap_text=True, vertical='top')
ws.column_dimensions['A'].width = 120
for i in (4, 5, 6, 10, 11): ws.row_dimensions[i].height = 30
ws.row_dimensions[4].height = 60; ws.row_dimensions[7].height = 45
ws['A25'] = 'Key numbers, linked live from the data sheets'; ws['A25'].font = B
links = [('Day 1 mean latency, females (s)', "=Latency!C35"), ('Day 1 mean latency, males (s)', "=Latency!C37"), ('Day 5 mean latency, females (s)', "=Latency!G35"), ('Day 5 mean latency, males (s)', "=Latency!G37"),
         ('Day 6 check: % on platform, females', "='Checking tests'!C35"), ('Day 6 check: % on platform, males', "='Checking tests'!C37"), ('Day 6 check: t-test p', "='Checking tests'!C39"), ('Day 8 check: % on platform, females', "='Checking tests'!D35"), ('Day 8 check: % on platform, males', "='Checking tests'!D37"), ('Day 8 check: t-test p', "='Checking tests'!D39"), ('Reminder: paired t-test p', "=Reminder!C41")]
ws.row_dimensions[15].height = 45
for i, (t, f) in enumerate(links, 26):
    ws.cell(i, 1, t).font = N; c = ws.cell(i, 2, f); c.font = GREEN; c.number_format = '0.000' if t.endswith(' p') else '0.0'
ws.column_dimensions['B'].width = 12
wb._sheets = [wb[n] for n in ['Summary', 'SP1 checking', 'Checking tests', 'Day 6 video tracking', 'Day 8 video tracking', 'Day 6 notes vs tracking', 'Day 8 notes vs tracking', 'Statistics', 'Latency', 'Swim speed', 'Reminder', 'Exploratory head scanning']]; wb.active = 0
OUT = os.path.join(HERE, 'water_maze_results.xlsx'); wb.save(OUT); print('saved', OUT)
