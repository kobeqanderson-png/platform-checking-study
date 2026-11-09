from pathlib import Path
import cv2,numpy as np,pandas as pd
HERE=Path(__file__).parent; OUT=HERE/'organization'
e=pd.read_csv(OUT/'excursions.csv'); e=e[(e.cond=='sp1')&e.complete]
f=e[e.sex=='F']; selected=pd.concat([f.iloc[[0,len(f)//2]],e[e.sex=='M'].iloc[[0]]])
rows=[]
for r in selected.itertuples():
    z=dict(np.load(HERE.parent/'dlc_cleaned/cache'/f'sp1_rat{r.rat:02d}.npz')); fps=int(z['fps'])
    cap=cv2.VideoCapture(str(z['video'])); assert cap.isOpened()
    tiles=[]
    for t in [max(0,r.start_s-.5),r.start_s+.5,(r.start_s+r.end_s)/2,r.end_s-.5,min(119.9,r.end_s+.5)]:
        i=round(t*fps);cap.set(cv2.CAP_PROP_POS_FRAMES,round((float(z['start'])+t)*fps));ok,frame=cap.read();assert ok
        body=z['body'][i]
        if np.isfinite(body).all(): cv2.circle(frame,tuple(np.rint(body).astype(int)),5,(0,200,0),2)
        cv2.circle(frame,tuple(np.rint(z['platform']).astype(int)),round(.165*z['pool'][2]),(255,255,255),1)
        frame=cv2.resize(frame,(320,240));cv2.putText(frame,f'{r.sex}{r.rat} t={t:.1f}s',(8,20),0,.5,(0,0,255),1)
        tiles.append(frame)
    cap.release();rows.append(np.hstack(tiles))
cv2.imwrite(str(OUT/'source_event_checks.jpg'),np.vstack(rows))
selected.to_csv(OUT/'source_event_checks.csv',index=False)
print('Saved source frames for three SP1 excursions, five times each.')
