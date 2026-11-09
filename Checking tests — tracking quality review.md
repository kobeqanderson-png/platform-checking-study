SP1 and KAC checking tests · November 7, 2026 · local reanalysis

# Tracking gaps made explicit

**Artifact removal is complete; recovery of the missing trajectories is not.**

The v2 model sometimes follows an empty rim location rather than the swimming rat. Those frames are masked, and long gaps remain unknown. Swimming distance, wall time, head/tail behaviors, and causal interpretations are not validated poster findings yet.

KAC uses best-240 on both days: 29 Day 6 and 30 Day 8 animals, with 29 pairs (14 males, 15 females). SP1 uses best-190 with test-to-rat mapping from AnyMaze, 16 animals per sex. SP1 sex labels (rats 1–16 male, 17–32 female) are inferred from the SP1 workbook grouping and still need confirming against the log.

## What the platform comparison can support

The control-condition sex difference must be assessed with unknown tracking time included in the bounds. The Day 6 to Day 8 comparison also combines water depth with test order and repeat exposure.

| Group | Pairs | D6 lower % | D6 upper % | D8 lower % | D8 upper % | Change min (pp) | Change max (pp) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| All | 29 | 84.00 | 85.32 | 79.42 | 86.44 | -5.90 | 2.44 |
| M | 14 | 98.00 | 98.00 | 97.29 | 97.34 | -0.71 | -0.65 |
| F | 15 | 70.94 | 73.49 | 62.74 | 76.27 | -10.75 | 5.33 |

KAC Day 6 · standard: 18/20 explicit stayed/left notes agree; 2 remain unknown. KAC Day 8 · raised: 29/30 explicit stayed/left notes agree; 1 remain unknown.

## Source-video checks

Selected source frames confirm the false rim points. Day 6 rat 4 is already swimming around 8–10 seconds, and rat 26 around 85 seconds. Day 8 rat 13 is on the platform at 65 seconds and swimming around 75–80 seconds. These spot checks do not establish exact departure times or replace the original notes.

SP1 rat 1 starts with a placement frame showing the hand outside the pool. Its full 120-second-from-release assumption needs review; cleaning treats the invalid initial frames as unknown, not a departure.

Open source-frame contact sheets

source_kac_d6_rat04

![Source-video tracking audit](review/source_kac_d6_rat04.jpg)

source_kac_d6_rat22

![Source-video tracking audit](review/source_kac_d6_rat22.jpg)

source_kac_d6_rat26

![Source-video tracking audit](review/source_kac_d6_rat26.jpg)

source_kac_d8_rat13

![Source-video tracking audit](review/source_kac_d8_rat13.jpg)

source_kac_d8_rat22

![Source-video tracking audit](review/source_kac_d8_rat22.jpg)

source_kac_d8_rat28

![Source-video tracking audit](review/source_kac_d8_rat28.jpg)

source_sp1_rat01

![Source-video tracking audit](review/source_sp1_rat01.jpg)

## Paths after cleaning

![Paths after cleaning](figures/01_cleaned_paths.png)

Long gaps are not joined. A smooth-looking plot is not proof of accurate tracking; all 91 individual panels are available below.

## Occupancy of tracked time

![Occupancy of tracked time](figures/02_observed_occupancy.png)

Each rat contributes equal weight. Missing swimming time makes these maps incomplete.

## On, off, and unknown

![On, off, and unknown](figures/03_platform_state.png)

Unknown frames are neither stayed nor left. Missing stretches cannot create additional departures.

## How much data was lost

![How much data was lost](figures/04_missingness.png)

Body coverage is reported per animal. Short internal gaps of at most 0.5 seconds may be interpolated; longer gaps stay missing.

## The Day 6 control and Day 8 comparison

![The Day 6 control and Day 8 comparison](figures/05_paired_platform_bounds.png)

These full-trial bounds allow missing time to be either on or off the platform. They are not statistical confidence intervals. Avoid treating observed-only time as an unbiased full-trial estimate.

## Head scanning candidates

