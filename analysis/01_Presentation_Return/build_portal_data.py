"""Lossless native-frame export for the protected Return portal.

No raw recordings are mutated. Binary layout: N x 4 little-endian float64
pixel coordinates (selected unsmoothed x/y, processed x/y), then N uint8 flags.
Flags: 1 valid processed, 2 interpolated, 4 rejected original, 8 off placement.
NaNs remain NaNs. No thinning, rounding, or temporal interpolation is added.
"""
from pathlib import Path
import hashlib, json, re, sys, shutil
import numpy as np
import pandas as pd
import openpyxl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

HERE=Path(__file__).resolve().parent
AN=HERE.parent
OUT=HERE/'site'/'portal_data'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(AN/'dlc_cleaned'))
from tracking_qc import runs

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj): (OUT/name).write_text(json.dumps(obj,allow_nan=False,separators=(',',':')),encoding='utf-8')

profiles=json.loads((AN/'individual_profiles/exports/profile_data.json').read_text())
prov=pd.read_csv(AN/'dlc_cleaned/results/provenance.csv').set_index(['cond','rat'])
P1={'kac_d6':[.28,-.355],'kac_d8':[.28,-.355],'sp1':[.4623,-.0624]}
sessions=[]
checks=[]
fig,axs=plt.subplots(1,3,figsize=(15,5.5))
proof_ids=['kac_d6_25','kac_d8_25','sp1_25']
for s in profiles['sessions']:
    cond,rat=s['cond'],s['rat']; p=AN/f'dlc_cleaned/cache/{cond}_rat{rat:02d}.npz'
    z=np.load(p); n=len(z['body']); fps=int(z['fps']); src=prov.loc[(cond,rat)]
    assert n==120*fps and str(z['model'])==s['model']
    coords=np.column_stack([z['body_raw'],z['body']]).astype('<f8')
    flags=(z['valid'].astype('u1')+2*z['body_interpolated'].astype('u1')+4*z['rejected'].astype('u1')+8*z['off'].astype('u1'))
    track=OUT/(s['id']+'.bin'); track.write_bytes(coords.tobytes()+flags.tobytes())
    # Exact roundtrip from bytes, including NaNs, for every exported coordinate.
    reload=np.frombuffer(track.read_bytes(),dtype='<f8',count=n*4).reshape(n,4)
    np.testing.assert_array_equal(reload,coords)
    source_path=Path(src.source)
    source_checked=False
    # Independently validate one SP1 proof against its actual HDF source.
    if s['id']=='sp1_25':
        assert source_path.exists()
        assert sha(source_path)==src.sha256
        df=pd.read_hdf(source_path); df.columns=df.columns.droplevel(0)
        a=round(float(src.start_s)*fps); df=df.iloc[a:a+n]
        raw=df['spine_mid'][['x','y']].to_numpy().copy()
        fallback=~np.isfinite(df['spine_mid']['likelihood']) | (df['spine_mid']['likelihood']<.3)
        raw[fallback]=df['head_center'][['x','y']].to_numpy()[fallback]
        unsure=fallback & (~np.isfinite(df['head_center']['likelihood']) | (df['head_center']['likelihood']<.3))
        raw[unsure]=np.nan
        np.testing.assert_allclose(raw,z['body_raw'],equal_nan=True)
        source_checked=True
    rawnear=z['off'] & z['valid'] & (np.linalg.norm((z['body']-z['pool'][:2])/z['pool'][2]-P1[cond],axis=1)*86<=20)
    complete=[e for e in s['return_timeline'] if e['complete']]
    hits=sum(bool(rawnear[round(e['start']*fps):round(e['end']*fps)].any()) for e in complete)
    assert hits==s['area_successes'] and len(complete)==s['complete_excursions']
    for radius in [10,20,30]:
        for dwell in [0,.5,1]:
            eligible=z['off'] & z['valid']
            near=eligible & (np.linalg.norm((z['body']-z['pool'][:2])/z['pool'][2]-P1[cond],axis=1)*86<=radius)
            episodes=runs(near,max(1,int(np.ceil(dwell*fps))))
            known=sum(a>0 and eligible[a-1] and not near[a-1] for a,b in episodes)
            checks.append(dict(id=s['id'],radius=radius,dwell=dwell,episodes=len(episodes),entries=int(known),occupied_frames=int(sum(b-a for a,b in episodes))))
    meta=dict(s,frames=n,fps=fps,start_s=float(src.start_s),source_frame_start=round(float(src.start_s)*fps),
        pool_px=z['pool'].tolist(),placement_px=z['platform'].tolist(),p1_normalized=P1[cond],
        track=s['id']+'.bin',track_sha256=sha(track),cache_file=str(p.relative_to(AN)),cache_sha256=sha(p),
        tracking_source=str(source_path),tracking_source_sha256=src.sha256,source_rechecked_this_build=source_checked,
        source_hash_status='Rechecked against HDF' if source_checked else 'Hash recorded by original analysis; this build verified local cache',
        cache_raw_definition='Selected unsmoothed spine_mid, head_center fallback if confidence <0.3; insufficient confidence is missing',
        video=str(z['video']),original_frame_indexing='zero-based positional HDF row; frame = start_frame + window_frame')
    sessions.append(meta)
    if s['id'] in proof_ids:
        ax=axs[proof_ids.index(s['id'])]; rawxy=(z['body_raw']-z['pool'][:2])/z['pool'][2]
        ok=np.isfinite(rawxy).all(1)&~z['rejected']
        for a,b in runs(ok): ax.plot(rawxy[a:b,0],rawxy[a:b,1],color='#176f84',lw=.65)
        bad=np.isfinite(rawxy).all(1)&z['rejected']
        ax.scatter(rawxy[bad,0],rawxy[bad,1],s=6,c='#bd5827',alpha=.6)
        fill=(z['body'][z['body_interpolated']]-z['pool'][:2])/z['pool'][2]
        if len(fill): ax.scatter(fill[:,0],fill[:,1],s=10,c='#b14dab',marker='x')
        ax.add_patch(plt.Circle((0,0),1,fill=False,color='#182b32'))
        placement=(z['platform']-z['pool'][:2])/z['pool'][2]
        ax.add_patch(plt.Circle(placement,.165,fill=False,color='#176f84',ls='--'))
        ax.add_patch(plt.Circle(P1[cond],20/86,fill=False,color='#b08028',ls=':'))
        ax.set(xlim=(-1.12,1.12),ylim=(1.12,-1.12),aspect='equal',title=f"{profiles['labels'][cond]} · F25\n{fps} Hz · 120 s",xlabel='Pool-radius units')
        ax.text(.02,.02,f"Unknown: {(~z['valid']).sum()/fps:.1f} s\nFilled: {z['body_interpolated'].sum()/fps:.1f} s",transform=ax.transAxes,fontsize=9)
