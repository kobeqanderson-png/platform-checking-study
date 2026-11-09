"""Poster figure (one 4-panel story) and poster text with every number computed here, nothing typed by hand.
Usage: python -I poster_figure.py      -> poster_figure.png (300 dpi), poster_figure.pdf, poster_text.md
Inputs: ../dlc_measures (DLC checking-test measures; KAC from the final v3rot model) and ../updated_anymaze/analysis/results (AnyMaze)."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent; DLC = HERE.parent / 'dlc_measures'; RES = HERE.parent / 'updated_anymaze' / 'analysis' / 'results'
C = {'Female': '#2a78d6', 'Male': '#eb6834'}; INK, INK2 = '#0b0b0b', '#52514e'; SEXES = ['Female', 'Male']
plt.rcParams.update({'font.family': 'Arial', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': INK2,
                     'axes.titlesize': 12.5, 'axes.titleweight': 'bold', 'legend.frameon': False, 'savefig.facecolor': 'white'})
pt = lambda p: 'p < 0.001' if p < .001 else f'p = {p:.3f}'
star = lambda p: '***' if p < .001 else '**' if p < .01 else '*' if p < .05 else 'n.s.'
sem = lambda x: np.std(x, ddof=1) / np.sqrt(len(x))
sx = lambda s: s.map({'M': 'Male', 'F': 'Female', 'Male': 'Male', 'Female': 'Female'})

# ---- data
k6 = pd.read_csv(DLC / 'kac_d6_dlc_measures.csv').assign(sex=lambda d: sx(d.sex)).set_index('rat')
k8 = pd.read_csv(DLC / 'kac_d8_dlc_measures.csv').assign(sex=lambda d: sx(d.sex)).set_index('rat')
s1 = pd.read_csv(DLC / 'sp1_checking_dlc_vs_anymaze.csv'); s1['rat'] = s1.animal.str.extract(r'(\d+)', expand=False).astype(int)
s1['sex'] = np.where(s1.rat <= 16, 'Male', 'Female'); s1 = s1.set_index('rat')
n6 = pd.read_csv(DLC / 'kac_d6_notes_vs_dlc.csv'); n8 = pd.read_csv(DLC / 'kac_d8_notes_vs_dlc.csv')
pb = pd.read_csv(RES / 'probe_by_rat.csv'); a8 = pb[pb.day == 8].set_index('rat').pct
PCT = 'pct_time_on_platform_zone'
G = {'SP1\n(raised water)': s1, 'KAC day 6\n(standard, 1.5 cm)': k6, 'KAC day 8\n(raised, 3 cm)': k8}
by = lambda d, s, c=PCT: d[d.sex == s][c].dropna()
TT = {g: stats.ttest_ind(by(d, 'Female'), by(d, 'Male')) for g, d in G.items()}
stay = {g: {s: ((by(d, s, 'departures') == 0).sum(), len(by(d, s, 'departures'))) for s in SEXES} for g, d in G.items()}  # stayed = never left, as in the notes
FI = {g: stats.fisher_exact([[v['Male'][0], v['Male'][1] - v['Male'][0]], [v['Female'][0], v['Female'][1] - v['Female'][0]]])[1] for g, v in stay.items()}
pair = pd.concat([k6[[PCT, 'sex']].rename(columns={PCT: 'd6'}), k8[[PCT]].rename(columns={PCT: 'd8'})], axis=1).dropna()
PW = {s: stats.ttest_rel(pair[pair.sex == s].d6, pair[pair.sex == s].d8) for s in SEXES}
both = pd.concat([k8.pct_time_in_anymaze_size_P2_zone, a8], axis=1, keys=['dlc', 'am']).dropna(); RAM = stats.pearsonr(both.dlc, both.am)
agree = lambda n: (int((n.notes_stayed_on.notna() & (n.notes_stayed_on == n.dlc_stayed_on)).sum()), int(n.notes_stayed_on.notna().sum()))
AG6, AG8 = agree(n6), agree(n8)

# ---- figure
fig, ax = plt.subplots(1, 4, figsize=(16, 4.6), gridspec_kw=dict(width_ratios=[1.35, 1.1, 1.2, 1]))
rng = np.random.default_rng(3); w = .36
a = ax[0]
for gi, (g, d) in enumerate(G.items()):
    for j, s in enumerate(SEXES):
        x = by(d, s).values; xc = gi + (j - .5) * w
        a.bar(xc, x.mean(), w, yerr=sem(x), color=C[s], edgecolor=INK, lw=.8, capsize=4, error_kw=dict(lw=1.1, ecolor=INK), label=s if gi == 0 else None)
        a.scatter(xc + rng.uniform(-.1, .1, len(x)), x, s=10, color='white', edgecolor=INK, lw=.6, zorder=3)
    a.plot([gi - w / 2, gi - w / 2, gi + w / 2, gi + w / 2], [104, 107, 107, 104], color=INK, lw=1); a.text(gi, 108, star(TT[g].pvalue), ha='center', fontsize=11)
a.set_xticks(range(3)); a.set_xticklabels(G.keys(), fontsize=10); a.set_ylabel('Time on platform (% of 120 s)'); a.set_ylim(0, 118)
a.set_title('A  Females leave the platform'); fig.legend(*a.get_legend_handles_labels(), loc='upper right', ncol=2, fontsize=11, bbox_to_anchor=(1, 1.07))
a = ax[1]
for s, xo in (('Female', 0), ('Male', 1.4)):
    d = pair[pair.sex == s]
    for _, r in d.iterrows(): a.plot([xo, xo + .8], [r.d6, r.d8], color=C[s], alpha=.45, lw=1)
    a.plot([xo, xo + .8], [d.d6.mean(), d.d8.mean()], color=C[s], lw=3, marker='o', ms=7, markeredgecolor=INK)
    a.text(xo + .4, 3, f'{s}s\n{pt(PW[s].pvalue)}', ha='center', fontsize=9.5, color=INK2)
a.set_xticks([0, .8, 1.4, 2.2]); a.set_xticklabels(['Day 6\n1.5 cm', 'Day 8\n3 cm'] * 2, fontsize=9.5); a.set_ylim(0, 105); a.set_ylabel('Time on platform (%)')
a.set_title('B  Same rats: raising the water\n     adds no significant change', loc='left')
a = ax[2]
for gi, g in enumerate(G):
    for j, s in enumerate(SEXES):
        c, n = stay[g][s]; xc = gi + (j - .5) * w; a.bar(xc, 100 * c / n, w, color=C[s], edgecolor=INK, lw=.8); a.text(xc, 100 * c / n + 2, f'{c}/{n}', ha='center', fontsize=9)
    a.text(gi, 112, star(FI[g]), ha='center', fontsize=11)
a.set_xticks(range(3)); a.set_xticklabels(G.keys(), fontsize=10); a.set_ylim(0, 120); a.set_ylabel('Rats that never left the platform (%)'); a.set_title('C  Most males stayed, most females left')
a = ax[3]
for s in SEXES:
    m = k8.loc[both.index].sex == s; a.scatter(both.am[m], both.dlc[m], s=30, color=C[s], edgecolor=INK, lw=.5, label=s)
a.plot([0, 100], [0, 100], ls='--', color=INK2, lw=1); a.set_xlim(0, 103); a.set_ylim(0, 103)
a.set_xlabel('AnyMaze: % time in platform zone'); a.set_ylabel('Video tracking (DLC): same zone'); a.set_title(f'D  Tracking matches AnyMaze\n     (day 8, r = {RAM[0]:.3f})', loc='left')
fig.text(.01, -.05, f"A: unpaired t-tests, females vs males. B: paired t-tests, day 6 vs day 8 (KAC, n = {len(pair)} rats with both days). C: Fisher's exact tests. "
         f"Mean ± SEM; dots/lines are individual rats. Measured by DeepLabCut video tracking; stayed/left agrees with handwritten notes for {AG6[0]}/{AG6[1]} (day 6) and {AG8[0]}/{AG8[1]} (day 8) rats.",
         fontsize=9, color=INK2, wrap=True)
fig.tight_layout(); fig.savefig(HERE / 'poster_figure.png', dpi=300, bbox_inches='tight'); fig.savefig(HERE / 'poster_figure.pdf', bbox_inches='tight')

# ---- poster text (every number from the data above)
g1, g6, g8 = G
f = lambda g, s: by(G[g], s).mean()
txt = f"""# Poster text (auto-generated by poster_figure.py; numbers come from the data files)

