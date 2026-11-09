"""Animal-level multidimensional profiles from existing, final research outputs."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SITE = ROOT / 'dlc_cleaned/site'
OUT = HERE / 'exports'
OUT.mkdir(exist_ok=True)
LABELS = {'kac_d8':'KAC Day 8', 'kac_d6':'KAC Day 6', 'sp1':'SP1'}
FEATURES = [
    ('head_sweeps_per_min','Head sweeps','Scanning','/min','Swings of at least 30 degrees per valid on-platform minute. Whole checking session.'),
    ('departures_observed','Departures','Initiation','count','Observed departures of at least 1 second. Gaps can leave departures unobserved.'),
    ('swim_seconds','Swimming time','Initiation','s','Observed off-platform time over the 120-second checking session.'),
    ('swim_speed','Swim speed','Movement','cm/s','Median smoothed off-platform speed; requires at least 1 second of observed swimming.'),
    ('p1_swim_pct','Near old location','Search','%','Percentage of observed swimming time within 20 cm of proposed P1; no visit dwell requirement.'),
    ('wall_swim_pct','Near wall','Search','%','Percentage of observed swimming time beyond 0.85 pool radii.'),
    ('complete_excursions','Round trips','Recurrence','count','Fully observed departure-to-return paths; gaps or trial end censor unfinished paths.'),
    ('area_successes','Trips reaching P1','Recurrence','count','Complete round trips with any off-platform entry within 20 cm of P1; no minimum dwell time. Zero if no complete trips were observed.'),
    ('area_success_pct','Trips reaching P1','Destination','%','Trips reaching P1 divided by complete round trips. Undefined when there are no complete trips.'),
    ('repeat_p1_trips','Later P1 trips','Repetition','count','Complete trips reaching P1 after the first such complete trip. A lower-bound count, not within-trip reentries or a diagnosis.'),
    ('median_round_trip_s','Round-trip duration','Return timing','s','Median departure-to-placement-return duration among complete round trips. Undefined with no complete trip.'),
    ('training_d5_latency','Day 5 latency','Acquisition','s','Corrected AnyMaze mean escape latency on Day 5. Trials have a 30-second cap; this is not pure memory accuracy.'),
    ('training_improvement','Day 1 minus Day 5','Acquisition','s','Difference between daily mean escape latencies; positive means a shorter latency on Day 5.'),
    ('reminder_change','Day 7 minus Day 5','Reminder','s','Change in mean latency; positive means longer on Day 7. Day 7 occurs after Day 6 checking and is not a baseline predictor of it.'),
]
def clean(v):
    if isinstance(v, dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v, (list, tuple)): return [clean(x) for x in v]
    if isinstance(v, np.ndarray): return clean(v.tolist())
    if isinstance(v, (float,np.floating)): return float(v) if np.isfinite(v) else None
    if isinstance(v, np.integer): return int(v)
    if isinstance(v, np.bool_): return bool(v)
    return v

paths = [ROOT/'dlc_explorer/exports/animal_summary.csv',
    ROOT/'dlc_cleaned/results/per_rat_measures.csv',
    ROOT/'scanning_accuracy/area_entry_paths.csv',
    ROOT/'updated_anymaze/analysis/results/rat_day_means.csv']
A, Q, E, T = [pd.read_csv(p) for p in paths]
assert len(A)==91 and not A.duplicated(['cond','rat']).any()
assert not T.duplicated(['rat','day']).any()
assert set(Q[Q.cond.str.startswith('kac')].model)=={'best-320'}
assert set(Q[Q.cond=='sp1'].model)=={'best-190'}
A = A.merge(Q[['cond','rat','model','first_off_lower_s','first_off_upper_s','pre_head_exposure_s']],on=['cond','rat'],validate='one_to_one')
hits=E[E.complete].groupby(['cond','rat']).agg(area_successes=('area_entry','sum'), checked_trips=('area_entry','size')).reset_index()
A=A.merge(hits,on=['cond','rat'],how='left',validate='one_to_one')
A['area_successes']=A.area_successes.fillna(0).astype(int)
assert (A.checked_trips.fillna(0)==A.complete_excursions).all()
A['area_success_pct']=np.where(A.complete_excursions>0,100*A.area_successes/A.complete_excursions,np.nan)
assert A.area_successes.sum()==40
assert A.loc[A.complete_excursions==0,'area_success_pct'].isna().all()
training={}
for rat,g in T.groupby('rat'):
    d=g.set_index('day'); assert set([1,5,7]).issubset(d.index)
    training[int(rat)]=dict(training_d5_latency=d.loc[5,'lat'],training_improvement=d.loc[1,'lat']-d.loc[5,'lat'],
        reminder_change=d.loc[7,'lat']-d.loc[5,'lat'],training=g.sort_values('day')[['day','lat','dist','speed','n']].to_dict('records'))
sessions=[]
repetition_events=[]
for r in A.to_dict('records'):
    cohort='SP1' if r['cond']=='sp1' else 'KAC'
    r.update(cohort=cohort,animal_id=f'{cohort}_{r["rat"]:02d}')
    if cohort=='KAC':
        ts=T[T.rat==r['rat']]
        assert set(ts.sex)==({'Female'} if r['sex']=='F' else {'Male'})
        r.update(training[int(r['rat'])])
    else: r.update(training_d5_latency=None,training_improvement=None,reminder_change=None,training=[])
    if r['departures_observed']:
        r['initiation_status']='Observed departure'
    elif r['pct_missing']>0:
        r['initiation_status']='No departure observed; some time unknown'
    else:r['initiation_status']='No departure during the observed 120 s'
    r['neural_status']='PV/WFA pending; no matched neural measurements imported'
    eg=E[(E.cond==r['cond'])&(E.rat==r['rat'])].sort_values('start')
    complete=eg[eg.complete]
    r['repeat_p1_trips']=max(0,int(r['area_successes'])-1)
    r['median_round_trip_s']=float(complete.duration.median()) if len(complete) else None
    r['observed_placement_returns']=int((~eg.right_censored).sum())
    r['incomplete_segments']=int((~eg.complete).sum())
    r['return_timeline']=[]
    with np.load(ROOT/f'dlc_cleaned/cache/{r["cond"]}_rat{r["rat"]:02d}.npz') as z:
        fps=int(z['fps']);p1=np.array({'kac_d6':(.28,-.355),'kac_d8':(.28,-.355),'sp1':(.4623,-.0624)}[r['cond']])
        xy=(z['body']-z['pool'][:2])/z['pool'][2]
        near=z['off'].astype(bool)&z['valid'].astype(bool)&(np.linalg.norm(xy-p1,axis=1)*86<=20)
        for e in eg.to_dict('records'):
            a,b=round(e['start']*fps),round(e['end']*fps)
            hit=np.flatnonzero(near[a:b])
            event=dict(number=e['number'],start=e['start'],end=e['end'],complete=e['complete'],
                returned=not e['right_censored'],onset_known=not e['left_censored'],
                p1_entry_s=(a+int(hit[0]))/fps if len(hit) else None,
                duration_s=e['duration'])
            assert bool(len(hit))==bool(e['area_entry'])
            r['return_timeline'].append(event)
            repetition_events.append(dict(cond=r['cond'],rat=r['rat'],sex=r['sex'],**event))
    sessions.append(clean(r))
assert len({r['animal_id'] for r in sessions})==62
assert len({r['rat'] for r in sessions if r['cond']=='kac_d6'} & {r['rat'] for r in sessions if r['cond']=='kac_d8'})==29
features=[dict(key=k,label=l,domain=d,unit=u,definition=n) for k,l,d,u,n in FEATURES]
payload=dict(sessions=sessions,features=features,labels=LABELS,
    sources=[dict(file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths],
    version='2026-11-08',area_radius_cm=20,area_dwell_s=0)
(OUT/'profile_data.json').write_text(json.dumps(payload,allow_nan=False,separators=(',',':')),encoding='utf-8')
flat=pd.DataFrame([{k:v for k,v in s.items() if k not in ['training','return_timeline']} for s in sessions])
flat.to_csv(OUT/'animal_profiles.csv',index=False)
pd.DataFrame(repetition_events).to_csv(OUT/'returns_and_repetition.csv',index=False)
T.to_csv(OUT/'kac_acquisition_by_day.csv',index=False)
correlations=[]
for cond in LABELS:
    for sex in ['all','F','M']:
        group=flat[(flat.cond==cond)&((flat.sex==sex) if sex!='all' else True)]
        for i,f in enumerate(features):
            for other in features[i+1:]:
                pair=group[[f['key'],other['key']]].dropna()
                rho=float(spearmanr(pair.iloc[:,0],pair.iloc[:,1]).statistic) if len(pair)>=6 and (pair.nunique()>1).all() else None
                correlations.append(dict(cond=cond,sex=sex,x=f['key'],y=other['key'],n=len(pair),rho=rho))
(OUT/'descriptive_correlations.json').write_text(json.dumps(correlations,allow_nan=False))

# Exportable matrix: raw individual dimensions, normalized only for color.
g=flat[flat.cond=='kac_d8'].sort_values(['sex','rat'])
matrix=np.full((len(g),len(features)),np.nan)
for j,f in enumerate(features):
    v=g[f['key']].to_numpy(dtype=float); ok=np.isfinite(v)
    matrix[ok,j]=(rankdata(v[ok],method='average')-1)/(ok.sum()-1) if ok.sum()>1 else .5
fig,ax=plt.subplots(figsize=(13,10))
cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#e6e9eb')
im=ax.imshow(matrix,vmin=0,vmax=1,cmap=cmap,aspect='auto')
ax.set_yticks(range(len(g)),[f'{r.sex}{r.rat}' for r in g.itertuples()])
ax.set_xticks(range(len(features)),[f"{f['label']} ({f['unit']})" for f in features],rotation=45,ha='right',fontsize=9)
ax.set_title('KAC Day 8: each animal across behavioral dimensions',loc='left',pad=18)
fig.colorbar(im,ax=ax,label='Relative position within Day 8 (higher value, not better)',fraction=.025,pad=.02)
fig.text(.03,.015,'91 sessions / 62 animals in the interactive dashboard. Gray = unavailable or not applicable. No overall score or inferred types.\nP1: proposed old-platform area. Area entry has no dwell threshold. Neural measurements are pending.',fontsize=9)
fig.tight_layout(rect=(0,.06,1,1));fig.savefig(OUT/'kac_day8_profile_matrix.png',dpi=180);fig.savefig(OUT/'kac_day8_profile_matrix.svg');plt.close(fig)

html=(HERE/'profiles_template.html').read_text(encoding='utf-8').replace('__PROFILE_DATA__',json.dumps(payload,allow_nan=False,separators=(',',':')))
(HERE/'profiles.html').write_text(html.replace('profile_exports/','exports/').replace('href="index.html"','href="../dlc_cleaned/dashboard.html"').replace('href="explorer.html"','href="../dlc_explorer/explorer.html"'),encoding='utf-8')
(SITE/'profiles.html').write_text(html,encoding='utf-8')
shutil.copy2(HERE/'profiles.js',SITE/'profiles.js')
(SITE/'profile_exports').mkdir(exist_ok=True)
for p in OUT.iterdir():shutil.copy2(p,SITE/'profile_exports'/p.name)
print(json.dumps(dict(sessions=len(sessions),animals=62,kac_paired=29,dimensions=len(features),available_per_dimension=flat[[f['key'] for f in features]].count().to_dict()),indent=2))
