"""Checks SP1 checking DLC measures against the AnyMaze export (sp1check.csv: 4 x 30 s segments per test)."""
import re
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
a = pd.read_csv(r"C:\Users\kobeq\Downloads\sp1check.csv", encoding="latin-1")
a.columns = [c.strip() for c in a.columns]
zones = sorted({c.split(" : ")[0] for c in a.columns if c.endswith(" : time (s)")})
print("AnyMaze zones:", zones)
sex_col = next((c for c in a.columns if c.lower() in ("sex", "sex field", "gender")), None)
g = a.groupby("Test")
per = pd.DataFrame({"animal": g["Animal"].first(), "segments": g.size(), "anymaze_duration_s": g["Duration (s)"].sum(),
                    "anymaze_tracked_pct": g["Tracked (%)"].mean().round(1), "anymaze_distance_cm": g["Distance (cm)"].sum().round(1)})
if sex_col:
    per["sex"] = g[sex_col].first()
for z in zones:
    per[f"{z} time_s"] = g[f"{z} : time (s)"].sum().round(1)
    if f"{z} : entries" in a.columns:
        per[f"{z} entries"] = g[f"{z} : entries"].sum()
d = pd.read_csv(HERE / "sp1_checking_dlc_measures.csv").set_index("test")
m = per.join(d[["pct_time_on_platform_zone", "departures", "first_departure_s", "pct_time_at_wall", "swim_path_off_platform_cm"]], how="inner")
print(f"\nmatched tests: {len(m)} | AnyMaze duration per test: {per.anymaze_duration_s.min()}-{per.anymaze_duration_s.max()} s | animal names e.g. {list(per.animal[:3])}")
print("test = rat number?", all(re.sub(r"\D", "", str(an)) == str(t) for t, an in per.animal.items()))
print("\nDLC % time on platform vs each AnyMaze zone's time (Pearson r):")
for z in zones:
    r = np.corrcoef(m["pct_time_on_platform_zone"], m[f"{z} time_s"])[0, 1] if m[f"{z} time_s"].std() else float("nan")
    print(f"  {z:22s} r = {r:.3f}   mean {m[f'{z} time_s'].mean():.1f} s")
r = np.corrcoef(m["swim_path_off_platform_cm"], m["anymaze_distance_cm"])[0, 1]
print(f"DLC swim path off platform vs AnyMaze total distance: r = {r:.3f}")
m.to_csv(HERE / "sp1_checking_dlc_vs_anymaze.csv")
print("\nsaved sp1_checking_dlc_vs_anymaze.csv; sex column:", sex_col)
