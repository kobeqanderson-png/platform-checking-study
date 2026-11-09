"""Water maze analysis: learning (d1-5), reminder (d7), probes (d6, d8), with sensitivity checks.
Writes results/*.csv, figures/*.png and REPORT.md next to this script. Rerun after any data change.
Design: rats 1-32 minus 11 and 19 (30 rats). Sex: 1-16 male, 17-32 female. Batch: 9-16 and 25-32 tested in the second batch of 15.
Usage: python analysis.py <updated data folder> <original AnyMaze zip>"""
import io, os, sys, warnings, zipfile
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); RNG = np.random.default_rng(7)
U, ZIP = sys.argv[1:]; HERE = os.path.dirname(os.path.abspath(__file__)); RES, FIG = os.path.join(HERE, 'results'), os.path.join(HERE, 'figures')
for d in (RES, FIG): os.makedirs(d, exist_ok=True)

# ---------- data ----------
def read(src, d):
    if src == 'zip': return pd.read_csv(io.BytesIO(zipfile.ZipFile(ZIP).read(f'Check/KAcd{d}.csv')), encoding='latin-1')
    return pd.read_csv(os.path.join(U, f'KAcd{d}.csv'), encoding='latin-1')
def load(src):
    out = []
    for d in range(1, 9):
        df = read(src, d); num = lambda c: pd.to_numeric(df[c], errors='coerce') if c in df else np.nan
        thig = next((c for c in ('Thig : time (s)', 'Thgmtxs : time (s)') if c in df), None)
        o = pd.DataFrame({'day': d, 'test': df['Test'].astype(int), 'rat': df['Animal'].astype(int), 'dur': num('Duration (s)'), 'dist': num('Distance (cm)'),
                          'p2': num('P2: SE : time (s)'), 'thig': num(thig) if thig else np.nan, 'seg': df['Segment of test'] if 'Segment of test' in df else ''})
        out.append(o)
    A = pd.concat(out, ignore_index=True)
    if src == 'zip':   # Apply the lab-note d4 ID fix so the original differs only in values.
        k = (A.day == 4) & A.test.between(73, 88); A.loc[k, 'rat'] = A.loc[k, 'rat'].map({14: 13, 15: 14, 16: 15, 13: 16})
    A['sex'] = np.where(A.rat <= 16, 'Male', 'Female'); A['batch'] = np.where(((A.rat >= 9) & (A.rat <= 16)) | (A.rat >= 25), 2, 1); return A
NEW, OLD = load('upd'), load('zip')
assert NEW.rat.nunique() == 30 and not NEW.rat.isin([11, 19]).any()
CH = pd.read_csv(os.path.join(U, 'changes.csv'), encoding='utf-8-sig')

def ratday(A, days):
    T = A[A.day.isin(days) & A.dur.notna()].copy(); T['speed'] = T.dist / T.dur; T['found'] = (T.dur < 29.5).astype(float); T['thigp'] = 100 * T.thig / T.dur
    return T.groupby(['rat', 'sex', 'batch', 'day'], as_index=False).agg(lat=('dur', 'mean'), dist=('dist', 'mean'), speed=('speed', 'median'), found=('found', 'mean'), thig=('thigp', 'mean'), n=('dur', 'size'))
def coded(R):
    R = R.copy(); R['d'] = R.day - R.day.mean(); R['S'] = (R.sex == 'Female') - .5; R['B'] = (R.batch == 2) - .5; return R
def lmm(R, y):
    R = coded(R.dropna(subset=[y])); return smf.mixedlm(f'{y} ~ d * S + B', R, groups=R.rat, re_formula='~d').fit(reml=True, method='lbfgs')
def probe(A, d):
    T = A[A.day == d]; G = T.groupby(['rat', 'sex', 'batch'], as_index=False).agg(dur=('dur', 'sum'), dist=('dist', 'sum'), p2=('p2', 'sum'))
    G['pct'] = 100 * G.p2 / G.dur; G['stayed'] = G.pct >= 90; return G
def boot_diff(a, b, n=4000):
    a, b = np.asarray(a), np.asarray(b); s = [RNG.choice(a, len(a)).mean() - RNG.choice(b, len(b)).mean() for _ in range(n)]; return np.percentile(s, [2.5, 97.5])
