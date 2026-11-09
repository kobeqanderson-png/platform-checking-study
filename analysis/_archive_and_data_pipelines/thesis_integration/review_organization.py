from pathlib import Path
import sys,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
from organization import excursions
HERE=Path(__file__).parent; OUT=HERE/'organization'; CACHE=HERE.parent/'dlc_cleaned/cache'
e=pd.read_csv(OUT/'excursions.csv'); d=pd.read_csv(OUT/'animals.csv')
assert len(d)==91 and not d.duplicated(['cond','rat']).any()
sens=[]
for p in CACHE.glob('*.npz'):
    z=dict(np.load(p)); fps=int(z['fps'])
    for threshold in (.5,1,2):
        ev=excursions(z['inside'],z['off'],z['valid'],round(fps*threshold))
        sens.append(dict(cond=str(z['cond']),rat=int(z['rat']),sex=str(z['sex']),minimum_off_and_return_s=threshold,
                         complete=sum(x['complete'] for x in ev),segments=len(ev)))
for r in e.itertuples():
    z=dict(np.load(CACHE/f'{r.cond}_rat{r.rat:02d}.npz')); fps=int(z['fps'])
    a,b=round(r.start_s*fps),round(r.end_s*fps)
    assert z['valid'][a:b].all()
    if r.complete:
        assert a>0 and z['inside'][a-1] and z['inside'][b:b+fps].all()
pd.DataFrame(sens).to_csv(OUT/'threshold_sensitivity.csv',index=False)
ex=e[(e.cond=='sp1')&e.complete].sort_values(['sex','rat','start_s'])
fig,axs=plt.subplots(4,6,figsize=(15,10))
for ax,r in zip(axs.flat,ex.itertuples()):
    z=dict(np.load(CACHE/f'sp1_rat{r.rat:02d}.npz')); fps=int(z['fps']); pool=z['pool']; ps=(z['platform']-pool[:2])/pool[2]
    a,b=round(r.start_s*fps),round(r.end_s*fps)
    xy=(z['body'][a:b+1]-pool[:2])/pool[2]
    ax.add_patch(Rectangle((0 if ps[0]<0 else -1,0 if ps[1]<0 else -1),1,1,color='#e9efff'))
    ax.add_patch(Circle((0,0),1,fill=False,color='#666',lw=.7))
    ax.add_patch(Circle(ps,.165,fill=False,color='#777',ls='--',lw=.7))
    ax.plot(*xy.T,color='#2a78d6' if r.sex=='F' else '#d9591f',lw=1)
    ax.scatter(*xy[0],color='green',s=14);ax.scatter(*xy[-1],color='black',s=14)
    ax.set(xlim=(-1.05,1.05),ylim=(1.05,-1.05),aspect='equal');ax.axis('off')
    ax.set_title(f'{r.sex}{r.rat} | {r.start_s:.1f}–{r.end_s:.1f}s',fontsize=9)
fig.suptitle('SP1: every fully observed excursion\nShading: opposite quadrant, not exact learned-place boundary; green: start, black: return',fontsize=13)
fig.tight_layout(rect=(0,0,1,.93));fig.savefig(OUT/'sp1_excursion_atlas.png',dpi=150);plt.close(fig)
print('All excursion spans verified; 24 SP1 complete paths plotted.')
print(pd.DataFrame(sens).groupby(['cond','minimum_off_and_return_s']).complete.sum().to_string())
