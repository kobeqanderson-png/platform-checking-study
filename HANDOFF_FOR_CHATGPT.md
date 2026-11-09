# Handoff for ChatGPT: KAC / SP1 water maze checking-test project

## Current access clarification — user reports the app is public

The user explicitly corrected the prior description: **“my vercel app is public now.”** Treat the app as public in future planning and communication. Earlier protected-publication notes describe the prior deployment workflow, not a current assurance that the app is private.

A read-only project check after this clarification still returned SSO protection `all_except_custom_domains`, with password protection disabled. Public app/domain access and protection on individual preview URLs may therefore differ; do not claim the preview URL is public or that all research content is protected without checking that specific URL. No access settings were changed in response to this clarification. It does not itself request a new deployment or broader sharing of additional files.

## Latest update — Return portal built and protected (9 November 2026)

This section supersedes the portal-awaiting-approval statements below. User approved the treatment with **“Yes do it.”**

- **Live portal:** `https://platform-checking-study-2nq09h1mj-kobeqanderson-pngs-projects.vercel.app/portal.html`. Existing dashboard at the same host `/index.html` links to it. Deployment `dpl_FbCKph2Q4RbWy3TVT4xkTndjxjLe`, READY, 138 source-file hashes verified, 23,760,952 bytes. Existing Vercel protection unchanged; no public promotion or share/bypass URL. Final portal tab was left open.
- Source/pipeline/docs: `analysis/portal/`. `return_portal_source.zip` contains the source and exported native-frame data. `deployment.json`, `verification_browser.md`, `README.md` and the version-2 planning decisions log record the implementation and bounds.
- Functionality: KAC paired replays with synchronized time; all SP1 sessions separately; unsmoothed/processed display and explicit interpolation/rejection; source-frame dialog; individual summaries; complete/incomplete return timelines and accessible tables; live radius/dwell controls; AK1 30-animal × 3-configuration paired passage comparison; PV/WFA hypothesis panel; optional synthesized ambience initially muted; reduced-motion CSS and phone layout.
- The portal export preserves all 250,800 native frames as float64 without rounding or thinning. Exact binary roundtrips passed for all 91 sessions. 819 JavaScript radius/dwell calculations matched independent NumPy results. SP1 F25 was rederived from its original HDF and source hash checked. KAC original HDF paths were unavailable this turn; portal uses the verified local caches and recorded original-source provenance, explicitly disclosed.
- Dynamic area controls count software-defined eligible bouts and known outside-to-inside transitions. No onset is inferred across an unknown gap. Defaults remain 20 cm / no dwell. These controls **do not change** the fixed complete-trip metrics; a boundary entry is not a new validated check. Filled-frame exclusion is optional and visible.
- Browser-verified downloads: `Downloads/return_SP1_25_native_frames.csv` (1,200 rows) and `Downloads/return_KAC_25_native_frames.csv` (7,200 rows), matching cached raw/processed coordinates, interpolation flags and source-frame offsets. Phone viewport 390 × 844 yielded 375 CSS px content with no horizontal page overflow. This is emulation, not a physical-phone benchmark. No 4-second/60-fps claim.
- Preserved newer local art/motion lab changes found in `analysis/dlc_cleaned/site/` (index ~80 KB, `dlc_motion_lab.html`, `dlc_motion_data.json`, Three.js files, `figures/art_*`). They were not part of the last published 35-file dashboard. This deployment adds the portal to that verified published baseline; it does not silently publish those local assets or overwrite them.
- Remaining scientific validation: register goal/zone maps to cameras; reconcile 172 vs 172.5 cm; recheck KAC source HDF when available; confirm AK1 `49-Prb4` endpoint identity; validate inferred events against video. Initial release intentionally remains overhead 2D. Exact-scale 3D and derivative video/poster assets follow the conditions in the approved treatment.

## Latest update — individual profiles, repetition and portal planning (8 November 2026)

This section supersedes older tracking/model and scope statements below.

