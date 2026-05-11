# Revision Report — methods_streamlined.tex — 2026-05-11
Scope: Full file (all sections)
Rules version: ~/.claude/writing/academic_writing_rules.md (Parts II–V)
Pre-draft anchor: docs/PAPER/pre_draft_2026-05-10.md (Methods ¶1–8)

---

## 1. Reverse Outline

### §Data collection

- L8 (¶Participants): HC (n=7) and CVD (n=2; deutan, protan) were classified via Ishihara test; 3 of 12 excluded; all CVD results treated as individual case demonstrations.
- L12 (¶fMRI stimuli): Eight CIELab-equidistant hues plus gray were presented under equiluminant conditions at fixed L*=75 and chroma=40.
- L14 (¶fMRI task): An RSVP K-detection task maintained attention during color stimulation; 6 runs per session with optimized order and variable ISI.
- L16 (¶Filter sessions): CVD participants underwent a second session comparing original, Windows-filter, and optimized-filter stimuli; CVD responses compared to HC originals.
- L18 (¶MRI acquisition): 3T scanner with 24 occipital oblique slices, 1.5s TR, 2mm isotropic voxels.

### §Preprocessing and response estimation

- L24 (¶Spatial normalization): Functional images were coregistered to T1w using Mutual Information, then warped to MNI space via FSL FLIRT + FNIRT.
- L28 (¶ROI definition): Bilateral V1/V2/V3/hV4 ROIs were defined from Wang probabilistic atlas at 50% threshold, intersected with each subject's BOLD mask.
- L32 (¶HRF estimation): A FIR model estimated an ROI-specific HRF per subject, and the top-50%-variance voxels were retained for subsequent GLM.
- L34 (¶Response amplitudes): A GLM using the ROI-specific HRF convolved with color conditions estimated per-voxel amplitude for each color and run.
- L38 (¶Procrustes alignment): Within-subject Procrustes alignment improved cross-run consistency (r: 0.54 → 0.71) without distorting color geometry.

### §Functional alignment and shared representational space

- L50 (¶SRM training): SRM was trained on HC data only; CVD mapping matrices were derived by SVD projection into the fixed HC-derived common space.
- L63 (¶RDM analysis): CVD–HC RDM element-wise differences were tested via 95% bootstrap CI to identify color pairs with geometric deviation.

### §Color decoding and voxel response prediction model

- L70 (¶Channel basis): Six cosine-squared basis functions spanning the hue circle constitute a complete representation basis for any hue-selective tuning curve.
- L72 (¶Forward model + training): W was estimated by ridge regression with GCV, enabling cross-validated color decoding (Eq. 6a) and voxel prediction (Eq. 6b).
- L91 (¶CV intro): LORO and LOCO dissociate color discrimination from hue-space interpolation.
- L93 (¶LORO): LORO holds out one run per fold to assess whether individual colors are reliably discriminated.
- L95 (¶LOCO): LOCO holds out all runs of one color to assess whether the model interpolates to unobserved hues.
- L97 (¶Evaluation): Both CV schemes are evaluated by Pearson correlation; LORO = discriminability, LOCO = geometry intactness.

### §Behavioral-neural concordance

- L103 (¶Behavioral rationale + JND): JND thresholds were estimated for 8 color pairs selected from RDM deviation analysis using adaptive staircases.
- L107 (¶8-AFC): An 8-AFC task assessed categorical color identification.

### §Filter design

- L111 (¶Filter): CVD distortion was modeled as spectral shift Δλ; filter parameters optimized to minimize CVD–HC neural response discrepancy, validated by RDM and V4 LOCO.

### §Reproducibility

- L115: Python environment, fixed seeds, code/data availability.

---

### Drift vs. intended outline (pre_draft_2026-05-10.md §Methods)

| Pre-draft | Present in tex | Status |
|---|---|---|
| ¶1 Participants + 8 hues, 6 runs | L8 + L12–L14 | ✓ Covered (split into subsections) |
| ¶2 GLMsingle, shape (6,8,n_vox) | L32–34 (FIR+GLM, not GLMsingle) | ⚠️ Method changed to FIR+GLM — verify intentional |
| ¶3 HC-only SRM, CVD projection | L50–62 | ✓ Covered |
| ¶4 LOCO, hV4 primary gate ROI | L91–97 | ⚠️ LOCO method present, but hV4 identified as primary gate is not stated |
| ¶5 SRM RDM, HC–CVD comparison | L63–64 | ✓ Covered |
| ¶6 2-component model (β_s + β_c) | **ABSENT** | ✗ FATAL — core contribution missing |
| ¶7 Pre-image derivation, 8 hue δ vectors | **ABSENT** | ✗ FATAL — inverse filter calculation missing |
| ¶8 JND behavioral validation [PENDING] | L103–107 | ✓ Structure present |

---

## 2. §19 Vocabulary

### Tier A — Banned (0 true hits)

- L16: "the first session" — false positive; ordinal use, not novelty claim. **PASS**
- L32: "first extracting" — false positive; ordinal. **PASS**
- L95: "novel hues not seen during training" — **PASS** in context: describes the LOCO procedure, not a novelty claim about the study.

### Tier B — Untestable verbs (2 hits)

- **L38**: "To improve cross-run consistency" → §19B: filler motivation opener; replace with topic sentence stating what was done. E.g., "Voxel response amplitudes were aligned across runs using Procrustes alignment to reduce cross-run noise while preserving color geometry."
- **L103**: "To examine the relationship between geometrical deviations in neural representations and perceptual color discrimination" → §19B: "examine" untestable + §8: motivation is not the topic sentence. Replace: "Participants completed two behavioral tasks under fMRI-matched display conditions: a JND threshold task and an 8-AFC color identification task."

