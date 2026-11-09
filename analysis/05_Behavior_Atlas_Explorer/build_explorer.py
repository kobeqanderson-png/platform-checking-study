"""Advanced descriptive visuals from final, existing checking-track caches only."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import sys
import shutil

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from matplotlib.patches import Circle, Patch

HERE = Path(__file__).resolve().parent
CLEAN = HERE.parent / 'dlc_cleaned'
SITE = CLEAN / 'site'
OUT = HERE / 'exports'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CLEAN))
from tracking_qc import runs, derivative, smooth
sys.path.insert(0, str(HERE.parent / 'thesis_integration'))
from organization import excursions

COLORS = ['#aab7bd', '#b39ad5', '#e4aa55', '#38a69a', '#253c4b']
NAMES = ['Placement zone', 'Near P1', 'Wall band', 'Other interior', 'Unknown']
LABEL = {'sp1': 'SP1', 'kac_d6': 'KAC Day 6', 'kac_d8': 'KAC Day 8'}
ORDER = ['sp1', 'kac_d6', 'kac_d8']
P1 = {'sp1': [.4623, -.0624], 'kac_d6': [.28, -.355], 'kac_d8': [.28, -.355]}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold',
    'savefig.facecolor': '#ffffff'})


def clean_json(value):
    if isinstance(value, dict):
        return {k: [[round(float(n),7) for n in row] for row in v] if k=='heat' else clean_json(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray): return clean_json(value.tolist())
    if isinstance(value, (float, np.floating)): return round(float(value), 3) if np.isfinite(value) else None
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, np.bool_): return bool(value)
    return value


def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=180, bbox_inches='tight')
    fig.savefig(OUT / f'{name}.svg', bbox_inches='tight')
    plt.close(fig)


def build():
    rows = pd.read_csv(CLEAN / 'results/per_rat_measures.csv')
    sessions, event_rows, provenance = [], [], []
    native = {}
    for p in sorted((CLEAN / 'cache').glob('*.npz')):
        z = {k: v.item() if v.ndim == 0 else v for k, v in dict(np.load(p)).items()}
        cond, rat, fps = z['cond'], int(z['rat']), int(z['fps'])
        assert z['model'] == ('best-190' if cond == 'sp1' else 'best-320'), (p, z['model'])
        valid = z['valid'].astype(bool); n = len(valid)
        assert n == 120 * fps
        xy = (z['body'] - z['pool'][:2]) / z['pool'][2]
        platform = (z['platform'] - z['pool'][:2]) / z['pool'][2]
        ins, off = z['inside'].astype(bool), z['off'].astype(bool)
        p1 = np.array(P1[cond]); dp1 = np.linalg.norm(xy - p1, axis=1) * 86
        dp2 = np.linalg.norm(xy - platform, axis=1) * 86
        wall = valid & (np.linalg.norm(xy, axis=1) > .85)
        near = off & (dp1 <= 20)
        state = np.full(n, 4, int)
        state[valid] = 3; state[wall] = 2; state[near] = 1; state[ins] = 0
        velocity = derivative(xy, fps) * 86
        speed = np.linalg.norm(velocity, axis=1)
        speed_smooth = smooth(speed, max(1, round(.3 * fps)), 'mean')
        head = z['head_angle']
        # All-frame head orientation, gated by existing confidence masks. Head-turn
        # speed uses the existing on-platform measure to avoid mixing locomotor turns.
        alignment = np.degrees(np.angle(np.exp(1j * (head - np.arctan2(p1[1]-xy[:,1], p1[0]-xy[:,0])))))
        alignment[~valid] = np.nan
        measures = rows[(rows.cond == cond) & (rows.rat == rat)].iloc[0]
        metrics = {k: measures[k] for k in ['pct_missing', 'pct_interpolated', 'platform_lower_pct',
            'platform_upper_pct', 'departures_observed', 'first_departure_s', 'head_turn_pre_deg_s',
            'head_sweeps_per_min', 'head_exposure_s']}
        metrics.update(swim_seconds=float(off.sum()/fps),
            swim_speed=float(np.nanmedian(speed_smooth[off])) if off.sum() >= fps else np.nan,
            p1_swim_pct=float(100*near.sum()/off.sum()) if off.sum() >= fps else np.nan,
            wall_swim_pct=float(100*(wall & off).sum()/off.sum()) if off.sum() >= fps else np.nan,
            path_cm=float(np.nansum(speed)/fps))
        # Explicitly exclude unresolved gaps from complete excursions. Short,
        # accepted interpolations remain present and their contribution is reported.
        events = []
        for j, e in enumerate(excursions(ins, off, valid, fps), 1):
            a, b = e['start'], e['end']
            assert valid[a:b].all()
            p1runs = runs(near[a:b], 1)  # Any tracked entry; user removed dwell threshold.
            wallruns = runs((wall & off)[a:b], max(1, round(.5*fps)))
            hits = []
            if p1runs: hits.append((p1runs[0][0], 'P1'))
            if wallruns: hits.append((wallruns[0][0], 'wall'))
            route = ' → '.join(x[1] for x in sorted(hits)) or 'interior'
            route_distance = np.linalg.norm(np.diff(xy[a:b], axis=0), axis=1).sum()*86
            event = dict(number=j, start=a/fps, end=b/fps, duration=(b-a)/fps,
                complete=e['complete'], left_censored=e['left_censored'], right_censored=e['right_censored'],
                route=route, path_cm=float(route_distance),
                interpolated_pct=float(z['body_interpolated'][a:b].mean()*100))
            events.append(event)
            event_rows.append(dict(cond=cond, rat=rat, sex=z['sex'], **event))
        metrics['complete_excursions'] = sum(e['complete'] for e in events)
        hist = np.histogram2d(xy[off,1], xy[off,0], bins=28, range=[[-1,1],[-1,1]])[0]
        if hist.sum(): hist /= hist.sum()
        # 5-Hz replay. A bin containing any unresolved body gap is shown unknown;
        # never connect a displayed path across a gap hidden by downsampling.
        step = fps // 5
        display = {k: [] for k in ['xy','speed','turn','p1','p2','angle','alignment','state','interp']}
        for a in range(0, n, step):
            b = min(n, a+step); ok = valid[a:b].all(); mid = a + (b-a)//2
            display['xy'].append(xy[mid] if ok else [np.nan,np.nan])
            for key, values in [('speed',speed_smooth),('turn',z['turn']),('p1',dp1),('p2',dp2),('alignment',alignment)]:
                arr = values[a:b]
                display[key].append(float(np.mean(arr)) if ok and np.isfinite(arr).all() else np.nan)
            display['angle'].append(float(head[mid]) if ok and np.isfinite(head[mid]) else np.nan)
            display['state'].append(int(state[mid]) if ok else 4)
            display['interp'].append(bool(z['body_interpolated'][a:b].any()))
        bouts = []
        for code in range(5):
            for a,b in runs(state==code): bouts.append([a/fps,b/fps,code])
        session = dict(id=f'{cond}_{rat}',cond=cond,rat=rat,sex=z['sex'],model=z['model'],
            platform=platform,p1=p1,metrics=metrics,events=events,bouts=bouts,
            occupancy=[float((state==k).sum()/fps) for k in range(5)],heat=hist,
            replay=display)
        sessions.append(session);native[session['id']] = (xy,state,fps,z)
        provenance.append(dict(session=session['id'],model=z['model'],cache_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        assert abs(metrics['pct_missing'] - 100*(~valid).mean()) < .001
    assert len(sessions)==91
    pd.DataFrame(event_rows).to_csv(OUT/'excursion_segments.csv',index=False)
    pd.DataFrame([dict(id=s['id'],cond=s['cond'],rat=s['rat'],sex=s['sex'],**s['metrics']) for s in sessions]).to_csv(OUT/'animal_summary.csv',index=False)
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))

    # Full-resolution categorical sequence atlas, all sessions.
    fig, axs = plt.subplots(1,3,figsize=(16,10))
    for ax,c in zip(axs,ORDER):
        ss=sorted([s for s in sessions if s['cond']==c],key=lambda s:(s['sex']=='F',s['rat']))
        for y,s in enumerate(ss):
            for a,b,k in s['bouts']: ax.broken_barh([(a,b-a)],(y-.4,.8),facecolors=COLORS[k],edgecolors='none')
        ax.set(yticks=range(len(ss)),yticklabels=[f"{s['sex']}{s['rat']:02d}" for s in ss],xlim=(0,120),xlabel='Seconds from supplied test start',title=LABEL[c]);ax.invert_yaxis()
    fig.suptitle('How checking unfolds: every animal, every recorded second',fontsize=18,y=.99)
    fig.legend(handles=[Patch(color=c,label=n) for c,n in zip(COLORS,NAMES)],loc='lower center',ncol=5)
    fig.tight_layout(rect=(0,.045,1,.96));save(fig,'01_behavior_sequences')

    # Equal-animal-weighted off-platform density; no pooling by swim duration.
    fig,axs=plt.subplots(2,3,figsize=(13,8))
    heats=[]
    for sex in 'MF':
        for c in ORDER:
            group=[s for s in sessions if s['cond']==c and s['sex']==sex and s['metrics']['swim_seconds']>=1]
            heats.append((sex,c,group,np.mean([s['heat'] for s in group],axis=0) if group else np.zeros((28,28))))
    vmax=max(h.max() for _,_,_,h in heats)*100
    for ax,(sex,c,g,h) in zip(axs.flat,heats):
        im=ax.imshow(h*100,extent=(-1,1,1,-1),cmap='magma',norm=PowerNorm(.5,vmin=0,vmax=vmax),interpolation='nearest')
        ax.add_patch(Circle((0,0),1,fill=False,color='#a0a0a0',lw=1));ax.add_patch(Circle((0,0),.85,fill=False,color='#a0a0a0',ls=':',lw=.7))
        pp=next(s['platform'] for s in sessions if s['cond']==c)
        ax.add_patch(Circle(pp,.165,fill=False,color='white',lw=1));ax.scatter(*P1[c],marker='D',s=35,color='#a78bfa',edgecolors='white')
        ax.set(title=f"{LABEL[c]} · {'males' if sex=='M' else 'females'} · {len(g)} swimmers",xticks=[],yticks=[],aspect='equal')
    fig.suptitle('Where swimming is distributed — each swimming animal gets equal weight',fontsize=15)
    fig.subplots_adjust(top=.88,bottom=.10,wspace=.13,hspace=.20,right=.88)
    fig.colorbar(im,cax=fig.add_axes([.91,.18,.018,.6]),label='Mean % of off-platform time per bin (square-root color scale)')
    fig.text(.04,.025,'Camera coordinates; compare sexes within each test. P1 is assumed in SP1 and transferred from training geometry in KAC.\nAnimals with <1 s observed off-platform time excluded. Descriptive maps, not a spatial-preference significance test.',fontsize=9)
    save(fig,'02_swimming_density')

    # Pair by rat ID only inside KAC. Each line is an animal, not independent days.
    fig,axs=plt.subplots(2,3,figsize=(14,8))
    keys=[('platform_lower_pct','Time in placement zone (%)'),('departures_observed','Observed departures'),
          ('head_turn_pre_deg_s','Head-turn speed before leaving (deg/s)'),('swim_speed','Median off-platform speed (cm/s)'),
          ('p1_swim_pct','Off-platform time near P1 (%)'),('wall_swim_pct','Off-platform time in wall band (%)')]
    for ax,(key,title) in zip(axs.flat,keys):
        count=0
        for rat in range(1,33):
            pair=[next((s for s in sessions if s['cond']==c and s['rat']==rat),None) for c in ['kac_d6','kac_d8']]
            if any(s is None for s in pair):continue
            vals=[s['metrics'][key] for s in pair]
            if not np.isfinite(vals).all():continue
            ax.plot([0,1],vals,'o-',color='#2a78d6' if pair[0]['sex']=='F' else '#d9591f',alpha=.6,lw=1,ms=3);count+=1
        ax.set(xticks=[0,1],xticklabels=['Day 6','Day 8'],title=f'{title}\n{count} paired animals')
    fig.suptitle('Same animals, two checking tests',fontsize=17)
    fig.tight_layout(rect=(0,.07,1,.94));fig.text(.04,.015,'Blue: females. Orange: males. Missing values are omitted per panel. P1 and wall percentages are conditional on observed swimming.\nWater depth, test order and camera differ together; these lines do not isolate a depth effect. Placement time uses the full-trial lower bound.',fontsize=9)
    save(fig,'03_paired_profiles')

    payload=clean_json(dict(sessions=sessions,labels=LABEL,colors=COLORS,stateNames=NAMES,
        methods={'scale':'172 cm pool diameter; SP1 physical scale assumed',
        'p1':'Existing proposed P1 geometry: KAC training-derived, assumes camera correspondence; SP1 mirrored placement (assumed).',
        'events':'At least 1 s off and 1 s on for sustained return. P1: any tracked entry within 20 cm, no dwell threshold. Wall: at least 0.5 s. Unknown gaps split/censor segments; short accepted interpolation remains.',
        'replay':'5 Hz display; numerical summaries and event detection use native sampling. Any body gap in a display bin stays unknown.',
        'models':'KAC final v3rot best-320 on both days; SP1 best-190.'}))
    packed=base64.b64encode(gzip.compress(json.dumps(payload,separators=(',',':'),allow_nan=False).encode())).decode()
    html=(HERE/'explorer_template.html').read_text(encoding='utf-8').replace('__DATA_GZIP__',packed)
    local_html=html.replace('explorer_exports/','exports/').replace('src="demos_trimmed/','src="../dlc_cleaned/demos_trimmed/').replace('href="index.html"','href="../dlc_cleaned/dashboard.html"')
    (HERE/'explorer.html').write_text(local_html,encoding='utf-8')
    (SITE/'explorer.html').write_text(html,encoding='utf-8')
    (SITE/'explorer_exports').mkdir(exist_ok=True)
    for f in OUT.iterdir():
        if f.suffix in ('.png','.svg','.csv','.json'):
            shutil.copy2(f,SITE/'explorer_exports'/f.name)
    print(json.dumps({'sessions':len(sessions),'segments':len(event_rows),'complete':sum(e['complete'] for e in event_rows),
        'explorer_bytes':len(html.encode()),'models':sorted(set(s['model'] for s in sessions))},indent=2))


if __name__=='__main__':build()
