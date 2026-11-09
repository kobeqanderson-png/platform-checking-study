"""Advanced analysis of the checking tests: leave -> where it goes -> does it come back, and what predicts it.
Usage: python -I advanced_analysis.py     -> bouts.csv, per_rat.csv, statistics.csv, figures/*.png, REPORT.md (all next to this script)

Data: DeepLabCut tracks (KAC Day 6 and Day 8 from the final v3rot model; SP1 checking), same 120 s windows and platform zone as
../dlc_measures/checking_dlc_measures.py, so departure counts can be checked against its measures. Training data: corrected AnyMaze.
Rule (the experimenter's): any departure means the rat left.

Analyses
1. Departure bouts: each time the body leaves the platform zone for >= 1 s. Per bout: time off, how far it went, whether it reached
   the wall, whether and when it came back (revisit of the learned place).
2. Time to first departure: Kaplan-Meier curves, log-rank tests, Cox model (sex + water level, KAC, robust SE by rat).
3. Whole-design models: logistic GEE for leaving (sex x water level, KAC; rats repeated), linear mixed model for % time on platform.
4. Effect sizes: Hedges' g with bootstrap 95% CIs, one forest plot.
5. Does training predict leaving? Spearman correlations within each sex (KAC): day 5 latency, swim speed, thigmotaxis.
6. Sensitivity: the sex difference in leaving with the platform zone 20% smaller or larger and the departure rule at 0.5 s or 2 s.
"""
import csv, os, re, warnings
from pathlib import Path
import numpy as np, pandas as pd, cv2
from scipy import stats
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.duration.survfunc import SurvfuncRight, survdiff
from statsmodels.duration.hazard_regression import PHReg
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')

