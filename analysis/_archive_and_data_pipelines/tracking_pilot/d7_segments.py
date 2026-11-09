"""Finds stretches with a rat in the pool in each d7 recording and prints them compactly.
Usage: d7_segments.py <track-folder> <out.csv>"""
import csv, glob, os, sys
import numpy as np
folder, out = sys.argv[1:]
GAP, MINLEN = 4.0, 1.0
rows = []
for f in sorted(glob.glob(os.path.join(folder, 'file*.csv'))):
    R = list(csv.DictReader(open(f, newline='')))
    t = np.array([float(r['t_s']) for r in R]); a = np.array([float(r['area']) for r in R])
    x = np.array([float(r['x_px']) if r['x_px'] else np.nan for r in R]); y = np.array([float(r['y_px']) if r['y_px'] else np.nan for r in R])
    idx = np.where(~np.isnan(x))[0]
    runs = []; s = p = idx[0]
    for i in idx[1:]:
        if t[i] - t[p] > GAP: runs.append((s, p)); s = i
        p = i
    runs.append((s, p))
    runs = [q for q in runs if t[q[1]] - t[q[0]] >= MINLEN]
    name = os.path.basename(f)[:5]
    print(f"\n{name}: span={t[-1]:.0f}s found={100 * len(idx) / len(t):.1f}% runs={len(runs)}")
    prev = None
    for s, e in runs:
        n = e - s + 1; w = np.arange(s, e + 1); ok = w[~np.isnan(x[w])]
        rows.append(dict(file=name, start=round(t[s], 1), end=round(t[e], 1), dur=round(t[e] - t[s], 1), gap_before=round(t[s] - prev, 1) if prev is not None else '',
                         end_x=round(float(np.median(x[ok[-20:]]))), end_y=round(float(np.median(y[ok[-20:]]))), med_area=int(np.median(a[ok])), max_area=int(a[w].max()),
                         path_px=round(float(np.nansum(np.hypot(np.diff(x[ok]), np.diff(y[ok]))))) ))
        prev = t[e]
    print(' '.join(f"{r['dur']:.0f}" + (f"(g{r['gap_before']:.0f})" if r['gap_before'] != '' else '') for r in rows if r['file'] == name))
with open(out, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('\ntotal runs', len(rows), 'of which >=5s', sum(r['dur'] >= 5 for r in rows))
for name in sorted({r['file'] for r in rows}):
    S = [r for r in rows if r['file'] == name and r['dur'] >= 5]
    print(name, 'end position median', int(np.median([r['end_x'] for r in S])), int(np.median([r['end_y'] for r in S])))
