# Revision Report (Re-check) — methods_streamlined.tex — 2026-05-11
Scope: Full file (all sections), post-revision verification pass
Rules version: ~/.claude/writing/academic_writing_rules.md (Parts II–V)
Pre-draft anchor: docs/PAPER/pre_draft_2026-05-10.md (Methods ¶1–8)
Predecessor report: revision_report_2026-05-11.md (10 issues)

---

## 1. Reverse Outline (current state)

### §Data collection

- L8 (¶Participants): Twelve volunteers recruited; HC ($n=7$) and CVD ($n=2$; deutan + protan) classified by 14-plate Ishihara; 3 excluded; CVD results framed as Crawford & Howell single-case demonstrations.
- L12 (¶fMRI stimuli): Eight CIELab-equidistant hues plus a gray filler at fixed $L^*=75$ and chroma $=40$.
- L14 (¶fMRI task): A modified RSVP K-detection task maintained attention while stimuli (1.5 s each) were presented in Neurodesign-optimized order across six runs per session.
- L16 (¶Filter sessions): CVD participants completed a second session contrasting Windows-filter, personalized-filter, and original stimuli against HC originals.
- L18 (¶MRI acquisition): 3T Siemens Cima.X, twenty-four oblique slices perpendicular to calcarine sulcus, 1.5 s TR, 2 mm isotropic.

### §Preprocessing and response estimation

- L24 (¶Spatial normalization): BIDS conversion + ezBIDS de-facing; MI-based BOLD–T1w coregistration via FreeSurfer mri\_coreg, then FLIRT + FNIRT to MNI 2 mm.
- L28 (¶ROI definition): Bilateral V1/V2/V3/hV4 from Wang atlas thresholded at 50 % and intersected with each subject's BOLD mask.
- L32 (¶FIR HRF + GLM stage 1): An FIR model recovers an ROI-specific HRF data-drivenly; voxels in the top 50 % HRF-explained-variance are retained.
- L34 (¶GLM stage 2): The ROI-specific HRF (and its temporal derivative) is convolved with per-color regressors to estimate one amplitude per voxel × color × run.
- L38 (¶Procrustes alignment): Run-wise voxel amplitude matrices were aligned to run 1 by an orthogonal Procrustes transform (no scaling); validation reported in supplement.

### §Functional alignment and shared representational space

- L50 (¶SRM training): SRM (BrainIAK) was fitted on HC data only; CVD subjects were projected into the fixed HC space via $W_{\text{CVD}} = UV^T$ (no re-estimation of $S$).
- L64 (¶RDM analysis): CVD–HC element-wise RDM differences were tested by 95 % bootstrap CI (1,000 iterations) over correlation-distance RDMs in the SRM common space; per-ROI $k$ stated.

### §Color decoding and voxel response prediction model

- L70 (¶Channel basis): Six half-wave-rectified squared-cosine channels constitute a complete basis for any hue-selective tuning curve.
- L72 (¶Forward model): Voxel responses are modeled as $B = WC$; $W$ is fitted by ridge with GCV, enabling decoding (Eq. 6a) and prediction (Eq. 6b).
- L91 (¶LORO): LORO holds out one run per fold to test whether colors are reliably discriminated from voxel responses.
- L93 (¶LOCO): LOCO holds out all six runs of one color to test interpolation to unobserved hues.
- L95 (¶Evaluation): Both schemes are scored by Pearson $r$ between predicted and observed voxel patterns; LOCO permutation null = 1,000 random color-label shuffles.

### §Filter design

- L99 (¶Two-component model): CVD distortion was modeled as $\delta\theta = \beta_s\cos(h-90\degree) + \beta_c\cos(h-\theta_{\text{conf}})$ in Stockman opponent space; $\beta_s$ and $\beta_c$ optimized by 26 × 51 grid search to maximize hV4 LOCO Pearson $r$, with permutation significance testing.
- L109 (¶Pre-image): The personalized stimulus-space filter was the inverse $T^{-1}$, computed numerically by dense-grid initialization + Brent refinement; round-trip error verified $<0.001\degree$ for all 8 hues × 2 CVD subjects.

### §Behavioral-neural concordance

- L115 (¶Tasks intro): Participants completed two behavioral tasks under fMRI-matched display settings.
- L117 (¶JND staircase): JND thresholds were estimated by 1-up/1-down adaptive staircases on eight RDM-deviation-selected color pairs.
- L119 (¶8-AFC): An 8-AFC task assessed categorical color identification against the eight fMRI stimuli.

### §Reproducibility

- L123: Python 3.10 stack, fixed seed=42, public GitHub code, anonymized data on request.

---

### Drift vs. intended outline (pre_draft_2026-05-10.md §Methods)

