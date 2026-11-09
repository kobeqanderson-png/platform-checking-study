# Checking results in the thesis

Working alignment, 8 November 2026. Based on Kobe's existing proposal, methods notes, current data, and clarifications in this conversation. This records the current working direction; it does not replace the approved protocol or silently revise the original proposal.

## The question being carried forward

The existing thesis asks how individual differences in place checking relate to striatal PV interneurons and their associated perineuronal nets. Memory systems and the expression of learned behavior remain the rationale. Sex differences are an important source of variation within that question.

The behavioral sequence is: **initiate a departure → approach the learned location → revisit that location**. These components require separate measurements. Current platform occupancy and departure results provide the first component; the primary learned-place visit measure has not yet been extracted and validated in the cleaned analysis.

## Decisions and records now established

| Item | Current evidence |
| --- | --- |
| Placement versus learned place | Kobe confirmed on 8 November that the checking-test placement platform is in the opposite quadrant from the learned platform location in SP1 and KAC. These must be separate regions in the analysis. |
| SP1 tissue | Kobe confirmed that SP1 brains are fixed. Availability and suitability must still be checked for each animal; fixation and storage details are not established by this statement. |
| KAC tissue | Kobe confirmed that the KAC animals are still alive. There is no collected KAC tissue sample to analyze yet. Future collection timing and intervening experiences remain relevant design decisions. |
| Anatomical priority | Kobe specified PV/WFA as Plan A, with GFAP staining as Plan B if PV/WFA are unavailable. This supersedes the October notes' treatment of GFAP solely as a possible additional exploratory assay. |
| SP1 sex | Verified directly against `Rat weights 12-30-24.xlsx`: sheets `1230` and `1-1` explicitly label rats 17–32 female; sheets `1231` and `1-2` label rats 1–16 male. All four complete ID sets were checked. |
| SP1 animal identity | Test numbers differ from rat numbers. The AnyMaze mapping is used; the legacy measures file and its generator now have corrected rat and sex labels. |

The weight workbook resolves the conflicting sex statements in the handoffs. Its dated weights are not automatically test-day body weights and have not been inserted as covariates.

## How the current results fit

| Thesis component | What exists | What it supports or still needs |
| --- | --- | --- |
| Acquisition | Corrected KAC training and reminder records | Learning and movement context. A nonsignificant sex term does not establish identical learning or memory. |
| Departure/initiation | Cleaned platform-zone time and observed departures across 91 sessions | A substantial sex difference is already present at standard depth. Zone exits still require event-level validation against complete physical departures. |
| Destination | Body trajectories, with explicit gaps | Locate and verify the former learned-place region. Time at the placement platform does not measure destination after departure. |
| Recurrence | Trajectories available; validated learned-place event table absent | Separate first learned-place visit, later reentries, return intervals, and returns to the placement platform. Departure totals cannot substitute for learned-place visits. |
| Microbehavior | Head rotation, tail motion, lean-out candidates | Secondary or exploratory descriptions pending independent manual validation. They do not establish deliberation, habit, or compulsion. |
| Anatomy | SP1 fixed brains reported; KAC animals alive | No PV/WFA or GFAP association has been measured here. Match tissue to individual behavior before estimating an association. |

There are **32 SP1 rats and 30 KAC rats**, not 91 independent animals: KAC contributes 29 Day 6 sessions, 30 Day 8 sessions, and 29 paired animals. SP1 and KAC remain separate cohorts by default. Tissue eligibility and the eventual matched sample size are unknown.

For context, the current missing-time bounds give female KAC platform-zone means of **70.9–73.5% on Day 6** and **62.7–76.3% on Day 8**. Male Day 6 occupancy is about **98.0%**. Female Day 8 missingness averages **13.5%**. The female paired change can range from approximately **−10.8 to +5.3 percentage points** under these bounds. These are conditional on accepted tracking and short-gap interpolation being correct; they are not confidence intervals or bounds on every tracking error. Depth also shares a fixed order with repeat testing and the intervening reminder.

## Plan A: PV/WFA