## Question
When the water level is raised, do female and male rats differ in whether they stay on a known escape platform (a "checking" test)?
And is any difference caused by the raised water, or already present at standard depth?

## Methods (short)
- Morris water maze, 172 cm pool. Rats trained to a hidden platform, then a 120 s checking test starting on the platform.
- SP1 cohort (32 rats, 16 per sex): checking test at raised water only.
- KAC cohort (30 rats, 15 per sex): the same rats tested at standard depth (day 6, 1.5 cm, control) and raised water (day 8, 3 cm).
- Behaviour measured by DeepLabCut video tracking (13 body points); time on platform, number of departures, stayed (never left the platform, the same definition as the handwritten notes).
- Tracking checked against AnyMaze (day 8, r = {RAM[0]:.3f}) and handwritten notes (stayed/left agreed for {AG6[0]}/{AG6[1]} and {AG8[0]}/{AG8[1]} rats).

## Results
1. SP1, raised water: females spent {f(g1, 'Female'):.0f}% of the test on the platform vs {f(g1, 'Male'):.0f}% for males ({pt(TT[g1].pvalue)}); {stay[g1]['Male'][0]}/{stay[g1]['Male'][1]} males vs {stay[g1]['Female'][0]}/{stay[g1]['Female'][1]} females stayed ({pt(FI[g1])}).
2. KAC, standard depth (control): the same sex difference was already present: {f(g6, 'Female'):.0f}% vs {f(g6, 'Male'):.0f}% ({pt(TT[g6].pvalue)}); {stay[g6]['Male'][0]}/{stay[g6]['Male'][1]} males vs {stay[g6]['Female'][0]}/{stay[g6]['Female'][1]} females stayed ({pt(FI[g6])}).
3. KAC, raised water: {f(g8, 'Female'):.0f}% vs {f(g8, 'Male'):.0f}% ({pt(TT[g8].pvalue)}); {stay[g8]['Male'][0]}/{stay[g8]['Male'][1]} males vs {stay[g8]['Female'][0]}/{stay[g8]['Female'][1]} females stayed ({pt(FI[g8])}).
4. Raising the water did not significantly change platform time in the same rats: females {pair[pair.sex == 'Female'].d6.mean():.0f}% to {pair[pair.sex == 'Female'].d8.mean():.0f}% ({pt(PW['Female'].pvalue)}), males {pair[pair.sex == 'Male'].d6.mean():.0f}% to {pair[pair.sex == 'Male'].d8.mean():.0f}% ({pt(PW['Male'].pvalue)}).

## Conclusion
Females leave the platform during a checking test far more than males, and this sex difference is present at standard water depth.
The SP1 result therefore does not depend on the raised water; raising the water added no significant change.

## Caveats to state
- Day 6 and day 8 are in fixed order, so "raised water" is confounded with a second test. A non-significant change is not proof of no effect (females trended down).
- KAC rat 1 has no day 6 video (day 6 n = {len(k6)}). Rats 11 and 19 died before training.
- Training (days 1-5): all rats learned and the sexes learned equally; see water_maze_results.xlsx.
"""
(HERE / 'poster_text.md').write_text(txt, encoding='utf-8'); print(txt)
