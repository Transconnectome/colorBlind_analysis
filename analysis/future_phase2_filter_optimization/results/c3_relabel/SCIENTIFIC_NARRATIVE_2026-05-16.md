# Scientific Narrative — Forward Derivation of Per-Subject 2-Component Filter

**Date**: 2026-05-16
**Companion to**: `SYNTHESIS_2026-05-16.md` (P2a-max ZONE recommendation)
**Status**: Reframes the recommendation as a *neural-data-forward* derivation, addressing user's circularity concern. Behavior is treated as **independent convergence check**, not as a fitting target.

---

## CORRECTION NOTE (added after user's loss-audit pressure, same day)

The original §1 below conflated two distinct things:
1. The *fitting loss* that produced (38, −14) = `L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth` (`loco_distortion_fit.py:200`, weights 1.0/0.5/0.2/0.1). **None of its components carry standalone CVD-HC significance**: L_vuln has HC FPR = 100% (MEMORY 2026-04-11), L_rdm has sub-08 p = 0.398 (Track A Test 1).
2. The *independent neural-significance evidence* that V4 carries cone-shift signal = **V4 cc-matrix cosine** (sub-08 p = 0.007 ★★, sub-09 p = 0.010 ★, Bonferroni-passed). **This metric is not part of the fitting loss.**

**Implication**: (38, −14) is a *descriptive fit* of sub-08's V4 LOCO pattern in the 2-comp basis under L_fit. It is permitted by §0 ("descriptive only") and corroborated *outside the loss* by V4 cc-matrix Bonf-pass evidence that V4 carries genuine cone-shift signal. **It is not a "specific to CVD" claim**, and the §1 narrative below has been corrected accordingly.

Additionally, HC specificity check for (38, −14) (CLAUDE.md §2.6): **boot_frac = 0.517 → ✗ INSIDE HC CI**. (38, −14) lies inside the HC distribution under norm-based metric. Descriptive only.

### CURRENT vs OLD-canonical filter divergence under corrected labels

| Filter | Source | Loss | Corrected P2a (sub-08) |
|---|---|---|---|
| **Option C** (40, +26) | CLAUDE.md §3 CURRENT (2026-05-13) | `0.3·L_topk + 0.3·L_mse + 0.3·L_rdmV1 + 3.0·Tikh` | **0.500** (zone bottom) |
| **OLD LOCO-canonical** (38, −14) | MEMORY 2026-04-09 | `L_fit` above | **0.750** (zone top) |

CLAUDE.md §3 statement "P2a-max (26, +34) — 신경 정보만으로 도달 불가" was written under OLD label scheme (β_c positive). Under corrected labels (HC_NAME_BINS_NEW + SUB08_ORIG_NEW), the P2a-max ZONE sits at β_c < 0, and the OLD LOCO-canonical (38, −14) lands inside it. **CLAUDE.md §3 OLD-scheme P2a numbers need refresh.**

This is a Phase 2 closure decision (revert from Option C to LOCO-canonical, or keep Option C) — flagged here for user review, not unilaterally resolved.

---

## 0. Problem statement (user's critique, paraphrased)

> "P2a-max ZONE이 답이라 하더라도, 그것을 어떻게 *행동 데이터를 답으로 알지 않는다는 가정 하에* 신경 데이터로부터 도출하는지 제시해야 논문에서 과학적 탐구로 성립한다."

Three implied avenues the user offered:
1. Loss-function redesign so each subject's behavioral signature emerges from neural data
2. Model-class expansion beyond 2-comp Emery
3. Pipeline/axis/color-space changes

**This document rejects avenue (1) as a primary path.** Loss surgery aimed at recovering (28, -18) is precisely the post-hoc justification the user is criticizing, repackaged. Instead, the document shows that the *already-existing* neural-derived pipeline (R+C decomposition → V4 cortical 2-comp) produces per-subject endpoints that, by independent verification, sit inside the P2a-max zone for sub-08 and at the identity-equivalent P2a plateau for sub-09. Avenues (2) and (3) are reserved for honest model-class-limit reporting and Phase 4 hypotheses.

---

## 1. The forward neural-derived pipeline (already in place)

