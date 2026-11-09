"""Rebuild all three checking cohorts with explicit tracking gaps and bounded claims.

Run: python analysis/dlc_cleaned/analyze.py
Original dlc_story outputs and Drive data are not changed.
"""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from tracking_qc import (clean_track, finite, runs, smooth, derivative,
                         angle_signal, unwrap_segments, platform_events,
                         swings, peaks_in_segments)

HERE=Path(__file__).resolve().parent
AN=HERE.parent
OLD=AN/'dlc_story'
# Final KAC model (rotation augmentation, 13 points), both days. Earlier best-240 setup kept in analyze_best240.py.bak.
KAC_RUN=Path(r'G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs\KAcheck_d6d8_v3rot_20261108')
KAC_MODEL='best-320'
RES=HERE/'results'
CACHE=HERE/'cache'
for p in (RES,CACHE,HERE/'figures',HERE/'demos'): p.mkdir(exist_ok=True)
ORDER=('sp1','kac_d6','kac_d8')


def mean(x):
    v=np.asarray(x); v=v[np.isfinite(v)]
    return float(v.mean()) if len(v) else np.nan


def ratio(n,d): return n/d if d>0 else np.nan


def holm(values):
    p=np.asarray(values,float); adj=np.full(len(p),np.nan)
    ix=np.flatnonzero(np.isfinite(p)); order=ix[np.argsort(p[ix])]
    adj[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(order)-np.arange(len(order)))))
    return adj


def wilcoxon(a,b):
    d=np.round(np.asarray(b)-np.asarray(a),8); d=d[np.isfinite(d)]
    return float(stats.wilcoxon(d).pvalue) if len(d)>=5 and np.any(d) else (1. if len(d)>=5 else np.nan)


def sex_stats(data, families):
    rows=[]
    for cond in ORDER:
        g=data[data.cond==cond]
        for family, keys in families.items():
            block=[]
            for key in keys:
                f=g.loc[g.sex=='F',key].dropna(); m=g.loc[g.sex=='M',key].dropna()
                p=stats.mannwhitneyu(f,m,alternative='two-sided').pvalue if min(len(f),len(m))>=3 else np.nan
                block.append(dict(cond=cond,family=family,measure=key,n_F=len(f),n_M=len(m),mean_F=f.mean(),mean_M=m.mean(),p=p))
            for row,adj in zip(block,holm([r['p'] for r in block])):
                row['holm_p']=adj
            rows.extend(block)
    return pd.DataFrame(rows)


def read_all():
    mapping=pd.read_csv(AN/'dlc_measures'/'sp1_checking_dlc_vs_anymaze.csv')
    amap=dict(zip(mapping.Test.astype(int),mapping.animal.str.replace('rat','').astype(int)))
    data=[]; prov=[]
    for p in sorted(CACHE.glob('*.npz')):  # metadata only; the dlc_story cache was removed
        meta=dict(np.load(p))
        z={k: (v.item() if v.ndim==0 else v) for k,v in meta.items() if k in ('rat','test','sex','cond','video','start','fps','pool')}
        cond,rat,test=z['cond'],int(z['rat']),int(z['test'])
        if cond=='sp1':
            assert amap[test]==rat
            files=list((HERE/'inputs'/'sp1_tracks').glob(f'sp1_check_Test_{test}DLC*.h5'))
            model='best-190'
        else:
            folder='d6_tracks' if cond=='kac_d6' else 'd8_tracks'
            files=[f for f in (KAC_RUN/folder).glob(f'*snapshot_{KAC_MODEL}.h5') if f.parent.name==folder
                   and f.name.startswith(f'Day06_Checking_1p5cm_Rat{rat:02d}DLC' if cond=='kac_d6' else f'Test_{test}DLC')]
            model=KAC_MODEL
        assert len(files)==1,(cond,rat,files)
        path=files[0]; df=pd.read_hdf(path)
        assert model in str(df.columns.get_level_values(0)[0])
        df.columns=df.columns.droplevel(0)
        a=round(z['start']*z['fps']); n=120*z['fps']
        df=df.iloc[a:a+n].reset_index(drop=True)
        assert len(df)==n,(cond,rat,len(df))
        z['sex']='M' if rat<=16 else 'F'
        z.update(clean_track(df,z['pool'],cond,z['fps']))
        z['model']=model
        z['_df']=df
        data.append(z)
        prov.append(dict(cond=cond,rat=rat,test=test,model=model,source=str(path),
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(),start_s=z['start'],fps=z['fps'],frames=n))
    assert len(data)==91
    pd.DataFrame(prov).to_csv(RES/'provenance.csv',index=False)
    return data


