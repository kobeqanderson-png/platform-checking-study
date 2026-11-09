# Head sweeping and visits to the old-platform area

8 November 2026. The user clarified that brief presence near the old location counts: no minimum dwell time is required. This replaces the previous 0.5-second visit requirement for this analysis. The separate first-departure direction analysis does not answer this question.

A visit is any valid off-platform body position within the existing 20 cm radius around proposed P1. Existing cleaned tracking and short accepted interpolations are retained. Every successful complete path also contains at least one qualifying position that was not body-interpolated. Presence measures visiting the area; it does not by itself distinguish intentional search from passing through.

For a direct comparison with the previous result, the denominator remains fully observed round trips: departure from placement through return, with no unresolved tracking gap. Each animal contributes one observation: its whole-session head sweeps per valid on-platform minute, compared with its successful-trip count and its successful-trip percentage. Rats with no complete paths have no percentage, rather than a zero. All three tests are analyzed separately. Repeated trips are not treated as independent animals.

| Test | Animals with complete trips | Trips reaching area / complete trips | Previous visits with 0.5 s cutoff | Spearman rho: sweeping vs visit count | Spearman rho: sweeping vs successful-trip percentage |
|---|---:|---:|---:|---:|---:|
| KAC Day 6 | 10 | 10 / 15 | 9 | 0.50 | 0.06 |
| KAC Day 8 | 10 | 16 / 23 | 14 | 0.64 | -0.29 |
| SP1 | 12 | 14 / 24 | 13 | -0.15 | -0.45 |

Day 8 adds M3 trip 2 (0.40 seconds in the region) and F25 trip 5 (0.23 seconds). Day 6 adds F28 trip 3 (0.37 seconds), and SP1 adds F19 segment 7 (0.40 seconds). Numbers refer to existing excursion-segment IDs, which can include incomplete segments.

The positive Day 8 association concerns the number of trips reaching the area. There is no positive rank association with the fraction of trips reaching it in this selected sample. These are descriptive exploratory coefficients, not evidence of causation or a confirmed population effect. Whole-session sweeping does not establish that sweeping preceded each successful trip. Pooled-sex coefficients can reflect sex differences as well as within-sex variation. More trips create more opportunities to visit, and long paths have more opportunities than short ones.

Incomplete segments are retained in the path audit: 13 of 23 Day 6 segments, 21 of 45 Day 8 segments, and 7 of 16 SP1 segments contain observed visits. These are not independent complete trips; multiple segments may belong to one interrupted trip. A segment without an observed visit is not assumed to be a failed trip. The complete-trip summary can therefore be selective and does not cover all swimming.

P1 geometry is unchanged: KAC uses the existing training-derived coordinates conditional on camera correspondence, and SP1 uses the assumed reflected location. A 20 cm neighborhood is an operational area, not the exact platform footprint or a validated boundary of search behavior.

Sources: existing final checking caches (KAC best-320, SP1 best-190), `../dlc_explorer/exports/animal_summary.csv`, and `../dlc_explorer/exports/excursion_segments.csv`. The previous 0.5-second visit label was independently reproduced from the native frame arrays for every segment before applying the revised rule. No original data or dashboard files were modified.

Outputs: `area_entry_day8.png` / `.svg`, `area_entry_paths.csv`, `area_entry_animals.csv`, `area_entry_results.json`. Rebuild with `python analysis/scanning_accuracy/check_area_entry.py`.
