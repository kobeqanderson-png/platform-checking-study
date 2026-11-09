"""Figures and a local report from the gap-aware reanalysis; no stale numbers."""
import html
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from tracking_qc import runs

HERE=Path(__file__).resolve().parent
RES=HERE/'results'; FIG=HERE/'figures'
D=pd.read_csv(RES/'per_rat_measures.csv')
S=pd.read_csv(RES/'sex_statistics.csv')
B=pd.read_csv(RES/'paired_platform_bounds.csv')
CA=pd.read_csv(RES/'committed_vs_aborted.csv')
ORDER=('sp1','kac_d6','kac_d8')
LABEL={'sp1':'SP1 · raised','kac_d6':'KAC Day 6 · standard','kac_d8':'KAC Day 8 · raised'}
COL={'F':'#2a78d6','M':'#eb6834'}
T={c:[] for c in ORDER}
for p in (HERE/'cache').glob('*.npz'):
    z={k:(v.item() if v.ndim==0 else v) for k,v in dict(np.load(p)).items()}
    T[z['cond']].append(z)
for c in ORDER: T[c].sort(key=lambda z:z['rat'])
plt.rcParams.update({'font.family':'Arial','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.titlesize':11,'axes.titleweight':'bold','savefig.facecolor':'white'})


def save(fig,name):
    fig.savefig(FIG/f'{name}.png',dpi=180,bbox_inches='tight')
    fig.savefig(FIG/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)


P1_SP1=(.4623,-.0624)  # SP1: checking platform mirrored through the pool centre (opposite quadrant)
P1=(.28,-.355)  # training platform, pool radii from centre (x right, y down)
def pool(ax,z):
    ax.add_patch(Circle((0,0),1,fill=False,color='#666',lw=.7))
    platform=(z['platform']-z['pool'][:2])/z['pool'][2]
    ax.add_patch(Circle(platform,.165,fill=False,color='#333',lw=.6,ls='--'))
    p1=P1 if z['cond'] in ('kac_d6','kac_d8') else P1_SP1  # P1: training platform; KAC from training tracks, SP1 assumed opposite quadrant
    ax.add_patch(Circle(p1,20/86,fill=False,color='#7a3fb0',lw=.7,ls=':')); ax.plot(*p1,marker='D',ms=3.5,color='#7a3fb0')
    ax.set(xlim=(-1.05,1.05),ylim=(1.05,-1.05),aspect='equal')
    ax.axis('off')


def positions(z,key='body'):
    return (z[key]-z['pool'][:2])/z['pool'][2]


fig,axs=plt.subplots(2,3,figsize=(12,8))
for j,c in enumerate(ORDER):
    for i,s in enumerate(('F','M')):
        ax=axs[i,j]; rats=[z for z in T[c] if z['sex']==s]; pool(ax,rats[0])
        for z in rats:
            xy=positions(z); ax.plot(*xy.T,color=COL[s],alpha=.5,lw=.6)
        cov=D[(D.cond==c)&(D.sex==s)].pct_missing.mean()
        ax.set_title(f'{LABEL[c]}\n{"Females" if s=="F" else "Males"}, n={len(rats)} · {cov:.1f}% unknown')
fig.suptitle('Cleaned paths: gaps stay blank; no lines bridge missing tracking',fontsize=16,fontweight='bold')
fig.tight_layout(rect=(0,0,1,.94)); save(fig,'01_cleaned_paths')

fig,axs=plt.subplots(2,3,figsize=(12,8))
for j,c in enumerate(ORDER):
    for i,s in enumerate(('F','M')):
        ax=axs[i,j]; rats=[z for z in T[c] if z['sex']==s]; H=[]
        for z in rats:
            xy=positions(z); xy=xy[np.isfinite(xy).all(1)]
            h,_,_=np.histogram2d(*xy.T,bins=[np.linspace(-1.05,1.05,44)]*2)
            H.append(h/max(h.sum(),1))
        ax.imshow(np.log10(np.mean(H,axis=0).T*100+1e-3),extent=(-1.05,1.05,1.05,-1.05),
                  cmap='Blues' if s=='F' else 'Oranges',vmin=-3,vmax=1.5)
        pool(ax,rats[0]); ax.set_title(f'{LABEL[c]}\n{"Females" if s=="F" else "Males"}')
