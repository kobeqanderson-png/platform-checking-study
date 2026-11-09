"""Exploratory test of a video-derived hypothesis, using existing final caches.

Chosen for this exploratory check: 5-s predeparture head rotation; initial 1-s heading
error and up-to-5-s radial progress/path length. One first departure per animal.
Day 6 is the primary geometry; Day 8/SP1 are conditional sensitivity contexts.
"""
from pathlib import Path
import json
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
CLEAN=HERE.parent/'dlc_cleaned'
sys.path.insert(0,str(CLEAN))
from tracking_qc import platform_events, runs, swings
P1={'kac_d6':(.28,-.355),'kac_d8':(.28,-.355),'sp1':(.4623,-.0624)}
LABEL={'kac_d6':'KAC Day 6','kac_d8':'KAC Day 8','sp1':'SP1'}


def correlation(x,y):
    mask=np.isfinite(x)&np.isfinite(y);x=np.asarray(x)[mask];y=np.asarray(y)[mask]
    if len(x)<4 or np.ptp(x)==0 or np.ptp(y)==0:
        return dict(n=len(x),rho=None,p=None)
    rho=float(stats.spearmanr(x,y).statistic)
    # Monte Carlo permutation of ranks; avoids small-sample asymptotic p-values.
    rng=np.random.default_rng(20261108)
    a=stats.rankdata(x);b=stats.rankdata(y);a-=a.mean();b-=b.mean()
    denom=np.linalg.norm(a)*np.linalg.norm(b)
    count=0;reps=19999
    for _ in range(reps):
        count+=abs(np.dot(a,rng.permutation(b))/denom)>=abs(rho)-1e-12
    return dict(n=len(x),rho=rho,p=(count+1)/(reps+1))


rows=[]
for f in sorted((CLEAN/'cache').glob('*.npz')):
    z={k:v.item() if v.ndim==0 else v for k,v in dict(np.load(f)).items()}
    c=z['cond'];fps=int(z['fps']);body=z['body'];valid=z['valid'].astype(bool)
    ins,off,events=platform_events(body,z['platform'],.165*z['pool'][2],fps)
    row=dict(cond=c,rat=int(z['rat']),sex=z['sex'],model=z['model'],included=False,reason='',
        scanning_deg_s=np.nan,head_sweeps_per_valid_min=np.nan,heading_error_deg=np.nan,progress_per_path=np.nan,
        initial_straightness=np.nan,path_cm=np.nan,outbound_seconds=np.nan,interpolated_pct=np.nan)
    if not events:
        row['reason']='no observed departure';rows.append(row);continue
    e=events[0];a=e['frame'];row['first_departure_s']=a/fps
    if not e['exact'] or not valid[:a+1].all():
        row['reason']='first departure uncertain due to earlier tracking gap';rows.append(row);continue
    if a<5*fps or not ins[a-5*fps:a].all():
        row['reason']='fewer than 5 continuously on-platform seconds before departure';rows.append(row);continue
    angle=z['head_angle'][a-5*fps:a]
    d=np.degrees(np.diff(angle));good=np.isfinite(d)
    row['head_pair_coverage_pct']=100*good.mean()
    if good.mean()<.8:
        row['reason']='under 80% usable head-angle pairs in predeparture window';rows.append(row);continue
    row['scanning_deg_s']=float(np.mean(np.abs(d[good]))*fps)
    sweep_count=len(swings(angle,np.isfinite(angle),fps,30))
    row['head_sweep_count']=sweep_count
    row['head_sweeps_per_valid_min']=60*sweep_count/(np.isfinite(angle).sum()/fps)
    p1=np.array(z['pool'][:2])+np.array(P1[c])*z['pool'][2]
    cm=86/z['pool'][2]
    distance=np.linalg.norm(body-p1,axis=1)*cm
    # End at first P1-ring entry or sustained return, before post-arrival turning.
    end=min(len(body)-1,a+5*fps)
    hit=np.flatnonzero(valid[a:end+1]&(distance[a:end+1]<=20))
    if len(hit):end=min(end,a+int(hit[0]))
    returns=runs(ins[a:end+fps+1],fps)
    if returns:end=min(end,a+returns[0][0])
    if end-a<fps or not valid[a:end+1].all():
        row['reason']='initial swim shorter than 1 s or interrupted by tracking gap';rows.append(row);continue
    route=body[a:end+1];path=float(np.linalg.norm(np.diff(route,axis=0),axis=1).sum()*cm)
    initial=body[a+fps]-body[a];target=p1-body[a]
    if path<5 or np.linalg.norm(initial)*cm<5:
        row['reason']='insufficient initial displacement for directional measurement';rows.append(row);continue
    row.update(included=True,reason='usable first departure',
        heading_error_deg=float(np.degrees(np.arccos(np.clip(np.dot(initial,target)/(np.linalg.norm(initial)*np.linalg.norm(target)),-1,1)))),
        progress_per_path=float((distance[a]-distance[end])/path),
        initial_straightness=float(np.linalg.norm(route[-1]-route[0])*cm/path),
        path_cm=path,outbound_seconds=(end-a)/fps,
        interpolated_pct=float(z['body_interpolated'][a:end+1].mean()*100))
    assert -1.00001<=row['progress_per_path']<=1.00001
    assert 0<=row['initial_straightness']<=1.00001
    rows.append(row)

