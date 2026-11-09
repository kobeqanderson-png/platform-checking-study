# Portal source inventory

Checked 8 November 2026. Paths are local Windows paths. Original files were read, not edited.

| Source | Found | What is established / still open |
|---|---|---|
| AK1 original | `C:/Users/kobeq/Downloads/AK1_complete.xlsx` | `49-Prb4`: 90 subject rows, 30 animals, three configurations, 120-second endpoint values. PASSTH01 means reproduced: 1.8, 3.633333, 5.233333. Same per-animal path distance across configurations. Other stages coexist in this workbook. |
| Integrated audit | `C:/Users/kobeq/Downloads/SfN_AK1_SP1_Integrated_Audit.xlsx` | `AK1 Probe Audit`: 90 rows with original source tab/row; `SP1 Test`: 32 rows; `SP1 Training`: 640 rows. Audit flags endpoint/zone-map ambiguities and provisional historical sex assignment. These flags remain visible; the current roster supersedes the provisional sex formula. |
| Other audit artifacts | `C:/Users/kobeq/Downloads/SfN_SIRT_AK1_SP1.xlsx`; `SfN_2026_AK1_SP1_Audit_Report.docx` | Located, not used to derive current profile measures. |
| SP1 original | `C:/Users/kobeq/Documents/2025/data/SP1.xlsx` | Sheets include `d1`–`d5`, `d6`, `d6rev`, combined tables and `Paths`. The last sheet contains no usable trajectory series in the inspected metadata. Other copies exist; canonical extraction should use hashes. |
| SP1 roster evidence | `C:/Users/kobeq/Documents/2025/data/Rat weights 12-30-24.xlsx` | Four dated sheets explicitly label 17–32 female and 1–16 male. Rechecked headers and identifiers. |
| Corrected KAC AnyMaze | `analysis/updated_anymaze/` under the KAC workspace | Preserved originals, corrected exports, changes log, and validated analysis outputs. `analysis/results/rat_day_means.csv` contains 180 rat/day summaries. |
| Final checking tracking | `analysis/dlc_cleaned/cache/` | 32 SP1 best-190 sessions, 29 KAC Day 6 and 30 KAC Day 8 best-320 sessions. Each has 120-second data, source metadata, masks and model identity. |
| Existing trajectory/event analysis | `analysis/dlc_explorer/exports/` | Native-sampling-derived animal and excursion summaries, hashes and export figures. Replay is downsampled to 5 Hz and disclosed. P1 visit labels now have no dwell threshold. |
| KAC zone evidence | `C:/Users/kobeq/Documents/KAC database/Individual zone border map for WM, PPT.csv` | A 640 × 480 map is present. This is not by itself a full registration of all training and checking cameras. |
| SP1 zone evidence | `C:/Users/kobeq/Documents/sp1 database/sp1DLC/AnyMaze_Zones/` | P1, P2, pool/periphery and quadrant CSV maps, plus a verification image. Need registration to the actual source video and current proposed P1. |
| Source recordings and review clips | KAC day folders, existing cache video metadata, and `analysis/dlc_cleaned/demos_trimmed/` | Existing KAC/SP1 material supports inspection. The portal's per-frame provenance must link its retained source positions back to source file and time. |
| Requested `reproduce_audit.py` | Not found in searched Documents/Downloads locations | Do not claim the old audit has been rerun from its original script. Current checks independently reread selected raw values. |
| AK1 coordinate/video series | Not located | User approved an initial measurement comparison without animated paths. No coordinates will be fabricated from summary metrics. |
| Matched neural values | Not imported / not supplied in the current outputs | PV/WFA pending; GFAP fallback only. |

## Corrections to the pasted brief

- Its SP1 sex formula is superseded by explicit roster labels.
- Its SP1 time-window question is now resolved by the user: use the existing 120 seconds from placement/start markers. Do not mix the 180-second older summary export into that window.
- Its AK1 numbers are reproducible, but the integrated audit still marks the candidate endpoint's intended experimental identity as open.
- Its pool diameter is 172.5 cm, while current analysis conversion is 172 cm. This small discrepancy still matters for a claimed exact-scale reconstruction and needs a documented resolution.
- The current individual-profile dashboard covers KAC and SP1 only: 62 animals, not three pooled cohorts. AK1 will enter the proposed portal separately.
