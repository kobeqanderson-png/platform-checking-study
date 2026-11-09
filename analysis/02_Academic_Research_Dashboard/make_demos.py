"""Read original video and render corrected, gap-aware overlays in local demos/."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import cv2
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent; DEM=HERE/'demos'; REVIEW=HERE/'review'
D=pd.read_csv(HERE/'results'/'per_rat_measures.csv')
FF=shutil.which('ffmpeg')
COL={'F':(214,120,42),'M':(52,104,235)}
NAME={'sp1':'SP1','kac_d6':'KAC Day 6','kac_d8':'KAC Day 8'}


def load(cond,rat):
    return {k:(v.item() if v.ndim==0 else v) for k,v in dict(np.load(HERE/'cache'/f'{cond}_rat{rat:02d}.npz')).items()}


def text(f,s,pt,size=.5,color=(255,255,255)):
    cv2.putText(f,s,pt,0,size,(0,0,0),3,cv2.LINE_AA)
    cv2.putText(f,s,pt,0,size,color,1,cv2.LINE_AA)


def typical(cond,sex,metric):
    d=D[(D.cond==cond)&(D.sex==sex)].dropna(subset=[metric])
    return int(d.loc[(d[metric]-d[metric].median()).abs().idxmin(),'rat'])


def frame_source(z,start,end,step):
    cap=cv2.VideoCapture(z['video']); assert cap.isOpened(),z['video']
    cap.set(cv2.CAP_PROP_POS_FRAMES,round((z['start']+start)*z['fps']))
    for i in range(round(start*z['fps']),round(end*z['fps'])):
        ok=cap.grab()
        if not ok: raise RuntimeError(f'Short source video: {z["video"]} at {i}')
        if (i-round(start*z['fps']))%step==0:
            ok,f=cap.retrieve()
            assert ok
            yield i,f
    cap.release()


def tile(f,z,i,mode,trail):
    R=z['pool'][2]; centre=z['platform'] if mode in ('head','tail') else z['pool'][:2]
    side=int((.68 if mode in ('head','tail') else 2.12)*R)
    x0,y0=np.floor(centre-side/2).astype(int)
    W=480; scale=W/side
    # Warp handles any frame edge without guessing padding indices.
    crop=cv2.warpAffine(f,np.array([[scale,0,-x0*scale],[0,scale,-y0*scale]],float),(W,W))
    def point(p): return tuple(np.rint((p-[x0,y0])*scale).astype(int))
    def ok(p): return np.isfinite(p).all()
    cv2.circle(crop,point(z['platform']),round(.165*R*scale),(255,255,255),1,cv2.LINE_AA)
    if True:  # P1: training platform location; KAC from training tracks, SP1 assumed opposite quadrant
        p1=point(np.array(z['pool'][:2])+np.array([.28,-.355] if z['cond']!='sp1' else [.4623,-.0624])*R)
        cv2.circle(crop,p1,round(20/86*R*scale),(176,63,122),1,cv2.LINE_AA)
        cv2.drawMarker(crop,p1,(176,63,122),cv2.MARKER_DIAMOND,10,2,cv2.LINE_AA)
        cv2.putText(crop,'P1 (trained)',(p1[0]+8,p1[1]-8),cv2.FONT_HERSHEY_SIMPLEX,.42,(176,63,122),1,cv2.LINE_AA)
    body=z['body'][i]
    if ok(body):
        trail.append((i,point(body)))
        trail[:]=[(t,p) for t,p in trail if t>=i-3*z['fps']]
        if len(trail)>1: cv2.polylines(crop,[np.array([p for _,p in trail],np.int32)],False,COL[z['sex']],2,cv2.LINE_AA)
        cv2.circle(crop,point(body),5,COL[z['sex']],-1)
    else:
        trail.clear()
    if mode=='audit' and ok(z['body_raw'][i]):
        cv2.circle(crop,point(z['body_raw'][i]),8,(0,0,255),2,cv2.LINE_AA)
    if mode in ('head','tail'):
        if ok(z['nose'][i]) and ok(z['neck'][i]) and np.isfinite(z['head_angle'][i]):
            a=point(z['neck'][i]); b=point(z['nose'][i])
            cv2.arrowedLine(crop,a,b,COL[z['sex']],2,cv2.LINE_AA,tipLength=.3)
        if mode=='tail':
            parts=['tail_base','tail_quarter','tail_mid','tail_three_quarter','tail_tip']
            for a,b in zip(parts[:-1],parts[1:]):
                if a in z and b in z and ok(z[a][i]) and ok(z[b][i]) and min(z[a+'_lk'][i],z[b+'_lk'][i])>=.5:
                    cv2.line(crop,point(z[a][i]),point(z[b][i]),(0,215,255),2,cv2.LINE_AA)
    state='UNKNOWN' if not z['valid'][i] else ('ON PLATFORM' if z['inside'][i] else 'OFF PLATFORM')
    label_y=420 if mode=='audit' else 24
    text(crop,f'{NAME[z["cond"]]} | {z["sex"]} rat {z["rat"]}',(10,label_y),.6)
    text(crop,state,(10,label_y+25),.55,(150,220,255) if state=='UNKNOWN' else (255,255,255))
    if mode=='head': text(crop,f'Head rotation: {z["turn"][i]:.0f} deg/s' if np.isfinite(z['turn'][i]) else 'Head rotation: unavailable',(10,460),.55)
    if mode=='tail': text(crop,f'Drift: {z["drift"][i]:.1f} cm/s' if np.isfinite(z['drift'][i]) else 'Drift: unavailable',(10,460),.55)
    return crop


def render(name,zs,start,end,mode,speed):
    fps=zs[0]['fps']; assert all(z['fps']==fps for z in zs)
    step=4 if fps==30 and speed==4 else 1
    outputfps=fps*speed/step
    width=480*len(zs); height=524
    out=DEM/(name+'.mp4')
    process=subprocess.Popen([FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{width}x{height}',
        '-r',str(outputfps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
    trails=[[] for z in zs]
    times=np.linspace(start,end-.5,5)
    if name=='artifact_kac_d6_rat22': times=[100,103.1,104.1,105.1,109.5]
    if name=='artifact_kac_d8_rat28': times=[50,54.7,55.7,56.7,59.5]
    wanted={round(t*fps) for t in times}
    snapshots=[]; next_snapshot=iter(sorted(wanted)); target=next(next_snapshot,None)
    count=0
    for fs in zip(*(frame_source(z,start,end,step) for z in zs)):
        i=fs[0][0]; tiles=[tile(f,z,idx,mode,trail) for (idx,f),z,trail in zip(fs,zs,trails)]
        bar=np.full((44,width,3),245,np.uint8)
        if mode=='audit':
            cv2.putText(bar,f't={i/fps:5.1f}s | {speed}x | red: original tracking',(10,17),0,.48,(25,35,45),1,cv2.LINE_AA)
            cv2.putText(bar,'colour: cleaned | gaps: UNKNOWN',(10,36),0,.48,(25,35,45),1,cv2.LINE_AA)
        else:
            cv2.putText(bar,f't={i/fps:5.1f}s | {speed}x | trail stops at missing tracking',(10,28),0,.52,(25,35,45),1,cv2.LINE_AA)
        frame=np.vstack([np.hstack(tiles),bar]); process.stdin.write(frame.tobytes()); count+=1
        if target is not None and i>=target:
            snapshots.append(cv2.resize(frame,(width//2,height//2)))
            target=next(next_snapshot,None)
    process.stdin.close(); assert process.wait()==0
    expected=len(range(round(start*fps),round(end*fps),step))
    assert count==expected,(name,count,expected)
    if snapshots: cv2.imwrite(str(REVIEW/(name+'_contact.jpg')),np.vstack(snapshots))
    cap=cv2.VideoCapture(str(out)); actual=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); savedfps=cap.get(cv2.CAP_PROP_FPS); cap.release()
    assert actual==expected,(name,actual,expected)
    assert abs(actual/savedfps-(end-start)/speed)<.1
    print(name,actual,'frames',flush=True)
    return dict(file=out.name,cond=zs[0]['cond'],rats=[z['rat'] for z in zs],mode=mode,start_s=start,end_s=end,playback_speed=speed,frames=actual)


if '--audit-only' in sys.argv:
    render('artifact_kac_d8_rat28',[load('kac_d8',28)],50,60,'audit',1)
    render('artifact_kac_d6_rat22',[load('kac_d6',22)],100,110,'audit',1)
    sys.exit(0)

made=[]
for cond in ('sp1','kac_d6','kac_d8'):
    zs=[load(cond,typical(cond,s,'platform_lower_pct')) for s in ('F','M')]
    made.append(render(f'leave_vs_stay_{cond}',zs,0,120,'body',4))
    zs=[load(cond,typical(cond,s,'head_turn_first10_deg_s')) for s in ('F','M')]
    made.append(render(f'head_turning_{cond}',zs,0,20,'head',1))
zs=[load('sp1',typical('sp1',s,'tail_sweeps_per_min')) for s in ('F','M')]
made.append(render('tail_sweeping_sp1',zs,0,20,'tail',1))
made.append(render('artifact_kac_d8_rat28',[load('kac_d8',28)],50,60,'audit',1))
made.append(render('artifact_kac_d6_rat22',[load('kac_d6',22)],100,110,'audit',1))
(DEM/'manifest.json').write_text(json.dumps(made,indent=2))
