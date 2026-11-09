"""Wire existing static pages without rebuilding unrelated dashboard results."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
profile_link='<p class="sub" style="margin-top:18px"><a href="profiles.html" style="font-weight:700;color:var(--accent)">Explore individual neurobehavioral profiles →</a> Learning history, scanning, initiation, search and recurrence for every animal. Neural measurements pending.</p>\n'
for p in [ROOT/'dlc_cleaned/dashboard.html',ROOT/'dlc_cleaned/site/index.html']:
    text=p.read_text(encoding='utf-8')
    if 'href="profiles.html"' not in text:
        marker='<p class="sub" style="margin-top:18px"><a href="explorer.html"'
        assert marker in text
        text=text.replace(marker,profile_link+marker,1)
        p.write_text(text,encoding='utf-8')
p=ROOT/'dlc_explorer/explorer_template.html'
text=p.read_text(encoding='utf-8')
if 'href="profiles.html"' not in text:
    text=text.replace('</header>','<p><a href="profiles.html">Open multidimensional individual profiles →</a></p></header>',1)
text=text.replace('P1/wall route labels require ≥0.5 s in that region.','P1 route labels count any entry within 20 cm, with no dwell threshold. Wall labels require ≥0.5 s.')
old="updateGroup();$('condition').onchange="
new="updateGroup();const requestedAnimal=new URLSearchParams(location.search).get('animal');if(S.some(s=>s.id===requestedAnimal))selectAnimal(requestedAnimal);$('condition').onchange="
if old in text:text=text.replace(old,new,1)
p.write_text(text,encoding='utf-8')
p=ROOT/'individual_profiles/profiles_template.html'
text=p.read_text(encoding='utf-8')
if 'data-view="repetition"' not in text:
    text=text.replace('<button data-view="relationships"','<button data-view="repetition" role="tab" aria-selected="false">Returns &amp; repetition</button><button data-view="relationships"',1)
p.write_text(text,encoding='utf-8')