- Protected dashboard update: `https://platform-checking-study-q8svng7mw-kobeqanderson-pngs-projects.vercel.app/profiles.html`. Deployment `dpl_9F634pepfQGeagmVbH3Eds6wP4Jb`; 35 source-file hashes verified. User explicitly approved hosting the animal profiles, acquisition summaries, correlations, downloads and existing videos in this existing protected Vercel project. Do not change public access.
- `analysis/individual_profiles/` implements 14 descriptive behavioral measures, 62 biological animals / 91 sessions / 29 paired KAC animals. It links corrected KAC AnyMaze acquisition, individual comparison, raw-value profile matrix, paired changes and descriptive correlations. Neural data remain pending. No overall compulsivity score, inferred clusters or missing-value imputation.
- User now explicitly prioritizes OCD-related checking, returns and repetition. The **Returns & repetition** dashboard view shows excursion timing, observed placement returns, first P1 entries per segment, complete trips and later complete P1-reaching trips. The last quantity is a lower bound and not all within-trip reentries. Do not call repetition alone demonstrated compulsion.
- User removed the 0.5-second P1 dwell rule. Current atlas and profile P1 visits count any valid off-platform entry within the existing 20 cm proposed area. Wall route labels retain 0.5 s. Original complete-path P1 totals now Day 6 10/15, Day 8 16/23, SP1 14/24. Day 8 F25: 7 observed placement returns, 6 complete trips, 5 complete P1-reaching trips, 4 later such trips. Unresolved gaps remain censored.
- Final models: KAC best-320 on both days; SP1 best-190. Current geometry is provisional; existing analysis scale is 172 cm. Do not revert to obsolete best-240 conclusions below.
- User supplied a new immersive portal brief at `C:/Users/kobeq/.codex/attachments/8515c607-8452-40a5-a08a-2322e604d36b/Pasted text.txt`. Its process explicitly asks for treatment + decisions log, then approval before portal construction. Those documents and a file inventory are in `analysis/portal_planning/`. The cinematic portal has not been built; treatment approval remains the next step.
- Portal clarifications confirmed by user: SP1 uses the existing 120-second window from placement/start markers; AK1 initially appears as a measurement comparison without animated paths. AK1 is now in scope for the portal, separately from the KAC/SP1 profiles.
- AK1 original found at `C:/Users/kobeq/Downloads/AK1_complete.xlsx`, integrated audit at `C:/Users/kobeq/Downloads/SfN_AK1_SP1_Integrated_Audit.xlsx`. Independently reproduced `49-Prb4`: 90 rows / 30 animals / 3 configurations, all 120 s, mean PASSTH01 1.8 / 3.633333 / 5.233333. Same path distance across configurations; coordinate series not located. Audit still flags intended endpoint identity as open.
- Rechecked original SP1 weight workbook: rats 1–16 male, 17–32 female. The pasted brief's old block-based formula grouping is superseded. Its 172.5 cm diameter differs from current 172 cm analysis conversion; log and reconcile before claiming exact-scale portal geometry.
- Browser verified individual comparison, filters, paired views, trajectory links, repetition data and phone-width layout. No console errors. Saved browser download verified against the source export: 91 unique sessions, 37 columns. Real physical-phone testing has not been performed. The offline site ZIP is updated. No tail-sweeping UI was reintroduced.

## Current update — 8 November 2026

**Labeling batch ready:** Kobe offered to label more frames. `training_packages/KAcheck_targeted_repair_20261108/` contains 24 targeted repair frames and 12 separate audit frames, full-resolution PNGs, blank DLC labels, manifests, previews, and isolated labeler launchers. Read its README before merging or training. Loading was checked (24/12 images, 17 bodyparts); original MobileDLC was not modified. Audit frames must remain outside the repair training batch, and are not claimed to be unseen under historical training.

**Tracking diagnosis:** a fresh same-video/same-QC comparison of all 30 Day 8 animals found female missingness **13.53% with current best-240 versus 2.20% with earlier best-400**, with false-spot frames 18.84% versus 2.26%. See [TRACKING_DIAGNOSIS.md](analysis/thesis_integration/TRACKING_DIAGNOSIS.md). Retained coverage still needs visual validation. Prioritize checking the recovered best-400 trajectories and completing its Day 6 inference before treating best-240 route fragmentation as an unavoidable recording limitation. No production caches have been switched.

**Behavioral organization is the primary analysis objective (Kobe reaffirmed this).** A first excursion/state-sequence analysis is now in [organization/RESULTS.md](analysis/thesis_integration/organization/RESULTS.md), with all 91 session timelines and all 24 complete SP1 excursion paths. Opposite-quadrant travel is explicitly a broad proxy; exact learned-place visits remain pending verified training-location geometry. Direct Drive inventory confirmed 32 SP1, 29 KAC Day 6, and 30 KAC Day 8 checking tracks; best-400 Day 6 still has 12. Do not confuse tracking completion with absence of missing/incorrect tracking.

