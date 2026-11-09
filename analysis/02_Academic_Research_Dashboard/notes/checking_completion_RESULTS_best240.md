# KAC Day 6 completion audit

November 7, 2026. Independent analysis using the measurement functions and handwritten-note transcription in `analysis/dlc_measures/checking_dlc_measures.py`. Existing story/report files were being updated concurrently, so this audit preserves them and writes its results separately.

## What finished

The Colab notebook reports all 29 Day 6 clips complete. Those files use **best-240 (v2)**, not best-400 as anticipated in the handoff. Matching best-240 Day 8 tracks exist for all 30 rats. The completed comparison therefore uses best-240 on **both days**, with 29 paired animals: 14 male and 15 female. Rat 1 has Day 8 only; rats 11 and 19 are absent. Best-400 still has only 12 Day 6 animals, all male.

All 101 copied tracking files passed the scorer/model check and contained a full 3,600-frame analysis window (120 seconds at 30 fps), with finite processed body coordinates. File hashes, rat identities, model, and release offsets are in `results/input_provenance.csv`.

## Platform-time result

| Paired group | n | Day 6 standard | Day 8 raised | Mean change, percentage points | Paired Wilcoxon p |
|---|---:|---:|---:|---:|---:|
| All | 29 | 83.99% | 79.42% | -4.57 | 0.0680 |
| Males | 14 | 98.00% | 97.29% | -0.71 | 0.5992 |
| Females | 15 | 70.91% | 62.74% | -8.17 | 0.1205 |

Female minus male platform time differs at standard depth (Mann–Whitney p = 0.0000462). The sex difference is therefore already present in the control condition. The paired depth comparison does not establish an additional change in platform time, but a nonsignificant result is not evidence of equivalence or no effect. Females' mean change has a percentile-bootstrap 95% interval of approximately -16.42 to +1.02 percentage points.

Statistics are exploratory and unadjusted. Wilcoxon tests use the per-rat values rounded as in the original measurement script, with differences rounded to avoid floating-point tie artifacts. The legacy story script uses slightly different smoothing and unrounded measures, so tiny numerical differences are expected. Day and depth are confounded by the fixed test order; do not interpret the paired contrast as isolating water depth from order or repeat exposure.

## Validation and claims to hold back

- Day 6 stayed/left classifications agree with **20/20 explicit notes**. Nine animals have no explicit stayed/left label; they are not counted as agreements.
- Day 8 stayed/left classifications agree with **30/30 notes**, for both models.
- Platform time is stable between models on overlapping animals: maximum difference **0.1 percentage point** for the 12 Day 6 males and **0.5 percentage point** for all 30 Day 8 rats. There is no best-400 Day 6 female comparison yet.
- Departure timing still needs video review for **Day 6 rat 4** (DLC 7.8 s versus notes ~40 s), **Day 6 rat 26** (85 s versus ~100 s), and **Day 8 rat 13** (75.3 s versus 65 s). Both models reproduce the rat 4 and rat 13 discrepancies; neither model resolves them automatically.
- Binary stayed/left validation does **not** validate departure counts. For example, Day 6 rat 28 has 4 DLC departures versus 2 in the notes, and rat 31 has 4 versus 2. Definitions and footage need reconciliation before presenting counts as validated.
- **Wall-time results are highly model-sensitive.** Female Day 8 wall time is **3.64% with best-400 versus 18.83% with best-240** using the same geometry, thresholds, and trial windows. Consequently, best-240's paired wall-time increase (females 3.23% to 18.83%) must not be presented as a robust behavioral result yet. The nominal p-value does not resolve this tracking uncertainty.
- Off-platform distance and departure-count increases are exploratory and require separate validation; reliable platform occupancy does not establish reliable swimming trajectories.

## Files

- `results/best240_paired_platform.png` and `.svg`: paired platform-time figure, with each animal and sex-specific means.
- `results/paired_statistics.csv`: paired means, changes, bootstrap intervals, and Wilcoxon tests.
- `results/best240_d6_measures.csv` and `best240_d8_measures.csv`: per-rat measures, kept separate from established first-model outputs.
- `results/best240_d6_notes.csv`, `best240_d8_notes.csv`, and corresponding timing files: note comparisons.
- `results/d6_model_comparison.csv` and `d8_model_comparison.csv`: same-animal comparison across models.

## Remaining work

Review the three timing discrepancies and model-dependent swimming trajectories in the source videos before finalizing those outcomes. If best-400 remains the selected primary model, track the remaining 17 Day 6 animals with best-400 and rerun its complete paired analysis. Do not mix those 17 with best-240 outputs or pool estimates across models. SP1 and AK1 were not modified by this audit.
