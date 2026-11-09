# Behavioral organization: first excursion analysis

8 November 2026. Descriptive analysis of all 91 cleaned checking sessions. The primary objective is the organization of behavior: initiation, destination, recurrence, and return. Sex comparisons provide context rather than define the behavioral categories.

## Completed tracking inventory

Directly checked the Drive `Colab_Training_Runs` tree: SP1 best-190 has 32 checking tracks; KAC best-240 has 29 Day 6 and 30 Day 8 tracks. These cover the available checking clips. Best-400 remains at 12 Day 6 and 30 Day 8 tracks. No completed training-day DLC set was identified in this tree; this is not a claim about unsearched locations. Evaluation files and demo outputs were excluded from trial counts. The full inventory is in `../dlc_inventory.json`.

## What was measured

A sequence timeline separates placement-zone occupancy, opposite-quadrant interior, opposite-quadrant wall, other interior, other wall, and unknown tracking. The quadrant is camera-aligned and opposite the placement platform across the pool center. It is a broad destination proxy, **not the exact former learned-platform region**.

An excursion starts with at least one second of observed off-zone tracking and ends at the start of at least one second back inside the placement zone. Short touches do not end an excursion. A complete excursion has an observed departure and sustained return within one uninterrupted valid tracking segment. Gaps and trial boundaries censor events. Fragments are retained as segments and must not be counted as additional departures. Retained short interpolations from the cleaning stage are included; “fully observed” means no unresolved missing frames, not independently verified coordinates at every frame.

An excursion reaches a destination after at least 0.5 seconds there. The wall band starts at 0.85 pool radii. These are operational definitions requiring further behavioral validation.

## Findings

| Test / sex | Animals with complete excursions / available | Complete excursions | Reached opposite quadrant | Reached wall band |
| --- | --- | --- | --- | --- |
| SP1 females | 10/16 | 22 | 17 | 1 |
| SP1 males | 2/16 | 2 | 2 | 0 |
| KAC Day 6 females | 3/15 | 5 | 4 | 1 |
| KAC Day 6 males | 3/14 | 3 | 2 | 0 |
| KAC Day 8 females | 2/15 | 2 | 0 | 0 |
| KAC Day 8 males | 1/15 | 2 | 2 | 0 |

These are pooled descriptive event counts, not independent samples for a sex test. Excursions are nested in animals. Complete-excursion filtering selects against difficult, long, interrupted, and unreturned swims, particularly in KAC. The Day 8 female zeros cannot be interpreted as an absence of opposite-quadrant travel: the timeline visibly contains such travel in incomplete sequences.

**Destination and initiation can now be separated.** Both rare complete male SP1 excursions reached the opposite quadrant, as did 17 of 22 female excursions. This motivates testing destination conditional on movement opportunity. It does not establish a sex difference in destination, spatial preference relative to chance, or precise learned-place checking.

**Organization varies within animals.** F24 contributes short local excursions at 32.0–34.5, 72.5–74.8, and 86.3–88.3 seconds, and a larger loop at 97.1–113.7 seconds. F18 contributes one long complete excursion at 13.9–95.5 seconds with multiple passes through the pool. F17 makes two shorter opposite-quadrant loops. These illustrate local movements, extended swimming, and repeated excursions without assuming discrete animal types.

**Completed tracking does not mean complete usable trajectories.** KAC tracking gaps sharply reduce uninterrupted excursions. A route-level conclusion based only on the small complete subset would be misleading. Interrupted and end-of-trial sequences remain in the timeline and event table.

## Checks

- Six excursion tests passed, covering complete events, missing-data splits, brief platform touches, non-initiation, and both forms of censoring.
- Every event span was checked against its cache; complete returns contain the required sustained on-zone interval, and no event crosses an unresolved tracking gap.
- Minimum off/return duration of 0.5, 1, and 2 seconds produced 24/24/24 complete SP1 excursions; KAC Day 6 produced 9/8/7 and Day 8 6/4/2. Counts alone do not establish stable individual boundaries or destinations.
- The sequence plot and all 24 SP1 complete-excursion paths were visually reviewed.
- Fifteen source-video frames covering departure, swimming, and return for F17, F24, and M4 were checked. They support the illustrated events; this is a spot check, not independent exhaustive event annotation.

## Next work

Recover the actual former-platform coordinates from training footage or verified zone records for each camera arrangement, then overlay them on checking videos. Do not infer the old platform center by reflecting the placement center. Extract first entry, distinct reentries, intervening travel, and return intervals for that region. Compare excursions within the same animal before imposing categories across animals.

For interrupted KAC excursions, preserve partial destinations and uncertainty rather than filling long paths or using complete cases as representative. Prioritize targeted tracking recovery or manual event annotation where gaps obscure the learned-location visit. SP1 currently supplies the cleanest first dataset for refining these definitions.

## Outputs

- `sequences.png` and `sequences.svg`: all 91 session timelines.
- `sp1_excursion_atlas.png`: all 24 complete SP1 excursion paths.
- `excursions.csv`: event segments, censoring, durations, destinations, and their order.
- `animals.csv`: one row per animal/session with exposure and complete-event summaries.
- `state_bouts.csv`: exact temporal state runs.
- `threshold_sensitivity.csv`, `method.json`: settings and sensitivity results.
- `source_event_checks.jpg` and `.csv`: the video spot checks and event identities.

PV/WFA remains the anatomical Plan A; GFAP remains Plan B if unavailable. Neither anatomical analysis has been performed. This pass advances the behavioral measurement needed for either plan.