HERE = Path(__file__).resolve().parent; FIG = HERE / 'figures'; FIG.mkdir(exist_ok=True); AN = HERE.parent
ROOT = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs"); KAC = ROOT / 'KAcheck_d6d8_v3rot_20261108'
ZONE, WALL, POOL_CM = 0.165, 0.85, 172.0
C = {'Female': '#2a78d6', 'Male': '#eb6834'}; INK, INK2 = '#0b0b0b', '#52514e'; SEXES = ['Female', 'Male']
plt.rcParams.update({'font.family': 'Arial', 'font.size': 10.5, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold', 'legend.frameon': False})
pt = lambda p: 'p < 0.001' if p < .001 else f'p = {p:.3f}'
sexof = lambda r: 'Male' if r <= 16 else 'Female'

# ---------------- tracking ----------------
def ls(folder, prefix):
    return sorted(Path(folder) / f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith('.h5') and 'DLC' in f)
def body(h5, start, end, fps):
    d = pd.read_hdf(h5); d.columns = d.columns.droplevel(0); d = d.iloc[int(round(start * fps)):int(round(end * fps))]
    def s(p):
        xy = d[p][['x', 'y']].to_numpy(float).copy(); xy[d[p]['likelihood'].to_numpy() < .3] = np.nan
        return pd.DataFrame(xy).interpolate(limit_direction='both').to_numpy().copy()
    b = s('spine_mid'); u = d['spine_mid']['likelihood'].to_numpy() < .3; b[u] = s('head_center')[u]
    return pd.DataFrame(b).rolling(max(3, int(fps * .3)), center=True, min_periods=1).median().to_numpy()
def pool_from(video):  # same circle fit as checking_dlc_measures.py (SP1 only; KAC pools are fixed there)
    cap = cv2.VideoCapture(str(video)); n = int(cap.get(7)); fr = []
    for i in np.linspace(0, n - 1, 15).astype(int):
        cap.set(1, int(i)); ok, f = cap.read()
        if ok: fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    g = np.median(np.stack(fr), axis=0).astype(np.uint8)
    _, b = cv2.threshold(cv2.GaussianBlur(g, (9, 9), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    k = max(5, g.shape[1] // 60) | 1
    b = cv2.morphologyEx(cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((k, k), np.uint8)), cv2.MORPH_CLOSE, np.ones((2 * k + 1, 2 * k + 1), np.uint8))
    pts = max(cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0, :].astype(float); H, W = g.shape
    pts = pts[(pts[:, 0] > 3) & (pts[:, 0] < W - 4) & (pts[:, 1] > 3) & (pts[:, 1] < H - 4)]
    a, c, e = np.linalg.lstsq(np.c_[2 * pts, np.ones(len(pts))], (pts ** 2).sum(axis=1), rcond=None)[0]
    return float(a), float(c), float(np.sqrt(e + a ** 2 + c ** 2))

TR = []  # (cohort, day, condition, rat, fps, body, pool)
man = {int(r['test']): r for r in csv.DictReader(open(r"C:\Users\kobeq\Videos\checkd8\trials\clip_manifest.csv"))}
for h5 in ls(KAC / 'd8_tracks', 'Test_'):
    r = man[int(h5.name.split('DLC')[0].split('_')[1])]; s = float(r['release_offset_in_clip_s'])
    TR.append(('KAC', 8, 'KAC raised (3 cm)', int(r['animal']), 30, body(h5, s, s + 120, 30), (962, 515, 485)))
rel = {int(r['rat']): float(r['release_clip_s']) for r in csv.DictReader(open(AN / 'tracking_pilot' / 'd6_tracker_vs_anymaze.csv'))}
for h5 in ls(KAC / 'd6_tracks', 'Day06_'):
    rat = int(re.search(r'Rat(\d+)', h5.name).group(1)); TR.append(('KAC', 6, 'KAC standard (1.5 cm)', rat, 30, body(h5, rel[rat], rel[rat] + 120, 30), (751, 510, 533)))
mp = pd.read_csv(AN / 'dlc_measures' / 'sp1_checking_dlc_vs_anymaze.csv'); smap = dict(zip(mp.Test.astype(int), mp.animal.str[3:].astype(int)))
clips = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\sp1_clips\sp1_check")
sp_pool = pool_from(sorted(clips / f for f in os.listdir(clips) if f.startswith('Test ') and f.endswith('.mp4'))[0])
for h5 in ls(ROOT / 'sp1' / 'sp1_tracks', 'sp1_check_Test_'):
    TR.append(('SP1', 6, 'SP1 raised', smap[int(h5.name.split('DLC')[0].split('_')[-1])], 10, body(h5, 0, 120, 10), sp_pool))

def runs(mask, n):
    out, s = [], None
    for i, v in enumerate(np.append(mask, False)):
        if v and s is None: s = i
        elif not v and s is not None:
            if i - s >= n: out.append((s, i))
            s = None
    return out

def analyse(zone=ZONE, min_s=1.0):
    bouts, rows = [], []
    # One platform location per test (median over rats of where each sat in its first 2 s), as in checking_dlc_measures.py;
    # a per-rat estimate fails for rats that leave within 2 s.
    PL = {c: np.median([np.nanmedian(t[5][:2 * t[4]], axis=0) for t in TR if t[2] == c], axis=0) for c in {t[2] for t in TR}}
    for coh, day, cond, rat, fps, b, (cx, cy, R) in TR:
        cm = (POOL_CM / 2) / R; plat = PL[cond]
        dpl = np.linalg.norm(b - plat, axis=1) * cm; drim = np.linalg.norm(b - (cx, cy), axis=1)
        off = runs(dpl > zone * R * cm, int(min_s * fps)); n = len(b)
        for k, (a, e) in enumerate(off):
            seg = slice(a, e); came_back = e < n
            bouts.append(dict(cohort=coh, day=day, condition=cond, rat=rat, sex=sexof(rat), bout=k + 1, start_s=a / fps, off_s=(e - a) / fps,
                              returned=came_back, max_dist_cm=np.nanmax(dpl[seg]), reached_wall=bool((drim[seg] > WALL * R).any()),
                              pct_bout_within_30cm=100 * np.mean(dpl[seg] <= 30)))
        rows.append(dict(cohort=coh, day=day, condition=cond, rat=rat, sex=sexof(rat), fps=fps, departures=len(off), left=len(off) > 0,
                         first_departure_s=off[0][0] / fps if off else np.nan, pct_on_platform=100 * np.mean(dpl <= zone * R * cm),
                         ended_on_platform=dpl[-fps:].mean() <= zone * R * cm))
    return pd.DataFrame(bouts), pd.DataFrame(rows)

B, P = analyse()
B.round(3).to_csv(HERE / 'bouts.csv', index=False)
# consistency with the measures used in the workbook
ref = pd.concat([pd.read_csv(AN / 'dlc_measures' / f).assign(condition=c) for f, c in (('kac_d6_dlc_measures.csv', 'KAC standard (1.5 cm)'), ('kac_d8_dlc_measures.csv', 'KAC raised (3 cm)'))])
chk = P.merge(ref[['rat', 'condition', 'departures']], on=['rat', 'condition'], suffixes=('', '_ref'))
CONS = (chk.departures == chk.departures_ref).mean()

# per-rat bout summaries (leavers)
bs = B.groupby(['condition', 'rat']).agg(bouts=('bout', 'size'), returned_pct=('returned', lambda x: 100 * x.mean()), mean_off_s=('off_s', 'mean'),
                                         max_excursion_cm=('max_dist_cm', 'max'), reached_wall=('reached_wall', 'any'), pct_near_platform=('pct_bout_within_30cm', 'mean')).reset_index()
first_ret = B[B.bout == 1].set_index(['condition', 'rat'])
bs = bs.merge(first_ret[['off_s', 'returned']].rename(columns={'off_s': 'first_bout_off_s', 'returned': 'first_bout_returned'}), left_on=['condition', 'rat'], right_index=True)
P = P.merge(bs, on=['condition', 'rat'], how='left')
lat = pd.read_csv(AN / 'updated_anymaze' / 'analysis' / 'results' / 'rat_day_means.csv')
tr = lat[lat.day.between(1, 5)].groupby('rat').agg(lat_d5=('lat', lambda x: np.nan), speed=('speed', 'mean'), thig=('thig', 'mean'))
tr['lat_d5'] = lat[lat.day == 5].set_index('rat').lat; tr['lat_d1'] = lat[lat.day == 1].set_index('rat').lat
P = P.merge(tr, left_on='rat', right_index=True, how='left'); P.loc[P.cohort == 'SP1', ['lat_d5', 'speed', 'thig', 'lat_d1']] = np.nan
P.round(3).to_csv(HERE / 'per_rat.csv', index=False)

S = []  # statistics table
def add(analysis, contrast, test, result, p, note=''): S.append(dict(analysis=analysis, contrast=contrast, test=test, result=result, p=p, note=note))
CONDS = ['SP1 raised', 'KAC standard (1.5 cm)', 'KAC raised (3 cm)']

# ---- 2. survival: time to first departure
fig, ax = plt.subplots(1, 3, figsize=(13, 3.9), sharey=True)
for a, c in zip(ax, CONDS):
    d = P[P.condition == c]; t = d.first_departure_s.fillna(120).clip(lower=.05); ev = d.left.astype(int)
    for s in SEXES:
        m = (d.sex == s).values; sf = SurvfuncRight(t[m], ev[m]); a.step(np.r_[0, sf.surv_times, 120], 100 * np.r_[1, sf.surv_prob, sf.surv_prob[-1]], where='post', color=C[s], lw=2.2, label=f'{s} (n = {m.sum()})')
    st, p = survdiff(t, ev, d.sex); add('Time to first departure', c, 'Log-rank, females vs males', f'chi2 = {st:.2f}', p)
    a.set_title(f'{c}\nlog-rank {pt(p)}', fontsize=11); a.set_xlabel('Seconds since release'); a.set_xlim(0, 120); a.set_ylim(0, 103)
ax[0].set_ylabel('Rats still on the platform (%)'); ax[0].legend(loc='lower left')
fig.tight_layout(); fig.savefig(FIG / '1_time_to_first_departure.png', dpi=300, bbox_inches='tight'); plt.close(fig)
k = P[P.cohort == 'KAC'].copy(); k['female'] = (k.sex == 'Female').astype(int); k['raised'] = (k.day == 8).astype(int)
k['t'] = k.first_departure_s.fillna(120).clip(lower=.05)
cox = PHReg(k.t.values, k[['female', 'raised']].values, status=k.left.astype(int).values).fit(groups=k.rat.values)
for i, nm in enumerate(['Female (vs male)', 'Raised water (vs standard)']):
    hr, lo, hi = np.exp(cox.params[i]), *np.exp(cox.conf_int()[i])
    add('Cox model, KAC (robust SE by rat)', nm, 'Hazard ratio for leaving', f'HR = {hr:.2f} (95% CI {lo:.2f}-{hi:.2f})', cox.pvalues[i])

# ---- 3. whole-design models (KAC, same rats on two days)
gee = smf.gee('left ~ female * raised', groups='rat', data=k.assign(left=k.left.astype(int)), family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
for nm, lab in (('female', 'Female (vs male)'), ('raised', 'Raised water (vs standard)'), ('female:raised', 'Sex x water level')):
    add('Logistic GEE for leaving, KAC', lab, 'Odds ratio', f'OR = {np.exp(gee.params[nm]):.2f}', gee.pvalues[nm], 'large OR for sex: few males left')
mlm = smf.mixedlm('pct_on_platform ~ female * raised', k, groups=k.rat).fit(reml=True)
for nm, lab in (('female', 'Female (vs male)'), ('raised', 'Raised water (vs standard)'), ('female:raised', 'Sex x water level')):
    add('Linear mixed model, % on platform, KAC', lab, 'Coefficient (percentage points)', f'b = {mlm.params[nm]:+.1f}', mlm.pvalues[nm])

# ---- 1. what leavers do (bouts)
for c in CONDS:
    f = B[(B.condition == c) & (B.sex == 'Female')]
    if len(f): add('After leaving (female bouts)', c, 'Descriptive', f'{len(f)} bouts, {100 * f.returned.mean():.0f}% returned, median {f.off_s.median():.1f} s off, median max distance {f.max_dist_cm.median():.0f} cm, {100 * f.reached_wall.mean():.0f}% reached the wall', np.nan)
fl = P[(P.cohort == 'KAC') & (P.sex == 'Female')].pivot(index='rat', columns='day')
for col, lab in (('departures', 'Departures'), ('mean_off_s', 'Mean time off per bout (s)'), ('max_excursion_cm', 'Furthest excursion (cm)'), ('returned_pct', 'Bouts that returned (%)')):
    x = fl[col].dropna()
    if len(x) >= 5: w = stats.wilcoxon(x[6], x[8]); add('KAC females, day 6 vs day 8 (paired, rats that left both days)' if col != 'departures' else 'KAC females, day 6 vs day 8 (paired)', lab, 'Wilcoxon signed-rank', f'{x[6].median():.1f} vs {x[8].median():.1f} (median), n = {len(x)}', w.pvalue)
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for c, mk in zip(CONDS, ('o', 's', '^')):
    for s in SEXES:
        d = B[(B.condition == c) & (B.sex == s)]; ax[0].scatter(d.off_s, d.max_dist_cm, s=26, marker=mk, color=C[s], edgecolor=INK, lw=.4, alpha=.8, label=f'{s}, {c}' if len(d) else None)
ax[0].set_xscale('log'); ax[0].set_xlabel('Time off the platform in the bout (s, log)'); ax[0].set_ylabel('Furthest distance from platform (cm)'); ax[0].set_title('A  Each departure bout'); ax[0].legend(fontsize=7.5, loc='upper center', bbox_to_anchor=(.5, -.16), ncol=2)
ax[0].set_xticks([2, 5, 10, 20, 50]); ax[0].set_xticklabels(['2', '5', '10', '20', '50'])
summ = B[B.sex == 'Female'].groupby('condition').agg(ret=('returned', 'mean'), wall=('reached_wall', 'mean'), near=('pct_bout_within_30cm', 'mean')).reindex(CONDS)
xx = np.arange(3); ww = .26
for i, (col, lab, colr) in enumerate((('ret', 'Came back to the platform', '#2a78d6'), ('wall', 'Reached the wall', '#8a8984'), ('near', 'Time within 30 cm of platform', '#9bc1ee'))):
    v = summ[col] * (100 if col != 'near' else 1); ax[1].bar(xx + (i - 1) * ww, v, ww, color=colr, edgecolor=INK, lw=.6, label=lab)
ax[1].set_xticks(xx); ax[1].set_xticklabels([c.replace(' (', '\n(') for c in CONDS], fontsize=9); ax[1].set_ylabel('% of female departure bouts'); ax[1].set_ylim(0, 105); ax[1].legend(fontsize=8.5, loc='upper center', bbox_to_anchor=(.5, -.16), ncol=1)
ax[1].set_title('B  Where females go after leaving')
fig.tight_layout(); fig.savefig(FIG / '2_after_leaving.png', dpi=300, bbox_inches='tight'); plt.close(fig)

# ---- 4. effect sizes
def hedges(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float); a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)); return (a.mean() - b.mean()) / sp * (1 - 3 / (4 * (len(a) + len(b)) - 9))
rng = np.random.default_rng(1); ES = []
for c in CONDS:
    d = P[P.condition == c]
    for col, lab in (('pct_on_platform', '% on platform'), ('departures', 'Departures')):
        a, b = d[d.sex == 'Male'][col].values, d[d.sex == 'Female'][col].values
        boot = [hedges(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(2000)]
        g = hedges(a, b) if col == 'pct_on_platform' else hedges(b, a); boot = boot if col == 'pct_on_platform' else [-x for x in boot]
        ES.append(dict(label=f'{c}: {lab}', g=g, lo=np.nanpercentile(boot, 2.5), hi=np.nanpercentile(boot, 97.5)))
pw = k.pivot(index='rat', columns='day', values='pct_on_platform').dropna().join(k.groupby('rat').sex.first())
for s in SEXES:
    x = pw[pw.sex == s]; dd = (x[6] - x[8]).values; boot = [np.mean(b) / np.std(b, ddof=1) for b in (rng.choice(dd, len(dd)) for _ in range(2000)) if np.std(b, ddof=1) > 0]
    ES.append(dict(label=f'KAC {s.lower()}s: day 6 vs day 8, % on platform (paired dz)', g=dd.mean() / dd.std(ddof=1), lo=np.percentile(boot, 2.5), hi=np.percentile(boot, 97.5)))
ES = pd.DataFrame(ES); ES.round(3).to_csv(HERE / 'effect_sizes.csv', index=False)
fig, ax = plt.subplots(figsize=(8, 4.2)); y = np.arange(len(ES))[::-1]
ax.errorbar(ES.g, y, xerr=[ES.g - ES.lo, ES.hi - ES.g], fmt='o', color=INK, ecolor=INK2, capsize=3); ax.axvline(0, color=INK2, lw=1)
for v in (.2, .5, .8): ax.axvline(v, color='#e4e3df', lw=1, zorder=0)
ax.set_yticks(y); ax.set_yticklabels(ES.label, fontsize=9); ax.set_xlabel("Effect size (Hedges' g; positive = males stay more / day 6 higher), 95% bootstrap CI")
ax.set_title('Effect sizes: the sex difference is large in every test; the water-level change is small'); fig.tight_layout(); fig.savefig(FIG / '3_effect_sizes.png', dpi=300, bbox_inches='tight'); plt.close(fig)

# ---- 5. does training predict leaving? (KAC, within sex)
fig, ax = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True); kk = k.groupby('rat').agg(pct=('pct_on_platform', 'mean'), sex=('sex', 'first'), lat_d5=('lat_d5', 'first'), speed=('speed', 'first'), thig=('thig', 'first'))
for a, (col, lab) in zip(ax, (('lat_d5', 'Day 5 escape latency (s)'), ('speed', 'Swim speed, days 1-5 (cm/s)'), ('thig', 'Wall-hugging, days 1-5 (%)'))):
    for s in SEXES:
        d = kk[kk.sex == s].dropna(subset=[col]); r = stats.spearmanr(d[col], d.pct); a.scatter(d[col], d.pct, s=30, color=C[s], edgecolor=INK, lw=.5, label=f'{s}: rho = {r[0]:.2f}, {pt(r[1])}')
        add('Training predicts checking? (KAC, Spearman within sex)', f'{lab} vs mean % on platform, {s.lower()}s', 'Spearman', f'rho = {r[0]:.2f}, n = {len(d)}', r[1])
    a.set_xlabel(lab); a.legend(fontsize=8, loc='lower left')
ax[0].set_ylabel('Mean % on platform, days 6 and 8'); fig.suptitle('Does training performance predict staying on the platform? (KAC)', fontweight='bold')
fig.tight_layout(); fig.savefig(FIG / '4_training_vs_checking.png', dpi=300, bbox_inches='tight'); plt.close(fig)

# ---- 6. sensitivity of the sex difference in leaving
SENS = []
for zone_f, min_s in ((1, 1), (.8, 1), (1.2, 1), (1, .5), (1, 2)):
    _, Q = analyse(ZONE * zone_f, min_s)
    for c in CONDS:
        d = Q[Q.condition == c]; fm = int(d[d.sex == 'Female'].left.sum()), int(d[d.sex == 'Male'].left.sum()); nf, nm = (d.sex == 'Female').sum(), (d.sex == 'Male').sum()
        SENS.append(dict(zone=f'{zone_f:.0%} zone', min_bout_s=min_s, condition=c, females_left=f'{fm[0]}/{nf}', males_left=f'{fm[1]}/{nm}', fisher_p=stats.fisher_exact([[fm[0], nf - fm[0]], [fm[1], nm - fm[1]]])[1]))
SENS = pd.DataFrame(SENS); SENS.round(5).to_csv(HERE / 'sensitivity.csv', index=False)
for c in CONDS: add('Sensitivity of "females leave more"', c, "Fisher's exact across 5 zone/bout settings", 'p range ' + f"{SENS[SENS.condition == c].fisher_p.min():.4f}-{SENS[SENS.condition == c].fisher_p.max():.4f}", SENS[SENS.condition == c].fisher_p.max())

ST = pd.DataFrame(S); ST.to_csv(HERE / 'statistics.csv', index=False)
# ---------------- report ----------------
L = ['# Advanced checking-test analysis', '', f'Auto-generated by advanced_analysis.py. Departure counts match the workbook measures for {100 * CONS:.0f}% of KAC trials (same tracks, zone and 1 s rule).', '',
     'Rule: any departure (>= 1 s outside the platform zone) means the rat left. KAC: same rats at standard (day 6, 1.5 cm) and raised water (day 8, 3 cm), fixed order. SP1: raised water only.', '']
for an, g in ST.groupby('analysis', sort=False):
    L += [f'## {an}', '', '| Contrast | Test | Result | p |', '|---|---|---|---|'] + [f"| {r.contrast} | {r.test} | {r.result} | {'' if pd.isna(r.p) else pt(r.p)} |" for r in g.itertuples()] + ['']
L += ['## Effect sizes', '', '| Contrast | g | 95% CI |', '|---|---|---|'] + [f'| {r.label} | {r.g:.2f} | {r.lo:.2f} to {r.hi:.2f} |' for r in ES.itertuples()] + ['',
      '## Caveats', '', '- Few males ever left, so models of leaving have wide intervals for sex, and bout analyses describe mostly females.',
      '- Day 6 vs day 8 is confounded with test order and a camera change; it is not a pure water-depth effect.',
      '- SP1 video is 10 fps and its pool size (172 cm) is assumed; distances in SP1 are approximate.',
      '- Exploratory, uncorrected for multiple tests. The figures are in figures/.']
(HERE / 'REPORT.md').write_text('\n'.join(L), encoding='utf-8'); print('\n'.join(L))
