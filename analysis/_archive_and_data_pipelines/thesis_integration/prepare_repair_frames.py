"""Extract targeted original-resolution frames; write no predictions as human labels."""
from pathlib import Path
import sys,json,copy
import numpy as np,pandas as pd,cv2,yaml
AN=Path(__file__).resolve().parents[1]; ROOT=AN.parent
sys.path.insert(0,str(AN/'dlc_cleaned'))
from tracking_qc import clean_track,runs
OUT=ROOT/'training_packages/KAcheck_targeted_repair_20261108';OUT.mkdir(exist_ok=True)
template=yaml.safe_load((ROOT/'training_packages/train_KAcheck_d6d8_v2_20261107/KAcheck_d6d8_v2_20261107/config.yaml').read_text())
files=list((AN/'checking_completion/inputs').rglob('*.h5'))
spec=[('repair','kac_d8',r,4) for r in (17,18,21,22)]+[('repair','kac_d6',r,2) for r in (18,22,26,30)]
spec += [('audit','kac_d8',r,2) for r in (20,24,28,32)]+[('audit','kac_d6',r,2) for r in (21,31)]
manifest=[];thumbs={'repair':[],'audit':[]}; rows={}; videos={'repair':{},'audit':{}}
for split,cond,rat,count in spec:
 z={k:v.item() if v.ndim==0 else v for k,v in dict(np.load(AN/'dlc_cleaned/cache'/f'{cond}_rat{rat:02d}.npz')).items()}
 fps=z['fps']; prior=None; q=z
 if cond=='kac_d8':
  candidates=[f for f in files if f.parent.name=='d8_tracks' and f.name.startswith(f'Test_{z["test"]}DLC') and f.name.endswith('best-400.h5')];assert len(candidates)==1
  df=pd.read_hdf(candidates[0]);df.columns=df.columns.droplevel(0);a=round(z['start']*fps);df=df.iloc[a:a+120*fps].reset_index(drop=True)
  prior=clean_track(df,z['pool'],cond,fps);q=prior
 indices=[]
 # Persistent gaps first, then false points/jumps and current-model failures.
 candidates=[]
 for mask in [~q['valid'],q['spot_rejected'],q['speed_rejected'],~z['valid']]:
  for a,b in sorted(runs(mask),key=lambda ab:ab[1]-ab[0],reverse=True): candidates.append((a+b-1)//2)
 for i in candidates:
  if 3*fps<=i<117*fps and all(abs(i-j)>=2*fps for j in indices): indices.append(i)
  if len(indices)==count: break
 assert len(indices)==count,(cond,rat,len(indices))
 cap=cv2.VideoCapture(z['video']);assert cap.isOpened(),z['video']
 folder=Path(z['video']).stem; project=OUT/split; target=project/'labeled-data'/folder;target.mkdir(parents=True,exist_ok=True)
 videos[split][z['video']]={'crop':f'0, {int(cap.get(3))}, 0, {int(cap.get(4))}'}
 for i in sorted(indices):
  source_frame=round(z['start']*fps)+i;cap.set(cv2.CAP_PROP_POS_FRAMES,source_frame);ok,frame=cap.read();assert ok
  name=f'img{source_frame:06d}.png';dest=target/name;assert cv2.imwrite(str(dest),frame)
  reason='earlier model unresolved gap' if prior is not None and not prior['valid'][i] else ('earlier model rejected point' if prior is not None and prior['rejected'][i] else 'current model rejected point/gap')
  entry=dict(split=split,condition=cond,rat=rat,test=z['test'],source_video=z['video'],source_frame=source_frame,
    fps=fps,trial_time_s=i/fps,reason=reason,image=str(dest),width=frame.shape[1],height=frame.shape[0])
  manifest.append(entry);rows.setdefault((split,folder),[]).append(('labeled-data',folder,name))
  tile=cv2.resize(frame,(320,240));bar=np.full((42,320,3),255,np.uint8)
  cv2.putText(bar,f'{cond} rat {rat} | {i/fps:.1f}s',(5,17),0,.46,(0,0,0),1)
  cv2.putText(bar,name,(5,35),0,.42,(0,0,0),1);thumbs[split].append(np.vstack([bar,tile]))
 cap.release()
for (split,folder),idx in rows.items():
 cols=pd.MultiIndex.from_product([['Kobe'],template['bodyparts'],['x','y']],names=['scorer','bodyparts','coords'])
 df=pd.DataFrame(np.nan,index=pd.MultiIndex.from_tuples(idx),columns=cols)
 p=OUT/split/'labeled-data'/folder
 df.to_hdf(p/'CollectedData_Kobe.h5',key='df_with_missing',mode='w');df.to_csv(p/'CollectedData_Kobe.csv')
for split in ('repair','audit'):
 cfg=copy.deepcopy(template);cfg['Task']='KAcheck_targeted_'+split;cfg['project_path']=str(OUT/split);cfg['video_sets']=videos[split]
 (OUT/split/'config.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
 ts=thumbs[split];contact=np.vstack([np.hstack(ts[i:i+4]) for i in range(0,len(ts),4)])
 cv2.imwrite(str(OUT/f'{split}_contact.jpg'),contact)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
pd.DataFrame(manifest).to_csv(OUT/'manifest.csv',index=False)
assert len(manifest)==36 and sum(x['split']=='repair' for x in manifest)==24
print('Prepared 24 repair frames and 12 separate audit frames. Blank labels; original-resolution PNGs.',flush=True)