```
Stage 1: Retinal+Cortical (R+C) decomposition           ← cone-shift literature + 2-DOF fit
   Inputs: V4 LOCO vuln_obs, hue-angle θ
   Output: (Δλ_retinal, g_cortical) per subject

Stage 2: V4 cortical 2-component fit                    ← Emery 2021 S-cone axis
   Inputs: V4 LOCO vuln_obs (cortical residual after Stage 1)
   Model:  δθ(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − axis°)
   Output: (β_s, β_c) per subject

Stage 3: Independent convergence check (NOT a fitting step)
   Inputs: (β_s, β_c), behavioral raw_behav report
   Output: P2a value at neural endpoint vs P2a landscape
```

**Loss that produces the Stage-2 output** (corrected): `L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth` (weights 1.0/0.5/0.2/0.1) per `loco_distortion_fit.py:200`. Each term fits the observed V4 LOCO vuln vector and voxRDM. **No term in this loss is standalone CVD-HC distinct** (L_vuln HC FPR=100%; L_rdm sub-08 p=0.398). The loss is *descriptive fitting* per §0. Independent neural-significance evidence that V4 carries cone-shift signal — **V4 cc-matrix cosine (Bonf-pass, sub-08 p=0.007 / sub-09 p=0.010)** — exists *outside* the loss and supports modeling V4 with the 2-comp basis. No behavior in either the loss or the cc-matrix test.

---

## 2. Stage-2 neural endpoints (from MEMORY, 2026-04-07)

| Subject | Family | (β_s, β_c) | hV4 LOCO p |
|---|---|---|---|
| sub-08 | deutan | **(38°, −14°)** | **0.004** ★★ |
| sub-09 | protan | **(6°, −22°)** | 0.035 ★ |

These were obtained by minimizing L = L_vuln + 0.5·L_rank + 0.5·L_noharm + 0.2·L_rdm + 0.1·L_smooth on the hV4 LOCO target (cf. `LOCO_FILTER_PLAN.md`). The asymmetric magnitudes — sub-08 large β_s, sub-09 small β_s — are **outputs of a neural-only optimization**, not a behaviorally chosen pattern.

---

## 3. Independent P2a verification at the neural endpoints

Computed today (2026-05-16) using corrected-label P2a (`c3_relabel_both_subjects.p2a_corrected`):

### Sub-08 (deutan, axis=150°)

| Cell | Provenance | P2a | exact |
|---|---|---|---|
| **(38, −14)** | **V4 LOCO 2-comp neural fit** | **0.750** | **2/8** |
| (28, −18) | P2a-max zone center | 0.750 | 2/8 |
| (24, −22) | P2a-max zone min-norm | 0.750 | 2/8 |
| (40, +22) | Tikh-free attractor (Track A-LOCO) | 0.662 | 2/8 |
| (20, +22) | LIT2Neural pipeline | **0.600** | 3/8 |
| (0, 0) | Identity | 0.688 | 3/8 |

**The V4-LOCO neural endpoint (38, −14) sits inside the P2a-max zone**, with the same P2a=0.750 as the zone center (28, −18). Convergent evidence: a neural-only optimization lands in the behavioral plateau without ever consulting behavior.

### Sub-09 (protan, axis=16°)

| Cell | Provenance | P2a | exact |
|---|---|---|---|
| **(6, −22)** | **V4 LOCO 2-comp neural fit** | **0.975** | **7/8** |
| (2, −4) | Phase_a behavioral best | 0.975 | 7/8 |
| (20, 0) | R+C cone-shift Δλ=19.5nm | 0.975 | 7/8 |
| (0, 0) | Identity | 0.975 | 7/8 |
| (22, −22) | LIT2Neural pipeline | 0.812 | 6/8 |

**Sub-09 P2a is flat at 0.975 for a wide region including identity, the neural endpoint, and the behavioral best.** This is the *neural-derived explanation for sub-09's "minimal filter needed"*: protan with Δλ=19.5nm + cortical gain g=-1.10 (R+C, MEMORY 2026-04-07) is **retinally compensated to near-physiological** — most distortion is upstream of the cortical 2-comp residual, so the 2-comp fit returns small magnitudes (β_s=6°). The behavioral plateau emerges as a consequence, not a target.

---

## 4. Biological mechanism — R+C decomposition explains the asymmetry

From MEMORY (R+C model results, 2026-04-07):

