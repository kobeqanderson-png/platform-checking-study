# Behavior Atlas

Built 8 November 2026 using all 91 existing checking-session caches: KAC Day 6 (29), KAC Day 8 (30), SP1 (32). KAC uses the final v3rot best-320 model on both days; SP1 uses best-190. No acquisition-trial results, new model training, or tail-sweeping analyses were added.

Open `explorer.html` locally or `../dlc_cleaned/site/explorer.html` in the complete website. The study dashboard links to the atlas. The downloadable site archive includes the atlas and its exports.

## Views

- Individual 5-Hz coordinate replay with synchronized speed, on-platform head-turn speed, distances to P1/placement, head orientation relative to P1, and spatial states.
- Equal-animal weighted off-platform density maps. A shared square-root color scale exposes low occupancy without giving long swimmers disproportionate weight.
- Every animal's full-resolution spatial timeline and occupancy allocation.
- Animal-level scatterplots with selectable measures and paired KAC Day 6/Day 8 profiles.
- 146 excursion segments, of which 62 meet the complete-excursion definition. Unknown gaps censor segments; these counts are not interchangeable with departure counts.
- Three scientific figure sets in PNG/SVG, animal and event tables, source-cache hashes, and existing comparison videos.

## Definitions and limitations

Native sampling is used for summaries, maps and event detection. Replay is reduced to 5 Hz; a bin containing an unresolved gap remains unknown. Short accepted interpolation is retained and reported. Speed uses the derivative of cleaned body coordinates, with a 0.3 s running mean for the displayed and median speed. Speed, P1 and wall summaries require at least 1 s off-platform time. Head-turn speed on the platform is inherited from the final cleaned analysis. Head direction is the noseâ€“neck axis, not measured eye gaze.

Placement zone radius: 0.165 pool radii. Wall band: beyond 0.85 radii. Near-P1 region: 20 cm radius. Region priority for exclusive timelines is placement, near P1, wall, other interior, unknown. P1 is assumed by reflection in SP1; KAC uses existing training-derived geometry, contingent on camera correspondence. SP1 physical distances assume a 172 cm pool diameter. These visuals do not validate the learned-location geometry or establish psychological states.

Excursion onset requires at least 1 s off; sustained return requires at least 1 s on. Unknown tracking splits and censors segments. A route label requires at least 0.5 s near P1 or in the wall band. Complete-case selection can omit difficult or interrupted swims. Events are nested in animals. Paired plots join the same KAC rat and omit unavailable measure pairs. Water depth, order and camera are confounded. No new inferential tests are presented.

## Verification

All caches asserted to use expected final models and 120 s windows. Unknown fractions match the existing per-rat results. All 91 spatial occupancy totals sum to 120 s. Replay arrays have 600 bins, preserve unknown intervals and contain no nonfinite JSON values. Swimming-density maps normalize per animal. Event segments never cross unresolved gaps. Existing six gap/censoring excursion tests passed. JavaScript syntax and referenced media were checked. Scientific figure exports were visually inspected.

## Rebuild

Run `python analysis/dlc_explorer/build_explorer.py` from the KAC database workspace. This reads existing caches and leaves tracking and established analysis results unchanged.

## Hosted atlas

https://platform-checking-study-1qu3wcaqf-kobeqanderson-pngs-projects.vercel.app/explorer.html

Private preview deployed and 26 file hashes verified. Browser checks passed for loading, replay time selection, path coloring, cohort/sex filtering, spatial maps, scatter axes, excursion filtering and linked selection. All three figure images loaded. The browser download-event monitor timed out, but the downloaded animal-summary CSV was found and verified to contain 91 unique animal/test records. CSV files are also present in `exports/` and the offline archive.