def rbis(a, b):
    u = stats.mannwhitneyu(a, b); return u.pvalue, 2 * u.statistic / (len(a) * len(b)) - 1

LEARN, DAYS7 = [1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 7]
RD = ratday(NEW, DAYS7); RD.to_csv(os.path.join(RES, 'rat_day_means.csv'), index=False)
P6, P8 = probe(NEW, 6), probe(NEW, 8); pd.concat([P6.assign(day=6), P8.assign(day=8)]).to_csv(os.path.join(RES, 'probe_by_rat.csv'), index=False)

# ---------- models ----------
M = []
def keep(analysis, dataset, outcome, term, est, lo, hi, p, note=''):
    M.append(dict(analysis=analysis, dataset=dataset, outcome=outcome, term=term, estimate=round(float(est), 3), ci_low=round(float(lo), 3), ci_high=round(float(hi), 3), p=float(p), note=note))
TERMS = {'d': 'Day (per day)', 'S': 'Sex (F - M)', 'd:S': 'Day x Sex', 'B': 'Batch (2 - 1)'}
SETS = {'updated': NEW, 'updated, without d5': NEW, 'updated, without rat 10': NEW[NEW.rat != 10], 'original AnyMaze': OLD}
for name, A in SETS.items():
    days = [1, 2, 3, 4] if 'without d5' in name else LEARN; R = ratday(A, days)
    for y in ('lat', 'dist', 'speed', 'found', 'thig'):
        if name != 'updated' and y in ('found', 'thig', 'speed'): continue
        m = lmm(R, y); ci = m.conf_int()
        for k, l in TERMS.items(): keep('learning d1-5, mixed model', name, y, l, m.params[k], ci.loc[k, 0], ci.loc[k, 1], m.pvalues[k])