def analyze(data):
    rows=[]; evrows=[]; sensitivity=[]
    for cond in ORDER:
        rats=[z for z in data if z['cond']==cond]
        first=[np.nanmedian(z['body'][:2*z['fps']],axis=0) for z in rats]
        platform=np.nanmedian(first,axis=0)
        for z in rats:
            fps=z['fps']; n=len(z['body']); cm=86/z['pool'][2]
            z['platform']=platform
            ins,off,events=platform_events(z['body'],platform,.165*z['pool'][2],fps)
            z['inside']=ins; z['off']=off; valid=z['valid']; missing=~valid
            z['first_event_lower_s']=events[0]['lower_s'] if events else np.nan
            first_idx=int(events[0]['lower_s']*fps) if events else n
            # A missing segment before departure can hide an earlier event.
            first_exact=bool(events and events[0]['exact'] and valid[:events[0]['frame']+1].all())
            pre=np.arange(n)<first_idx
            dist=np.linalg.norm(z['body']-platform,axis=1)*cm
            wall=valid & (np.linalg.norm(z['body']-z['pool'][:2],axis=1)>.85*z['pool'][2])
            vel=derivative(z['body'],fps)*cm
            speed=np.linalg.norm(vel,axis=1)
            drift=np.linalg.norm(smooth(vel,round(.5*fps),'mean'),axis=1)
            head_ok=(z['nose_lk']>=.6)&(z['neck_lk']>=.6)&valid
            th=angle_signal(z['nose'],z['neck'],fps,head_ok)
            eligible=ins & finite(th)
            dth=np.abs(np.degrees(derivative(th,fps)))
            dth[~eligible | ~np.r_[False,eligible[:-1]]]=np.nan
            turn=smooth(dth,fps,'mean')
            z['head_angle']=th; z['turn']=turn; z['drift']=drift
            sw=swings(th,eligible,fps,30)
            vte=0; i=0
            while i<len(sw)-1:
                a,b=sw[i],sw[i+1]
                if np.sign(a[2])!=np.sign(b[2]) and b[1]-a[0]<=2*fps and eligible[a[0]:b[1]+1].all():
                    vte+=1; i+=2
                else: i+=1
            reach=np.linalg.norm(z['nose']-platform,axis=1)*cm
            reach_ok=ins & finite(reach) & head_ok
            base=np.median(reach[reach_ok]) if reach_ok.any() else np.nan
            peaks=peaks_in_segments(reach,reach_ok,fps,3,base+3)
            oscillations=peaks_in_segments(reach,reach_ok,fps,1.5,spacing=.3)
            departures=[e['frame'] for e in events if e['exact']]
            # One committed event per departure; no duplicate nose-peak event.
            selected=[]
            for t in peaks:
                if t<2*fps or t+2*fps>=n:
                    continue
                if any(0<=d-t<=1.5*fps for d in departures):
                    continue
                if reach_ok[t-2*fps:t+2*fps+1].all():
                    selected.append((t,'aborted'))
            for t in departures:
                if t>=2*fps and eligible[t-2*fps:t].all() and np.isfinite(reach[t]):
                    selected.append((t,'committed'))
            for t,kind in selected:
                h=th[t-2*fps:t]
                idphi=np.abs(np.degrees(np.diff(h))).sum() if np.isfinite(h).all() else np.nan
                evrows.append(dict(cond=cond,rat=z['rat'],sex=z['sex'],frame=t,t_s=t/fps,kind=kind,
                    idphi_2s_before=idphi,reach_above_base_cm=reach[t]-base,
                    approach_cm_s=(reach[t]-reach[t-2*fps])/2))
            # Tail angle relative to body axis, continuous only within valid runs. The final KAC model has no tail
            # quarter/mid points (MobileDLC labels 13 points), so KAC tail measures come out missing rather than guessed.
            for tp in ('tail_mid','tail_quarter'):
                if tp not in z: z[tp]=np.full((n,2),np.nan); z[tp+'_lk']=np.zeros(n)
            tip=np.where((z['tail_mid_lk']>=.5)[:,None],z['tail_mid'],z['tail_quarter'])
            tail_ok=((z['tail_mid_lk']>=.5)|(z['tail_quarter_lk']>=.5)) & (z['tail_base_lk']>=.5)&(z['spine_mid_lk']>=.5)&valid
            tv=tip-z['tail_base']; axis=z['tail_base']-z['spine_mid']
            phi=np.angle(np.exp(1j*(np.arctan2(tv[:,1],tv[:,0])-np.arctan2(axis[:,1],axis[:,0]))))
            phi[~tail_ok | ~finite(tv) | ~finite(axis) | (np.linalg.norm(tv,axis=1)<1) | (np.linalg.norm(axis,axis=1)<1)]=np.nan
            phi=smooth(unwrap_segments(phi),max(1,round(.1*fps)),'mean')
            tail_on=ins & finite(phi)
            vig=np.abs(np.degrees(derivative(phi,fps)))
            vig[~tail_on | ~np.r_[False,tail_on[:-1]]]=np.nan
            vig=smooth(vig,fps,'mean')
            tail_sw=swings(phi,tail_on,fps,20,.1)
            z['tail_angle']=phi; z['tail_vigour']=vig
            together=ins & np.isfinite(vig)&np.isfinite(drift)
            ids=np.full(n,-1)
            for seg,(a,b) in enumerate(runs(together)): ids[a:b]=seg
            correlations=[]; lags=np.arange(-2*fps,2*fps+1)
            for lag in lags:
                ia=np.arange(max(0,-lag),n-max(0,lag)); ib=ia+lag
                ok=(ids[ia]>=0)&(ids[ia]==ids[ib])
                a,b=vig[ia[ok]],drift[ib[ok]]
                correlations.append(float(np.corrcoef(a,b)[0,1]) if len(a)>=3*fps and a.std()>0 and b.std()>0 else np.nan)
            z['tail_drift_lags']=lags/fps; z['tail_drift_correlations']=np.array(correlations)
            row=dict(cond=cond,rat=z['rat'],test=z['test'],sex=z['sex'],model=z['model'],
                pct_missing=missing.mean()*100,pct_interpolated=z['body_interpolated'].mean()*100,
                pct_spot_rejected=z['spot_rejected'].mean()*100,pct_outside_rejected=z['outside_rejected'].mean()*100,
                pct_speed_rejected=z['speed_rejected'].mean()*100,
                max_gap_s=max([b-a for a,b in runs(missing)],default=0)/fps,
                platform_lower_pct=100*ins.mean(),platform_upper_pct=100*(ins|missing).mean(),
                platform_observed_pct=100*ratio(ins.sum(),valid.sum()),
                wall_lower_pct=100*wall.mean(),wall_upper_pct=100*(wall|missing).mean(),
                wall_observed_pct=100*ratio(wall.sum(),valid.sum()),
                departures_observed=len(events),confirmed_departures=sum(e['exact'] for e in events),
                stayed=0 if events else (1 if valid.all() else np.nan),
                first_departure_s=events[0]['upper_s'] if first_exact else np.nan,
                first_off_lower_s=events[0]['lower_s'] if events else np.nan,
                first_off_upper_s=events[0]['upper_s'] if events else np.nan,
                distance_observed_cm=np.nansum(np.linalg.norm(np.diff(z['body'],axis=0),axis=1))*cm,
                mean_distance_observed_cm=mean(dist),speed_observed_cm_s=mean(speed[off]),
                head_exposure_s=eligible.sum()/fps,
                pre_head_exposure_s=(pre&eligible).sum()/fps,
                head_turn_pre_deg_s=mean(turn[pre&eligible]),
                head_turn_first10_deg_s=mean(turn[eligible & (np.arange(n)<10*fps)]),
                head_sweeps_per_min=60*ratio(len(sw),eligible.sum()/fps),
                vte_episodes_per_min=60*ratio(vte,eligible.sum()/fps),
                idphi_deg_s=mean(dth[eligible]),
                edge_oscillations_per_min=60*ratio(len(oscillations),reach_ok.sum()/fps),
                aborted_lean_outs=sum(kind=='aborted' for _,kind in selected),
                committed_lean_outs=sum(kind=='committed' for _,kind in selected),
                tail_exposure_s=tail_on.sum()/fps,
                tail_sweeps_per_min=60*ratio(len(tail_sw),tail_on.sum()/fps),
                tail_vigour_deg_s=mean(vig[tail_on]),drift_observed_cm_s=mean(drift[ins]),
                tail_drift_r=correlations[2*fps],
                tail_drift_best_lag_s=lags[np.nanargmax(correlations)]/fps if np.isfinite(correlations).any() else np.nan)
            if row['head_exposure_s']<3:
                for key in ('head_sweeps_per_min','vte_episodes_per_min','idphi_deg_s'): row[key]=np.nan
            if row['pre_head_exposure_s']<3: row['head_turn_pre_deg_s']=np.nan
            if row['tail_exposure_s']<3:
                for key in ('tail_sweeps_per_min','tail_vigour_deg_s','tail_drift_r'): row[key]=np.nan
            rows.append(row)
            # Sensitivity to the unvalidated speed cutoff; geometry and spot masks fixed.
            for limit in (40.,100.,150.):
                alt=clean_track(z['_df'],z['pool'],cond,fps,speed_limit=limit)
                ai,ao,ae=platform_events(alt['body'],platform,.165*z['pool'][2],fps)
                missing_alt=~alt['valid']
                sensitivity.append(dict(cond=cond,rat=z['rat'],sex=z['sex'],speed_limit=limit,
                    pct_missing=100*missing_alt.mean(),platform_lower_pct=100*ai.mean(),
                    platform_upper_pct=100*(ai|missing_alt).mean(),departures_observed=len(ae)))
            tosave={k:v for k,v in z.items() if k!='_df'}
            np.savez_compressed(CACHE/f'{cond}_rat{z["rat"]:02d}.npz',**tosave)
        print(f'{cond}: {len(rats)} animals cleaned',flush=True)
    d=pd.DataFrame(rows)
    d.to_csv(RES/'per_rat_measures.csv',index=False)
    e=pd.DataFrame(evrows)
    e.to_csv(RES/'lean_out_events.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(RES/'speed_sensitivity.csv',index=False)
    return d,e


def statistics(d,e):
    families={'platform':['platform_lower_pct','platform_upper_pct'],
              'head':['head_turn_pre_deg_s','head_turn_first10_deg_s','head_sweeps_per_min','vte_episodes_per_min','idphi_deg_s','edge_oscillations_per_min'],
              'tail':['tail_sweeps_per_min','tail_vigour_deg_s','drift_observed_cm_s']}
    sex_stats(d,families).to_csv(RES/'sex_statistics.csv',index=False)
    pairs=d[d.cond=='kac_d6'].merge(d[d.cond=='kac_d8'],on=['rat','sex'],suffixes=('_d6','_d8'),validate='one_to_one')
    assert len(pairs)==29
    pairs.to_csv(RES/'paired_rats.csv',index=False)
    paired=[]
    for sex in ('All','M','F'):
        g=pairs if sex=='All' else pairs[pairs.sex==sex]
        low=g.platform_lower_pct_d8-g.platform_upper_pct_d6
        high=g.platform_upper_pct_d8-g.platform_lower_pct_d6
        paired.append(dict(group=sex,n=len(g),day6_lower=g.platform_lower_pct_d6.mean(),day6_upper=g.platform_upper_pct_d6.mean(),
                           day8_lower=g.platform_lower_pct_d8.mean(),day8_upper=g.platform_upper_pct_d8.mean(),
                           change_min=low.mean(),change_max=high.mean()))
    pd.DataFrame(paired).to_csv(RES/'paired_platform_bounds.csv',index=False)
    ca=[]
    for cond in ORDER:
        block=e[e.cond==cond]
        g=block.groupby(['rat','kind']).idphi_2s_before.mean().unstack()
        if {'committed','aborted'}<=set(g.columns):
            g=g.dropna()
            ca.append(dict(cond=cond,n=len(g),aborted_mean=g.aborted.mean(),committed_mean=g.committed.mean(),p=wilcoxon(g.aborted,g.committed)))
    ca=pd.DataFrame(ca); ca['holm_p']=holm(ca.p)
    ca.to_csv(RES/'committed_vs_aborted.csv',index=False)
    # Use the same note transcription; never reinterpret blanks as stayed.
    tree=ast.parse((AN/'dlc_measures'/'checking_dlc_measures.py').read_text())
    notes={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('NOTES6','NOTES8') for t in n.targets):
            notes[n.targets[0].id]=ast.literal_eval(n.value)
    checks=[]
    for day in (6,8):
        note=pd.DataFrame(notes[f'NOTES{day}'],columns=['rat','notes_stayed_on','notes_departures','notes_first_s','notes_text'])
        q=d[d.cond==f'kac_d{day}'].merge(note,on='rat',how='left',validate='one_to_one')
        q['cleaned_class']=np.where(q.departures_observed>0,'LP',np.where(q.pct_missing==0,'SOP','unknown'))
        q['known_note']=q.notes_stayed_on.isin(['SOP','LP'])
        q['agreement']=np.where(q.known_note,q.notes_stayed_on==q.cleaned_class,np.nan)
        checks.append(q[['cond','rat','notes_stayed_on','cleaned_class','known_note','agreement','notes_first_s','first_departure_s','first_off_lower_s','first_off_upper_s','pct_missing','notes_text']])
    pd.concat(checks).to_csv(RES/'notes_validation.csv',index=False)
    # Compare with previous estimates while explicitly separating definitions.
    if (OLD/'results'/'per_rat_measures.csv').exists():  # the dlc_story folder has since been removed
        old=pd.read_csv(OLD/'results'/'per_rat_measures.csv')
        d.merge(old,on=['cond','rat','sex'],suffixes=('_cleaned','_old'),validate='one_to_one').to_csv(RES/'before_after.csv',index=False)
    print('Platform bounds by cohort and sex:\n',d.groupby(['cond','sex'])[['platform_lower_pct','platform_upper_pct','pct_missing']].mean().round(2).to_string(),flush=True)
    print('Paired platform bounds:\n',pd.DataFrame(paired).round(2).to_string(index=False),flush=True)


if __name__=='__main__':
    data=read_all()
    d,e=analyze(data)
    statistics(d,e)
    (RES/'method.json').write_text(json.dumps(dict(body_confidence=.3,head_confidence=.6,tail_confidence=.5,
        false_spots={'kac_d6':[310,210],'kac_d8':[870,50]},spot_radius_px=40,outer_radius_fraction=.98,
        speed_cutoff_cm_s=60,speed_sensitivity=[40,100,150],max_interpolated_gap_s=.5,
        unknown_time='excluded from observed-time denominator; full-trial bounds reported',
        caution='These thresholds are QC assumptions, not validated limits on rat motion.',
        primary_kac_model='KAcheck_d6d8_v3rot_20261108 best-320 (rotation augmentation, 13 points) on both days',sp1_model='best-190',
        sp1_pool_scale='172 cm assumed; SP1 distances approximate'),indent=2))
