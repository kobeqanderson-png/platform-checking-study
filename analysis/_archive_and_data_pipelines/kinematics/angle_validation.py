"""Do DLC angles match hand-labelled angles? Compares the final KAC model (v3rot, best-320) with the hand labels on held-out frames.
Usage: python -I angle_validation.py   (prints a table and writes angle_validation.csv)"""
import pickle, numpy as np, pandas as pd
from pathlib import Path
R = Path(r"G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs\KAcheck_d6d8_v3rot_20261108")
lab = pd.read_hdf(R / "training-datasets/iteration-0/UnaugmentedDataSet_KAcheck_d6d820261108/CollectedData_Kobe.h5"); lab.columns = lab.columns.droplevel(0)
pred = pd.read_hdf(R / "evaluation-results-pytorch/iteration-0/KAcheck_d6d820261108-trainset85shuffle1/DLC_Resnet50_KAcheck_d6d820261108shuffle1_snapshot_best-320.h5"); pred.columns = pred.columns.droplevel([0, 1]); pred = pred.reindex(lab.index)  # same frames, same order as the labels
class Safe(pickle.Unpickler):  # data only: numpy arrays and plain Python containers, nothing executable
    def find_class(self, mod, name):
        if mod.split('.')[0] in ('numpy', 'builtins', 'collections', 'copyreg', 'codecs'): return super().find_class(mod, name)
        raise pickle.UnpicklingError(f'blocked {mod}.{name}')
doc = Safe(open(R / "training-datasets/iteration-0/UnaugmentedDataSet_KAcheck_d6d820261108/Documentation_data-KAcheck_d6d8_85shuffle1.pickle", 'rb')).load()
test = [i for i in doc[2]]; print('frames:', len(lab), 'held out:', len(test))
def angles(df, conf=None):
    g = lambda p: df[p][['x', 'y']].to_numpy(float)
    ok = np.ones(len(df), bool) if conf is None else np.all([df[p]['likelihood'].to_numpy() >= .6 for p in ('nose', 'neck', 'spine_mid', 'tail_base', 'left_hip', 'right_hip')], axis=0)
    ax = g('neck') - g('spine_mid'); L = np.linalg.norm(g('neck') - g('tail_base'), axis=1)
    ang = lambda v: np.degrees(np.arctan2(ax[:, 0] * v[:, 1] - ax[:, 1] * v[:, 0], (ax * v).sum(1)))
    u = ax / np.linalg.norm(ax, axis=1, keepdims=True); hm = (g('left_hip') + g('right_hip')) / 2 - g('spine_mid')
    return pd.DataFrame({'tail_angle_deg': ang(g('spine_mid') - g('tail_base')) , 'hip_offset_BL': (u[:, 0] * hm[:, 1] - u[:, 1] * hm[:, 0]) / L,
                         'head_yaw_deg': ang(g('nose') - g('neck'))}).where(np.repeat(ok[:, None], 3, axis=1))
A, B = angles(lab.iloc[test]), angles(pred.iloc[test], conf=True)
A['tail_angle_deg'] = ((A.tail_angle_deg + 180) % 360) - 180  # wrap
out = []
for c in A:
    d = (B[c] - A[c]); d = ((d + 180) % 360 - 180) if 'deg' in c else d; ok = d.notna()
    out.append(dict(measure=c, frames=int(ok.sum()), median_abs_error=d[ok].abs().median(), p90_abs_error=d[ok].abs().quantile(.9),
                    true_spread_sd=A[c][ok].std(), r=np.corrcoef(A[c][ok], B[c][ok])[0, 1]))
T = pd.DataFrame(out).round(3); T.to_csv(Path(__file__).with_name('angle_validation.csv'), index=False); print(T.to_string(index=False))