Retain the proposal's primary anatomical quantity: the animal-level fraction of eligible sampled DMS PV-positive profiles associated with a surrounding WFA-positive net. Retain the numerator and denominator, and keep PV density and WFA net density separate. DLS remains an optional regional comparison, subject to sample and tissue feasibility.

Briones and colleagues found increased DMS PV-with-net proportions across four mouse models of repetitive behavior. This supports the proposal's regional association hypothesis, while the task and species differences remain substantial. It does not predict our rats' results or make PV labeling a functional assay. [Briones et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9616293/)

The existing working prediction is a positive association between learned-place checking and DMS PV/WFA proportion, tested two-sided. It must be attached to the validated checking outcome. A relationship with placement-platform occupancy would answer a different behavioral question and should be identified as such.

## Plan B: GFAP if PV/WFA are unavailable

The fallback preserves the behavioral question and changes the anatomical endpoint. A candidate question is: **Do individual differences in learned-place checking relate to DMS GFAP labeling?**

A candidate endpoint is GFAP-positive area fraction within consistently sampled DMS regions. The pilot must determine whether that quantity is repeatable and suitable in the available tissue; it is not yet a finalized endpoint or a guarantee of feasibility. Region, image acquisition, background handling, thresholding, and animal-level aggregation need to be fixed before testing behavioral associations. No directional GFAP prediction is established by the present data.

GFAP labeling cannot, by itself, provide a census of all astrocytes, measure calcium activity or glutamate handling, or establish a pathological/reactive state. The interpretation must stay attached to the measured marker. The authors' consensus guidance specifically cautions against inferring astrocyte numbers or function from GFAP changes alone. [Escartin et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8007081/)

Choose the fallback because of documented availability or assay feasibility, before inspecting behavior–histology significance. If activated, record the revised anatomical aim and analysis in the proposal/committee materials. GFAP would be the selected anatomical arm, not a mandatory addition to a successful PV/WFA study. If its pilot also fails, that is a technical limitation; a valid anatomical thesis result cannot be assumed.

## Cohort implications

**SP1** offers existing behavior and fixed brains for an archival feasibility assessment. First link rat IDs to actual specimen IDs and document fixation, storage, later behavioral exposures, and section availability. A staining pilot can evaluate technical quality without selecting animals for an attractive biological association. Fixed tissue alone does not establish quantitative comparability across rats.

**KAC** supplies the same animals' standard- and raised-depth checking sessions and acquisition records. Because the animals are alive, collection timing and subsequent experiences can be documented prospectively. This does not retroactively counterbalance the completed behavioral order. Terminal tissue would reflect the animal's full history through collection, rather than provide a separate anatomical measurement for each checking day.

The primary anatomical cohort and session-level behavioral summary should be selected from scientific fit and matched-sample feasibility before examining anatomical associations. Current evidence does not establish that either cohort has sufficient usable matched tissue.

## Next analysis that advances the thesis

1. **Recover the learned-location geometry.** Use training footage or verified zone definitions to identify its actual center and extent separately for each camera/session. “Opposite quadrant” identifies the relationship but is insufficient to infer exact coordinates by mirroring the placement point. Save overlays showing both regions.
2. **Build a destination and return event table.** Retain animal, session, event frame, time, visited region, first visit versus reentry, departure episode, and tracking status. Fix reentry separation and minimum-duration rules against video before examining histology.
3. **Validate events independently.** Include different animals, both sexes, both cohorts, easy and difficult footage, non-initiators, and long gaps. Report detection agreement and timing error. Mask anatomical results during behavioral scoring.
4. **Keep missing observation distinct from zero behavior.** Known non-initiators can contribute zero visits. A gap can conceal a visit or departure; it must not manufacture an entry or certify zero events. Postdeparture destination measures remain undefined without an observed departure. Return/first-event times require censoring rules. Dividing by observed time alone does not remove behavior-dependent tracking bias.
5. **Join behavior to the specimen inventory.** Use cohort plus animal ID as the key. Retain one biological subject per rat; sections and cells improve its estimate without increasing the independent animal count. Keep both KAC sessions linked to the same rat.
6. **Limit the association analysis.** Plot individual data by sex and cohort, retain continuous variation, and prespecify a small adjustment set compatible with the matched sample. A pooled relationship could reflect sex or cohort separation. Avoid selecting the behavioral endpoint or stain because its p value is smallest.

