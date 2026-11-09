"""User-defined area visit: any valid off-platform sample within 20 cm of P1.

No dwell threshold. Compare with the previous 0.5-s label, retaining the same
complete round trips for a matched comparison. Incomplete paths are reported
separately; lack of an observed visit on them is not treated as failure.
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'dlc_cleaned'))
from tracking_qc import runs
P1 = {'kac_d6': (.28, -.355), 'kac_d8': (.28, -.355), 'sp1': (.4623, -.0624)}
LABEL = {'kac_d6': 'KAC Day 6', 'kac_d8': 'KAC Day 8', 'sp1': 'SP1'}
source = ROOT / 'dlc_explorer/exports'
animals = pd.read_csv(source / 'animal_summary.csv')
events = pd.read_csv(source / 'excursion_segments.csv')
records = []
for (cond, rat), group in events.groupby(['cond', 'rat']):
    with np.load(ROOT / f'dlc_cleaned/cache/{cond}_rat{rat:02d}.npz') as z:
        fps = int(z['fps'])
        assert str(z['model']) == ('best-190' if cond == 'sp1' else 'best-320')
        xy = (z['body'] - z['pool'][:2]) / z['pool'][2]
        distance = np.linalg.norm(xy - np.array(P1[cond]), axis=1) * 86
        near = z['valid'].astype(bool) & z['off'].astype(bool) & (distance <= 20)
        interpolated = z['body_interpolated'].astype(bool)
        for event in group.to_dict('records'):
            a, b = round(event['start'] * fps), round(event['end'] * fps)
            assert z['valid'][a:b].all()
            previous = bool(runs(near[a:b], max(1, round(.5 * fps))))
            # Recompute the historical dwell rule independently. Atlas route labels
            # now use the user's no-dwell definition and cannot validate the old rule.
            hit = bool(near[a:b].any())
            assert hit or not previous
            records.append(dict(**event, area_entry=hit, previous_dwell_visit=previous,
                near_frames=int(near[a:b].sum()), near_seconds=float(near[a:b].sum()/fps),
                entry_without_body_interpolation=bool((near[a:b] & ~interpolated[a:b]).any())))

E = pd.DataFrame(records)
E.to_csv(HERE / 'area_entry_paths.csv', index=False)
complete = E[E.complete]
A = complete.groupby(['cond', 'rat']).agg(paths=('area_entry', 'size'),
    successful_paths=('area_entry', 'sum'), previous_successes=('previous_dwell_visit', 'sum'),
    hits_without_interpolation=('entry_without_body_interpolation', 'sum')).reset_index()
A = A.merge(animals[['cond', 'rat', 'sex', 'head_sweeps_per_min']],
    on=['cond', 'rat'], validate='one_to_one')
A['success_pct'] = 100 * A.successful_paths / A.paths
A.to_csv(HERE / 'area_entry_animals.csv', index=False)
results = []
for cond in LABEL:
    g = A[A.cond == cond]
    incomplete = E[(E.cond == cond) & ~E.complete]
    results.append(dict(cond=cond, animals=len(g), complete_paths=int(g.paths.sum()),
        successful_paths=int(g.successful_paths.sum()), previous_successes=int(g.previous_successes.sum()),
        added_visits=int((g.successful_paths-g.previous_successes).sum()),
        successful_paths_supported_only_by_interpolation=int((g.successful_paths-g.hits_without_interpolation).sum()),
        rho_success_count=float(spearmanr(g.head_sweeps_per_min, g.successful_paths).statistic),
        rho_success_pct=float(spearmanr(g.head_sweeps_per_min, g.success_pct).statistic),
        incomplete_segments=len(incomplete), incomplete_segments_with_observed_entry=int(incomplete.area_entry.sum())))
(HERE / 'area_entry_results.json').write_text(json.dumps(results, indent=2))

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False})
g = A[A.cond == 'kac_d8']
fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
for ax, outcome, label in zip(axs, ['successful_paths', 'success_pct'],
        ['Trips entering the old-platform area', 'Trips entering the area (%)']):
    for sex, color in [('F', '#2878d4'), ('M', '#d65c20')]:
        gg = g[g.sex == sex]
        ax.scatter(gg.head_sweeps_per_min, gg[outcome], color=color, s=65,
            label='Female' if sex == 'F' else 'Male', edgecolor='white', zorder=3)
        for r in gg.itertuples():
            offset, align = {
                31: ((-5, 10), 'right'), 13: ((4, -17), 'left'),
                23: ((-4, 23), 'right'), 18: ((4, -17), 'left'),
                30: ((4, 24), 'left'),
            }.get(r.rat, ((4, 7), 'left'))
            ax.annotate(f'{r.sex}{r.rat} ({r.successful_paths}/{r.paths})',
                (r.head_sweeps_per_min, getattr(r, outcome)),
                xytext=offset, ha=align, textcoords='offset points', fontsize=8)
    ax.set(xlabel='Head sweeps / valid on-platform minute', ylabel=label, xlim=(16, 44))
    ax.grid(axis='y', alpha=.2)
axs[0].set_ylim(-.3, max(g.successful_paths) + .8)
axs[0].set_yticks(range(int(max(g.successful_paths)) + 1))
axs[1].set_ylim(-7, 112)
axs[1].set_yticks([0, 25, 50, 75, 100])
axs[0].legend(loc='upper left')
fig.suptitle('Head sweeping and reaching the old-platform area — KAC Day 8', fontsize=16)
fig.text(.06, .025, 'Any tracked entry within 20 cm; no minimum dwell time. Each dot is one rat. Labels show visits / round trips.\n'
    'Fully observed round trips only. Whole-session sweep rate; association does not establish temporal order. P1 geometry is provisional.', fontsize=9)
fig.tight_layout(rect=(0, .12, 1, .94))
fig.savefig(HERE / 'area_entry_day8.png', dpi=180, bbox_inches='tight')
fig.savefig(HERE / 'area_entry_day8.svg', bbox_inches='tight')
plt.close(fig)
print(json.dumps(results, indent=2))
print('Newly counted complete-path visits:')
print(E[E.complete & E.area_entry & ~E.previous_dwell_visit][['cond', 'rat', 'number', 'near_seconds']].to_string(index=False))
