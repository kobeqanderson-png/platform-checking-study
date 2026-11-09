"""Repair legacy SP1 labels only, retaining every measurement and its test ID."""
import csv
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = HERE.parent / 'dlc_measures' / 'sp1_checking_dlc_measures.csv'
backup = HERE / 'inputs' / 'sp1_measures_before_id_fix.csv'
if not backup.exists():
    shutil.copy2(source, backup)
with (HERE.parent / 'dlc_measures' / 'sp1_checking_dlc_vs_anymaze.csv').open(newline='') as f:
    mapping = {int(r['Test']): int(r['animal'].removeprefix('rat')) for r in csv.DictReader(f)}
assert set(mapping) == set(range(1, 33)) and set(mapping.values()) == set(range(1, 33))
with source.open(newline='') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    original = list(reader)
updated = []
for row in original:
    row = row.copy()
    rat = mapping[int(row['test'])]
    row.update(rat=str(rat), sex='M' if rat <= 16 else 'F')
    updated.append(row)
with source.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(updated)
assert all(a[k] == b[k] for a, b in zip(original, updated) for k in fields if k not in ('rat', 'sex'))
print('Corrected 32 SP1 identities/sex labels; measurement text and test IDs preserved.')
