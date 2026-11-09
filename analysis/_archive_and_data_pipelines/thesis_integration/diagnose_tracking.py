from pathlib import Path
import sys
import numpy as np,pandas as pd
HERE=Path(__file__).parent;AN=HERE.parent
sys.path.insert(0,str(AN/'dlc_cleaned'))
from tracking_qc import clean_track
rows=[]
files=list((AN/'checking_completion/inputs').rglob('*.h5'))
for p in sorted((AN/'dlc_cleaned/cache').glob('kac_d8*.npz')):
    z=dict(np.load(p)); test=int(z['test']);rat=int(z['rat']);fps=int(z['fps']);start=round(float(z['start'])*fps)
    for model in ('best-240','best-400'):
        matches=[f for f in files if f.parent.name=='d8_tracks' and f.name.startswith(f'Test_{test}DLC') and f.name.endswith(model+'.h5')]
        assert len(matches)==1,(test,model,matches)
        df=pd.read_hdf(matches[0]);df.columns=df.columns.droplevel(0);df=df.iloc[start:start+120*fps].reset_index(drop=True)
        q=clean_track(df,z['pool'],'kac_d8',fps)
        rows.append(dict(rat=rat,sex='M' if rat<=16 else 'F',model=model,
            missing_pct=100*(~q['valid']).mean(),spot_pct=100*q['spot_rejected'].mean(),
            outside_pct=100*q['outside_rejected'].mean(),speed_pct=100*q['speed_rejected'].mean()))
d=pd.DataFrame(rows);d.to_csv(HERE/'tracking_model_diagnostic.csv',index=False)
print('Same Day 8 videos, same QC rules:');print(d.groupby(['model','sex']).mean(numeric_only=True).drop(columns='rat').round(2).to_string())
s=pd.read_csv(AN/'dlc_cleaned/results/speed_sensitivity.csv')
print('Speed threshold sensitivity, Day 8 females:');print(s[(s.cond=='kac_d8')&(s.sex=='F')].groupby('speed_limit').pct_missing.mean().round(2).to_string())
print('Raw mask rates for current model, by cohort:')
x=pd.read_csv(AN/'dlc_cleaned/results/per_rat_measures.csv');print(x.groupby(['cond','sex'])[['pct_missing','pct_spot_rejected','pct_outside_rejected','pct_speed_rejected']].mean().round(2).to_string())
