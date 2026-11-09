# Individual neurobehavioral profiles

Verified protected dashboard: https://platform-checking-study-q8svng7mw-kobeqanderson-pngs-projects.vercel.app/profiles.html

Final deployment `dpl_9F634pepfQGeagmVbH3Eds6wP4Jb`: 35 file hashes matched. Browser checks passed for individual comparison, condition/sex filters, paired values, trajectory links, returns/repetition, and a 390 px responsive layout. The saved browser CSV matched all 91 source sessions and 37 columns. No browser console errors were observed. Responsive emulation is not a physical-phone test.

Built 8 November 2026 from final KAC best-320 and SP1 best-190 checking outputs, corrected KAC AnyMaze acquisition summaries, and the user's no-dwell area-entry definition. The behavioral profile is measured; matched neural data are pending.

91 sessions represent 62 animals (30 KAC, 32 SP1). There are 29 KAC Day 6/Day 8 pairs. Rat IDs are qualified by cohort, so KAC rat 17 is not SP1 rat 17. KAC rat 1 has no Day 6 checking cache. No missing destination or swimming values are filled with zeros.

The dashboard contains a raw-value profile matrix, individual comparisons, acquisition history, paired checking changes, descriptive correlation exploration, and a returns/repetition timeline. Relative positions use average tied ranks within the selected test or test/sex reference. These are display positions, not an overall phenotype score. Features are correlated and are not asserted to be independent biological dimensions.

The repetition view distinguishes observed placement returns from complete round trips and repeated P1-reaching trips. P1 visits require any valid off-platform sample within the existing 20 cm proposed P1 area, with no dwell threshold. Later P1 trips count complete P1-reaching trips after the first, not all reentries within a swim. Complete-trip selection produces lower-bound counts and can omit difficult/long swims. Observed placement returns can include segments with unknown departures. First P1 entry times for each segment are recomputed from native frame arrays. The timing table retains incomplete segments rather than counting their absence of an observed visit as failure.

OCD-related interpretation: return frequency, timing and spatial organization motivate the analysis. Compulsion is not inferred from repetition alone. The experimental criteria in [Szechtman et al. (2001)](https://link.springer.com/article/10.1186/1471-2202-2-4) provide measurement context, not validation of this different water-maze paradigm. No neural mechanisms, clinical symptoms or automatic behavioral types are assigned.

Acquisition fields use daily mean capped escape latency: Day 5, Day 1 minus Day 5, and Day 7 minus Day 5. The reminder measure occurs after Day 6 checking. Full daily latency/distance/trial counts are shown. SP1 acquisition is available elsewhere but has not been linked here. These data are existing AnyMaze summaries, not a completed training-DLC pilot.

P1 coordinates remain provisional. KAC camera correspondence and SP1 reflected P1 require validation. Current metric values retain the existing 172 cm scale; the portal's requested 172.5 cm calibration is logged separately. Short accepted body interpolation remains disclosed in the research dashboard. Tail measures are excluded.

Rebuild: `python analysis/individual_profiles/wire_dashboard.py`, then `python analysis/individual_profiles/build_profiles.py`. The area-entry path audit is produced by `analysis/scanning_accuracy/check_area_entry.py`; the atlas by `analysis/dlc_explorer/build_explorer.py`. Outputs include source hashes, flat animal data, event timing data, descriptive correlation tables, PNG/SVG matrix figures, local HTML and static-site copies. Source workbooks and tracking caches are never overwritten.

Verification: unique animal/session keys and training joins; final model identities; 62 biological IDs and 29 paired KAC animals; complete-trip counts matched to source event tables; 40 complete trips reaching P1 across the three tests; undefined destination percentages retained for nonparticipants; native-frame P1 visits matched to the event audit. JavaScript syntax was checked. Deployment/browser verification is recorded separately.
