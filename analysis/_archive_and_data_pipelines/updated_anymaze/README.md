# Updated AnyMaze files

`KAcd1.csv` to `KAcd8.csv` are the water maze AnyMaze exports with corrections checked against overhead video.
The originals are unchanged in `original/Check (1).zip`. The analysis and its report are in `analysis/` (start with `analysis/REPORT.md`).

## Folder map

| Path | What it is |
|---|---|
| `KAcd1.csv` ... `KAcd8.csv` | Corrected data, one file per day, same columns as AnyMaze plus 6 `Retrack` columns |
| `changes.csv` | Every changed value: old, new, reason |
| `review_list.csv` | Verdict and reason for every flagged trial that was not replaced |
| `original/` | The untouched AnyMaze export |
| `analysis/` | `analysis.py`, `REPORT.md`, `results/`, `figures/` (full analysis) |
| `analysis/lab_version/` | `water_maze_results.xlsx` and slide-ready bar graphs for lab meetings. Checking tests first (SP1, then KAC Day 6 control vs Day 8 raised water, from DeepLabCut video tracking), training days after (corrected AnyMaze). Plain t-tests, paired t-tests, two-way ANOVA, Fisher's exact test |
| `scripts/` | Tools that build and check the corrected files (see Rebuilding) |
| `../tracking_pilot/` | Camera tracks, trial matching and clock tables used by the scripts |
| `../dlc_measures/` | DeepLabCut checking-test measures made by `checking_dlc_measures.py`: KAC Day 6 and Day 8 from the final model (KAcheck_d6d8_v3rot_20261108; rat 1 has no Day 6 clip) with handwritten-note checks, and SP1 with its AnyMaze cross-check |

## What changed

40 trials have new values, d5 test 53 is blanked, and d4 tests 73-88 have corrected rat IDs.

| Day | Trials replaced |
|---|---|
| d1 | 22, 92 |
| d2 | 112 |
| d3 | 25, 39, 49, 51, 59, 74, 78, 97 (49 and 97 distance only) |
| d4 | 2, 12, 18, 23, 25, 41, 62, 72, 97, 98, 99, 120 |
| d5 | 55, 112, 118 (118 distance only) |
| d6 | 3, 4, 18, 22 |
| d7 | 1, 20, 21, 23, 30, 98, 100 (21 distance only) |
| d8 | 4, 9, 25 |

- On a replaced row, Duration, Distance and Mean speed are updated, plus P2 time on d6 and d8. Other measurements on that row (zone times, max speed) are blank because they came from the bad AnyMaze path. Metadata and `Reason ended` keep their original values.
- d6 test 4 stopped inside its first 30 s segment, so three segment rows were added: d6 has 120 rows instead of 117.
- Blank cells mean missing, never zero.

## How errors were found

- **AnyMaze stops on first platform entry.** Its stored `Pfound` procedure stops a test on the first zone entry, with no stay requirement, while the lab rule is touch and stay. Rats that crossed the platform and swam on were set to the 30 s cap with the path measured to 30 s. This also explains d8 test 9 stopping at 75.5 s and probably d6 test 4 at 4.6 s.
- **AnyMaze's clock sometimes started late or early.** Test start times were read from the `.szd` databases (d1-d4, d6, d8) and the `.szv` file headers (d7), and d4 save times from its `.szv` files. Matched to the video by clock, AnyMaze's end lines up with the rat settling to within about 0.3 s, which exposed wrong durations and re-matched runs on d1-d4 and d7.
- **Tracking loss.** Low tracking, speed jumps and impossible speeds (for example 1681 cm in 17.7 s) were replaced from the camera when the video showed the swim.
- Every replacement was checked on video frames. Most flagged trials were not replaced, because the camera tracker can mark a pass as an arrival and its distance scale is calibrated from AnyMaze.

## New columns on every row

| Column | Meaning |
|---|---|
| Retrack status | `replaced`, `relabeled`, `keep_anymaze`, `no_video`, `excluded`, `flag_not_confirmed`, `tracked_unchanged` or `not_tracked` |
| Retrack time (s) | Raw camera reading (settle time where matched by clock), before any day offset |
| Retrack distance (cm) | Camera distance. Blank on capped trials and on runs that do not match the trial |
| Retrack P2 time (s) | d6 and d8 only |
| Retrack match confidence | How the run was matched: `clock_match`, `save_timestamp`, `one_clip_per_test`, or the d5 block-match rating |
| Retrack note | Why the row has its status |

## Rat IDs, checked against the lab notes