fig.suptitle('Occupancy of observed time · each rat has equal weight',fontsize=16,fontweight='bold')
fig.text(.5,.01,'These maps omit unknown time; they do not recover the missing swimming trajectories.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.03,1,.94)); save(fig,'02_observed_occupancy')

fig,axs=plt.subplots(1,3,figsize=(13,8))
for ax,c in zip(axs,ORDER):
    rs=sorted(T[c],key=lambda z:(z['sex']=='F',z['rat']))
    for y,z in enumerate(rs):
        ax.barh(y,120,height=.85,color='#e9ecef')
        for a,b in runs(z['off']): ax.barh(y,(b-a)/z['fps'],left=a/z['fps'],height=.85,color=COL[z['sex']])
        for a,b in runs(~z['valid']): ax.barh(y,(b-a)/z['fps'],left=a/z['fps'],height=.85,color='#32383e')
    ax.set(yticks=range(len(rs)),yticklabels=[f'{z["sex"]}{z["rat"]}' for z in rs],xlim=(0,120),xlabel='Seconds from release',title=LABEL[c])
    ax.invert_yaxis(); ax.tick_params(axis='y',labelsize=8)
fig.suptitle('Platform state: grey = on · sex colour = off · dark = unknown',fontsize=15,fontweight='bold')
fig.tight_layout(rect=(0,0,1,.95)); save(fig,'03_platform_state')

fig,axs=plt.subplots(1,3,figsize=(12,7))
for ax,c in zip(axs,ORDER):
    d=D[D.cond==c].sort_values('pct_missing')
    ax.barh(range(len(d)),d.pct_missing,color=[COL[s] for s in d.sex])
    ax.set(yticks=range(len(d)),yticklabels=[f'{s}{r}' for s,r in zip(d.sex,d.rat)],xlabel='Unknown body tracking (%)',title=LABEL[c])
    ax.set_xlim(0,max(1,D.pct_missing.max()*1.1)); ax.tick_params(axis='y',labelsize=8)
fig.suptitle('Missingness is an outcome of quality control, not zero movement',fontsize=15,fontweight='bold')
fig.tight_layout(rect=(0,0,1,.95)); save(fig,'04_missingness')

fig,axs=plt.subplots(1,2,figsize=(9,5),sharey=True)
for ax,s in zip(axs,('M','F')):
    r=B[B.group==s].iloc[0]
    low=np.array([r.day6_lower,r.day8_lower]); high=np.array([r.day6_upper,r.day8_upper])
    ax.fill_between([0,1],low,high,color=COL[s],alpha=.25)
    ax.plot([0,1],low,'o-',color=COL[s],label='Retained on-platform time')
    ax.plot([0,1],high,'o--',color=COL[s],label='Upper bound: all unknown time on')
    for x,a,b in zip((0,1),low,high): ax.text(x,b+2,f'{a:.1f}–{b:.1f}%',ha='center',fontsize=11)
    ax.set(xticks=[0,1],xticklabels=['Day 6\nstandard 1.5 cm','Day 8\nraised 3 cm'],ylim=(0,108),xlim=(-.2,1.2),
           title=f'{"Males" if s=="M" else "Females"} · n={int(r.n)}')
    ax.grid(axis='y',alpha=.15)
axs[0].set_ylabel('Mean time in platform zone (% of full trial)')
axs[0].legend(loc='lower left',fontsize=8)
fig.suptitle('Paired platform occupancy with tracking uncertainty',fontsize=16,fontweight='bold')
fig.text(.5,.01,'Bands bound unknown time; they are not confidence intervals. Day and depth share the same test order.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.93)); save(fig,'05_paired_platform_bounds')


def distributions(keys,filename,title):
    fig,axs=plt.subplots(1,len(keys),figsize=(4.5*len(keys),4.5))
    axs=np.atleast_1d(axs); rng=np.random.default_rng(12)
    for ax,(key,label) in zip(axs,keys):
        for j,c in enumerate(ORDER):
            for k,s in enumerate(('M','F')):
                vals=D[(D.cond==c)&(D.sex==s)][key].dropna()
                x=j*3+k
                ax.scatter(x+rng.uniform(-.17,.17,len(vals)),vals,color=COL[s],s=18,alpha=.7)
                ax.plot([x-.24,x+.24],[vals.mean()]*2,color='#222',lw=2)
        ax.set(xticks=[.5,3.5,6.5],xticklabels=['SP1','KAC D6','KAC D8'],ylabel=label)
        ax.grid(axis='y',alpha=.13)
    fig.suptitle(title,fontsize=15,fontweight='bold')
    fig.text(.5,.01,'Orange: males · Blue: females · Bars: means. Pose-derived candidates; manual behavioral validation remains pending.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.94)); save(fig,filename)


distributions([('head_turn_pre_deg_s','Head turn before first observed departure (deg/s)'),
               ('head_sweeps_per_min','Head sweeps / valid on-platform minute'),
               ('vte_episodes_per_min','Alternating-sweep episodes / valid minute')],
              '06_head_scanning','Head scanning after shared artifact masking')
distributions([('tail_sweeps_per_min','Tail sweeps / valid on-platform minute'),
               ('tail_vigour_deg_s','Tail angular speed (deg/s)'),
               ('drift_observed_cm_s','Observed on-platform body drift (cm/s)')],
              '07_tail_drift','Tail motion and drift after shared artifact masking')

E=pd.read_csv(RES/'lean_out_events.csv')
fig,axs=plt.subplots(1,3,figsize=(12,4.5),sharey=True)
for ax,c in zip(axs,ORDER):
    g=E[E.cond==c].groupby(['rat','kind']).idphi_2s_before.mean().unstack()
    if {'aborted','committed'}<=set(g.columns):
        g=g.dropna()
        for _,r in g.iterrows(): ax.plot([0,1],[r.aborted,r.committed],'-o',color='#aab2b8',ms=3,lw=.8)
        ax.plot([0,1],[g.aborted.mean(),g.committed.mean()],'-o',color='#172b3a',lw=2.5)
    q=CA[CA.cond==c]
    extra=f'\nn={int(q.iloc[0].n)}, Holm p={q.iloc[0].holm_p:.3f}' if len(q) else ''
    ax.set(xticks=[0,1],xticklabels=['Pulled-back peak','Confirmed departure'],title=LABEL[c]+extra,xlim=(-.2,1.2))
axs[0].set_ylabel('Head rotation in preceding 2 seconds (degrees)')
fig.suptitle('Exploratory lean-out comparison · complete observed windows only',fontsize=14,fontweight='bold')
fig.tight_layout(rect=(0,0,1,.93)); save(fig,'08_lean_outs')

sens=pd.read_csv(RES/'speed_sensitivity.csv')
main=D[['cond','rat','sex','pct_missing','platform_lower_pct','platform_upper_pct','departures_observed']].copy(); main['speed_limit']=60
sens=pd.concat([sens,main],ignore_index=True)
fig,axs=plt.subplots(1,2,figsize=(10,4))
for j,c in enumerate(ORDER):
    g=sens[sens.cond==c].groupby('speed_limit').mean(numeric_only=True)
    axs[0].plot(g.index,g.pct_missing,'o-',label=LABEL[c])
    axs[1].plot(g.index,g.platform_lower_pct,'o-',label=LABEL[c])
axs[0].set_ylabel('Mean unknown body tracking (%)'); axs[1].set_ylabel('Retained on-platform fraction (%)')
for ax in axs:
    ax.set_xlabel('Speed rejection cutoff (cm/s)'); ax.set_xticks([40,60,100,150]); ax.grid(alpha=.15)
axs[0].legend(fontsize=8)
fig.suptitle('Sensitivity check: cutoff values are analysis choices',fontsize=14,fontweight='bold')
fig.tight_layout(rect=(0,0,1,.92)); save(fig,'09_threshold_sensitivity')

# Every animal gets an individual path panel, not just a cohort overlay.
for c in ORDER:
    for s in ('M','F'):
        rats=[z for z in T[c] if z['sex']==s]
        fig,axs=plt.subplots(4,4,figsize=(10,10))
        for ax in axs.flat: ax.axis('off')
        for ax,z in zip(axs.flat,rats):
            pool(ax,z); xy=positions(z); ax.plot(*xy.T,color=COL[s],lw=.7)
            missing=100*(~z['valid']).mean()
            ax.set_title(f'Rat {z["rat"]}\n{missing:.1f}% unknown',fontsize=9)
        fig.suptitle(f'{LABEL[c]} · {"males" if s=="M" else "females"} · individual cleaned paths',fontsize=15,fontweight='bold')
        fig.tight_layout(rect=(0,0,1,.96)); save(fig,f'atlas_{c}_{s}')

q=D.groupby(['cond','sex'])[['pct_missing','pct_interpolated','head_exposure_s','tail_exposure_s']].mean().round(2).reset_index()
q.to_csv(RES/'coverage_summary.csv',index=False)
notes=pd.read_csv(RES/'notes_validation.csv')
summary=[]
for c,g in notes[notes.known_note].groupby('cond'):
    summary.append(f'{LABEL[c]}: {int(g.agreement.sum())}/{len(g)} explicit stayed/left notes agree; '
                   f'{int((g.cleaned_class=="unknown").sum())} remain unknown.')
table=B.round(2).rename(columns={'group':'Group','n':'Pairs','day6_lower':'D6 lower %','day6_upper':'D6 upper %',
    'day8_lower':'D8 lower %','day8_upper':'D8 upper %','change_min':'Change min (pp)','change_max':'Change max (pp)'})
sections=[
('01_cleaned_paths','Paths after cleaning','Long gaps are not joined. A smooth-looking plot is not proof of accurate tracking; all 91 individual panels are available below.'),
('02_observed_occupancy','Occupancy of tracked time','Each rat contributes equal weight. Missing swimming time makes these maps incomplete.'),
('03_platform_state','On, off, and unknown','Unknown frames are neither stayed nor left. Missing stretches cannot create additional departures.'),
('04_missingness','How much data was lost','Body coverage is reported per animal. Short internal gaps of at most 0.5 seconds may be interpolated; longer gaps stay missing.'),
('05_paired_platform_bounds','The Day 6 control and Day 8 comparison','These full-trial bounds allow missing time to be either on or off the platform, conditional on retained tracking and short-gap interpolation being correct. They are not statistical confidence intervals and do not include every possible tracking error. Avoid treating observed-only time as an unbiased full-trial estimate.'),
('06_head_scanning','Head scanning candidates','Angles restart after gaps. Rates use valid on-platform exposure. These measures are operational definitions, not a validated measure of deliberation.'),
('07_tail_drift','Tail movement and drift candidates','Circular angle differences avoid false 360-degree turns. Tail motion and drift correlation do not establish which causes the other.'),
('08_lean_outs','Pulled-back peaks versus departures','Each confirmed departure appears once. Events need complete observed pre-event windows; this changes the eligible sample. The three cohort p-values are Holm-corrected.'),
('09_threshold_sensitivity','Dependence on the speed cutoff','The 60 cm/s threshold is a QC assumption, tested against 40, 100, and 150 cm/s. False-spot and rim thresholds remain fixed; full threshold validation is still pending.')]
parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Checking tests — tracking quality review</title><style>
body{font:17px/1.55 system-ui,sans-serif;background:#f3f5f6;color:#1b2b36;margin:0}main{max-width:1120px;margin:auto;padding:32px 24px 80px}
h1{font-size:40px;line-height:1.1}h2{margin-top:36px}p{max-width:85ch}img,video{width:100%;height:auto;background:white;border:1px solid #d8dfe3}
.notice{padding:18px;background:#fff3d8;border-left:5px solid #b67919}table{border-collapse:collapse;font-size:14px;width:100%;background:white}
th,td{padding:9px;text-align:right;border-bottom:1px solid #ddd}th:first-child,td:first-child{text-align:left}.scroll{overflow:auto}a{color:#17637e}
section{margin:36px 0}summary{cursor:pointer;font-weight:bold}.small{font-size:14px;color:#52616a}</style><main>
<p class="small">SP1 and KAC checking tests · November 7, 2026 · local reanalysis</p>
<h1>Tracking gaps made explicit</h1>
<div class="notice"><strong>Known artifact locations are masked; missing trajectories remain unresolved.</strong>
<p>The v2 model sometimes follows an empty rim location rather than the swimming rat. Those frames are masked, and long gaps remain unknown. Swimming distance, wall time, head/tail behaviors, and causal interpretations are not validated poster findings yet.</p></div>
<p>KAC uses best-240 on both days: 29 Day 6 and 30 Day 8 animals, with 29 pairs (14 males, 15 females). SP1 uses best-190 with test-to-rat mapping from AnyMaze, 16 animals per sex. SP1 sex labels were already confirmed in the earlier handoff.</p>
<h2>What the platform comparison can support</h2>
<p>Day 6 females spent 70.9–73.5% of the trial in the platform zone under the missing-time bounds, versus 98.0% for males. Day 8 female bounds widen to 62.7–76.3%, with 13.5% unknown tracking on average. The female change from Day 6 is bounded by −10.8 to +5.3 percentage points; its direction is unresolved under these assumptions.</p>
<p>These bounds assume retained tracking and short-gap interpolation are correct. They do not cover all tracking errors or sampling uncertainty. The Day 6 to Day 8 comparison also combines water depth with test order and repeat exposure.</p>
<p>Head and tail sex differences remain in the exploratory calculations. The pulled-back-versus-departure comparison is no longer significant in any cohort after complete-window filtering, removal of duplicate departure events, and correction across three cohorts. This does not prove the behaviors are equivalent; it changes what the present analysis supports.</p>''',
        '<div class="scroll">'+table.to_html(index=False,border=0)+'</div>',
        '<p>'+' '.join(summary)+'</p>',
        '<h2>Source-video checks</h2><p>Selected source frames confirm the false rim points. Day 6 rat 4 is already swimming around 8–10 seconds, and rat 26 around 85 seconds. Day 8 rat 13 is on the platform at 65 seconds and swimming around 75–80 seconds. These spot checks do not establish exact departure times or replace the original notes.</p>',
        '<p>Time zero follows the supplied release markers; these are not all frame-verified. SP1 rat 1 starts with a placement frame showing the hand outside the pool, and placement frames also remain at the start of some KAC clips. Precise first-departure and early head-motion measures remain provisional. Invalid initial tracking is unknown, not a departure.</p>',
        '<details><summary>Open source-frame contact sheets</summary>']
for p in sorted((HERE/'review').glob('source_*.jpg')):
    parts.append(f'<p>{html.escape(p.stem)}</p><img loading="lazy" src="review/{p.name}" alt="Source-video tracking audit">')
parts.append('</details>')
for name,title,caption in sections:
    parts.append(f'<section><h2>{title}</h2><img src="figures/{name}.png" alt="{title}"><p>{caption}</p><a href="figures/{name}.svg">Editable SVG</a></section>')
parts.append('<h2>Every animal</h2><details><summary>Individual path atlas — 91 animals</summary>')
for c in ORDER:
    for s in ('M','F'):
        parts.append(f'<img loading="lazy" src="figures/atlas_{c}_{s}.png" alt="{LABEL[c]}, {s}, individual paths">')
parts.append('</details><h2>Video checks</h2><p>White circle: platform zone. Coloured point and trail: cleaned tracking. Red point in artifact examples: original tracking. UNKNOWN is displayed during long gaps; trails stop rather than connecting across them. Female/male examples are selected nearest the within-sex median platform occupancy, early head rotation, or tail-sweep rate, as appropriate; one example does not summarize a group.</p>')
for p in sorted((HERE/'demos').glob('*.mp4')):
    title=p.stem.replace('leave_vs_stay','Typical female and male trial').replace('_',' ')
    parts.append(f'<h3>{html.escape(title)}</h3><video src="demos/{p.name}" controls preload="metadata"></video>')
parts.extend(['<h2>Coverage</h2><div class="scroll">'+q.to_html(index=False,border=0)+'</div>',
'''<h2>Method and remaining limits</h2><ul>
<li>Body: mid-spine, head-center fallback below confidence 0.3. One shared artifact mask invalidates body, head and tail together.</li>
<li>Mask body points within 40 pixels of the documented false spot, beyond 0.98 of outer pool radius, or either side of a smoothed-body speed jump above 60 cm/s. These geometry and speed thresholds may remove some genuine edge movement.</li>
<li>Interpolate whole internal gaps only when at most 0.5 seconds; no partial filling of longer gaps, no edge filling. Smoothing and angle derivatives do not bridge long gaps.</li>
<li>Platform zone: 0.165 pool radii. Departure: at least one second of observed off-platform frames. Missing onset intervals are labelled; departure counts are observed lower bounds when data are missing.</li>
<li>Head confidence 0.6; tail confidence 0.5. Rates use eligible observed time, not the full trial. Head sweeps are at least 30 degrees, tail sweeps at least 20 degrees; alternating head sweeps within two seconds are labelled VTE-like candidates only.</li>
<li>Head and tail exposure differs by sex. Rate normalization does not guarantee that missing observations are unbiased. Individual retained segments, posture labels, and behavioral event definitions still need manual validation.</li>
<li>SP1 linear distances assume the KAC 172-cm pool diameter. Percentages and angles do not require that assumption.</li>
<li>Next: recover KAC swimming tracks (first-model rerun or additional labeling), validate representative head/tail/lean-out events manually, confirm SP1 release alignment, and then reassess the poster claims. Day 7 remains untracked; AK1 remains out of scope.</li>
</ul><p class="small">Original dlc_story numerical outputs are preserved. All 15 figure images were visually inspected; sampled frames from each of the nine videos were inspected and the complete video files were decoded for integrity. This is not frame-by-frame behavioral annotation. This report replaces none of the raw videos or tracking files and is not published externally.</p>
<p><a href="results/per_rat_measures.csv">Per-rat results</a> · <a href="results/notes_validation.csv">Notes comparison</a> · <a href="results/provenance.csv">Input provenance</a> · <a href="results/sex_statistics.csv">Exploratory sex comparisons</a> · <a href="results/method.json">Method settings</a></p></main></html>'''])
(HERE/'report.html').write_text('\n'.join(parts),encoding='utf-8')
print('Saved 9 summary figures, 6 individual atlases, and report.html',flush=True)
