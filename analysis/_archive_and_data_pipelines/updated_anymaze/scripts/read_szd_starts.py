"""Extracts test start times from copies of AnyMaze .szd files. The source files are only copied, never opened for writing.
Test records hold a Windows FILETIME followed by a fixed marker value 52 bytes later, and may be spread across the file.
Usage: read_szd_starts.py <KAC database folder> <work folder> <out.csv>"""
import csv, datetime as dt, os, shutil, struct, sys
import numpy as np
D, W, OUT = sys.argv[1:]
FILES = {1: 'kacd1.szd', 2: 'kacd2.szd', 3: 'kacd3 - created from backup.szd', 4: 'kacd4.szd', 6: 'check d6.szd', 8: 'checkd8.szd'}
ft = lambda y, m, d: int((dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp() + 11644473600) * 10 ** 7)
LO, HI = ft(2026, 10, 25), ft(2026, 11, 10); MARK = 926297655; rows = []
os.makedirs(W, exist_ok=True)
for day, name in FILES.items():
    c = os.path.join(W, f'd{day}.szd'); shutil.copy2(os.path.join(D, name), c); b = open(c, 'rb').read(); hits = {}
    for sh in range(8):
        q = np.frombuffer(b[sh:sh + (len(b) - sh) // 8 * 8], '<u8')
        for i in np.where((q >= LO) & (q < HI))[0]: hits[int(i) * 8 + sh] = int(q[i])
    # Test which offset from the timestamp holds the marker, and keep only true test records.
    marked = sorted(o for o in hits if o + 56 <= len(b) and struct.unpack('<I', b[o + 52:o + 56])[0] == MARK)
    T = sorted({hits[o] for o in marked}); print(f'd{day} {name}: timestamps {len(hits)}, marked {len(marked)}, unique {len(T)}', end=' ')
    S = [dt.datetime(1601, 1, 1) + dt.timedelta(microseconds=x // 10) for x in T]
    if S: print(f'{S[0]} to {S[-1]}')
    for i, x in enumerate(S, 1): rows.append(dict(day=day, index=i, start=x.isoformat(sep=' ', timespec='milliseconds')))
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