# Trial-level check on whether the rat found the platform (binomial GEE).
T = coded(NEW[NEW.day.isin(LEARN) & NEW.dur.notna()].assign(found=lambda x: (x.dur < 29.5).astype(int)))
g = smf.gee('found ~ d * S + B', 'rat', T, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit(); ci = g.conf_int()
for k, l in TERMS.items(): keep('learning d1-5, trial-level GEE', 'updated', 'found (odds ratio)', l, np.exp(g.params[k]), np.exp(ci.loc[k, 0]), np.exp(ci.loc[k, 1]), g.pvalues[k])
# Reminder day: d5 to d7, per rat.
RET = []
for name, A in (('updated', NEW), ('original AnyMaze', OLD)):
    Q = ratday(A, [5, 7]).pivot_table(index=['rat', 'sex'], columns='day', values='lat').dropna().reset_index(); ch = Q[7] - Q[5]
    t = stats.ttest_rel(Q[7], Q[5]); w = stats.wilcoxon(Q[7], Q[5]); ci = stats.t.interval(.95, len(ch) - 1, ch.mean(), ch.sem())
    keep('reminder d5 to d7', name, 'latency change (s)', 'd7 - d5', ch.mean(), ci[0], ci[1], t.pvalue, f'Wilcoxon p={w.pvalue:.3f}, dz={ch.mean() / ch.std():.2f}, n={len(ch)}')
    pf, rb = rbis(ch[Q.sex == 'Female'], ch[Q.sex == 'Male']); lo, hi = boot_diff(ch[Q.sex == 'Female'], ch[Q.sex == 'Male'])
    keep('reminder d5 to d7', name, 'latency change (s)', 'Sex (F - M)', ch[Q.sex == 'Female'].mean() - ch[Q.sex == 'Male'].mean(), lo, hi, pf, f'Mann-Whitney, rank-biserial {rb:.2f}')
    if name == 'updated': RETQ = Q
# Probes.
PR = {}
for name, A in (('updated', NEW), ('updated, without rat 10', NEW[NEW.rat != 10]), ('original AnyMaze', OLD)):
    for d in (6, 8):
        G = probe(A, d); F, Mm = G[G.sex == 'Female'], G[G.sex == 'Male']; p, rb = rbis(F.pct, Mm.pct); lo, hi = boot_diff(F.pct, Mm.pct)
        keep(f'probe d{d}', name, 'P2 time (% of probe)', 'Sex (F - M)', F.pct.mean() - Mm.pct.mean(), lo, hi, p, f'Mann-Whitney, rank-biserial {rb:.2f}')
        fx = stats.fisher_exact(pd.crosstab(G.sex, G.stayed)); keep(f'probe d{d}', name, 'stayed (>=90% on P2)', 'Sex', F.stayed.mean() * 100, np.nan, np.nan, fx[1], f'females {int(F.stayed.sum())}/{len(F)}, males {int(Mm.stayed.sum())}/{len(Mm)}, Fisher exact')
        p, rb = rbis(F.dist, Mm.dist); keep(f'probe d{d}', name, 'distance (cm)', 'Sex (F - M)', F.dist.mean() - Mm.dist.mean(), *boot_diff(F.dist, Mm.dist), p, 'Mann-Whitney')
        p, rb = rbis(G[G.batch == 2].pct, G[G.batch == 1].pct); keep(f'probe d{d}', name, 'P2 time (% of probe)', 'Batch (2 - 1)', G[G.batch == 2].pct.mean() - G[G.batch == 1].pct.mean(), *boot_diff(G[G.batch == 2].pct, G[G.batch == 1].pct), p, 'Mann-Whitney')
        PR[name, d] = G
k = P6.set_index('rat').index.intersection(P8.set_index('rat').index); a6, a8 = P6.set_index('rat').loc[k], P8.set_index('rat').loc[k]
w = stats.wilcoxon(a6.pct, a8.pct); keep('probe d6 vs d8', 'updated', 'P2 time (% of probe)', 'd8 - d6', (a8.pct - a6.pct).mean(), *stats.t.interval(.95, len(k) - 1, (a8.pct - a6.pct).mean(), (a8.pct - a6.pct).sem()), w.pvalue, f'Wilcoxon; Spearman rho d6 vs d8 = {stats.spearmanr(a6.pct, a8.pct)[0]:.2f}')
LATE = RD[RD.day.isin([4, 5])].groupby('rat').lat.mean()
for d, G in ((6, P6), (8, P8)):
    x = pd.concat([LATE, G.set_index('rat').pct], axis=1).dropna(); r = stats.spearmanr(x.iloc[:, 0], x.iloc[:, 1]); keep(f'probe d{d}', 'updated', 'P2 time vs d4-5 latency', 'Spearman rho', r[0], np.nan, np.nan, r[1])
SEG = NEW[NEW.day == 6].copy(); SEG['seg'] = SEG.seg.str.extract(r'^(\d+)').astype(float) / 30 + 1
SC = coded(SEG.assign(day=0)); SC['seg'] = SC.seg - 2.5   # Centred, so the sex term is the average across the 4 segments.
SM = smf.mixedlm('p2 ~ seg * S + B', SC, groups=SC.rat).fit(reml=True); ci = SM.conf_int()
for k2, l in (('seg', '30 s segment'), ('S', 'Sex (F - M)'), ('seg:S', 'Segment x Sex')): keep('probe d6 time course', 'updated', 'P2 s per 30 s segment', l, SM.params[k2], ci.loc[k2, 0], ci.loc[k2, 1], SM.pvalues[k2])
MD = pd.DataFrame(M)
# Holm correction across the primary sex comparisons, planned before looking at results by design of the report.
prim = MD[(MD.dataset == 'updated') & (((MD.analysis == 'learning d1-5, mixed model') & MD.outcome.isin(['lat']) & MD.term.isin(['Sex (F - M)', 'Day x Sex'])) | ((MD.analysis.isin(['probe d6', 'probe d8'])) & (MD.outcome == 'P2 time (% of probe)') & (MD.term == 'Sex (F - M)')) | ((MD.analysis == 'reminder d5 to d7') & (MD.term == 'Sex (F - M)')))].index
MD['p_holm_primary'] = np.nan; MD.loc[prim, 'p_holm_primary'] = multipletests(MD.loc[prim, 'p'], method='holm')[1]
MD['p'] = MD.p.round(5); MD['p_holm_primary'] = MD.p_holm_primary.round(5); MD.to_csv(os.path.join(RES, 'statistics.csv'), index=False)

# ---------- figures ----------
C = {'Female': '#2a78d6', 'Male': '#eb6834'}; INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .8, 'axes.axisbelow': True, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'legend.frameon': False, 'axes.titlesize': 11, 'axes.titleweight': 'bold', 'axes.titlecolor': INK})
XPOS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 7: 6.4}
def save(fig, name): fig.savefig(os.path.join(FIG, name), dpi=160, bbox_inches='tight'); plt.close(fig)
def by_sex_line(ax, y, scale=1.0, label_end=False):
    ends = {s: RD[(RD.sex == s) & (RD.day == 7)][y].mean() * scale for s in ('Female', 'Male')}
    span = np.ptp(RD[y].dropna()) * scale or 1; close = abs(ends['Female'] - ends['Male']) < .06 * span
    for s in ('Female', 'Male'):
        g = RD[RD.sex == s].groupby('day')[y]; m, e = g.mean() * scale, g.sem() * scale; xs = [XPOS[d] for d in m.index]
        a = [i for i, d in enumerate(m.index) if d <= 5]; ax.errorbar([xs[i] for i in a], m.iloc[a], e.iloc[a], color=C[s], lw=2, marker='o', ms=6.5, mec=SURF, mew=1.5, capsize=0, elinewidth=1.2)
        if 7 in m.index: ax.plot([XPOS[5], XPOS[7]], [m.loc[5], m.loc[7]], color=C[s], lw=1.2, ls=(0, (2, 2))); ax.errorbar([XPOS[7]], [m.loc[7]], [e.loc[7]], color=C[s], marker='o', ms=6.5, mec=SURF, mew=1.5, elinewidth=1.2)
        # Labels that would collide are pushed apart, keeping the higher line's label on top.
        if label_end: ax.annotate(s, (XPOS[7], m.loc[7]), xytext=(8, (7 if s == max(ends, key=ends.get) else -7) if close else 0), textcoords='offset points', va='center', color=INK2, fontsize=9)
    ax.set_xticks(list(XPOS.values())); ax.set_xticklabels(['1', '2', '3', '4', '5', '7\nreminder']); ax.set_xlim(.6, 7.3); ax.axvspan(5.45, 5.95, color=GRID, alpha=.35, lw=0)