The tail-while-swimming idea can contribute to movement strategy as a secondary pilot. The highest-priority behavioral gap for this thesis is the learned-place destination and return measure. The current on-platform tail results are a separate observation.

## SfN and thesis wording

For SfN, the defensible descriptive emphasis is the separation between remaining on the placement platform and initiating swimming, including the sex difference at standard depth. Report occupancy uncertainty and label pose-derived behaviors as exploratory.

For the thesis, the added question is how those departures are directed and repeated with respect to the learned place, and whether individual variation relates to the selected anatomical endpoint. The current analyses alone cannot establish memory-system dominance, causal PV/net or astrocyte control, or clinical compulsion. Functional DLS evidence from habitual lever pressing motivates the broader circuitry discussion while remaining distinct from this DMS anatomical association. [O'Hare et al.](https://elifesciences.org/articles/26231)

## Source and quality notes

- The latest dashboard's “never left” counts are calculated as no observed departure. Four sessions have no detected departure plus some missing time: SP1 rat 1, KAC Day 6 rats 20 and 29, and Day 8 rat 10. Preserve the uncertainty or resolve it against video; do not quietly promote these to fully observed stayers.
- The handwritten-note comparison has 18 resolved agreements and 2 unknowns out of 20 explicit Day 6 notes, and 29 agreements and 1 unknown out of 30 Day 8 notes. Unknown is not demonstrated disagreement.
- Placement frames remain near the start of some clips. Time-zero and onset-sensitive measures need frame-level checking. The existing three note/timing discrepancies remain documented.
- All 91 cleaned caches and source-file hashes, 45 report asset links, nine fully decoded videos, and six gap-handling regression tests passed integrity checks. Fifteen figure images and sampled demo frames were reviewed. This is not exhaustive behavioral annotation.
- The standalone site/archive and private published preview predate this thesis update. No external deployment was changed.

### Working sources

- [Existing thesis proposal](<C:/Users/kobeq/Documents/Kobe Research/Thesis/THESIS PROPOSAL.md>) and [current decisions](<C:/Users/kobeq/Documents/Kobe Research/Thesis/Current decisions.md>).
- [Behavioral codebook](<C:/Users/kobeq/Documents/Kobe Research/Methods/Behavioral codebook.md>), [analysis plan](<C:/Users/kobeq/Documents/Kobe Research/Methods/Analysis plan.md>), and [histology plan](<C:/Users/kobeq/Documents/Kobe Research/Methods/Histology plan.md>).
- [Astrocyte rationale](<C:/Users/kobeq/Documents/Kobe Research/Thesis/Astrocytes and the thesis.md>) and [claim/source guide](<C:/Users/kobeq/Documents/Kobe Research/Thesis/Claim and source guide.md>). The new Plan B decision above takes precedence over their earlier scope.
- [SP1 sex/weight record](<C:/Users/kobeq/Documents/2025/data/Rat weights 12-30-24.xlsx>).
- [Cleaned report](<C:/Users/kobeq/Documents/KAC database/analysis/dlc_cleaned/report.html>), [per-rat measures](<C:/Users/kobeq/Documents/KAC database/analysis/dlc_cleaned/results/per_rat_measures.csv>), and [verification record](<C:/Users/kobeq/Documents/KAC database/analysis/dlc_cleaned/results/verification.json>).
- [Corrected KAC acquisition report](<C:/Users/kobeq/Documents/KAC database/analysis/updated_anymaze/analysis/REPORT.md>). Its mixed-model results and the traditional workbook's ANOVA results are different analyses; retain the model label with every p value.

This is a targeted alignment and source check, not a systematic literature review or a full audit of every bibliography entry. Original thesis documents were read and preserved.