D=pd.DataFrame(rows);D.to_csv(HERE/'first_departure_audit.csv',index=False)
results=[]
for c in LABEL:
    for group in ('F','all'):
        g=D[(D.cond==c)&D.included]
        if group!='all':g=g[g.sex==group]
        for predictor in ('scanning_deg_s','head_sweeps_per_valid_min'):
            for y in ('heading_error_deg','progress_per_path'):
                results.append(dict(cond=c,group=group,predictor=predictor,outcome=y,**correlation(g[predictor].to_numpy(),g[y].to_numpy())))
(HERE/'correlations.json').write_text(json.dumps(results,indent=2))

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,3,figsize=(14,8))
for j,c in enumerate(LABEL):
    g=D[(D.cond==c)&D.included]
    for i,(key,lab) in enumerate([('heading_error_deg','Initial heading error to P1 (degrees)\nLower = more directed'),('progress_per_path','Progress toward P1 / path length\nHigher = more directed')]):
        ax=axs[i,j]
        for s,col in [('F','#2a78d6'),('M','#d9591f')]:
            gg=g[g.sex==s];ax.scatter(gg.scanning_deg_s,gg[key],c=col,s=42,edgecolors='white',lw=.7,label='Females' if s=='F' else 'Males')
            for r in gg.itertuples():ax.annotate(f'{s}{r.rat}',(r.scanning_deg_s,getattr(r,key)),xytext=(4,4),textcoords='offset points',fontsize=8,color=col)
        ax.set(title=f'{LABEL[c]} · {len(g)} usable first departures',xlabel='Head rotation in 5 s before leaving (deg/s)',ylabel=lab)
        if i==0:ax.set_ylim(-5,185)
        else:ax.set_ylim(-1.05,1.05);ax.axhline(0,color='#ccc',lw=.8)
        ax.grid(axis='y',alpha=.15)
axs[0,0].legend(fontsize=9)
fig.suptitle('Does predeparture scanning accompany a more directed initial search?',fontsize=17)
fig.tight_layout(rect=(0,.09,1,.94))
fig.text(.04,.02,'Exploratory, video-derived hypothesis. One first departure per animal; strict predeparture and tracking requirements.\nP1 geometry is conditional in KAC and assumed in SP1. These selected cases do not represent all leavers. Blue: females; orange: males.',fontsize=10)
fig.savefig(HERE/'scanning_vs_direction.png',dpi=180,bbox_inches='tight')
fig.savefig(HERE/'scanning_vs_direction.svg',bbox_inches='tight')
plt.close(fig)
print(D.groupby(['cond','included']).size().to_string())
print(json.dumps(results,indent=2))
print('EXCLUSIONS\n'+D.groupby(['cond','reason']).size().to_string())
