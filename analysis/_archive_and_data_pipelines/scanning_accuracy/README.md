# Scanning and initial travel toward the learned location

8 November 2026. Exploratory follow-up to the user's video observation: rats that scanned more appeared to swim more directly toward the old training-platform location. The original screenshot plots whole-session head sweeps against complete excursions; it does not measure travel accuracy.

## What was checked

Existing final checking caches only: KAC best-320, SP1 best-190. One first qualifying departure per animal, without substituting a later departure if the first fails. Require no earlier missing body tracking, five continuously on-platform seconds before departure, and at least 80% usable adjacent head-angle pairs. No-departure animals do not have a directional outcome.

Predictors: mean absolute head rotation (degrees/second) in those five seconds, and a supplementary count of head sweeps of at least 30 degrees divided by valid head-angle exposure. The sweep sensitivity check was added after inspecting the rotation results, to match the dashboard definition more closely. All analyses are exploratory, not preregistered. Short windows can truncate sweeps and yield coarse sweep counts.

Outcomes: (1) direction of net body displacement over the first second after departure, relative to P1 (lower angular error is better); (2) reduction in distance to P1 divided by distance swum over up to five seconds (higher is better). Stop the latter at entry into the 20 cm P1 region or a sustained platform return. Require continuous observed or accepted short-interpolated body tracking and sufficient displacement. First-second direction can reflect dismounting as well as subsequent navigation. These measures do not establish memory accuracy or subjective intent.

P1 uses the existing proposed geometry. KAC coordinates are training-derived and conditional on camera correspondence; Day 8 needs particular care. SP1 P1 is assumed by reflection. Camera geometry needs visual validation before interpreting precise direction as travel toward the actual learned location.

## Results

| Test | Usable first departures | Rotation vs heading error, Spearman rho | Rotation vs progress/path, Spearman rho |
|---|---:|---:|---:|
| KAC Day 6 | 6 of 29 sessions | 0.60 | -0.37 |
| KAC Day 8 | 9 of 30 sessions | 0.02 | -0.50 |
| SP1 | 13 of 32 sessions | 0.13 | -0.02 |

The hypothesized pattern would be negative for heading error and positive for progress/path. This first-departure check does not show that pattern. Day 8 sweep-rate results are similarly unconvincing: rho 0.03 for heading error and -0.48 for progress/path.

`correlations.json` includes all 24 exploratory combinations of cohort, group (female-only or pooled), predictor and outcome, with unadjusted two-sided Monte Carlo permutation p-values (19,999 draws; fixed seed). They are overlapping comparisons, not independent replications. The Day 6 supplementary sweep/progress association has nominal p=0.0338, in the opposite direction to the proposed relationship, among just six selected animals; it does not survive even a simple correction across these comparisons. It is not evidence for a confirmed inverse relationship. KAC days reuse animals and cannot be pooled as independent subjects.

## Missingness and scope

Day 6: 14 no observed departures, 7 uncertain first departures from earlier gaps, 2 insufficient predeparture platform time, 6 included.

Day 8: 14 no observed departures, 3 uncertain first departures, 4 insufficient predeparture time, 9 included.

SP1: 16 no observed departures, 2 uncertain first departures, 1 short or interrupted initial swim, 13 included.

These selected cases cannot settle the user's broader observation about scanning across animals or later excursions. The next useful validation is to mark the actual learned location on the relevant camera views and compare scan-to-departure-to-route sequences against video, retaining the animal as the independent unit when examining repeated trips. Head movement is a tracking-based proxy, not a validated behavioral scanning label or measured gaze.

## Outputs

- `scanning_vs_direction.png` and `.svg`: labeled animal-level plots for the rotation predictor.
- `first_departure_audit.csv`: every session, inclusion/exclusion reason, metrics and interpolation fraction.
- `correlations.json`: full exploratory results, including the sweep sensitivity analysis.

Rebuild: `python analysis/scanning_accuracy/check_initial_search.py`. This writes only this analysis folder. Existing caches and the live dashboard remain unchanged. Metrics are checked for geometric bounds; the figure was visually inspected. No additional tracking or model training was performed.
