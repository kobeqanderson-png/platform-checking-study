"""Adds d7 start times to the start-time table, from the header of each AnyMaze .szv file: FILETIME at byte 8, frame count at byte 20.
Usage: read_szv_starts.py <szv folder> <starts.csv> <day>"""
import csv, datetime as dt, glob, os, re, struct, sys
X, OUT, DAY = sys.argv[1:]
R = []
for f in glob.glob(os.path.join(X, '*.szv')):
    t = int(re.search(r'Test (\d+)', os.path.basename(f)).group(1)); h = open(f, 'rb').read(32)
    R.append((t, dt.datetime(1601, 1, 1) + dt.timedelta(microseconds=struct.unpack('<Q', h[8:16])[0] // 10), struct.unpack('<I', h[20:24])[0]))
R.sort(); print('tests', len(R), R[0][1], 'to', R[-1][1], 'chronological by test number', all(a[1] <= b[1] for a, b in zip(R, R[1:])), 'out of order', [a[0] for a, b in zip(R, R[1:]) if a[1] > b[1]])
K = list(csv.DictReader(open(OUT, newline=''))); K = [r for r in K if r['day'] != DAY] + [dict(day=DAY, index=t, start=s.isoformat(sep=' ', timespec='milliseconds')) for t, s, _ in R]
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['day', 'index', 'start']); w.writeheader(); w.writerows(K)
print('frames/10 vs nothing: first', [(t, n / 10) for t, _, n in R[:4]])
