from pathlib import Path
import json,hashlib,shutil,zipfile
H=Path(__file__).resolve().parent
base=json.loads((H.parent/'individual_profiles/deploy_files.json').read_text())
src=H/'published_index.html'
assert hashlib.sha1(src.read_bytes()).hexdigest()=='036c2b8829036b2fb6141003e87abbf9e13e5420'
text=src.read_text(encoding='utf-8')
link='<p class="sub" style="margin-top:18px"><a href="portal.html" style="font-weight:700;color:var(--accent)">Enter Return — the interactive checking portal →</a> Paired trajectories, individual profiles, returns and the definitions behind the counts.</p>\n'
text=text.replace('<p class="sub" style="margin-top:18px"><a href="profiles.html"',link+'<p class="sub" style="margin-top:18px"><a href="profiles.html"')
(H/'site/index.html').write_text(text,encoding='utf-8')
for name,source in [('README.md',H/'README.md'),('DECISIONS_LOG.md',H.parent/'portal_planning/DECISIONS_LOG.md')]:shutil.copy2(source,H/'site/portal_data'/name)
manifest_path=H/'site/portal_data/manifest.json'
manifest=json.loads(manifest_path.read_text())
manifest['files']=[dict(file=p.relative_to(H/'site').as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((H/'site').rglob('*')) if p.is_file() and p!=manifest_path]
manifest['pipeline']=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [H/'build_portal_data.py',H/'package_portal.py',H/'verify_portal.js']]
manifest_path.write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
fresh=[]
for p in sorted((H/'site').rglob('*')):
    if p.is_file():fresh.append(dict(file=p.relative_to(H/'site').as_posix(),sha=hashlib.sha1(p.read_bytes()).hexdigest(),size=p.stat().st_size))
names={f['file'] for f in fresh};allfiles=[f for f in base if f['file'] not in names]+fresh
assert len({f['file'] for f in allfiles})==len(allfiles)
assert sum(f['size'] for f in allfiles)<25_000_000
(H/'deploy_files.json').write_text(json.dumps(allfiles),encoding='utf-8')
(H/'upload_files.json').write_text(json.dumps(fresh),encoding='utf-8')
with zipfile.ZipFile(H/'return_portal_source.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(H.rglob('*')):
        if p.is_file() and p.name!='return_portal_source.zip' and '__pycache__' not in p.parts and p.name!='published_index.html':z.write(p,p.relative_to(H))
print(json.dumps(dict(portal_files=len(fresh),deployment_files=len(allfiles),portal_bytes=sum(f['size'] for f in fresh),deployment_bytes=sum(f['size'] for f in allfiles))))
