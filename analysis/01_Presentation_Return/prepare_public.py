"""Prepare the explicitly authorized public Return release without editing the old site."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
OUT=H/'public_overlay'
(OUT/'portal_data').mkdir(parents=True,exist_ok=True)
domain='https://returnto-kobe.vercel.app'
html=(H/'site/portal.html').read_text(encoding='utf-8').replace('Protected research preview','Public research preview')
(OUT/'portal.html').write_text(html,encoding='utf-8')
(OUT/'vercel.json').write_text(json.dumps({'rewrites':[{'source':'/','destination':'/portal.html'}]}),encoding='utf-8')
readme=(H/'README.md').read_text(encoding='utf-8')
readme=readme.replace('# Return — protected research portal','# Return — public research portal')
old='Deploy by uploading the new files and reusing existing hashes in the manifest on the existing protected project; do not alter protection or promote to a public domain.'
new='The separately authorized public release uses project `returnto` and https://returnto-kobe.vercel.app. Run `prepare_public.py` after the base packaging step, then upload the public overlay and deploy `public_deploy_files.json` to that project. The root route opens the portal; `/index.html` retains the research dashboard.'
assert old in readme
readme=readme.replace(old,new)
(OUT/'portal_data/README.md').write_text(readme,encoding='utf-8')
log=(H.parent/'portal_planning/DECISIONS_LOG.md').read_text(encoding='utf-8')
log=log.replace('# Portal decisions log','# Portal decisions log\n\n## Public release authorized\n\nThe user explicitly requested a separate public Vercel deployment of the new app and selected `returnto-kobe.vercel.app` after Vercel reported `returnto.vercel.app` owned by another team. Destination project: `returnto`. The research portal and its existing linked dashboard/data are public on this host. Earlier protection notes below are historical and do not describe this public release. The old project was not changed.',1)
(OUT/'portal_data/DECISIONS_LOG.md').write_text(log,encoding='utf-8')
manifest=json.loads((H/'site/portal_data/manifest.json').read_text())
manifest['public_release']={'domain':domain,'project':'returnto','authorization':'User explicitly requested public deployment, then selected returnto-kobe.vercel.app','root':'/portal.html'}
for p in sorted(OUT.rglob('*')):
    if not p.is_file() or p.name=='manifest.json':continue
    name=p.relative_to(OUT).as_posix()
    manifest['files']=[f for f in manifest['files'] if f['file']!=name]
    manifest['files'].append(dict(file=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
manifest['pipeline'].append(dict(file='prepare_public.py',sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
(OUT/'portal_data/manifest.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
over=[dict(file=p.relative_to(OUT).as_posix(),sha=hashlib.sha1(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in sorted(OUT.rglob('*')) if p.is_file()]
names={f['file'] for f in over}
files=[f for f in json.loads((H/'deploy_files.json').read_text()) if f['file'] not in names]+over
assert len(files)==len({f['file'] for f in files})
(H/'public_upload_files.json').write_text(json.dumps(over),encoding='utf-8')
(H/'public_deploy_files.json').write_text(json.dumps(files),encoding='utf-8')
print(json.dumps({'domain':domain,'changed_files':len(over),'total_files':len(files),'bytes':sum(f['size'] for f in files)}))
