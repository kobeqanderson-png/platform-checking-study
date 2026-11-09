# Handoff: SP1 and KAC water maze checking tasks (DLC tracking + analysis)

Status as of 2026-11-07. Goal: SfN poster (about 3 days). AK1 (Aizad) is a separate study and out of scope.

## Study design
- **SP1 checking:** checking test at a raised water level only, with no standard-depth comparison. 32 rats, 120 s each.
- **KAC checking:** the follow-up that adds the missing control, with the same rats tested twice:
  - Day 6 = 1.5 cm, the **standard** water level (control)
  - Day 8 = 3 cm, the **raised** water level
- SP1 sex (from Documents\2025\data\Rat weights 12-30-24.xlsx, confirmed by the user): rats 1-16 male, 17-32 female, the same numbering as KAC. Which animals died differs from KAC; see the SP1 spreadsheets in Documents\2025.
- Rats are placed on the platform. "SOP" = stayed on platform, "LP" = left platform.
- KAC: rats 1-16 male, 17-32 female. Test order on both cohorts: 1-8, 17, 18, 20-24, 9, 10, 12-16, 25-32. KAC Rat 19 died, rat 11 is absent, and there's no Day 6 footage for rat 1.
- Pool: 172 cm across at the outer rim. For KAC, 485 px = 86 cm.

## Where things are
**Google Drive: `My Drive/DLC output[sp1--kac1.5cm-3.0cm]/`** (the brackets break `glob` and IPython `%run`; use `%run -G "..."`)
| Folder | Contents |
|---|---|
| `Colab_Training_Runs/KAcheck_d6d8_20261107 (1)/` and `KAcheck_d6d8_20261107/` | **KAC model to use** (best-400), split across two copies Drive made after a rename: 30 Day 8 and 12 Day 6 tracking files in `(1)`; the rest of Day 6 goes to the other. The measures script reads both |
| `Colab_Training_Runs/KAcheckd6d8_v2_20261107/` | Retrained model (197 frames, best-240). It came out slightly worse (median error 3.9 vs 2.6 px), so it isn't used. Day 8 only |
| `Colab_Training_Runs/sp1/` | SP1 model outputs: `sp1_tracks` (32), `sp1_videos_final` (32) |
| `d6_clips`, `d8_clips`, `sp1_clips/sp1_check` | Source clips |
| `finish_videos.py` | One script that tracks and draws: `%run -G ".../finish_videos.py" 6` (or `8`, `sp1`). Finished clips are skipped |
| `clip_windows.csv` | Release-to-removal window per KAC clip (used to hide the experimenter's head and hand) |

**This computer: `C:\Users\kobeq\Documents\KAC database\`**
| Path | Contents |
|---|---|
| `analysis\dlc_measures\checking_dlc_measures.py` | Measures for all three tasks, with the method at the top |
| `analysis\dlc_measures\kac_d8_dlc_measures.csv`, `kac_d8_notes_vs_dlc.csv` | KAC Day 8 per rat, plus the check against the handwritten notes |
| `analysis\dlc_measures\sp1_checking_dlc_measures.csv`, `sp1_checking_dlc_vs_anymaze.csv` | SP1 per test, plus the AnyMaze comparison (use its `animal` column for rat numbers) |
| `analysis\` | Lab workbook and figures, built by the analysis session ("KAC cohort water maze results") |
| `colab_scripts\` | All Colab notebooks and scripts |
| `training_packages\` | DLC training packages (also zipped in Drive) |

## Method (DLC measures)
- Window: release to release + 120 s.
- Body = spine middle (head centre if unsure); points under 0.3 confidence are interpolated.
- Platform position = where rats sit in the first 2 s. The zone radius is 0.165 pool radii (80 px on KAC Day 8): stay-on rats never went beyond 74 px, and swimmers went 200-600 px.
- Departure = out of the zone for at least 1 s. Wall time = beyond 0.85 of the rim radius.
- Rearing isn't measured, because it can't be detected from overhead; use the handwritten notes for rearing.
- Videos are drawn at 0.3 confidence, with no tail (tail base is the last tail point kept), and stray points more than ~180 px from the body centre hidden.

## Validation (the poster's credibility)
- **KAC Day 8:** stayed on vs left matches the handwritten notes on **30 of 30 rats**. First departure time is within about 0-7 s of the notes on 12 of 13 rats. Time in an AnyMaze-sized P2 zone matches AnyMaze at **r = 0.998**.
- **SP1:** swim distance matches AnyMaze at **r = 0.994**. AnyMaze's P2 platform time is unreliable: it logs 30+ entries for rats sitting still (e.g. test 14 / rat 22: AnyMaze 22.5 s, but the video shows 120 s on the platform). Use DLC for SP1 platform time and departures.

## Results so far (preliminary)
- KAC Day 8: females left the platform 3.9 times on average, males 0.2. Wall time: females 3.6%, males 0%.
- SP1 checking (DLC): males 98% vs females 74% time on platform (p < 0.001); 16/16 males vs 5/16 females stayed on (Fisher p < 0.001); departures 0.3 vs 1.9 (p = 0.001); no difference in wall time.
- KAC Day 6 vs Day 8, % time on platform, paired: all rats p = 0.109; females 68% vs 60% (p = 0.093); males 97% vs 97%. So the sex difference is already present at standard depth, and raising the water didn't significantly add to it. This used pre-DLC Day 6 data, so **redo it with DLC Day 6**.

## To do
1. When the two first-model folders together hold 29 Day 6 tracking files, run `checking_dlc_measures.py` again. It writes `kac_d6_dlc_measures.csv` and `kac_d6_notes_vs_dlc.csv`, with the Day 6 handwritten notes already typed into the script. Then redo the paired Day 6 vs Day 8 test.
2. ~~SP1 exclusions~~ Done: Documents\2025\data\SP1.xlsx shows all 32 SP1 rats on every day with no exclusions, so n = 16 per sex. SP1 is final.
3. Build the poster figures around: SP1 (raised water) → KAC control (standard vs raised, same rats) → validation (DLC vs notes and AnyMaze).
4. Later, not for the poster: training days, more labeling and retraining (the 64 new Day 6/8 frames are labeled on the site but didn't improve the model), and head direction (computed, not validated).

## Labeling site
https://mobile-dlc-labeler.pages.dev — Day 6 and Day 8 worklists have 13 points (no tail), with model suggestions (hollow rings; "Accept" saves them; "Next: model's worst frame"). The app code lives in `Documents\MobileDLC` and is separate from the experiment files.

## UPDATE 2026-11-08: final model and results
- **Final KAC model: `Colab_Training_Runs/KAcheck_d6d8_v3rot_20261108`** (all 197 labels, rotation augmentation, best-320). Both days are complete: 29 Day 6 + 30 Day 8 tracks. It's used for both days, so they're compared like for like.
- Measures rebuilt from it (`checking_dlc_measures.py`): `kac_d6_*`, `kac_d8_*`, `sp1_checking_*` in `analysis\dlc_measures`.
- Validation against the handwritten notes (stayed on vs left): **Day 6 20/20, Day 8 30/30**.
- SP1 is final (n = 16 per sex, no exclusions).
- The older model folders (first model, v2, v3) are superseded. The analysis session has a list of what's safe to delete; ask before deleting anything on Drive.
- Remaining: the analysis session rebuilds the workbook and the Day 6 vs Day 8 paired test from these files.