fig.suptitle('Three source trajectories before visual treatment',fontsize=18)
fig.text(.05,.02,'Teal: accepted unsmoothed selected positions. Orange: rejected points. Magenta: processing-filled points. No lines across gaps.\nDashed: placement region. Dotted: provisional former-goal neighborhood. KAC source HDF currently unavailable; local caches verified.',fontsize=10)
fig.tight_layout(rect=(0,.16,1,.93));fig.savefig(OUT/'three_trajectories.png',dpi=150);plt.close(fig)

akpath=Path('C:/Users/kobeq/Downloads/AK1_complete.xlsx')
wb=openpyxl.load_workbook(akpath,read_only=True,data_only=True)
values=list(wb['49-Prb4'].values); names=[str(v).strip() for v in values[0]]
ak=[]
for rownum,row in enumerate(values[1:],2):
    d=dict(zip(names,row)); subject=str(d.get('SUBJECT$','')).strip()
    if not re.fullmatch(r'rat\d+',subject): continue
    ak.append(dict(rat=int(subject[3:]),configuration=int(d['CTR_SIZE']),passages=float(d['PASSTH01']),path_m=float(d['PATHISmt']),duration_s=float(d['LATENTsc']),source_row=rownum))
akdf=pd.DataFrame(ak)
assert len(ak)==90 and akdf.rat.nunique()==30
assert (akdf.groupby('rat').configuration.nunique()==3).all() and (akdf.duration_s==120).all()
assert (akdf.groupby('rat').path_m.nunique()==1).all()
means=akdf.groupby('configuration').passages.mean().tolist()
np.testing.assert_allclose(means,[1.8,109/30,157/30])
write('ak1.json',dict(source=str(akpath),sha256=sha(akpath),sheet='49-Prb4',endpoint_status='Candidate 120-second endpoint; conference endpoint identity remains unconfirmed',column='PASSTH01',means=means,records=ak))
write('sessions.json',dict(sessions=sessions,features=profiles['features'],labels=profiles['labels'],format='float64-le x4 per frame, followed by uint8 flags',pool_diameter_cm_analysis=172,geometry_status='Provisional; brief specifies 172.5 cm. No rescaling applied.',p1_status='Assumed camera correspondence in KAC; reflected placement in SP1. Registration pending.',window_seconds=120))
write('verification_cases.json',checks)
write('verification.json',dict(sessions=len(sessions),animals=len({s['animal_id'] for s in sessions}),native_frames=sum(s['frames'] for s in sessions),binary_roundtrips='Exact, all coordinates including NaNs',source_hdf_rechecked=['sp1_25'],kac_original_hdf='Unavailable at recorded Drive path during this build; verified existing local cache hashes',complete_trips=sum(s['complete_excursions'] for s in sessions),complete_p1_trips=sum(s['area_successes'] for s in sessions),ak1_animals=30,ak1_rows=90,ak1_means=means,threshold_cases=len(checks)))
manifest=dict(version=1,approval='User: Yes do it (portal treatment approved)',sources=[dict(file=str(p),sha256=sha(p)) for p in [AN/'individual_profiles/exports/profile_data.json',AN/'dlc_cleaned/results/provenance.csv',AN/'dlc_cleaned/tracking_qc.py',akpath]],files=[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'])
write('manifest.json',manifest)
print(json.dumps(dict(sessions=len(sessions),bytes=sum(p.stat().st_size for p in OUT.iterdir()),ak1_means=means,proof=str(OUT/'three_trajectories.png'))))