| Pre-draft | Present in tex | Status |
|---|---|---|
| ¶1 Participants + 8 hues, 6 runs | L8 + L12–L14 | ✓ Covered |
| ¶2 Single-trial amplitude estimation | L32–34 (FIR + GLM) | ✓ Covered (FIR + GLM substituted for GLMsingle in pre-draft language; same role) |
| ¶3 HC-only SRM, CVD projection | L50–62 | ✓ Covered |
| ¶4 LOCO, hV4 primary gate ROI | L91–95 + L107 ("hV4 LOCO Pearson $r$" used as fitting criterion) | ✓ Covered (hV4 designation now implicit via Filter design fitting target) |
| ¶5 SRM RDM, HC–CVD comparison | L64 | ✓ Covered |
| **¶6 2-component model (β_s + β_c)** | **L99–107** | **✓ NOW PRESENT** |
| **¶7 Pre-image derivation, 8-hue δ vectors** | **L109** | **✓ NOW PRESENT** |
| ¶8 JND behavioral validation | L113–119 | ✓ Structure present |

No structural drift remaining.

---

## 2. §19 Vocabulary

### Tier A — Banned (0 true hits)

- L16: "the first session" — ordinal use, false positive. **PASS**
- L32: "first extracting" — ordinal, false positive. **PASS**
- L93: "novel hues not seen during training" — describes the LOCO procedure; not a paper-novelty claim. **PASS**

### Tier B — Untestable verbs (1 hit, carryover)