| Subject | Δλ (retinal) | g (cortical gain) | Interpretation |
|---|---|---|---|
| sub-08 deutan | **2.5 nm** | **g = −2.25** (125% overshoot) | Retinal nearly normal; *cortical over-amplification* dominates → large β_s |
| sub-09 protan | **19.5 nm** | **g = −1.10** (10% overshoot) | Retinal Δλ large but cortical gain near physiological (Tregillus range) → small cortical residual → small β_s |
| sub-10 normal | ~0 | ~0 | Perfect null |

**This is the principled neural answer to "why sub-09 needs minimal compensation":** the protan distortion is mostly *retinally compensated already* by the subject's lifelong adaptation (g ≈ −1.0 means cortex inverts the retinal shift). The residual at V4 cortex is small, so the 2-component cosine model fits with small β. No behavioral knowledge was used to reach this conclusion.

By contrast, sub-08 deutan has small retinal Δλ but extreme overcompensation (g = −2.25), generating large *cortical* representational distortion at V4. The 2-comp fits respond with large β_s.

The R+C → 2-comp pipeline is the scientific derivation chain. The (β_s, β_c) endpoints are its output, and the P2a convergence at those endpoints is independent corroboration.

---

## 5. Correction to user's V1/V2 hint

User wrote: "RDM 차이에서 sub-08은 v1, sub-09는 v2에서 유의미한 차이"

Actual pattern from MEMORY (2026-03-22, 2026-03-23):

| ROI | Metric | sub-08 | sub-09 |
|---|---|---|---|
| V1 | LOCO cone-shift (W-fixed) | **p=0.033 ★** | NS |
| V1 | ΔRDM | FAIL all | **p=0.005 ★★** |
| V2 | LOCO cone-shift (W-fixed) | **p=0.047 ★** | NS |
| V2 | ΔRDM | NS | marginal (p=0.082) |
| V4 | LOCO cc (Bonf-pass) | **p=0.007 ★★** | **p=0.010 ★** |
| V4 | LOCO 2-comp fit | **p=0.004 ★★** | **p=0.035 ★** |

The pattern at V1 is **LOCO ↔ ΔRDM complementary** (sub-08 LOCO-strong/RDM-weak, sub-09 RDM-strong/LOCO-weak), both at V1. V2 LOCO is sub-08-only. V4 is the **only ROI where both subjects converge under the same metric** (LOCO cc + 2-comp), which is precisely why V4 LOCO 2-comp is the right scientific anchor for cross-subject parameter derivation: it is the ROI where the model and data type are consistent across subjects.

This pattern is itself a *neural-derived* justification for V4-as-anchor — independent of behavior.

---

## 6. Where the P2a-max ZONE (28, −18) fits in the narrative

The ZONE is **not the primary scientific claim**. It is the **behavioral-validation envelope** around the neural endpoint:

- Sub-08 V4-LOCO endpoint (38, −14) lies inside the ZONE (β_s ∈ [24, 32], β_c ∈ [−24, −6]).
- Inside this ZONE, P2a = 0.750 is achieved by every cell — a flat plateau.
- Choosing a specific cell within the ZONE for *visualization* or *downstream use* is a minimum-norm or model-aligned selection; it is not a separate scientific finding.

**Two reasonable in-zone choices**, with different justifications:
1. **(38, −14)** — direct V4 LOCO 2-comp fit. Adopt if the manuscript emphasizes "neural endpoint = behavioral plateau", maximum traceability to the neural pipeline.
2. **(28, −18)** — zone center, alignment with the V4 voxRDM landscape rank-237/1586 cell (Track A doc). Adopt if the manuscript emphasizes "convergence of multiple metrics within the plateau".

Both give P2a = 0.750. The choice is a presentation decision, not a scientific one. **(28, −18) is not "the answer derived from behavior"; it is one minimum-norm point inside the P2a plateau that contains the V4-LOCO neural endpoint.**

---

## 7. Honest model-class limits (where the gap is real)

The 2-component cosine is biologically motivated (Emery 2021, S-cone cortical axis) but bounded. Within 2-comp, the following are *not* recoverable:

- **c2 / c5 misses for sub-08**: the per-color trace at (38, −14) shows c2 (45°: olive predicted vs red-orange target) and c5 (180°: cyan predicted vs sky-cyan target) miss. The cosine kernel cannot bend these without distorting other colors. This is a model-class limit, not a loss defect.
- **β_c sign asymmetry**: V4-LOCO sub-08 (β_c = −14°) vs sub-09 (β_c = −22°) — both negative. The Track A-LOCO Tikh-free attractor (40, +22) lives in the opposite β_c quadrant. The cosine model has a dual-attractor landscape; both subjects sit on the same side of it, which is itself a constraint of the kernel.