The thesis is now part of the active scope alongside SfN. Start with [the thesis alignment note](analysis/thesis_integration/THESIS_ALIGNMENT.md) and the existing proposal in `C:\Users\kobeq\Documents\Kobe Research\Thesis\THESIS PROPOSAL.md`.

- Kobe confirmed that the checking placement platform is in the **opposite quadrant** from the learned platform location. The current platform occupancy/departure analysis does not yet quantify the thesis's primary learned-place visits and reentries. Recover the actual trained-location geometry before calculating those events.
- Kobe confirmed **SP1 brains are fixed** and **KAC animals are still alive**. Per-animal specimen inventory and SP1 fixation/storage history remain to be established.
- Kobe specified **PV/WFA as Plan A; GFAP staining as Plan B if PV/WFA are unavailable**. GFAP requires its own anatomical endpoint and revised interpretation, rather than being treated as a measurement of PV/net association. The older thesis notes' optional-addition framing is superseded by this working decision.
- **SP1 sex mapping is resolved:** the original `Documents\2025\data\Rat weights 12-30-24.xlsx` explicitly labels all rats 1–16 male and 17–32 female across four sheets, checked directly. The “inferred/not confirmed” statements below are superseded. The legacy measures CSV and generator now also use the correct test-to-rat mapping.
- “No observed departure” and “never left” need to remain distinct when tracking is missing. Four sessions have zero detected departures plus missing time. Notes validation is 18 Day 6 agreements + 2 unknowns, and 29 Day 8 agreements + 1 unknown; unknown is not a demonstrated disagreement.
- The cleaned local report, 91 caches/input hashes, nine videos, and six regression tests have passed integrity checks. Known artifact masks do not constitute exhaustive manual behavioral validation. Full-trial platform bounds are conditional on retained/interpolated tracking being correct.
- Published/private dashboards and the site ZIP were not redeployed for this update. The original handoff below remains useful history where it does not conflict with these newer facts.

---

Written 2026-11-07 at the end of the Claude sessions. From here on the work continues in ChatGPT. This file is the single entry point. Every path below is on the user's Windows PC.

---

## 1. Rules that matter
1. **Never write into `C:\Users\kobeq\Documents\MobileDLC`.** That is the user's own app. All experiment work lives in `C:\Users\kobeq\Documents\KAC database\`.
2. **Look at the tracking before trusting any DeepLabCut number:** the path map, the per-rat atlas and the demo videos. Confident false detections are not caught by likelihood filters. This already happened once; see section 5.
3. The audience is senior and traditional (bar graphs, Excel, simple tests). DLC must add what AnyMaze can't, and every DLC number must be checkable against AnyMaze, the notes or video.
4. Be careful with claims: say what holds and what is exploratory (section 7).
5. The user watches usage, so prefer targeted reruns over rebuilding everything.

## 2. Study design (confirmed by the user unless marked)
- **SP1** (earlier cohort, 32 rats): trained Days 1–5 at 1.5 cm platform submersion. Checking test (Day 6) with the **water raised (3.0 cm)**. No standard-depth control. Grey 10 fps video.
  - **Sex labels are inferred, not confirmed:** rats 1–16 male, 17–32 female, from the SP1 workbook grouping. **Confirm against the log before the poster.**
- **KAC** (32 rats; **rat 11 died before Day 1, rat 19 also absent**, so 30): training Days 1–5 and Day 7 (reminder).
  - **Checking tests:** Day 6 at **standard depth 1.5 cm (the control)** and Day 8 with the **water raised to 3 cm**, same rats (within-subject). Rats 1–16 male, 17–32 female.
  - "Groups 1/2" were only testing batches of 15, not treatments.
- **Checking test:** the rat is placed on the platform for 120 s. Lab rule: "found" means touch and stay. Stayed = never left the platform.
- **AK1** is another student's (Aizad's) separate study. It is **out of scope**.
- Poster: SfN, about 2026-11-10. Thesis: May 2027.

