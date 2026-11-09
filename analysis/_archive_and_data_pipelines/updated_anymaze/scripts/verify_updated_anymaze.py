"""Checks the updated AnyMaze files against the original zip without using the build script's logic.
Usage: verify_updated_anymaze.py <Check.zip> <updated folder> <tracking_pilot folder>"""
import csv, hashlib, io, os, sys, zipfile
ZIP, U, P = sys.argv[1:]
Z = zipfile.ZipFile(ZIP); fails = []
def check(ok, msg):
    if not ok: fails.append(msg)
NEW = 6; IDS = {'Test', 'Animal', 'Stage', 'Trial', 'Apparatus', 'Reason ended', 'Date', 'Day of week', 'Time', 'Time of day', 'User', 'Test notes', 'Recorded video file', 'Segment of test', 'Weight (g)', 'Sex', 'Treatment', 'Group', 'Strain', 'Age'}
CH = list(csv.DictReader(open(os.path.join(U, 'changes.csv'), encoding='utf-8-sig', newline='')))
key = lambda d, t, s: (int(d), int(t), s)
CK = {key(c['day'], c['test'], c['segment']): c for c in CH}
tot = byte = 0; used = set(); cap = {1: 30, 2: 30, 3: 30, 4: 30, 5: 30, 7: 30, 6: 120, 8: 120}
for d in range(1, 9):
    obytes = Z.read(f'Check/KAcd{d}.csv'); O = list(csv.reader(io.StringIO(obytes.decode('latin-1'), newline='')))
    ubytes = open(os.path.join(U, f'KAcd{d}.csv'), 'rb').read(); N = list(csv.reader(io.StringIO(ubytes.decode('latin-1'), newline='')))
    H = O[0]; check(N[0][:len(H)] == H, f'd{d} header'); check(all(len(r) == len(H) + NEW for r in N), f'd{d} width')
    check(obytes.count(b'\r\n') == len(O) and b'\xef\xbb\xbf' not in ubytes[:3], f'd{d} line endings/BOM')
    col = {n: i for i, n in reversed(list(enumerate(H)))}; st = len(H)
    seg = col.get('Segment of test'); olds = {(r[col['Test']], r[seg] if d == 6 else ''): r for r in O[1:]}
    news = {(r[col['Test']], r[seg] if d == 6 else ''): r for r in N[1:]}
    check(len(news) == len(N) - 1 and len(olds) == len(O) - 1, f'd{d} duplicate keys')
    check(set(olds) <= set(news), f'd{d} lost rows'); added = set(news) - set(olds)
    check((d == 6 and len(added) == 3 and all(k[0] == '4' for k in added)) or (d != 6 and not added), f'd{d} unexpected added rows {added}')
    for k, r in news.items():
        o = olds.get(k); tag = r[st]; c = CK.get(key(d, k[0], k[1] if d == 6 else '')); tot += 1
        check(tag in ('replaced', 'relabeled', 'keep_anymaze', 'no_video', 'excluded', 'flag_not_confirmed', 'tracked_unchanged', 'not_tracked'), f'd{d} {k} tag {tag}')
        if tag == 'excluded':
            check((d, k[0]) in ((5, '53'), (4, '97')), f'd{d} {k} unexpected exclusion'); check(c is not None and o[col['Duration (s)']] == c['old_duration_s'] and o[col['Distance (cm)']] == c['old_distance_cm'], f'd{d} {k} exclusion log'); used.add(key(d, k[0], ''))
            for i, n in enumerate(H): check(r[i] == (o[i] if n in IDS else ''), f'd{d} {k} exclusion column {n}')
            check(r[st + 1] == '' and r[st + 2] == '', f'd{d} {k} exclusion tracker values'); continue
        if tag == 'relabeled':
            want = {'14': '13', '15': '14', '16': '15', '13': '16'}.get(o[col['Animal']]); block = 73 + ((int(k[0]) - 73) // 4) * 4
            check(d == 4 and 73 <= int(k[0]) <= 88 and r[col['Animal']] == want, f'd{d} {k} relabel'); check(all(r[i] == o[i] for i in range(st) if i != col['Animal']), f'd{d} {k} relabel changed other columns')
            lg = CK.get(key(d, str(block), '')); check(lg is not None and lg['old_animal'] == o[col['Animal']] and lg['new_animal'] == want, f'd{d} {k} relabel log'); used.add(key(d, block, '')); continue
        if tag != 'replaced':
            check(o is not None and r[:st] == o, f'd{d} {k} altered without being marked replaced'); check(c is None, f'd{d} {k} in change log but not marked replaced'); continue
        check(c is not None, f'd{d} {k} replaced but missing from change log')
        if c is None: continue
        used.add(key(d, k[0], k[1] if d == 6 else ''))
        dur, dist = float(r[col['Duration (s)']]), float(r[col['Distance (cm)']]); check(r[col['Duration (s)']] == c['new_duration_s'] and r[col['Distance (cm)']] == c['new_distance_cm'], f'd{d} {k} log new value')
        if o is not None:
            check(o[col['Duration (s)']] == c['old_duration_s'] and o[col['Distance (cm)']] == c['old_distance_cm'], f'd{d} {k} log old value')
            for i, n in enumerate(H):
                if n in IDS: check(r[i] == o[i], f'd{d} {k} metadata {n} changed')
                elif n in ('Duration (s)', 'Distance (cm)', 'Mean speed (cm/s)', 'P2: SE : time (s)'): pass
                else: check(r[i] == '', f'd{d} {k} stale value in {n}')
        check(abs(float(r[col['Mean speed (cm/s)']]) - dist / dur) < .01, f'd{d} {k} speed arithmetic')
        check(dist / dur <= 40, f'd{d} {k} implausible speed {dist / dur:.1f}'); check(0 < dur <= (30 if d == 6 else cap[d]), f'd{d} {k} duration {dur}')
        if d in (6, 8): check(float(r[col['P2: SE : time (s)']]) <= dur + .05, f'd{d} {k} P2 over duration')
    print(f'd{d}: original rows={len(O) - 1} updated rows={len(N) - 1} replaced={sum(r[st] == "replaced" for r in N[1:])} keep={sum(r[st] == "keep_anymaze" for r in N[1:])} no_video={sum(r[st] == "no_video" for r in N[1:])} excluded={sum(r[st] == "excluded" for r in N[1:])} flag_not_confirmed={sum(r[st] == "flag_not_confirmed" for r in N[1:])} tracked_unchanged={sum(r[st] == "tracked_unchanged" for r in N[1:])} not_tracked={sum(r[st] == "not_tracked" for r in N[1:])}')
check(used == set(CK), f'log entries with no row: {set(CK) - used}')
# d6 segments must sum to the separately published 120 s totals.
for r in csv.DictReader(open(os.path.join(P, 'd6_tracker_vs_anymaze.csv'), newline='')):
    if r['test'] in ('3', '4', '18', '22'):
        S = [c for c in CH if c['day'] == '6' and c['test'] == r['test']]
        check(abs(sum(float(c['new_distance_cm']) for c in S) - float(r['tracker_full120_dist'])) < 1, f"d6 t{r['test']} distance sum {sum(float(c['new_distance_cm']) for c in S)} vs {r['tracker_full120_dist']}")
        check(abs(sum(float(c['new_p2_s']) for c in S) - float(r['tracker_full120_p2_s'])) < 1.5, f"d6 t{r['test']} P2 sum {sum(float(c['new_p2_s']) for c in S)} vs {r['tracker_full120_p2_s']}")
# Byte check for one way of writing: re-serialising the original must reproduce the original exactly.
for d in range(1, 9):
    b = Z.read(f'Check/KAcd{d}.csv'); s = io.StringIO(newline=''); csv.writer(s, lineterminator='\r\n').writerows(csv.reader(io.StringIO(b.decode('latin-1'), newline='')))
    check(s.getvalue().encode('latin-1') == b, f'd{d} csv round trip is not byte-identical')
A4 = {r[0]: r[1] for r in list(csv.reader(open(os.path.join(U, 'KAcd4.csv'), encoding='latin-1', newline='')))[1:]}
check([A4[str(x)] for x in (69, 73, 77, 81, 85, 89)] == ['12', '13', '14', '15', '16', '25'], 'd4 final rat order')
print('rows checked', tot, 'change-log rows', len(CH), 'trials', len({(c['day'], c['test']) for c in CH}))
print('zip sha256', hashlib.sha256(open(ZIP, 'rb').read()).hexdigest().upper())
print('FAILURES:', len(fails)); [print(' ', f) for f in fails[:30]]
