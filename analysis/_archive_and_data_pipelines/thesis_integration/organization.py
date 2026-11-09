"""Descriptive excursion organization; opposite quadrant is NOT a learned-place ROI."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).parents[1]/'dlc_cleaned'))
from tracking_qc import runs

HERE=Path(__file__).parent
OUT=HERE/'organization'; OUT.mkdir(exist_ok=True)
ORDER=['sp1','kac_d6','kac_d8']
LABEL={'sp1':'SP1','kac_d6':'KAC Day 6','kac_d8':'KAC Day 8'}

def excursions(inside,off,valid,fps):
    """Require sustained observed off and return runs; censor gaps and boundaries."""
    events=[]
    for a,b in runs(valid):
        off_runs=runs(off[a:b],fps)
        on_runs=runs(inside[a:b],fps)
        cursor=a
        for start,stop in off_runs:
            start+=a; stop+=a
            if start<cursor: continue
            returns=[(x+a,y+a) for x,y in on_runs if x+a>=stop]
            end=returns[0][0] if returns else b
            left_known=start>a and inside[start-1]
            returned=bool(returns)
            events.append(dict(start=start,end=end,left_known=bool(left_known),returned=returned,
                complete=bool(left_known and returned),left_censored=not left_known,
                right_censored=not returned))
            cursor=returns[0][1] if returns else b
    return events

def analyze():
    eventrows=[]; ratrows=[]; boutrows=[]; tracks=[]
    for path in sorted((HERE.parent/'dlc_cleaned/cache').glob('*.npz')):
        z={k:v.item() if v.ndim==0 else v for k,v in dict(np.load(path)).items()}
        body=z['body']; pool=z['pool']; fps=z['fps']; valid=z['valid']; ins=z['inside']; off=z['off']
        rel=(body-pool[:2])/pool[2]; ps=(z['platform']-pool[:2])/pool[2]
        # Camera-aligned quadrants: both coordinate signs opposite placement.
        opp=valid & (rel[:,0]*ps[0]<0) & (rel[:,1]*ps[1]<0)
        wall=valid & (np.linalg.norm(rel,axis=1)>.85)
        state=np.full(len(body),5,int)
        state[valid]=1; state[opp]=2; state[wall & ~opp]=3; state[wall & opp]=4; state[ins]=0
        ident=dict(cond=z['cond'],rat=z['rat'],sex=z['sex'])
        for code in range(6):
            for a,b in runs(state==code):
                boutrows.append(dict(**ident,state=code,start_s=a/fps,end_s=b/fps,duration_s=(b-a)/fps))
        ev=excursions(ins,off,valid,fps)
        for num,e in enumerate(ev,1):
            a,b=e['start'],e['end']
            # Destination is sustained presence for >=0.5 s, not a one-frame crossing.
            qr=runs(opp[a:b],max(1,round(.5*fps))); wr=runs(wall[a:b],max(1,round(.5*fps)))
            qt=qr[0][0]/fps if qr else np.nan; wt=wr[0][0]/fps if wr else np.nan
            route='neither'
            if qr and not wr: route='opposite_only'
            elif wr and not qr: route='wall_only'
            elif qr and wr: route='simultaneous' if qt==wt else ('opposite_first' if qt<wt else 'wall_first')
            eventrows.append(dict(**ident,segment=num,start_s=a/fps,end_s=b/fps,duration_s=(b-a)/fps,
                **{k:v for k,v in e.items() if k not in ['start','end']},
                reaches_opposite=bool(qr),reaches_wall=bool(wr),opposite_latency_s=qt,wall_latency_s=wt,
                opposite_s=opp[a:b].sum()/fps,wall_s=wall[a:b].sum()/fps,route=route))
        complete=[e for e in eventrows if e['cond']==z['cond'] and e['rat']==z['rat'] and e['complete']]
        on_dwell=[(b-a)/fps for a,b in runs(ins) if a>0 and b<len(ins) and valid[a-1] and valid[b]]
        ratrows.append(dict(**ident,unknown_s=(~valid).sum()/fps,observed_off_s=off.sum()/fps,
            observed_excursion_segments=len(ev),complete_excursions=len(complete),
            opposite_complete=sum(e['reaches_opposite'] for e in complete),wall_complete=sum(e['reaches_wall'] for e in complete),
            complete_duration_median_s=np.median([e['duration_s'] for e in complete]) if complete else np.nan,
            on_dwell_median_s=np.median(on_dwell) if on_dwell else np.nan,
            observed_opposite_s=(opp & off).sum()/fps,observed_wall_s=(wall & off).sum()/fps))
        tracks.append((ident,state,fps))
    e=pd.DataFrame(eventrows); d=pd.DataFrame(ratrows)
    e.to_csv(OUT/'excursions.csv',index=False); d.to_csv(OUT/'animals.csv',index=False)
    pd.DataFrame(boutrows).to_csv(OUT/'state_bouts.csv',index=False)
    summaries=[]
    for (c,s),g in d.groupby(['cond','sex']):
        ex=e[(e.cond==c)&(e.sex==s)&e.complete]
        summaries.append(dict(cond=c,sex=s,animals=len(g),animals_with_complete=int((g.complete_excursions>0).sum()),
            complete_excursions=len(ex),complete_opposite=int(ex.reaches_opposite.sum()),complete_wall=int(ex.reaches_wall.sum()),
            duration_median_s=ex.duration_s.median(),unknown_s=g.unknown_s.sum(),observed_off_s=g.observed_off_s.sum()))
    summary=pd.DataFrame(summaries); summary.to_csv(OUT/'summary.csv',index=False)
    colors=['#d6dce1','#a3c4bb','#245dcc','#e7a446','#8c4db1','#252c32']
    names=['Placement zone','Other interior','Opposite interior','Other wall','Opposite wall','Unknown']
    fig,axs=plt.subplots(1,3,figsize=(15,9))
    for ax,c in zip(axs,ORDER):
        ts=sorted([t for t in tracks if t[0]['cond']==c],key=lambda t:(t[0]['sex']=='F',t[0]['rat']))
        for y,(ident,st,fps) in enumerate(ts):
            for code in range(6):
                for a,b in runs(st==code): ax.barh(y,(b-a)/fps,left=a/fps,height=.85,color=colors[code],linewidth=0)
        ax.set(yticks=range(len(ts)),yticklabels=[f'{x[0]["sex"]}{x[0]["rat"]}' for x in ts],xlim=(0,120),xlabel='Seconds from supplied start marker',title=LABEL[c])
        ax.invert_yaxis(); ax.tick_params(axis='y',labelsize=8)
    fig.suptitle('Behavioral sequences: placement, opposite quadrant, and wall',fontsize=16)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c,label=n) for c,n in zip(colors,names)],loc='lower center',ncol=6)
    fig.tight_layout(rect=(0,.05,1,.95)); fig.savefig(OUT/'sequences.png',dpi=160); fig.savefig(OUT/'sequences.svg'); plt.close(fig)
    methods=dict(min_off_s=1,min_return_s=1,min_destination_s=.5,wall_radius_fraction=.85,
        quadrant='Both camera-coordinate signs opposite placement relative to pool center; broad proxy, not former-platform ROI',
        gaps='Split and censor; never bridge unknown tracking. Counts of segments are not departure counts.',
        complete='Observed off onset preceded by on within contiguous valid segment, followed by >=1 second on before a gap/end',
        bias='Complete-excursion summaries preferentially exclude difficult swims; pooled excursions are not independent animals.')
    (OUT/'method.json').write_text(json.dumps(methods,indent=2))
    print(summary.to_string(index=False)); print(e[e.complete].groupby(['cond','route']).size().to_string())
    return d,e

if __name__=='__main__': analyze()