### Tier C — Vague (2 hits)

- **L32**: "recovers a more accurate HRF than canonical models" → §19C: "accurate" requires reference standard or error bound. No tolerance given. Fix: "recovers an HRF that explains more voxel variance than canonical models [cite comparison study, or qualify as 'in our limited-FOV acquisition']"
- **L64**: "capturing pattern similarity while being robust to amplitude scaling and additive offsets" → technically operationalized inline (specifies what robust means). **PASS**.
- **L64**: "significant deviation" (in "pairs exhibiting significant deviation") → §19C: in the context of bootstrap CIs, acceptable. **PASS** — procedure described.
- **L105**: "significant difference" (3×) → describes behavioral pair selection criterion. In context it refers to RDM bootstrap CI results. **PASS** if that analysis already reports CIs.

### Tier D — Self-praise (0 hits)

No Tier D violations found.

---

## 3. §20 Citations

### Method origin issues (1 suspect)

- **L111**: "cone-specific spectral shift (Δλ in nm) applied to the stimulus hue angles \cite{brettel1997}" → §20 suspect: Brettel et al. (1997) describe a dichromacy simulation model based on projection onto a confusion plane, not a spectral shift parameterized as Δλ nm. If the actual implementation follows Machado et al. (2009) or similar, that paper should be cited instead. Brettel 1997 is not the method origin for a Δλ parameterization.

### General-claim ↔ specific-cite mismatches (0 suspect)

No mismatches identified.

### Specific-claim ↔ review mismatches (0 suspect)

No mismatches identified.

### Citation density warnings

- L32: `\citeNP{dale1999, brouwer2009, brouwer2013}` — 3 citations for GLM. Acceptable; all three serve different roles (GLM origin, paradigm, application). **PASS**.

---

## 4. §26 Checklist

### Reverse outline
- [✓] Paragraphs summarizable in one sentence
- [✗] Match to §1 Step 5 outline: ¶6 (2-component model) and ¶7 (pre-image derivation) entirely absent from Filter design section
- [✓] No paragraph requires two sentences for summary — except L103 which mixes rationale and procedure

### Claims
- [N/A] Central contribution not assessable from Methods alone
- [✓] Numeric Δ in Methods (r=0.54→0.71 at L38) has before/after values and SD
- [✓] No Tier A banned vocabulary
- [✗] Untestable verbs: L38, L103 (§19B)
- [✗] Vague adjective: L32 "more accurate HRF" without bound (§19C)
- [✓] No self-praise

### Citations
- [✗] Method origin mismatch: L111 Brettel 1997 cited for Δλ spectral shift (§20)
- [✓] All other citations match claim specificity

### Structure
- [✓] Most paragraphs have one role
- [✗] L38 paragraph: reports empirical result (r=0.54→0.71) inside Methods — §23 violation ("No results in Methods")
- [✗] L103: topic sentence opens with motivation "To examine…" not main claim — §8 violation
- [✓] Pronouns unambiguous throughout
- [✓] HC/CVD terminology consistent
- [✗] L91 is a single-sentence paragraph (1 sentence ≠ paragraph with developed role); merge into L93 or expand

### Section-by-section
- [N/A] Abstract not present
- [N/A] Introduction not present
- [⚠️] Methods order vs. expected Results order: Filter design (L109) comes after Behavioral (L99); if Results presents filter before behavioral JND, order should be reversed
- [✗] §23 "No results in Methods": L38 reports r=0.54/0.71 — move to supplement or rephrase as "alignment was evaluated by computing mean pairwise Pearson correlation [supplement]"
- [✗] CRITICAL: §Filter design is 3 lines. Pre-draft ¶6 (2-component model β_s+β_c, 26×51 grid search) and ¶7 (pre-image derivation, err<0.001°) are completely absent
- [✓] Reproducibility section complete

### Content inconsistency (not a style rule — flagged separately)

- **L8 participant count**: "Twelve volunteers were recruited … Three excluded → n=9 total." But project data include HC sub-01–07 (n=7) + CVD sub-08, sub-09, sub-10 (n=3) = 10 subjects. If sub-10 was excluded, the draft should say so explicitly; if sub-10 was included, "Twelve" should be "Thirteen" and CVD n=2 should be n=3. Pre-draft explicitly includes sub-10 as deutan mild/normal control for specificity. **Verify and reconcile.**

---

## 5. Priority Summary

**Total issues: 10**
- **Fatal (2)**: 2-component model (¶6) and pre-image derivation (¶7) absent from Filter design — core contribution missing from Methods
- **Serious (5)**: L38 results in Methods; L103 §8+§19B; L32 §19C "accurate"; L111 Brettel 1997 citation mismatch; participant count inconsistency (sub-10)
- **Minor (3)**: L91 single-sentence orphan paragraph; L38 "improve" opener; Methods/behavioral section order vs Results order

**Recommended sequence:**

1. **Write Filter design ¶6–7** (2-component model + pre-image): β_s retinal shift, β_c cortical rotation, 26×51 grid search on hV4 LOCO, pre-image derivation (err<0.001°). This is the paper's primary contribution.
2. **Fix L111 citation**: Replace `\cite{brettel1997}` with Machado et al. 2009 (or correct original source for Δλ parameterization).
3. **Resolve participant count (L8)**: Determine sub-10 status; if included, change to "Thirteen volunteers" and CVD n=3.
4. **Move or cut L38 result**: r=0.54→0.71 is a result. Move to supplement, or reframe: "cross-run correlation was computed as a quality check (reported in supplement)."
5. **Fix L103 topic sentence**: Remove "To examine…" opener; start with what participants did.