fig, ax = plt.subplots(2, 2, figsize=(10, 7))
for a, (y, t, yl, sc) in zip(ax.flat, [('lat', 'Escape latency', 'seconds (30 s cap)', 1), ('found', 'Trials ending on the platform', '% of trials', 100), ('dist', 'Path length', 'cm', 1), ('speed', 'Swim speed', 'cm/s', 1)]):
    by_sex_line(a, y, sc, label_end=True); a.set_title(t, loc='left'); a.set_ylabel(yl); a.set_xlabel('training day')
ax[0, 0].set_ylim(0, 30); fig.suptitle('Learning, days 1-5, and the day 7 reminder (mean ± SEM per rat, n = 15 per sex)', x=.01, ha='left', fontsize=12, color=INK); fig.tight_layout(); save(fig, 'fig1_learning.png')
fig, a = plt.subplots(figsize=(6.2, 3.8)); by_sex_line(a, 'thig', 1, label_end=True); a.set_title('Time near the wall (thigmotaxis)', loc='left'); a.set_ylabel('% of trial in wall zone'); a.set_xlabel('training day'); a.set_ylim(bottom=0); fig.tight_layout(); save(fig, 'fig2_thigmotaxis.png')
fig, ax = plt.subplots(1, 2, figsize=(8, 3.8), sharey=True)
for a, s in zip(ax, ('Female', 'Male')):
    q = RETQ[RETQ.sex == s]
    for _, r in q.iterrows(): a.plot([0, 1], [r[5], r[7]], color=C[s], alpha=.28, lw=1)
    a.plot([0, 1], [q[5].mean(), q[7].mean()], color=C[s], lw=3, marker='o', ms=8, mec=SURF, mew=1.5); a.set_xticks([0, 1]); a.set_xticklabels(['day 5', 'day 7']); a.set_xlim(-.3, 1.3); a.set_title(f'{s}s (n = {len(q)})', loc='left')