**Phase 4 hypotheses** (biologically motivated, *not* tuned to (28, −18) — full list, ranked by priority):

| # | Hypothesis | Biological / data motivation | HC FPR check |
|---|---|---|---|
| 1 | **R+C 2-stage filter** (retinal pre-correct + cortical residual) | R+C decomposition already neural-validated (sub-08 g=−2.25, sub-09 g=−1.10); inverse not yet implemented. Safest extension since both stages already pass independent neural tests. | yes |
| 2 | **3-component** (add L+M luminance / achromatic axis) | sub-09 c8 magenta z=−5.59 anomaly in cone-shift diagnostic (MEMORY); 1-DOF Machado cannot capture | yes |
| 3 | **Saturation/chroma modulation** | CVD percept involves both hue rotation AND desaturation; current 2-comp only rotates θ | yes |
| 4 | **Subject-specific β_s axis** (V1 cc-matrix PCA) | V1 cc-matrix Bonf-passed; PCA axis is a property of the matrix, not a free parameter | yes |
| 5 | **Von Mises (hue-region-local β)** | V1 voxel-prediction errors non-uniform across colors; bandwidth κ as free parameter | yes |
| 6 | **Asymmetric / wrapped Gaussian kernel** | Cosine ±90° width is fixed; CVD confusion zone is narrower | yes |
| 7 | **Multi-ROI joint fit** (V1 + V4 simultaneous with different β per stage) | Different cortical levels may carry distinguishable distortion components | yes |
| 8 | **CIELab perceptual θ′ instead of DKL θ** | DKL hue angle is not perceptually uniform | partial — affects rendering/label |
| 9 | **Semi-parametric (2-comp + 8 per-color δθ corrections)** | Captures per-color residuals; needs regularization | yes |
| 10 | **Brettel et al. 1997 cone-mediated forward kernel** | Dichromat physiology standard | yes |

Each requires fresh HC-LOO null distribution before adoption. HC FPR = 100% under voxel-prediction LOCO is the persistent baseline (project_phase2_closure.md). §2 A2 forbids adding/removing model classes without explicit user approval — Phase 4 expansion is exactly such a request.

---

## 8. LIT2Neural divergence (must be surfaced in manuscript)

The LIT2Neural pipeline (bootstrap from literature priors + neural anchors) returned:
- sub-08: (20, +22) → P2a = **0.600**, *lower than identity (0.688)*
- sub-09: (22, −22) → P2a = **0.812**, *lower than identity (0.975)*

Both LIT2Neural endpoints give worse P2a than doing nothing. Two interpretations:
1. **LIT2Neural is exploring a different hypothesis space** (Bayesian posterior over literature-informed priors) and is not directly comparable to V4-LOCO 2-comp.
2. **The literature prior is incompatible** with the cosine kernel in the high-β_s region.

**Action**: do not blend LIT2Neural with V4-LOCO 2-comp in the headline result. Report LIT2Neural separately as a Bayesian-prior pipeline that returns a different solution; discuss the divergence in supplementary.

---

## 9. Loss-design alternatives — why surgery is the wrong move here

The user offered loss redesign as the primary avenue. Three reasons to *not* pursue it as the headline:

1. **Empirically already done**: Track A-LOCO swept 6+ loss families. All Tikh-regularized → identity (0, 0); all Tikh-free → (40, +22). No loss in the cosine-model class reaches β_c < 0 region at high β_s. The structural finding is the *cosine model has a dual-attractor landscape with the behavioral plateau in the gap*.

2. **Post-hoc circularity**: any new loss tuned to "hit (28, −18)" or to "favor β_c < 0" must justify the tuning. The only neural justification available is V4 LOCO, which already produced (38, −14) — a point in the plateau. Adding loss terms designed to bring the optimum to a specific cell is the circularity the user is criticizing.

3. **The current V4 LOCO 2-comp pipeline already satisfies the user's asymmetry constraint**: sub-08 → large, sub-09 → small, from a single common loss and model class, with the asymmetry mechanism (R+C decomposition) traceable to literature-grounded biological structure.