![Head scanning candidates](figures/06_head_scanning.png)

Angles restart after gaps. Rates use valid on-platform exposure. These measures are operational definitions, not a validated measure of deliberation.

## Tail movement and drift candidates

![Tail movement and drift candidates](figures/07_tail_drift.png)

Circular angle differences avoid false 360-degree turns. Tail motion and drift correlation do not establish which causes the other.

## Pulled-back peaks versus departures

![Pulled-back peaks versus departures](figures/08_lean_outs.png)

Each confirmed departure appears once. Events need complete observed pre-event windows; this changes the eligible sample. The three cohort p-values are Holm-corrected.

## Dependence on the speed cutoff

![Dependence on the speed cutoff](figures/09_threshold_sensitivity.png)

The 60 cm/s threshold is a QC assumption, tested against 40, 100, and 150 cm/s. False-spot and rim thresholds remain fixed; full threshold validation is still pending.

## Every animal

Individual path atlas — 91 animals

![SP1 · raised, M, individual paths](figures/atlas_sp1_M.png) ![SP1 · raised, F, individual paths](figures/atlas_sp1_F.png) ![KAC Day 6 · standard, M, individual paths](figures/atlas_kac_d6_M.png) ![KAC Day 6 · standard, F, individual paths](figures/atlas_kac_d6_F.png) ![KAC Day 8 · raised, M, individual paths](figures/atlas_kac_d8_M.png) ![KAC Day 8 · raised, F, individual paths](figures/atlas_kac_d8_F.png)

## Video checks

White circle: platform zone. Coloured point and trail: cleaned tracking. Red point: original tracking. UNKNOWN is displayed during long gaps; trails stop rather than connecting across them.

## Coverage

| cond | sex | pct_missing | pct_interpolated | head_exposure_s | tail_exposure_s |
| --- | --- | --- | --- | --- | --- |
| kac_d6 | F | 2.55 | 4.04 | 84.80 | 81.56 |
| kac_d6 | M | 0.00 | 0.14 | 117.16 | 83.48 |
| kac_d8 | F | 13.53 | 7.84 | 75.21 | 73.34 |
| kac_d8 | M | 0.05 | 0.23 | 116.82 | 86.79 |
| sp1 | F | 0.15 | 2.18 | 88.39 | 88.49 |
| sp1 | M | 0.12 | 0.07 | 117.88 | 118.06 |

## Method and remaining limits

- Body: mid-spine, head-center fallback below confidence 0.3. One shared artifact mask invalidates body, head and tail together.
- Mask body points within 40 pixels of the documented false spot, beyond 0.98 of outer pool radius, or either side of a smoothed-body speed jump above 60 cm/s. These geometry and speed thresholds may remove some genuine edge movement.
- Interpolate whole internal gaps only when at most 0.5 seconds; no partial filling of longer gaps, no edge filling. Smoothing and angle derivatives do not bridge long gaps.
- Platform zone: 0.165 pool radii. Departure: at least one second of observed off-platform frames. Missing onset intervals are labelled; departure counts are observed lower bounds when data are missing.
- Head confidence 0.6; tail confidence 0.5. Rates use eligible observed time, not the full trial. Head sweeps are at least 30 degrees, tail sweeps at least 20 degrees; alternating head sweeps within two seconds are labelled VTE-like candidates only.
- SP1 linear distances assume the KAC 172-cm pool diameter. Percentages and angles do not require that assumption.
- Next: recover KAC swimming tracks (first-model rerun or additional labeling), validate representative head/tail/lean-out events manually, confirm SP1 release alignment, and then reassess the poster claims. Day 7 remains untracked; AK1 remains out of scope.

Original dlc_story files remain available unchanged. This report replaces none of the raw videos or tracking files and is not published externally.

[Per-rat results](results/per_rat_measures.csv) · [Notes comparison](results/notes_validation.csv) · [Input provenance](results/provenance.csv) · [Exploratory sex comparisons](results/sex_statistics.csv) · [Method settings](results/method.json)