"""Do rats that leave the checking platform swim toward the platform location they were trained on?
KAC Day 6 only: the training days and Day 6 were filmed by the same webcam, so the training platform maps onto the Day 6 frame.
Training platform = densest resting spot in days 1-5 training tracks, in pool radii from the pool centre: (0.28, -0.355).
Compares each leaving rat's closest approach to that spot with three control spots at the same distance from the pool centre (rotated 90/180/270 deg)."""
import numpy as np, pandas as pd
from scipy import stats
from pathlib import Path
src = open(Path(__file__).with_name('advanced_analysis.py'), encoding='utf-8').read().split("def runs(mask, n):")[0]
ns = {'__file__': str(Path(__file__).with_name('advanced_analysis.py'))}; exec(compile(src, 'loaders', 'exec'), ns)
P1 = np.array([0.28, -0.355]); d6 = [t for t in ns['TR'] if t[2] == 'KAC standard (1.5 cm)']
plat = np.median([np.nanmedian(t[5][:60], axis=0) for t in d6], axis=0); cx, cy, R = d6[0][6]; cm = 86 / R; ZR = 0.165 * R
rot = lambda v, a: np.array([v[0] * np.cos(a) - v[1] * np.sin(a), v[0] * np.sin(a) + v[1] * np.cos(a)])
T = {n: np.array([cx, cy]) + rot(P1, a) * R for n, a in (('trained', 0), ('rot90', np.pi / 2), ('rot180', np.pi), ('rot270', 3 * np.pi / 2))}
rows = []
for coh, day, cond, rat, fps, b, pool in d6:
    off = np.linalg.norm(b - plat, axis=1) > ZR
    if off.sum() < fps: continue
    rows.append(dict(rat=rat, sex='Male' if rat <= 16 else 'Female', off_s=off.sum() / fps,
                     **{f'closest_{k}_cm': np.nanmin(np.linalg.norm(b[off] - v, axis=1)) * cm for k, v in T.items()},
                     **{f'within20_{k}': bool((np.linalg.norm(b[off] - v, axis=1) * cm <= 20).any()) for k, v in T.items()},
                     **{f'pct_off_time_within20_{k}': 100 * np.mean(np.linalg.norm(b[off] - v, axis=1) * cm <= 20) for k, v in T.items()}))
D = pd.DataFrame(rows); D.round(1).to_csv(Path(__file__).with_name('trained_platform_approach_d6.csv'), index=False)
ctrl = D[['closest_rot90_cm', 'closest_rot180_cm', 'closest_rot270_cm']].mean(axis=1)
print(D.round(1).to_string(index=False))
print(f"\nCheck platform px {plat.round(0)}, trained platform px {T['trained'].round(0)}, {np.linalg.norm(plat - T['trained']) * cm:.0f} cm apart")
print(f"Closest approach, trained spot vs mean of 3 controls (median cm): {D.closest_trained_cm.median():.1f} vs {ctrl.median():.1f}; Wilcoxon p = {stats.wilcoxon(D.closest_trained_cm, ctrl).pvalue:.4f}; n = {len(D)}")
print('Rats coming within 20 cm:', {k: int(D[f'within20_{k}'].sum()) for k in T})
dw = D[['pct_off_time_within20_rot90', 'pct_off_time_within20_rot180', 'pct_off_time_within20_rot270']].mean(axis=1)
print(f"Time within 20 cm while off the platform, trained spot vs mean of controls (median %): {D.pct_off_time_within20_trained.median():.1f} vs {dw.median():.1f}; Wilcoxon p = {stats.wilcoxon(D.pct_off_time_within20_trained, dw).pvalue:.4f}")
print(D[[c for c in D if c.startswith('pct_off')]].median().round(1).to_dict())
