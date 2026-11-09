import sys
sys.stdout.reconfigure(encoding='utf-8')

DASH = r'c:\Users\kobeq\Documents\KAC database\analysis\dlc_cleaned\dashboard.html'
SITE = r'c:\Users\kobeq\Documents\KAC database\analysis\dlc_cleaned\site\index.html'

NEW_LINK = ('<p class="sub" style="margin-top:10px">'
            '<a href="../correlations/correlations_dashboard.html" '
            'style="font-weight:700;color:var(--accent)">'
            'Cross-experiment correlations: Anxiety &amp; Exploration \u2192'
            '</a> EPM, open field, and NOR measures correlated with checking behaviour.</p>')

for path in [DASH]:
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    # Find the explorer paragraph closing and insert after it, before </header>
    MARKER = '</header>'
    idx = html.find(MARKER)
    if idx == -1:
        print(f'MARKER not found in {path}')
        continue
    # Check if already added
    if 'correlations_dashboard.html' in html:
        print(f'Link already present in {path}')
        continue
    html = html[:idx] + NEW_LINK + '\r\n' + html[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Updated: {path}')

# Now handle site/index.html
with open(SITE, 'r', encoding='utf-8') as f:
    site_html = f.read()
print(f'site/index.html size: {len(site_html)} chars')
# Find the atlas link in site index
if 'correlations_dashboard.html' in site_html:
    print('Link already in site/index.html')
else:
    # Try to find similar anchor
    target = 'explorer.html'
    idx2 = site_html.find(target)
    if idx2 == -1:
        print('explorer.html not found in site/index.html')
        # Find </header>
        idx2 = site_html.find('</header>')
        if idx2 != -1:
            SITE_LINK = NEW_LINK.replace('../correlations/', '../../correlations/')
            site_html = site_html[:idx2] + SITE_LINK + '\r\n' + site_html[idx2:]
            with open(SITE, 'w', encoding='utf-8') as f:
                f.write(site_html)
            print(f'Updated site/index.html via </header>')
    else:
        # Find end of that paragraph
        p_end = site_html.find('</p>', idx2)
        if p_end == -1:
            print('Could not find paragraph end')
        else:
            SITE_LINK = NEW_LINK.replace('../correlations/', '../../correlations/')
            site_html = site_html[:p_end+4] + '\r\n' + SITE_LINK + site_html[p_end+4:]
            with open(SITE, 'w', encoding='utf-8') as f:
                f.write(site_html)
            print(f'Updated site/index.html')
print('Done.')
