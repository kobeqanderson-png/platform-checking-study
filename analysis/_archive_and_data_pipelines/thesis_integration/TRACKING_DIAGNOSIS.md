# Why the high-resolution KAC paths break

8 November 2026. Reprocessed both existing Day 8 model outputs for all 30 animals using identical windows and cleaning rules. No production caches were replaced.

| Model | Female mean missing time after QC | Female raw false-spot frames | Male mean missing time |
| --- | --- | --- | --- |
| Current best-240 | 13.53% | 18.84% | 0.05% |
| Earlier best-400 | 2.20% | 2.26% | 0.00% |

The same video supports markedly better retained coverage with the earlier model. This demonstrates a model-dependent failure, rather than establishing that the high-resolution recordings are inherently unsuitable. Retained coverage is not itself ground-truth accuracy: recovered trajectories still require source-video checks.

The current model sometimes confidently follows the empty rim location. Cleaning removes those frames; only short gaps can be interpolated. The broken paths show unresolved tracking, not discontinuous movement by the animal. Raw false-spot and outside-pool masks overlap and must not be added together. Final missingness is lower than raw rejection because short gaps can be filled.

Relaxing the speed cutoff from 60 to 100 or 150 cm/s only changes Day 8 female missingness from 13.53% to 12.95% or 12.93%. The speed cutoff is therefore not the main cause of missing time, although it can still fragment some genuine movement. The false spot is also outside the accepted pool boundary, so the present diagnostic does not separately establish how much each geometric criterion contributes.

SP1's own model has about 0.15% female and 0.12% male unknown time. Video resolution alone does not explain model performance. Whether the KAC model failed because of training coverage, labeling quality, resizing, or other training choices is not yet established. Raw pixel evaluation errors across different resolutions are not directly comparable.

Best-240 was used for the paired KAC analysis because it covers 29 Day 6 and 30 Day 8 animals. Best-400 currently covers only 12 Day 6 animals, all male, and all 30 Day 8 animals. For route organization, improving trajectory fidelity now takes priority over accepting the complete best-240 dataset as adequate.

Next: visually check best-400 on the specific Day 8 frames rejected under best-240, assess route/event continuity and residual errors, then complete Day 6 inference with the better validated model. If failures remain, select representative difficult swimming frames for corrected labels and retraining. Do not simply connect long gaps. Training repair follows the official [DeepLabCut refinement workflow](https://deeplabcut.github.io/DeepLabCut/docs/standardDeepLabCut_UserGuide).

Per-animal results: `tracking_model_diagnostic.csv`. Reproduce with `diagnose_tracking.py`. Existing behavioral findings based on best-240 retain their stated missingness limitations until a validated replacement analysis is run.
