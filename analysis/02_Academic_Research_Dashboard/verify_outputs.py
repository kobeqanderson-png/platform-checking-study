"""Integrity checks across all animals, linked assets, and fully decoded videos."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import cv2
import numpy as np
import pandas as pd
from tracking_qc import runs, derivative, finite

HERE = Path(__file__).resolve().parent
D = pd.read_csv(HERE / 'results/per_rat_measures.csv')
P = pd.read_csv(HERE / 'results/provenance.csv')
assert len(D) == len(P) == 91
assert not D.duplicated(['cond', 'rat']).any()
expected = {'sp1': set(range(1, 33)), 'kac_d6': set(range(2, 33)) - {11, 19}, 'kac_d8': set(range(1, 33)) - {11, 19}}
qc = []
for cond, ids in expected.items():
    assert set(D[D.cond == cond].rat) == ids
for r in D.itertuples():
    z = dict(np.load(HERE / 'cache' / f'{r.cond}_rat{r.rat:02d}.npz'))
    fps = int(z['fps'])
    n = 120 * fps
    valid = z['valid']
    assert len(valid) == n and np.array_equal(valid, finite(z['body']))
    assert str(z['sex']) == r.sex == ('M' if r.rat <= 16 else 'F')
    assert not (z['inside'] & z['off']).any()
    assert np.array_equal(z['inside'] | z['off'], valid)
    assert np.isclose(r.pct_missing, 100 * (~valid).mean())
    assert np.isclose(r.platform_lower_pct, 100 * z['inside'].mean())
    assert np.isclose(r.platform_upper_pct - r.platform_lower_pct, r.pct_missing)
    assert 0 <= r.platform_lower_pct <= r.platform_upper_pct <= 100 + 1e-9
    assert not np.isfinite(z['head_angle'][~valid]).any()
    assert not np.isfinite(z['tail_angle'][~valid]).any()
    for key in [k.removesuffix('_lk') for k in z if k.endswith('_lk')]:
        assert not np.isfinite(z[key][~valid]).any(), (r.cond, r.rat, key)
    for a, b in runs(z['body_interpolated']):
        assert a > 0 and b < n and b - a <= round(.5 * fps)
        assert valid[a-1] and valid[b]
    velocity = derivative(z['body'], fps)
    starts = valid & ~np.r_[False, valid[:-1]]
    assert not np.isfinite(velocity[starts]).any()
    assert not np.isfinite(z['drift'][starts]).any()
    provenance = P[(P.cond == r.cond) & (P.rat == r.rat)].iloc[0]
    assert hashlib.sha256(Path(provenance.source).read_bytes()).hexdigest() == provenance.sha256
    qc.append({'cond': r.cond, 'rat': r.rat, 'max_retained_speed_cm_s': float(np.nanmax(np.linalg.norm(velocity, axis=1) * 86 / z['pool'][2])),
               'initial_unknown_s': (np.flatnonzero(valid)[0] / fps) if valid.any() else 120})
E = pd.read_csv(HERE / 'results/lean_out_events.csv')
assert not E.duplicated(['cond', 'rat', 'frame', 'kind']).any()
assert np.isfinite(E.idphi_2s_before).all()
assert len(pd.read_csv(HERE / 'results/paired_rats.csv')) == 29
legacy = pd.read_csv(HERE.parent / 'dlc_measures/sp1_checking_dlc_measures.csv')
mapping = pd.read_csv(HERE.parent / 'dlc_measures/sp1_checking_dlc_vs_anymaze.csv')
amap = dict(zip(mapping.Test, mapping.animal.str.replace('rat', '', regex=False).astype(int)))
assert (legacy.rat == legacy.test.map(amap)).all()
assert (legacy.sex == legacy.rat.map(lambda r: 'M' if r <= 16 else 'F')).all()

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href') and value and not value.startswith(('http:', 'https:', '#')):
                self.assets.append(value)
links = Links()
links.feed((HERE / 'report.html').read_text(encoding='utf-8'))
for asset in links.assets:
    p = (HERE / asset).resolve()
    assert p.is_relative_to(HERE) and p.is_file() and p.stat().st_size > 0, asset
manifest = json.loads((HERE / 'demos/manifest.json').read_text())
assert len(manifest) == 9
ffmpeg = shutil.which('ffmpeg')
assert ffmpeg
def verify_video(v):
    p = HERE / 'demos' / v['file']
    cap = cv2.VideoCapture(str(p))
    assert cap.isOpened(), p
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    assert count == v['frames']
    duration = count / fps
    assert abs(duration - (v['end_s'] - v['start_s']) / v['playback_speed']) < .1
    result = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(p), '-f', 'null', '-'], capture_output=True, text=True)
    assert result.returncode == 0 and not result.stderr.strip(), (p, result.stderr)
    return {'file': p.name, 'frames': count, 'fps': fps, 'seconds': duration, 'full_decode': 'passed'}
with ThreadPoolExecutor(max_workers=3) as executor:
    videos = list(executor.map(verify_video, manifest))
pd.DataFrame(qc).to_csv(HERE / 'results/additional_qc.csv', index=False)
summary = {'animal_caches': len(D), 'source_hashes_verified': len(P), 'paired_animals': 29,
           'local_asset_links_verified': len(links.assets), 'legacy_sp1_labels': 'correct',
           'unit_tests': 'Run test_tracking_qc.py separately; six regression tests',
           'videos': videos, 'visual_review': '15 figure images and sampled frames from every demo reviewed; no exhaustive behavioral annotation'}
(HERE / 'results/verification.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