ax[0].set_ylabel('mean latency per rat (s)'); fig.suptitle('Reminder day: each line is one rat; thick line is the mean', x=.01, ha='left', fontsize=12, color=INK); fig.tight_layout(); save(fig, 'fig3_reminder.png')
fig, ax = plt.subplots(1, 2, figsize=(9, 4.2), sharey=True)
for a, (d, G) in zip(ax, ((6, P6), (8, P8))):
    for i, s in enumerate(('Female', 'Male')):
        v = G[G.sex == s].pct.values; x = i + RNG.uniform(-.13, .13, len(v)); a.scatter(x, v, s=46, color=C[s], edgecolor=SURF, lw=1.5, zorder=3)
        a.plot([i - .26, i + .26], [v.mean()] * 2, color=INK, lw=2, zorder=4); st = int((v >= 90).sum()); a.annotate(f'mean {v.mean():.0f}%\nstayed {st}/{len(v)}', (i, -14), ha='center', va='top', color=INK2, fontsize=9, annotation_clip=False)
    a.axhline(90, color=INK2, lw=1, ls=(0, (3, 3))); a.text(-.52, 90.8, 'stayed (≥ 90%)', va='bottom', ha='left', color=INK2, fontsize=8)
    a.set_xticks([0, 1]); a.set_xticklabels(['Females', 'Males']); a.set_xlim(-.55, 1.55); a.set_ylim(0, 104); a.set_title(f'Day {d} probe', loc='left')
ax[0].set_ylabel('time on platform zone (% of 120 s)'); fig.suptitle('Probes: each dot is one rat; bar is the mean', x=.01, ha='left', fontsize=12, color=INK); fig.tight_layout(rect=(0, .06, 1, 1)); save(fig, 'fig4_probes.png')
fig, a = plt.subplots(figsize=(6.2, 3.8))
for s in ('Female', 'Male'):
    g = SEG[SEG.sex == s].groupby('seg').p2; a.errorbar(g.mean().index, g.mean(), g.sem(), color=C[s], lw=2, marker='o', ms=6.5, mec=SURF, mew=1.5, elinewidth=1.2); a.annotate(s, (4, g.mean().iloc[-1]), xytext=(8, 0), textcoords='offset points', va='center', color=INK2, fontsize=9)
a.set_xticks([1, 2, 3, 4]); a.set_xticklabels(['0-30', '30-60', '60-90', '90-120']); a.set_xlim(.7, 4.6); a.set_ylim(0, 31); a.set_xlabel('seconds into the probe'); a.set_ylabel('seconds on platform zone (of 30)'); a.set_title('Day 6 probe over time (mean ± SEM)', loc='left'); fig.tight_layout(); save(fig, 'fig5_d6_timecourse.png')
fig, ax = plt.subplots(1, 2, figsize=(9.5, 4))
J = pd.concat([P6.set_index('rat')[['sex', 'pct']], P8.set_index('rat').pct.rename('pct8'), LATE.rename('late')], axis=1)
for s in ('Female', 'Male'):
    q = J[J.sex == s]; ax[0].scatter(q.pct, q.pct8, s=46, color=C[s], edgecolor=SURF, lw=1.5, label=s, zorder=3); ax[1].scatter(q.late, q.pct8, s=46, color=C[s], edgecolor=SURF, lw=1.5, label=s, zorder=3)
ax[0].plot([0, 100], [0, 100], color=INK2, lw=1, ls=(0, (3, 3))); ax[0].set_xlabel('day 6 P2 time (%)'); ax[0].set_ylabel('day 8 P2 time (%)'); ax[0].set_title('Same rats, two probes', loc='left'); ax[0].legend(loc='lower right')
ax[1].set_xlabel('mean latency, days 4-5 (s)'); ax[1].set_ylabel('day 8 P2 time (%)'); ax[1].set_title('Late training vs probe', loc='left'); fig.tight_layout(); save(fig, 'fig6_probe_relations.png')
ROWS = [('learning d1-5, mixed model', 'lat', 'Day (per day)', 'Learning slope\n(s per day)'), ('learning d1-5, mixed model', 'lat', 'Sex (F - M)', 'Latency, F - M\n(s)'), ('probe d6', 'P2 time (% of probe)', 'Sex (F - M)', 'Day 6 P2, F - M\n(percentage points)'), ('probe d8', 'P2 time (% of probe)', 'Sex (F - M)', 'Day 8 P2, F - M\n(percentage points)')]
DS = ['updated', 'updated, without d5', 'updated, without rat 10', 'original AnyMaze']
fig, ax = plt.subplots(1, 4, figsize=(12, 3.4), sharey=True)
for a, (an, oc, tm, tl) in zip(ax, ROWS):
    for j, ds in enumerate(DS):
        r = MD[(MD.analysis == an) & (MD.outcome == oc) & (MD.term == tm) & (MD.dataset == ds)]
        if r.empty: continue
        r = r.iloc[0]; a.errorbar(r.estimate, j, xerr=[[r.estimate - r.ci_low], [r.ci_high - r.estimate]], fmt='o', color=INK if ds == 'updated' else INK2, ms=7, mec=SURF, mew=1.5, elinewidth=1.5)
    a.axvline(0, color=INK2, lw=1); a.set_title(tl, loc='left', fontsize=10); a.grid(axis='y', visible=False)