## 3. Folder map (`C:\Users\kobeq\Documents\KAC database\analysis\`)
| Folder | What it is | Status |
|---|---|---|
| `updated_anymaze\` | Corrected AnyMaze exports KAcd1–8 (40 trials replaced, d5 t53 excluded, d4 tests 73–88 relabelled), `changes.csv`, `README.md`, originals in `original\` | Final |
| `updated_anymaze\analysis\` | `analysis.py` (mixed models etc.), `REPORT.md`, `results\`, `figures\` | Final |
| `updated_anymaze\analysis\lab_version\` | `water_maze_results.xlsx`, the traditional Excel workbook (live formulas, bar charts, t-tests); `lab_version.py` rebuilds it | Final for AnyMaze; centred on the KAC checking tests |
| `dlc_measures\` | Per-rat DLC measures made by the other Claude session. **`sp1_checking_dlc_measures.csv` assumes test number = rat number, which is WRONG for tests 9–24.** | Superseded by `dlc_cleaned` |
| `dlc_story\` | Claude's first frame-level DLC analysis. **Contaminated by false rim points in KAC; do not use its KAC numbers.** `HANDOFF.md` there documents the defect. | Historical |
| `checking_completion\` | ChatGPT's Day 6 audit (`RESULTS.md`): model provenance, notes validation, model sensitivity | Valid |
| **`dlc_cleaned\`** | **Current DLC analysis**: `tracking_qc.py` (cleaning, unit tests in `test_tracking_qc.py`), `analyze.py`, `make_demos.py`, `verify_outputs.py`, `make_dashboard.py`, `results\`, `figures\` (PNG + editable SVG), `demos\`, `demos_trimmed\`, `review\` (source-frame checks), `site\` (standalone website), `platform_checking_site.zip` | **Use this** |

Run from `dlc_cleaned`: `python analyze.py`, then `python make_demos.py`, `python verify_outputs.py`, `python make_dashboard.py`. Run them without Python's `-I` flag, because the scripts import local modules.

## 4. Data sources
- **DLC outputs on Google Drive:** `G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\Colab_Training_Runs\`. The brackets break glob; use `os.listdir`.
  - **KAC, both days, model v2 (best-240):** Day 6 from `KAcheck_d6d8_v2_20261107\d6_tracks` (29 rats), Day 8 from `KAcheck_d6d8_v2_20261107 (1)\d8_tracks` (30 rats). Held-out error 12.1 px (5.3 px at p-cutoff 0.6).
  - KAC first model (best-400), `KAcheck_d6d8_20261107 (1)`: more accurate (4.8 px) but Day 6 has only 12 males. It agrees with v2 on platform time to within 0.5 points.
  - **SP1:** `sp1\sp1_tracks` (32 rats, best-190, 2.4 px). The test-to-rat mapping comes from AnyMaze's `animal` column (`dlc_measures\sp1_checking_dlc_vs_anymaze.csv`): **tests 9–16 are rats 17–24, and tests 17–24 are rats 9–16.**
- **Clips:** `...\d6_clips`, `...\d8_clips`, `...\sp1_clips\sp1_check`. Release offsets: Day 8 `C:\Users\kobeq\Videos\checkd8\trials\clip_manifest.csv`; Day 6 `analysis\tracking_pilot\d6_tracker_vs_anymaze.csv`.
- **AnyMaze databases** (`.szd`) hold test start times (FILETIME, marker 926297655 at +52 bytes); `updated_anymaze\scripts\read_szd_starts.py`.
- **Raw videos:** KAC 1080p 30 fps (Day 4 video in Downloads, 7.87 GB). SP1 grey 10 fps. SP1 workbooks: `C:\Users\kobeq\Downloads\SP1.xlsx` and `SfN_AK1_SP1_Integrated_Audit.xlsx`.

## 5. The tracking defect and how it was fixed
- **The defect:** DLC (KAC v2) jumps to a fixed false point on the pool rim whenever it loses the rat, then jumps back.
  - Day 8: around pixel (870, 50), 9.4% of frames, 18 rats.
  - Day 6: around (310, 210), 1.4% of frames, 10 rats.
  - It shows as fans of straight lines in the path plots. Some points also land outside the pool.
- **The fix** (`dlc_cleaned\tracking_qc.py`, settings in `results\method.json`):
  - Mask points within 40 px of the false spot, beyond 0.98 of the pool radius, or across body jumps above 60 cm/s.
  - Interpolate gaps of 0.5 s or less; longer gaps stay **unknown**.
  - Report platform time as bounds: unknown counted as off, and unknown counted as on.
- **After cleaning:** paths verified by eye, with no rim fans and nothing outside the pool. Unknown time: KAC Day 8 females 13.5% (rat F22 41%), Day 6 females 2.5%, males and SP1 about 0%.

## 6. Results

### 6a. AnyMaze, KAC training (final)
- Escape latency fell from 25.7 to 16.1 s over Days 1–5 (two-way mixed ANOVA, Day p < 0.001).
- No sex effect (p = 0.153) and no Day × Sex interaction (p = 0.275).
- Females swam faster, by about 4 cm/s (p < 0.001).
- No forgetting by the Day 7 reminder (p = 0.269).

### 6b. Staying vs leaving (holds; checked against AnyMaze and the notes)

| Test | Males stayed | Females stayed | Fisher p |
|---|---|---|---|
| SP1, raised water | 12/16 | 4/16 | 0.012 |
| KAC Day 6, standard 1.5 cm | 11/14 | 3/15 | 0.003 |
| KAC Day 8, raised 3 cm | 13/15 | 1/15 | < 0.001 |

- Time on platform, females vs males: about 74% vs 98% (SP1); Day 6 71–73% vs 98%; Day 8 63–76% vs 97%.
- DLC vs AnyMaze platform time: r = 0.998 (Day 8), 0.991 (Day 6).
- Stayed/left matches the handwritten notes for 18/20 rats on Day 6 and 29/30 on Day 8 (after cleaning).
- **SP1 AnyMaze tracking is unreliable** (r = 0.78). Video confirms DLC is right, for example SP1 rat 22 stayed the whole test while AnyMaze said 19%.
- **Same rats, standard vs raised water (KAC):**
  - Males: 98% → 97%.
  - Females: 71–73% → 63–76%. Given the unknown time, the change could be anywhere from −11 to +5 points.
  - Depth is confounded with test order and repeat exposure.
  - **The sex split already exists at standard depth; the raised water did not create it.**

### 6c. Micro-behaviour on the platform (cleaned; Mann-Whitney, Holm within test; female vs male)
- **Head-turn speed before leaving:** higher in females in all three tests (SP1 74 vs 52 deg/s; Day 6 86 vs 51; Day 8 76 vs 46; all p < 0.001).
- **IdPhi (summed head rotation) and the tail measures** (tail sweeps per minute, tail vigour, body drift on the platform): higher in females in **all three tests**, and all survive correction.
- **Head sweeps, VTE-like episodes and edge rocking:** significant in SP1 and Day 6. On Day 8, VTE-like episodes and edge rocking are not significant.
- **Lean-outs** (nose pushes toward the edge): both sexes pull back at similar rates, but female lean-outs end in leaving far more often (about 10–18% vs about 2%).
- **VTE-like hypothesis** (more head rotation before pulling back than before leaving): **only a trend after cleaning** (Holm p = 0.16, 0.49, 0.16). Not a finding.
- **Tail–drift coupling** on the platform: tail vigour and drift co-occur (r about 0.3–0.4, peak at zero lag), so the timing does not show which drives which.
- **Within females on Day 6 only** (first, pre-clean analysis), more head turning in the first 10 s went with leaving sooner (ρ = −0.69). Not replicated on Day 8 or SP1; recheck on the cleaned data.

### 6d. The user's newest idea: tail sweeping *while swimming to find the platform*
- **Not measured yet.** The on-platform tail results are a different thing.
- **Tracking feasibility** (share of swimming frames with confident tail points):

  | | Tail base | Tail middle | Tail tip |
  |---|---|---|---|
  | SP1 | 100% | 100% | 99% |
  | KAC Day 6 | 76% | 27% | 92% |
  | KAC Day 8 | 100% | 43% | 2% |

  KAC needs extra labelled underwater-tail frames.
- Checking-test swimming is almost all females (about 500–670 s per cohort vs 30–46 s for all males), so a sex comparison needs the **training trials** (Days 1–5 and 7), which are **not DLC-tracked yet**.
- **Plan:**
  1. Pilot on SP1 checking-test swims, within females: tail sweeps vs turning, speed and approach to the platform.
  2. Track SP1 training trials, then KAC after retraining.
  3. Ask whether tail sweeping changes with learning, differs by sex, and predicts latency.
  4. Validate the automatic tail-beat count against counts by eye on about 10 clips.

## 7. Claims: what holds, what to hold back
- **Holds:**
  - A large sex split in staying vs leaving, in three tests across two cohorts, present at standard depth.
  - Females turn their heads and sweep their tails more on the platform.
  - Tracking is validated against AnyMaze, the notes and video.
- **Hold back:**
  - The depth effect.
  - VTE/deliberation interpretations.
  - Causal tail→drift.
  - Anything resting on SP1 sex labels until they're confirmed.
  - KAC Day 8 swimming paths (13.5% unknown).
  - Departure counts as validated: binary stayed/left is validated, counts are not. Day 6 rats 4 and 26 and Day 8 rat 13 have timing discrepancies with the notes; video spot-checks lean toward DLC.

## 8. Published outputs
- **Claude artifact (private):** https://claude.ai/artifact/3J12bMJtsL2mNnm4xVRJWW (the latest dashboard).
- **Vercel** (account kobeqanderson-png, project `platform-checking-study`):
  - Latest version, private preview: https://platform-checking-study-au1j1dniu-kobeqanderson-pngs-projects.vercel.app
  - An older version sits at `platform-checking-study-kobeqanderson-pngs-projects.vercel.app` (protected).
  - The public alias `platform-checking-study.vercel.app` was removed. **A `vercel deploy --prod` re-creates a public address. Use `vercel deploy --target preview` to keep it private.**
  - The CLI is logged in on this PC (`npx vercel`).
- **Offline website:** `analysis\dlc_cleaned\site\index.html`, or `platform_checking_site.zip` to send.
- **Best demo clips:** `demos_trimmed\leave_vs_stay_sp1.mp4`, `head_turning_kac_d6.mp4`, `tail_sweeping_sp1.mp4`. Placement seconds are trimmed off. The KAC Day 8 leave-vs-stay clip has 18% UNKNOWN for its female.

## 9. Open items, in priority order
1. **Confirm SP1 sex labels** against the log. The whole SP1 replication rests on this.
2. Poster figures: start from `dlc_cleaned\figures\*.svg` and the lab workbook. Key panels:
   - the stayed/left bar chart for the three tests;
   - the on/off raster (`03_platform_state`);
   - head-turn and tail bars (`06`, `07`);
   - one demo screenshot.
3. Video-check the three timing discrepancies (Day 6 rats 4 and 26, Day 8 rat 13).
4. Tail-while-swimming pilot (section 6d), then track the training days.
5. Optionally reduce KAC unknown time: rerun the best-400 model on Day 6, or label more frames of underwater rats and retrain.
6. Day 7 reminder training is untracked. The user noticed striking behaviour on the reminder day and on the second platform exposure.
7. For the thesis, look in the literature for sex differences in Morris water maze strategy, platform leaving, thigmotaxis and anxiety-like behaviour, and estrous effects, before claiming novelty. Collect estrous stage and body weight if possible, since they are obvious confound questions.

## 10. Update 2026-11-08: KAC v3 model (13 points)
- Labels: 281 KAC frames (197 earlier + 84 labelled on 2026-11-08 in the hosted MobileDLC labeler, all Day 8). The MobileDLC labeler has **13 points: no tail quarter, middle, three-quarter or tip**, so v3 learns only those 13.
- Package: `G:\My Drive\DLC output[sp1--kac1.5cm-3.0cm]\MobileDLC_KAcheck_d6d8_v3_20261108\KAcheck_d6d8_v3_20261108.zip`, built by `KAC database\training_packages\build_v3_package.py` from the v2 zip plus `d1_labels_20261108.txt` (a read-only export of the labeler's Cloudflare D1 table `edits`). Coordinate check against v2: 0.08 px.
- Notebook: `16_train_v3_13point_and_track.ipynb`, in the same Drive folder. L4 GPU, Run all twice. It trains 400 epochs, evaluates, then tracks Day 6 and Day 8 with `finish_videos.py`.
- Output: `Colab_Training_Runs\KAcheck_d6d8_v3_20261108\` (`d6_tracks`, `d8_tracks`, `*_videos_final`, `evaluation-results-pytorch`).
- After it runs:
  - Compare held-out error with v2 (12.1 px) and the first model (4.8 px).
  - Point `dlc_cleaned` at the v3 tracks and rerun.
  - Check the unknown share (Day 8 females were 13.5%), rim jumps before cleaning, and AnyMaze agreement.
  - Look at the path map and videos before trusting numbers.
  - v3 has no tail middle or tip, so tail-sweep measures in KAC must use the tail base relative to the body axis, or stay SP1-only.