- Rats 11 and 19 died and are not in the data. Rat 11 died before d1, but AnyMaze's list kept a slot for it, so several video file names are one number off.
- **d4, corrected:** the notes say rats 13-15 were logged as 14-16 and rat 16 as 13. The file's test order (14, 15, 16, 13) and the save times match, so tests 73-88 are relabeled.
- **Kept as AnyMaze's Animal column:** d1 tests 73-120 (15 blocks for 15 rats in note order), tests 69-72 on d1 and d2 and 68-71 on d3 and d6 test 18 (rat 12; files say 11), d7 tests 2-4 and d6 test 19 (files follow slot or test numbers).
- Groups 1 and 2 were only testing batches of 15 (batch 2 = rats 9-16 and 25-32).

## Limits

- **d5 has no start times** (no `.szd`, no `.szv` on this computer), so it keeps the less certain block matching. Filmed d5 trials were still checked on video. Missing d5 footage: before 10:04 (probably rats 1-8), 10:22-10:27 and 10:33-10:45.
- Unfilmed trials keep AnyMaze's values and its first-entry rule: d1 61-65, d2 61-75, d7 rats 21-23 and others listed in `review_list.csv`. Flagged trials with no footage: d1 t104, d5 t21, d5 t29. d4 t10 merges with test 9 on video.
- Replaced times on d5 and d7 subtract the day's camera offset (+1.30 s and +1.75 s). Raw readings are in `changes.csv`.
- Camera distance over-reads rats sitting still by tens of cm, so replaced stayer distances on d6 and d8 are upper estimates.
- AnyMaze's scale is stable across days (its zone distances agree within 1-2%), so distances compare across days without rescaling. With a 172 cm outer rim, AnyMaze reads roughly 5% low in absolute cm; values are not rescaled.
- d4 came from a different camera (1280x720) and was fitted separately.
- d5 test 53 is blank: AnyMaze ended while the rat swam, and the recording stops 12.6 s into the trial.

## From the lab notes, for analysis

- **d4 rat 10 (tests 65-68) dived under water and had a nose bleed.** The trial is unknown, so all 4 rows are marked.
- d3 rats 18 and 28 each missed one trial.
- d3 rat 22 had start order W, S, E, N instead of W, E, S, N. d3 rat 25's E start was messed up (times still agree).
- d8 rat 32: heat pad off at 90 s.
- HVS data exists but is inconsistent, so only camera recordings were used.
- Notes disagree with AnyMaze on d2 rat 22 (all timed out vs 15 s and 20 s) and d1 rat 27 (could not find vs 17 s and 12 s). The tracks support AnyMaze, so values are kept.

## Source files

- AnyMaze databases and d3, d5, d6 videos: `Documents\KAC database` (videos renamed `kacd3`, `kacd5.1` and so on).
- d1, d2 videos: `OneDrive\Pictures\Camera Roll`. d7, d8 videos: `Videos`. d4 video: `Downloads\2026-11-01 09-18-44.mp4`.
- d7 `.szv` files: `Downloads\OneDrive_2026-11-07.zip`. d4 `.szv` save times: `../tracking_pilot/d4_szv_times.csv`.

## Rebuilding

Run from this folder with Python 3 (pandas, numpy, scipy, statsmodels, matplotlib, opencv). `WORK` is any empty folder.

```bash
python -I scripts/read_szd_starts.py "C:/Users/kobeq/Documents/KAC database" WORK ../tracking_pilot/szd_test_starts.csv
python -I scripts/read_szv_starts.py WORK/d7_szv ../tracking_pilot/szd_test_starts.csv 7
python -I scripts/clock_match_days.py ../tracking_pilot WORK/anymaze_raw/Check ../anymaze_trial_audit.csv ../tracking_pilot/run_logs WORK 1,2,3,7
python -I scripts/build_updated_anymaze.py "original/Check (1).zip" ../anymaze_trial_audit.csv ../tracking_pilot . WORK
python -I scripts/verify_updated_anymaze.py "original/Check (1).zip" . ../tracking_pilot
python -I analysis/analysis.py . "original/Check (1).zip"
python -I analysis/lab_version/lab_version.py analysis/results ../dlc_measures
```

The second line needs the d7 `.szv` files unzipped into `WORK/d7_szv`. The third needs `original/Check (1).zip` unzipped into `WORK/anymaze_raw`. `scripts/d4_clock_check.py` rebuilds `../tracking_pilot/d4_clock_check.csv`. `scripts/find_platform_pass_stops.py` is kept as a record only; its results are written into the build script.