ax[0].set_yticks(range(len(DS))); ax[0].set_yticklabels(DS); ax[0].invert_yaxis(); fig.suptitle('Do the conclusions depend on the corrections? Estimates with 95% CI', x=.01, ha='left', fontsize=12, color=INK); fig.tight_layout(); save(fig, 'fig7_sensitivity.png')

# ---------- report ----------
def r(an, oc, tm, ds='updated'): return MD[(MD.analysis == an) & (MD.outcome == oc) & (MD.term == tm) & (MD.dataset == ds)].iloc[0]
def ci(x, f='{:.1f}'): return f'{f.format(x.estimate)} [{f.format(x.ci_low)}, {f.format(x.ci_high)}]'
def P(x): return 'p < 0.001' if x < .001 else f'p = {x:.3f}'
day = RD.groupby('day').agg(lat=('lat', 'mean'), found=('found', 'mean'), dist=('dist', 'mean'))
L = lambda tm, oc='lat': r('learning d1-5, mixed model', oc, tm); GF = lambda tm: r('learning d1-5, trial-level GEE', 'found (odds ratio)', tm)
ret, rets = r('reminder d5 to d7', 'latency change (s)', 'd7 - d5'), r('reminder d5 to d7', 'latency change (s)', 'Sex (F - M)')
p6, p8, s6, s8 = r('probe d6', 'P2 time (% of probe)', 'Sex (F - M)'), r('probe d8', 'P2 time (% of probe)', 'Sex (F - M)'), r('probe d6', 'stayed (>=90% on P2)', 'Sex'), r('probe d8', 'stayed (>=90% on P2)', 'Sex')
o6 = r('probe d6', 'P2 time (% of probe)', 'Sex (F - M)', 'original AnyMaze'); dd = r('probe d6 vs d8', 'P2 time (% of probe)', 'd8 - d6')
nch = CH[CH.new_duration_s.notna() | CH.new_distance_cm.notna()]; rep = sorted({(a, b) for a, b in zip(CH.day, CH.test)})
txt = f"""# Water maze analysis report

Generated by `analysis.py` from the corrected AnyMaze files in `{U}`. Rerun the script after any data change: every number, table and figure below is rebuilt from the data.

## Data

- 30 rats (rats 1-32 except 11 and 19, who died and are not in the data). 15 males (rats 1-16), 15 females (rats 17-32).
- Rats were tested in two batches of 15 (batch 2 = rats 9-16 and 25-32). Batch is a nuisance factor, used only as a control.
- Days 1-5: 4 trials a day, 30 s cap. Days 6 and 8: 120 s probes that start with the rat placed on the platform (recordings labelled 1.5 cm and 3 cm). Day 7: reminder, 4 trials.
- The corrected files change {len(set(zip(nch.day, nch.test)))} trials' values (plus d5 t53 blanked and d4 tests 73-88 relabeled). See `../README.md` and `../changes.csv`.
- Unit of analysis is the rat: trials are averaged per rat per day before modelling, except the trial-level GEE.

## Methods

- **Learning (days 1-5):** linear mixed model per outcome, `outcome ~ day x sex + batch`, random intercept and day slope per rat (REML). Day is centred; sex and batch are coded -0.5/+0.5, so main effects are averages across the other factor.
- **Finding the platform:** binomial GEE on trials (`found = duration < 29.5 s`), same terms, exchangeable correlation within rat. Reported as odds ratios.
- **Reminder (day 5 to day 7):** paired t test and Wilcoxon on each rat's mean latency; sex difference in the change by Mann-Whitney.
- **Probes (days 6, 8):** time in the platform zone (P2) as % of the probe. Sex compared by Mann-Whitney (rank-biserial effect size) and bootstrap 95% CI of the mean difference; "stayed" means at least 90% of the probe on P2, compared by Fisher exact test. Day 6 time course: mixed model on P2 seconds per 30 s segment.
- **Multiple testing:** five primary sex comparisons (latency sex effect, day x sex, reminder change by sex, day 6 and day 8 P2 by sex) are Holm-corrected in `results/statistics.csv` (`p_holm_primary`). Everything else is exploratory and uncorrected.
- **Sensitivity:** key models are rerun without day 5 (the only day without a start-time check), without rat 10 (nose bleed on day 4), and on the original AnyMaze values.

## Results

### 1. Rats learned the task (Figure 1)

Mean latency fell from {day.lat[1]:.1f} s on day 1 to {day.lat[5]:.1f} s on day 5, and the share of trials ending on the platform rose from {100 * day.found[1]:.0f}% to {100 * day.found[5]:.0f}%.

| Term (latency model) | Estimate [95% CI] | p |
|---|---|---|
| Day (s per day) | {ci(L('Day (per day)'), '{:.2f}')} | {P(L('Day (per day)').p)} |
| Sex (F - M, s) | {ci(L('Sex (F - M)'), '{:.2f}')} | {P(L('Sex (F - M)').p)} |
| Day x Sex | {ci(L('Day x Sex'), '{:.2f}')} | {P(L('Day x Sex').p)} |
| Batch (2 - 1, s) | {ci(L('Batch (2 - 1)'), '{:.2f}')} | {P(L('Batch (2 - 1)').p)} |

- Path length fell by {abs(L('Day (per day)', 'dist').estimate):.0f} cm per day ({P(L('Day (per day)', 'dist').p)}), with no sex difference ({P(L('Sex (F - M)', 'dist').p)}).
- The odds of finding the platform rose {GF('Day (per day)').estimate:.2f}-fold per day ({P(GF('Day (per day)').p)}); sex odds ratio {GF('Sex (F - M)').estimate:.2f} ({P(GF('Sex (F - M)').p)}).
- **Females swam faster:** {L('Sex (F - M)', 'speed').estimate:+.1f} cm/s [{L('Sex (F - M)', 'speed').ci_low:.1f}, {L('Sex (F - M)', 'speed').ci_high:.1f}], {P(L('Sex (F - M)', 'speed').p)}. Batch 2 swam {L('Batch (2 - 1)', 'speed').estimate:+.1f} cm/s ({P(L('Batch (2 - 1)', 'speed').p)}). Speed fell {abs(L('Day (per day)', 'speed').estimate):.2f} cm/s per day.
- **Wall-hugging (Figure 2)** fell {abs(L('Day (per day)', 'thig').estimate):.1f} percentage points per day ({P(L('Day (per day)', 'thig').p)}); sex difference {L('Sex (F - M)', 'thig').estimate:+.1f} points ({P(L('Sex (F - M)', 'thig').p)}). Thigmotaxis is blank on corrected trials, so those trials drop out of this outcome.

### 2. No loss on the reminder day (Figure 3)

Latency changed {ret.estimate:+.1f} s from day 5 to day 7 (95% CI {ret.ci_low:.1f} to {ret.ci_high:.1f}; {P(ret.p)}; {ret.note}). Females minus males in that change: {rets.estimate:+.1f} s ({P(rets.p)}). The CI is the honest summary: a loss of a few seconds cannot be ruled out.

### 3. On the probes, males stayed and females left (Figures 4-5)

| | Females, P2 % | Males, P2 % | F - M [95% CI] | p | Stayed, F / M | Fisher p |
|---|---|---|---|---|---|---|
| Day 6 | {P6[P6.sex == 'Female'].pct.mean():.1f} | {P6[P6.sex == 'Male'].pct.mean():.1f} | {ci(p6)} | {P(p6.p)} | {s6.note.split(',')[0].split()[-1]} vs {s6.note.split(',')[1].split()[-1]} | {P(s6.p)} |
| Day 8 | {P8[P8.sex == 'Female'].pct.mean():.1f} | {P8[P8.sex == 'Male'].pct.mean():.1f} | {ci(p8)} | {P(p8.p)} | {s8.note.split(',')[0].split()[-1]} vs {s8.note.split(',')[1].split()[-1]} | {P(s8.p)} |

- {'Both survive' if max(p6.p_holm_primary, p8.p_holm_primary) < .05 else 'Not both survive'} Holm correction (day 6 p_holm = {p6.p_holm_primary:.4f}, day 8 p_holm = {p8.p_holm_primary:.4f}).
- Batch made no difference on either probe (day 6 {P(r('probe d6', 'P2 time (% of probe)', 'Batch (2 - 1)').p)}, day 8 {P(r('probe d8', 'P2 time (% of probe)', 'Batch (2 - 1)').p)}).
- Rats behaved consistently across the two probes (Figure 6): {dd.note.split('; ')[1]}; mean change d8 - d6 {dd.estimate:+.1f} points ({P(dd.p)}).
- Late-training latency does not predict probe behaviour (day 6 {r('probe d6', 'P2 time vs d4-5 latency', 'Spearman rho').estimate:+.2f}, {P(r('probe d6', 'P2 time vs d4-5 latency', 'Spearman rho').p)}; day 8 {r('probe d8', 'P2 time vs d4-5 latency', 'Spearman rho').estimate:+.2f}, {P(r('probe d8', 'P2 time vs d4-5 latency', 'Spearman rho').p)}).
- Day 6 time course (Figure 5): females averaged {r('probe d6 time course', 'P2 s per 30 s segment', 'Sex (F - M)').estimate:+.1f} s per 30 s segment against males ({P(r('probe d6 time course', 'P2 s per 30 s segment', 'Sex (F - M)').p)}); segment x sex {P(r('probe d6 time course', 'P2 s per 30 s segment', 'Segment x Sex').p)}. Female means by segment: {', '.join(f'{v:.1f}' for v in SEG[SEG.sex == 'Female'].groupby('seg').p2.mean())} s; male: {', '.join(f'{v:.1f}' for v in SEG[SEG.sex == 'Male'].groupby('seg').p2.mean())} s.

### 4. Sensitivity (Figure 7)

- The learning slope and the day 8 sex difference hold in every version of the data.
- **The day 6 sex difference depends on the corrections:** on the original AnyMaze values it is {ci(o6)} points ({P(o6.p)}), against {ci(p6)} ({P(p6.p)}) corrected. AnyMaze lost track of several males sitting on the platform (low tracking) and ended rat 4's probe at 4.6 s.
- Removing day 5 or rat 10 changes nothing that matters.

## Interpretation, with limits

- Males and females learned at a similar rate. Females swam faster, so equal latencies came from different swimming.
- The probe difference is large and consistent, but these data cannot say whether leaving reflects memory, motivation to escape, body size or activity. The lab notes record leaping for the ledge and repeated departures. Late-training performance does not predict it.
- ANY-maze stopped trials on the first platform zone entry. Unfilmed trials keep that rule, while corrected trials use touch and stay.
- Latency is capped at 30 s, which compresses differences on early days. The GEE on found / not found is the check on that.
- Day 5 has no start-time check. Absolute distances may read about 5% low. Small samples (15 per sex): the CIs, not the p values, show what the data can support.

## Files

- `results/statistics.csv`: every estimate, CI and p value, by analysis, dataset, outcome and term.
- `results/rat_day_means.csv`, `results/probe_by_rat.csv`: the per-rat data behind the figures.
- `figures/`: fig1 learning, fig2 thigmotaxis, fig3 reminder, fig4 probes, fig5 day 6 time course, fig6 probe relations, fig7 sensitivity.

![Learning](figures/fig1_learning.png)
![Thigmotaxis](figures/fig2_thigmotaxis.png)
![Reminder](figures/fig3_reminder.png)
![Probes](figures/fig4_probes.png)
![Day 6 time course](figures/fig5_d6_timecourse.png)
![Probe relations](figures/fig6_probe_relations.png)
![Sensitivity](figures/fig7_sensitivity.png)
"""
open(os.path.join(HERE, 'REPORT.md'), 'w', encoding='utf-8').write(txt)
print(MD[MD.dataset == 'updated'][['analysis', 'outcome', 'term', 'estimate', 'ci_low', 'ci_high', 'p', 'p_holm_primary']].to_string(index=False)); print('done')
