# Return — protected research portal

Approved treatment: `../portal_planning/CREATIVE_TREATMENT.md`. Source files are in `site/`; this is a buildless HTML/CSS/JavaScript application with no runtime dependencies, analytics, third-party fonts or external code. Existing dashboard pages remain available.

## Reproduce

From the KAC database directory, run `python analysis/portal/build_portal_data.py`, then `node analysis/portal/verify_portal.js`. The Python environment needs NumPy, pandas, openpyxl, matplotlib and PyTables for the independent SP1 HDF check. The AK1 workbook is read from the explicitly recorded Downloads path. The extraction script does not modify source recordings or workbooks.

`package_portal.py` copies these notes and the decisions log into the site, adds a portal link to a hash-verified copy of the previously published dashboard index, writes the deployment manifest, and creates a source ZIP. It preserves the newer local dashboard index/art/motion lab. Deploy by uploading the new files and reusing existing hashes in the manifest on the existing protected project; do not alter protection or promote to a public domain.

## Data and provenance

- 91 checking sessions / 62 animals: KAC Day 6 (29), KAC Day 8 (30), SP1 (32). KAC rat 11 and 19 excluded; Day 6 rat 1 cache unavailable. Native rates: KAC 30 Hz, SP1 10 Hz; 120 seconds from existing markers for all sessions.
- Model: KAC best-320, SP1 best-190. Sex: rats 1–16 male, 17–32 female, matching the verified roster. A shared rat number across cohorts is not the same animal.
- The manifest hashes each exported file and source. Per-session metadata records original HDF path/hash, cache path/hash, start marker, zero-based original frame offset, model and binary export hash. Original HDF hashes are inherited from the existing analysis unless explicitly marked rechecked.
- KAC original HDF files were unavailable at recorded Drive paths during this build. No claim is made that all original files were independently re-read. The local caches are the immediate source. SP1 F25 unsmoothed coordinates were independently rederived from its HDF and source hash verified.
- Binary files contain `frames × 4` little-endian float64 coordinates in row order: raw selected body x/y, processed body x/y, followed by `frames` uint8 flags. Flags: bit 0 processed valid, bit 1 interpolated, bit 2 original rejected, bit 3 off placement. NaNs remain NaNs. Full precision, native frames, no added interpolation or downsampling.
- Unsmoothed positions are confidence-gated spine-mid, with head-center fallback if likelihood <0.3. They are not raw video pixels or every original pose keypoint. Processing retains original pipeline smoothing and short fills of at most 0.5 seconds. See `../dlc_cleaned/tracking_qc.py` for exact code and manifest hash.
- Drawing connects adjacent eligible native samples only. Processed interpolation segments are gold dashed lines; unknown samples break trails. Rejected original points can be shown separately. Canvas clips the rendered trail at the pool boundary; all coordinates, including rejected outside-pool points, remain in the CSV.

## Definitions and limitations

The placement site is distinct from the former training goal. Former-goal coordinates remain provisional: assumed camera correspondence in KAC and a reflected location in SP1. The analysis uses 172 cm pool diameter while the brief states 172.5 cm. No metric rescaling or exact 3D geometry is silently introduced.

Complete round trips and placement returns are inherited from the gap-aware existing event analysis. Complete trips require known departure and sustained return with no unresolved gap, including the original short-fill handling. Later goal-reaching trips = max(complete goal-reaching trips − 1, 0), a lower-bound measure. The fixed trip metrics use a 20 cm old-goal neighborhood, any eligible sample, no dwell.

The definition explorer changes **software area entries and bouts**, not the fixed complete-trip event labels. It uses processed coordinates, valid off-placement frames, the selected radius, and a minimum consecutive-frame dwell rounded upward to the next frame. A qualifying bout counts as an observed entry only if its immediately preceding sample is eligible and outside the area. Otherwise its onset is unknown/unobserved. Gap boundaries and excluded filled samples cannot create known entries. Time in qualifying bouts includes all frames of qualifying bouts; short nonqualifying bouts are excluded. Displayed totals always span the full 120 s, independent of the replay cursor. Unsmoothed display mode does not change these counting coordinates.

AK1 is a separate 30-animal paired comparison with three representations each, not 90 independent animals. Workbook sheet `49-Prb4`, column `PASSTH01`; source row shown for every value. Means: 1.8, 3.633333, 5.233333. All selected LATENTsc values are 120 s and path-distance values agree across configurations. Source endpoint identity needs confirmation against the experimental record; raw coordinates and actual center geometries are unavailable. No AK1 path animation or continuous size slider is fabricated.

Repeated returns are relevant to checking research, not sufficient evidence of compulsion. The portal does not estimate an overall compulsivity score, cluster animals, impute absent measures, or claim neural effects. PV/WFA is planned; GFAP is backup only if PV/WFA is unavailable. KAC tests differ jointly in depth, time/order and camera, so paired differences cannot isolate depth effects.

## Verification and access

The Python build asserts exact binary roundtrips for 250,800 native frames, 91 sessions, 62 complete trips and 40 complete trips reaching the proposed P1 area. JavaScript results are checked against 819 independent NumPy radius/dwell cases. Synthetic checks cover gaps, one-frame entries, dwell and excluding interpolated points. The AK1 means are derived from the source workbook, not copied from the audit.

Sound starts off and is generated locally after opt-in; it is not a recording, physiological signal or emotional inference. Reduced-motion preferences stop decorative animation; replay starts only on explicit Play. All controls use native keyboard-operable elements; timelines have equivalent event tables, AK1 has a full value/source-row table, and a data dialog provides coordinates and downloadable native-frame CSVs.

Browser QA and deployment results are recorded in `verification_browser.md` and `deployment.json` when completed. Viewport emulation is not a real-phone test. No 4-second/60-fps performance claim is made without a measured benchmark. Exact-scale 3D, physical-phone testing and derivative cinematic/poster assets are outside this initial release, as recorded in the approved treatment.