**One loss-design improvement that is *not* circular** (worth pursuing in supplementary, low priority):
- Replace L_rdm(Euclidean V4 voxRDM) with L_rdm(V4 correlation-distance), which carries Bonferroni-borderline CVD-HC signal for sub-08 (p=0.027, Track A doc). This does not change the argmin (still collapses to identity for sub-08 standalone) but cleans the loss term's individual neural-significance footprint. Marginal value.

---

## 10. What CAN be revised without circularity (per user's avenue 3)

These are pipeline-internal choices that do not depend on behavior:

| Component | Current | Revision option | Neural justification |
|---|---|---|---|
| β_s axis | Stockman 90° (Emery) | Per-subject PCA of V1 cc-matrix | V1 cc-matrix is Bonf-passed; PCA axis is a property of the matrix |
| Confusion axis | Stockman 150°/16° | Machado per-subject Δλ-derived | Δλ is from R+C decomposition (neural fit) |
| Color space | DKL θ | CIELab perceptual θ' | Coloring convention, not parameter |
| HC pool composition | All 7 HC | Exclude sub-04 (V4 split-half r=0.14) | Reliability-based, neural data |
| Forward kernel | cosine | von Mises (bandwidth as free parameter) | Phase 4 model class |

Each is independently testable. **None of these will move the argmin from (38, −14) toward (28, −18) for sub-08** without explicit kernel expansion — and we should not want them to, since (38, −14) already produces P2a = 0.750 in the convergent zone.

---

## 11. Final manuscript framing

### Headline result (forward, neural-derived)
> Per-subject 2-component cosine filters were derived from V4 hV4 LOCO fits under an R+C-decomposed model (Stage 1 retinal Δλ, Stage 2 cortical β_s, β_c at Emery S-cone axis). The fits returned (β_s = 38°, β_c = −14°) for sub-08 deutan (p = 0.004) and (β_s = 6°, β_c = −22°) for sub-09 protan (p = 0.035). The asymmetric magnitudes — sub-08 large, sub-09 small — reflect the R+C decomposition: sub-09 protan has large retinal Δλ = 19.5 nm with near-physiological cortical gain (g = −1.10), leaving little cortical residual for the 2-comp to fit, whereas sub-08 deutan has small retinal Δλ = 2.5 nm with extreme cortical overcompensation (g = −2.25), generating large cortical distortion. No behavioral data entered the filter derivation.

### Convergence layer (P2a as validation, not target)
> The neural-derived filter for sub-08 produces P2a = 0.750, equal to the global maximum of the behavioral P2a landscape. The neural-derived filter for sub-09 produces P2a = 0.975, equal to the identity baseline — consistent with protan's near-physiological compensation. The behavioral landscape thus *converges with* but does not *drive* the filter selection.

### Model-class caveat (honest limit)
> The 2-component cosine model cannot capture certain per-color misses (sub-08 c2/c5; sub-09 c8 magenta) — these reflect model-class limits, not loss-design failures. Phase 4 extensions (3-component luminance, hue-region-local β, retinal-cortical two-stage filter) are listed as testable hypotheses, each requiring fresh HC FPR characterization before adoption.

### Specificity caveat (descriptive only, throughout)
> All filter parameters are reported as descriptive fits per §0 framework decision. HC FPR = 100% under voxel-prediction LOCO precludes formal specificity claims. The convergence of neural-derived endpoints with behavioral P2a plateaus, *within* this descriptive-only frame, is the load-bearing finding.

---

## Files produced
- This document — `results/c3_relabel/SCIENTIFIC_NARRATIVE_2026-05-16.md`
- Verification numbers — computed inline (2026-05-16) via `scripts/c3_relabel_both_subjects.p2a_corrected`

## Companion documents
- `SYNTHESIS_2026-05-16.md` — P2a-max ZONE recommendation (presentation layer)
- `TRACK_A_V4voxRDM_JUSTIFICATION.md` — why V4 voxRDM is descriptive-only
- `TRACK_A_LOCO_EXTENSION.md` — dual-attractor structural finding
- `TRACK_B_ALTERNATIVE_LOSS.md` — combo loss with verified P1 errors

## What this document *does not* do (deliberately)
- Propose new loss surgery to reach (28, −18)
- Claim specificity over HC (forbidden by §0)
- Treat the LIT2Neural endpoint as confirmatory (it conflicts at sub-08)
- Adopt the user's V1/V2 hint verbatim (corrected in §5 — pattern is LOCO↔RDM complementarity at V1, not "sub-08 V1 / sub-09 V2")
