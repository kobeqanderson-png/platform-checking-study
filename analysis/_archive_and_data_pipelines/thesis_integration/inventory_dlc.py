from pathlib import Path
import os,json,collections
root=Path(r'G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs')
rows=[]
for folder,dirs,files in os.walk(root):
    hs=[x for x in files if x.endswith('.h5') and 'DLC' in x]
    if hs:
        counts=collections.Counter(x.split('snapshot_')[-1].removesuffix('.h5') for x in hs)
        rows.append(dict(folder=folder,count=len(hs),models=dict(counts),files=hs))
out=Path(__file__).parent/'dlc_inventory.json'
out.write_text(json.dumps(rows,indent=2))
for r in rows: print(r['folder'],r['count'],r['models'])
