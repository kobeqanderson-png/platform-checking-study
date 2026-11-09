# Browser verification — Return

Protected initial preview tested in authenticated Chrome. Project protection unchanged. The portal loaded all initial data without console errors.

- KAC F25 paired Day 6/8 paths and counts matched existing exports. Day 8: 7 placement returns, 6 complete trips, 5 complete P1-reaching trips, 4 later such trips.
- Play advanced both panels; Pause stopped playback. A keyboard Enter on a timeline segment selected its departure time.
- Raw/processed selection and rejected-point visibility controls changed state. No unknown-frame bridging is added by the renderer; adjacency is enforced in code.
- Changing radius from 20 to 10 cm and dwell from any entry to 0.5 s changed F25 full-session counts to Day 6: 1 observed entry / 0.5 s; Day 8: 3 / 1.9 s. Excluding filled samples removed the Day 6 qualifying bout in that setting. Fixed round-trip metrics stayed unchanged. Reset restored 20 cm and zero dwell.
- KAC M1 shows no Day 6 trajectory and the available Day 8 session; no imputed track.
- Switching to SP1 F25 showed a single, separate cohort animal and its 1200 native frames at 10 Hz. Data panel source hash was marked independently checked against the HDF.
- Source dialog displayed pixel coordinates, frame offset, quality flags and source hashes. Escape and Close worked.
- AK1 selected Rat 30 / Center 3: 5 passages, mean 5.23, n=30, workbook row 103. All source-row values also available in the table.
- Sound started off, toggled on after explicit click, and was turned off again. Audio generation is local synthesized noise; acoustic quality was not independently assessed by listening.
- Phone-width viewport set to 390 × 844 (375 CSS px content width after scrollbar). Document scroll width equaled client width, with no page-level horizontal overflow. Measurement controls and metrics stacked visibly; data dialog and download controls remained usable. Physical phone performance was not tested.
- Hero title size adjusted after visual review to retain the intended three-line composition on compact screens. Final verification recorded after deployment.
- Final deployment `dpl_FbCKph2Q4RbWy3TVT4xkTndjxjLe` loaded successfully; all 138 source hashes match the prepared deployment, total 23,760,952 bytes. Dashboard-to-portal navigation verified. Final mobile hero has the entry control visible and no horizontal overflow. Viewport restored, sound left off, portal tab marked as deliverable.
- Saved browser CSVs independently checked: SP1 F25 1,200 rows, KAC F25 Day 6/8 7,200 rows, matching cache raw/processed coordinates, interpolation flags and original frame indices. No duplicate session/frame pairs.

Numerical tests: 819 Python/JavaScript crosschecks, exact float64 roundtrip of 250,800 native frames, source workbook AK1 means and SP1 F25 original-HDF comparison. Downloads are independently checked from saved browser CSVs. No 4-second first-interaction or 60 fps claim is made; timing benchmark not performed. Reduced motion is implemented through the OS preference media query, with no automatic replay; an OS-setting change was not made during QA.