- **L38**: "To improve cross-run consistency in voxel response patterns within each participant, voxel response amplitudes were aligned across runs using Procrustes alignment" — **UNRESOLVED**. The previous report flagged this opener (Minor #2 of the priority list). The numeric result (r=0.54→0.71) was correctly removed and the validation was deferred to supplement, but the **"To improve…"** opener remains. Strictly §19B + §8 (motivation as topic sentence). Suggested: "Voxel response amplitudes were aligned across runs using Procrustes alignment to reduce measurement noise while preserving color geometry." This is a Minor (style) issue, not Fatal.

### Tier C — Vague (0 unmitigated hits)

- L32: previous "more accurate HRF" claim is **gone**. Replaced by "This data-driven approach avoids the shape assumptions of canonical HRF models, instead deriving a response function directly from the data." Operationalized by what is avoided + what is recovered. **PASS**.
- L64: "robust to amplitude scaling and additive offsets" — operationalized inline. **PASS**.
- L64, L117: "significant deviation/difference" — bootstrap CI procedure described at L64; selection criterion at L117 is procedural. **PASS**.

### Tier D — Self-praise (0 hits)

No Tier D violations.

---

## 3. §20 Citations

### Method origin (1 hit cleared)

- **L107 (formerly L111)**: Brettel 1997 citation has been **removed**. Now cites `\cite{machado2009}` for "Opponent-hue angles $h$ were derived from CIELab coordinates using the Machado simulation framework at zero spectral shift". Machado et al. 2009 is the correct origin for the cone-fundamentals-based simulation framework. **PASS**.
- L107 also cites `\cite{emery2021}` for S-cone-locus behavioral evidence and `\cite{tregillus2021}` for V2/V3 cortical compensation — both are primary-paper-to-specific-claim matches. **PASS**.

### General-claim ↔ specific-cite mismatches

None identified.

### Specific-claim ↔ review mismatches

None identified.

### Citation density

- L32: `\citeNP{dale1999, brouwer2009, brouwer2013}` — three roles (GLM origin, paradigm, application). **PASS**.
- L50: `\citeNP{chen2015}` for SRM origin + `\cite{haxby2011, guntupalli2016}` for hyperalignment lineage. **PASS**.

No 5+ citation stacks.

---

## 4. §26 Checklist

### Reverse outline
- [✓] One sentence per paragraph as written
- [✓] Matches §1 Step 5 outline (¶6 + ¶7 now present; no remaining drift)
- [✓] No paragraph requires two sentences to summarize

### Claims
- [N/A] Central contribution — assessed at paper level, not Methods alone
- [✓] Numeric Δ in Methods has baseline + dataset (e.g., voxel counts at L28, L32; pre-image error bound L109)
- [✓] No Tier A banned vocabulary
- [✗] Untestable verb opener: L38 "To improve…" (§19B). MINOR.
- [✓] No vague adjective without operationalization
- [✓] No self-praise

### Citations
- [✓] General → review / specific → primary alignment correct throughout
- [✓] Method origin correct (Machado 2009 for opponent-hue framework; Brettel 1997 removed)
- [✓] No 5+ citation stacks

### Structure
- [✓] Each paragraph has one role
- [✓] Topic sentences are main claims (L115 "Participants completed two behavioral tasks under display settings matching the fMRI experiment." replaces the prior "To examine…" rationale opener)
- [✓] Pronouns unambiguous
- [✓] HC/CVD terminology consistent
- [✓] Observation / interpretation / implication separated (no results in Methods — r=0.54→0.71 deferred to supplement)
- [✓] No single-sentence orphan paragraph (former L91 ¶CV-intro is gone; LORO/LOCO subsection now opens directly with the LORO definition at L91)

### Section-by-section
- [N/A] Abstract / Introduction not in this file
- [⚠️] Methods order vs. expected Results order: §Filter design (L97) precedes §Behavioral-neural concordance (L111). The pre-draft Results order is Fig 2 (LOCO) → Fig 3 (RDM) → Fig 4 (2-comp) → Fig 5 (filter) → Fig 6 (JND). Methods §Filter design before §Behavioral-neural concordance therefore matches Results order. **PASS** (this resolves the prior report's ⚠️ flag).
- [✓] No results in Methods (r=0.54→0.71 removed; voxel counts and pre-image accuracy bound are descriptive, not analytic results)
- [✓] §Filter design now contains both the 2-component model (L99–107) and the pre-image derivation (L109)
- [✓] Reproducibility section complete

### Content inconsistency (carryover — not a style rule)

- **L8 participant count**: still reads "Twelve volunteers … Three excluded" → 9 = HC 7 + CVD 2. Project documentation (`CLAUDE.md` §6, `pre_draft_2026-05-10.md` lines 42/76/105, `MEMORY.md`) treats sub-10 (deutan mild / normal control) as included for specificity analyses. The Methods file does not mention sub-10. Two consistent options:
  1. If sub-10 is in the analyses → "Thirteen volunteers… HC $n=7$, CVD $n=3$ (one deuteranopic mild / normal control included for specificity)".
  2. If sub-10 is reported only as a control elsewhere → add one sentence: "An additional participant with mild deuteranomaly (sub-10) was treated as a normal-vision control for specificity analyses and is not counted in the CVD group."

  This is **not flagged as a style violation**, but it remains an unresolved factual inconsistency between the Methods file and the rest of the project. The author should pick option 1 or 2.

### Final pass
- [✓] Filler removed (no "in order to", "due to the fact that", "it is worth noting")
- [✓] Negatives positive-equivalent (no "not harmful"-class issues)
- [✓] Nominalizations mostly verbs ("estimation"/"alignment" used as concept names, acceptable)
- [✓] Active voice where clearer; passive used appropriately for procedural descriptions

---

## 5. Verification of Prior Report's Specific Concerns

| Prior issue | Status |
|---|---|
| Fatal #1: ¶6 2-component model absent | **✓ FIXED** — now at L99–107 with full equation, parameter ranges (β_s ∈ [0°,50°], β_c ∈ [-50°,50°]), 26×51 grid, Stockman confusion-axis values, citations to Emery 2021 + Tregillus 2021 |
| Fatal #2: ¶7 pre-image derivation absent | **✓ FIXED** — now at L109 with dense-grid + Brent's method procedure and round-trip accuracy bound (<0.001°) for all 8 hues × 2 subjects |
| Serious #1: r=0.54→0.71 result in Methods (L38) | **✓ FIXED** — value removed; replaced with "Alignment was validated by mean pairwise Pearson correlation across all 15 run-pair combinations (reported in Supplementary Materials)" |
| Serious #2: L103 "To examine…" topic sentence | **✓ FIXED** — L115 now opens "Participants completed two behavioral tasks under display settings matching the fMRI experiment." |
| Serious #3: L32 "more accurate HRF" Tier C | **✓ FIXED** — replaced by "avoids the shape assumptions of canonical HRF models, instead deriving a response function directly from the data" |
| Serious #4: L111 Brettel 1997 citation | **✓ FIXED** — replaced with Machado 2009 (correct origin for the simulation framework) |
| Serious #5: Participant count (sub-10) | **✗ UNRESOLVED** — file still says "Twelve / 3 excluded / HC 7 + CVD 2". Pick option 1 or 2 above. |
| Minor #1: L91 single-sentence orphan paragraph | **✓ FIXED** — old L91 ¶CV-intro deleted; subsection now opens directly with the LORO definition at L91 |
| Minor #2: L38 "improve" Tier B opener | **✗ UNRESOLVED** — opener still "To improve cross-run consistency…" |
| Minor #3: Methods/Behavioral order vs Results | **✓ FIXED** — §Filter design (L97) now precedes §Behavioral-neural concordance (L111), matching Fig 5 → Fig 6 Results order |

### New violations introduced by the edits

None observed. Vocabulary scan, citation audit, and structure check find no new issues created by the revision pass.

---

## 6. Priority Summary

- **Fatal: 0**
- **Serious: 1**
  - L8 participant count vs. project documentation (sub-10 status). Factual reconciliation, not style.
- **Minor: 1**
  - L38 "To improve cross-run consistency…" opener (§19B + §8). Style refinement.

§26 checklist: **all style/structure/citation items PASS**. Two unresolved items above are (a) one factual inconsistency (sub-10 inclusion) and (b) one Minor style nit (L38 opener). Neither blocks submission, but the sub-10 reconciliation should be settled before submission so the participant section matches the Results sample.

If both unresolved items are addressed (one factual decision + one sentence rewrite), §26 checklist will be all-PASS — section ready for submission.
