"""Copy SP1 raw tracks and inspect selected source-video frames; no Drive writes."""
from pathlib import Path
import shutil
import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'dlc_story'
G = Path(r'G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]')
(HERE / 'inputs' / 'sp1_tracks').mkdir(parents=True, exist_ok=True)
(HERE / 'review').mkdir(exist_ok=True)
for p in (G / 'Colab_Training_Runs' / 'sp1' / 'sp1_tracks').iterdir():
    if p.suffix == '.h5':
        shutil.copy2(p, HERE / 'inputs' / 'sp1_tracks' / p.name)

for cond, rat in [('kac_d8',28), ('kac_d8',22), ('kac_d6',22), ('kac_d6',4), ('kac_d6',26), ('kac_d8',13), ('sp1',1)]:
    z = dict(np.load(OLD / 'cache' / f'{cond}_rat{rat:02d}.npz'))
    fps, start = int(z['fps']), float(z['start'])
    if cond == 'kac_d8' and rat in (28,22):
        near = np.linalg.norm(z['body'] - [870,50], axis=1) < 40
        indices = np.flatnonzero(near)
        target = indices[len(indices)//2] / fps
        ts = [max(0,target-1),target,min(119,target+1)]
    elif cond == 'kac_d6' and rat == 22:
        far = np.linalg.norm(z['body'] - z['pool'][:2], axis=1) > .98*z['pool'][2]
        indices = np.flatnonzero(far)
        target = indices[len(indices)//2] / fps
        ts = [max(0,target-1),target,min(119,target+1)]
    elif cond == 'kac_d6' and rat == 4:
        ts = [7.8,10,40]
    elif cond == 'kac_d6' and rat == 26:
        ts = [85,90,100]
    elif cond == 'kac_d8' and rat == 13:
        ts = [65,75.3,80]
    else:
        target = np.argmax(np.linalg.norm(z['body'] - z['pool'][:2],axis=1))/fps
        ts = [max(0,target-1),target,min(119,target+1)]
    cap = cv2.VideoCapture(str(z['video'].item()))
    assert cap.isOpened(), str(z['video'])
    frames=[]
    for t in ts:
        cap.set(cv2.CAP_PROP_POS_FRAMES, round((start+t)*fps))
        ok, f = cap.read()
        assert ok, (cond,rat,t)
        i = min(len(z['body'])-1, round(t*fps))
        x,y = z['body'][i].round().astype(int)
        cv2.circle(f,(x,y),12,(0,0,255),3)
        f = cv2.resize(f,(640,round(f.shape[0]*640/f.shape[1])))
        cv2.putText(f,f'{cond} rat {rat} | t={t:.2f}s | red=old body',(8,24),0,.55,(0,0,0),4,cv2.LINE_AA)
        cv2.putText(f,f'{cond} rat {rat} | t={t:.2f}s | red=old body',(8,24),0,.55,(255,255,255),1,cv2.LINE_AA)
        frames.append(f)
    cap.release()
    out=HERE/'review'/f'source_{cond}_rat{rat:02d}.jpg'
    cv2.imwrite(str(out),np.vstack(frames))
    print(out.name, flush=True)
print('SP1 tracks copied:',len(list((HERE/'inputs'/'sp1_tracks').glob('*.h5'))),flush=True)
