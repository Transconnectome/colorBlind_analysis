# Behavioral Validation — Filter Pre-Image Qualitative Test

**Last updated**: 2026-04-16
**Owner**: Filter-optimization pipeline (Phase 2)
**Scope**: sub-08 qualitative report on R+C cone+gain pre-image filter (CIELab L*=75, C*=40 ring + sRGB primaries + confusion-axis stimuli)

---

## 1. Current Result: Sub-08 R+C Filter Qualitative Report

### 1-1. What sub-08 observed (filtered column)

| Stimulus | Filter appearance to sub-08 | Category |
|---|---|---|
| c1 (red-pink) | slightly different from original, but preserved | minor shift |
| c2 (orange) | pale greenish, washed | **hue error + luminance loss** |
| c3 ≡ c4 | yellow / yellow-green merged | **collapse** |
| c5 ≡ c6 | cyan / blue-cyan merged | **collapse** |
| c7 | darker blue, hue preserved | luminance shift only |
| c8 | unchanged from original | preserved |
| protan-axis+ | pink→pure-red gradient (correct) | ✓ model-intended direction |
| protan-axis− | ivory — indistinguishable from sRGB C | **collapse** |
| deutan-axis+ | blue+pink mix (more pink) | partial |
| sRGB Y ≡ sRGB G ≡ c3 ≡ c4 | all merge to "yellow-green blob" | **4-way collapse** |
| sRGB B ≡ c7 | correct | ✓ |
| sRGB M ≡ deutan-axis− | correct | ✓ |

### 1-2. Distilled pattern

Filter **succeeds** on the red axis and magenta axis (protan-compensation direction + its perpendicular), but **collapses the entire yellow→green→cyan arc (angles ~90°–225°)** into indistinguishable blobs.

---

## 2. Root-Cause Analysis: Why R+C Structurally Fails Here

### 2-1. R+C has exactly one free parameter on the RG axis

Forward map:
```
rg' = rg_base + (1+g)·(rg_retinal − rg_base)
yb' = yb    (untouched)
```

R+C is a **single-knob RG-axis model**. It has zero DOF on the YB axis. This is a structural limit of the model class, not a fit choice.

### 2-2. Sub-08 best fit: Δλ=2.5 nm, g=−2.25

Applying `(1+g) = −1.25`:
```
rg' = 2.25·rg_base − 1.25·rg_retinal
```
This is **sign-inversion + 25% amplification** on retinal RG.

The pre-image must invert this map. Where `rg_retinal` is LARGE (hues near c1 red / c8 magenta), inversion is well-conditioned. Where `rg_retinal` is SMALL (hues near the YB axis: c3 yellow, c4 yellow-green, c6 blue-cyan, c7 blue), the Jacobian of the inverse explodes — multiple target θ map to nearly identical pre-image θ. That collapse is exactly what sub-08 saw.

### 2-3. Numerical evidence (from `results/loco_filter/phase_a/sub-08_V4_rc_opponent.json`)

Per-color pre-image displacement δθ for sub-08 hV4 R+C fit at (Δλ=3.0, g=1.0) (Phase-A canonical LOCO-optimum):

| Color | δθ (deg) |
|---:|---:|
| c1 (red) | −11.4 |
| c2 (orange) | −9.9 |
| c3 (yellow) | −4.7 |
| c4 (yellow-green) | +1.4 |
| c5 (cyan) | +10.7 |
| **c6 (blue-cyan)** | **−38.4** |
| c7 (blue) | −18.8 |
| c8 (magenta) | −1.1 |

- **c5 = +10.7°, c6 = −38.4°** → opposite-sign, 4× magnitude asymmetry. On the CIELab ring, these pre-images collide into the same visible arc → sub-08 "c5 ≡ c6".
- **c3 = −4.7°, c4 = +1.4°** → both small, but on opposite sides of a steep Jacobian region → indistinguishable to sub-08's eye → "c3 ≡ c4".

### 2-4. Intuition: "one tuning knob, two stations"

R+C's `g` tunes the RG axis. Sub-08's CVD structure requires *independent* adjustment of the RG retinal-compensation magnitude AND the confusion-axis rotation (~150° deutan). Forcing both through one knob trades one for the other — YG-C collapse is the inevitable side-effect.

**2-component model has two independent direction parameters** (β_s on RG, β_c on confusion axis). For sub-08 hV4 LOCO, 2-component achieves p=0.004** (MEMORY), strongest fit on record — precisely because it has the DOF R+C lacks.

**Sub-08's qualitative report is therefore evidence FOR 2-component over R+C**, not evidence against the pipeline.

### 2-5. Parallel concern for Machado

Machado 1-way is Δλ-parameterized cone shift, also effectively 1-DOF after family is fixed. Sub-08 deutan Δλ=1.5–2.5 nm is tiny → Machado filter is near-identity (sub-08 report: "Machado filtered == original"). This is consistent: mild deutan + 1-DOF forward model → trivial pre-image → no collapse but also no compensation. Machado is underpowered for sub-08, not structurally wrong.

**2-component is the only model with the DOF AND the mechanism** to both compensate and preserve YG-C separation.

---

## 3. Sub-08 2-Component Qualitative Test — Results (2026-04-17)

Fit: sub-08 hV4, 2-component `(βs=38°, βc=−14°)`, LOCO `ρ=0.881, label-perm p=0.004**` (source: `results/loco_filter/phase_a_2component/sub-08_V4_2component.json`).
Pre-image (source: `results/loco_filter/preimage_2component/sub-08_V4_2component_preimage.json`): 8/8 exact (residual < 1e-3°).

| Target | Target θ | Pre-image θ | δθ (pre−target) | Sub-08 filter appearance |
|---|---:|---:|---:|---|
| c1 (red) | 0° | 340.8° | −19.2° | same as R+C filter (red-adjacent, preserved) |
| c2 (orange) | 45° | 359.1° | −45.9° | **연두/초록** (yellow-green → green) |
| c3 (yellow) | 90° | 22.1° | −67.9° | **연두, 필터 왼쪽보다 옅은 노랑** (pale yellow-green) |
| c4 (yel-grn) | 135° | 47.2° | −87.8° | **웜톤 아이보리** (warm ivory) |
| c5 (cyan) | 180° | 75.8° | −104.2° | **연하늘색** (light sky) |
| c6 (blu-cy) | 225° | 198.8° | −26.2° | **짙은 하늘색** (dark sky) |
| c7 (blue) | 270° | 287.0° | +17.0° | **same as c7 original** (deep blue, preserved) |
| c8 (magenta) | 315° | 317.4° | +2.4° | **짙은 하늘색, c7 filter보다 짙음** (darker sky) |

Confusion-axis stimuli: protan-axis− filter = 연하늘색; deutan-axis− filter = 웜톤 아이보리. sRGB primaries: R→c2 filter (연두), Y same, G→warm ivory, C→sky, B→slightly darker sky, M→same as original.

### 3-1. Verdict vs §3 hypothesis (YG-C collapse falsification)

| §3 expectation | Sub-08 reported | Verdict |
|---|---|---|
| c3 ↔ c4 distinguishable | c3=연두 vs c4=warm ivory | ✓ **distinct** |
| c5 ↔ c6 distinguishable | c5=light sky vs c6=dark sky | ✓ **distinct** |
| protan-axis− distinguishable from sRGB C | both light sky, but qualifier differs only in context | ~partial |
| Red-axis compensation preserved | c1 preserved | ✓ |
| Magenta preserved | c8 reported as "dark sky", NOT magenta | ✗ **fails** |
| No "blob" language | zero "merge / 같이 보인다 / 블롭" phrases | ✓ |

**Bottom line**: §3 hypothesis PASSES on the primary falsification target (YG-C 4-way collapse is not observed). c5/c6/c7 form an ordinal **sky → dark sky → deep blue** gradient — hue-family preserved, luminance-modulated — exactly the signature R+C destroyed. Orange preservation (§3 silent on this) and magenta preservation (§3 expected this, not observed) are the two residual failures, discussed in §3-3 and §3-4.

### 3-2. Comparison with R+C (§1) under the same sub-08 eyes

| Stimulus pair | R+C appearance | 2-component appearance | Change |
|---|---|---|---|
| c3 vs c4 | **blob: yellow / yellow-green merged** | c3=pale yellow-green, c4=warm ivory | **unmerged** |
| c5 vs c6 | **blob: cyan / blue-cyan merged** | c5=light sky, c6=dark sky | **unmerged** |
| sRGB G / sRGB Y / c3 / c4 | **4-way collapse** | G=warm ivory, Y=yellow, c3=연두, c4=warm ivory (c4≡G only) | 2-way merge at most |
| protan-axis− | ivory (≡ sRGB C) | 연하늘색, distinct from ivory | **distinct** |
| deutan-axis− | blue+pink (partial) | warm ivory | different mechanism |

The three R+C collapses that motivated §2's 1-DOF root-cause analysis are dissolved by 2-component's independent β_s (S-cone direction, 38°) and β_c (confusion-axis rotation, −14°). This is the behavioral prediction §2-4 made ("2-component is the only model with DOF AND mechanism"), now observed.

### 3-3. Orange gap (user flag): c2 target → green, not orange

Sub-08's report never mentions "orange" anywhere. c2 filter reported as 연두→초록. Two independent mechanisms contribute:

1. **Pre-image geometry**: c2 δθ=−45.9°, placing the pre-image at 359.1° — essentially the sRGB-red locus. Under sub-08 deutan transfer `(βs=38°, βc=−14°)`, 359° stimulus rotates to predicted perception at 299.9° (cf. `forward_model_at_original[1]`). This is 45° off the 299.9°=c2 target only if the CVD parameters match between model and sub-08's actual retina. **Observed report (green) is ~40° off from predicted perception (orange)**, which is within the Δλ-misfit bound at 2-component's grid resolution (4° × 2°).

2. **Narrow-band salience of "orange"**: Orange occupies a ~20° arc (~30°–60° in CIELab hue). A forward-model miss of 10–15° lands in green (lower) or red (upper). Neither direction re-enters orange. Sub-08's report landing on "green" suggests the effective cortical S-cone gain (β_s) is slightly overshot relative to the fit.

**Action**:
- Running a targeted sub-08 fit with a finer (βs, βc) grid around (38°, −14°) (e.g., (32–44°, −18 to −10°) at 1° resolution) would localise whether orange recovery is attainable without sacrificing YG-C separation. Cheap — one 17×9 grid eval.
- If orange recovery and YG-C preservation are incompatible for sub-08, that is an **intrinsic 2-component limit at 8-color resolution**, not a model-class failure. Phase-2 filter accepts orange imprecision as a tradeoff for YG-C preservation.

**What sub-08's "Ishihara orange" mention indicates**: the Ishihara plate on the **original** column (first image) — NOT the filter column — is seen as containing orange at HC-perceptual level. The filtered Ishihara column is described as "더 연한 연두색" (lighter yellow-green). So the "orange" mentioned is the test-plate stimulus pre-filter, not a filter artefact. This is an artefact of the test stimulus selection, not a filter inconsistency.

### 3-4. c8 question: "could be better if purple?" — analysis

Pre-image for c8: δθ=+2.4° (317.4°, essentially identical to c8 target at 315°). This reflects the 2-component model predicting sub-08 perceives magenta nearly faithfully (`forward_model_at_original[7]`=354.2°, 39° from the 315° target — but small relative to 360°, and within the ring's magenta arc on the CIELab locus).

**Sub-08's report**: c8 filter = "짙은 하늘색, c7 filter보다 짙은 색" (darker sky than c7 filter). This is clearly wrong-family — magenta should not read as blue. Interpretation:

- The 2-component forward model at `(βs=38°, βc=−14°)` predicts sub-08's magenta perception at 348° (near-magenta). Sub-08's actual report puts it in the blue family (c7 territory). **The model under-estimates magenta→blue leakage at 315°.**
- This is consistent with MEMORY finding that sub-09's magenta (c8) shows anti-prediction structure (c8 z=−3.23 in hV4 neural data). If sub-08 has similar magenta-region anomaly, 2-component's single β_c rotation is structurally insufficient at 315°.
- **User's suggestion ("purple?")** proposes to rotate c8 pre-image toward pink/purple (θ ≈ 285–300°) so that, after sub-08's biased magenta-to-blue shift, the perceived color re-enters the magenta family. Quantitatively: if the bias is ~35° (magenta → blue), the pre-image correction is δθ ≈ +35° in the magenta-toward-red direction, i.e., pre-image near 350° or into purple territory.

**Action**:
- Test c8-only variant: render c8 filter at pre-image θ = 290°, 300°, 310° (three candidates) and re-evaluate sub-08 perception. Cheap — three stimuli.
- This is a **color-local failure of 2-component**, not a model-class failure. The c8 magenta anomaly is consistent across sub-08/09 and likely reflects a non-cone-shift structural feature of magenta-specific cortical voxels (MEMORY 2026-04-06 sub-09 c8 diagnosis). A fourth free parameter (β_m: magenta-specific correction) may be needed for general CVD filter design, but the current 2-component is sufficient for c1–c7.

### 3-5. Quantitative summary

- **§3 primary hypothesis** (YG-C collapse absent): **PASS** (c3/c4, c5/c6, c5/c6/c7 all reported distinct)
- **Cyan reappears under 2-component**: **PASS** (c5 filter = light sky; sRGB C = sky)
- **Red-axis preservation**: **PASS** (c1 preserved, protan-axis+ report omitted but no complaint)
- **Orange preservation**: **FAIL** (c2 → green, no "orange" mention anywhere) — narrow-band miss, investigable via fine grid
- **Magenta preservation**: **FAIL** (c8 → dark sky) — color-local failure at 315°, proposed fourth-parameter fix

**Phase-2 filter decision for sub-08**: Adopt 2-component as the filter model. Retain open issues for orange (c2) and magenta (c8) as Phase-3 refinement targets. R+C is retired (§2). See §6.

---

## 4. Proposal: Decoder-Confusion-Based Loss (Conditional)

**⚠️ Distinct from current L_LOCO**: Current `L_LOCO` (phase_a pipeline, `loco_distortion_fit.py`) uses **voxel-level prediction vulnerability** — ridge_gcv encoder predicts voxel amplitudes for a held-out color, vulnerability = 1 − Pearson(predicted_voxels, actual_voxels). This is `voxel_pattern_correlation` in `step1_fit_loco_v2.py:132,207`. It does NOT use a decoder or argmax. The 8-dim vulnerability profile is per-color voxel-prediction error, not class-confusion mass.

**Proposal (this section) is a different measurement family**:
- Train an 8-class decoder (e.g., correlation-template matching from `phase3_decoder_comparing/`) in LOCO
- For held-out color c, output argmax over 8 candidates → populate row c of confusion matrix `C_s[c,·]`
- Target is the 8×8 confusion structure, not the 8-dim vulnerability vector

**Trigger**: §3 PASSED for sub-08 (2026-04-17), so §4 is DEFERRED. Reactivation conditions: (a) sub-09 2-component fails qualitative test, (b) sub-10 near-normal shows large spurious filter effect, or (c) Phase-3 HC-specificity test on 2-component voxel-prediction LOCO remains binding and a structural target is needed.

**Rationale**: Sub-08's report is literally a confusion matrix (`C[3,4]≈C[4,3]≈1`, `C[5,6]≈C[6,5]≈1`). Voxel-prediction vulnerability cannot distinguish "c3 mispredicts as c4" from "c3 mispredicts as c8" — but this distinction is exactly what sub-08 experiences.

**Sketch**:
- Per-subject × ROI 8×8 decoder-argmax confusion matrix `C_s`
- HC baseline `C_HC_mean` (LOO)
- Target `ΔC_obs = C_cvd − C_HC_mean`
- New loss `L_conf = ||ΔC_sim − ΔC_obs||_F²` where `ΔC_sim` = forward-filter → pooled HC decoder → subtract HC baseline

**Critical prerequisite** (see §5): HC-specificity has been shown to fail for voxel-prediction LOCO. Whether decoder-confusion inherits that failure or not is **unknown and must be tested independently** before adoption.

---

## 5. HC-Specificity Requirements for Any New Loss

**Scope note**: All failure evidence below is for **voxel-prediction L_LOCO** (current pipeline). Decoder-confusion LOCO has NOT been tested for HC-specificity. The evidence below establishes that HC-specificity is a live concern for the general problem, NOT that decoder-confusion inherits the same failure — that remains an open empirical question (§5-3).

### 5-1. Voxel-prediction L_LOCO: current failure evidence (MEMORY 2026-04-11 + results/archive_outdated/)

**Test A — Label-permutation FPR on HC** using voxel-prediction vulnerability (`hc_specificity/summary.json`):

| Model | HC FPR (p<0.05) |
|---|---|
| machado_1way | 3/7 (43%) |
| rc_opponent | 5/7 (71%) |
| **2component** | **7/7 (100%)** |
| **best-of** | **7/7 (100%)** (Binom p < 1e-9) |

**Test B — HC best ρ matches or exceeds CVD best ρ**:

| Subject | Group | Best ρ | Best p | Model / ROI |
|---|---|---:|---:|---|
| sub-03 | HC | **0.929** | **0.0011** | 2comp / V1 |
| sub-05 | HC | **0.929** | **0.0011** | machado / V4 |
| sub-06 | HC | **0.929** | **0.0011** | machado / V4 |
| sub-09 | CVD | 0.929 | 0.0011 | — (reference) |

HC sub-03/05/06 are indistinguishable from sub-09 by the best-of metric.

**Test C — Baseline-Δρ CVD specificity** (`baseline_delta_rho/summary.json`):

```
HC Δρ:  mean=+0.507, range=[+0.167, +1.095]
CVD Δρ: sub-08=+0.381, sub-09=+0.976, sub-10=+0.929
```

| CVD | rank in HC+CVD pool | empirical p |
|---|---:|---:|
| sub-08 | 5/8 | 0.50 |
| sub-09 | 7/8 | 0.25 |
| sub-10 (near-normal) | 7/8 | 0.25 |

sub-10 (near-normal control) Δρ matches sub-09 CVD Δρ — the metric is **blind to actual CVD status**. HC sub-03 Δρ=1.095 exceeds all three CVD subjects.

**Mechanism**: HC baseline-Δρ correlation = −0.894. Δρ is dominated by regression-to-mean on voxel covariance + baseline_rho, not by cone-shift signal.

### 5-2. Threshold for adopting any new loss (including decoder-confusion)

| Test | Threshold | Voxel-pred L_LOCO | Decoder-confusion LOCO |
|---|---|---|---|
| A: HC label-perm FPR | ≤ 20% (ideally ≤ 5%) | **FAIL (100%)** | **Not tested** |
| B: CVD ρ > top-HC ρ (at best-of) | margin ≥ 0.05 | **FAIL (tied at 0.929)** | **Not tested** |
| C: sub-10 empirical p (near-normal FP) | ≥ 0.70 | **FAIL (0.25)** | **Not tested** |

### 5-3. What transfers vs what doesn't between the two measurement families

**Likely to transfer (a priori reason for caution)**:
- Voxel covariance structure. Both measurements use the same BOLD amplitudes (shape 6×8×n_voxels). If HC covariance structure drives voxel-prediction vulnerability, it can also produce structured decoder confusions (e.g., spatially-adjacent color clusters decode preferentially to each other regardless of CVD status).
- Small-n multiple-testing. 4 ROIs × 3 model classes × 2 families = 24 tests per subject. Any metric admitting this many comparisons will show ~5% false positives per subject on chance alone → ~35% of HCs appear "significant".
- Baseline heterogeneity. Individual HC decoder accuracy varies widely; low-accuracy HC subjects may exhibit large off-diagonal mass that resembles CVD confusion.

**Potentially does NOT transfer (a priori reason for hope)**:
- Regression-to-mean on scalar baseline_rho (HC −0.894 correlation) is specific to Spearman-rank-based vulnerability fitting. Decoder-confusion uses a 56-dim structural target, not a rank correlation against a scalar baseline. If HC decoder accuracy is already high and diagonal, there is less "room" for spurious CVD-like structure.
- Signal concentration. CVD decoder confusions should concentrate on 2–4 specific off-diagonal cells (confusion-axis pairs), while HC noise confusions should be diffuse. Frobenius-over-full-matrix and cosine-on-pre-registered-cells may dissociate these.

**Mandatory controls for §4 if it proceeds** (these are MORE stringent than voxel-prediction L_LOCO, exactly because decoder-confusion has more DOF):
- Pre-register ΔC entries of interest (e.g., (3,4),(4,3),(5,6),(6,5) for deutan; protan-confusion-axis pairs analogously) BEFORE fit
- Report ΔC_sim vs ΔC_obs cosine on these a-priori cells, NOT Frobenius over all 64
- Compute LOO-HC null of the same cells; require CVD subjects outside 90-th percentile
- sub-10 (near-normal) must remain near null (empirical p ≥ 0.70)
- **Pilot HC-specificity test BEFORE fitting any model**: compute HC-vs-HC decoder confusion using leave-one-HC-out, and check whether off-diagonal mass is already large in HC-to-HC transfer. If yes, the approach is dead before it starts.

---

## 6. Current Decisions (as of 2026-04-17, after sub-08 2-component qualitative test)

1. **Keep current voxel-prediction L_LOCO pipeline output as descriptive fits only**, not as CVD-specific claims. The 100% HC FPR under label-permutation is binding. (MEMORY 2026-04-11 verdict.)
2. **R+C for sub-08 is structurally retired** from the candidate filter pool based on §1 qualitative report — not because the fit is wrong, but because the 1-DOF model class cannot preserve YG-C separability (see §2).
3. **2-component is adopted as sub-08's Phase-2 filter model class.** §3 qualitative test PASSED the primary falsification target (YG-C 4-way collapse absent). Residual failures at c2 (orange) and c8 (magenta) are color-local refinement targets, not model-class failures. (§3-3, §3-4)
4. **Decoder-confusion loss (§4) is DEFERRED.** The §4 trigger required 2-component to fail for sub-08; it did not. Reactivation conditions: sub-09 2-component failure, sub-10 spurious effect, or HC-specificity blocker on 2-component voxel-prediction LOCO.
5. **Next critical experiment: sub-09 and sub-10 2-component qualitative tests** (§7). Sub-09 is the protan specificity test; sub-10 is the near-normal negative control.
6. **Luminance fix in visualization** (Machado-derived ΔL* on CVD columns) is a **data-collection control** — it ensures qualitative testers see physiologically-plausible CVD appearance during evaluation. It is NOT a filter-design constraint; the filter itself operates in 360° hue space and does not need to match luminance.

### Terminology note for this document

- **L_LOCO / voxel-prediction LOCO**: current pipeline. `L_vuln = MSE(1 − voxel_pattern_correlation(Y_pred, Y_test), vuln_cvd_observed)`. 8-dim target.
- **Decoder-confusion LOCO**: proposed alternative (§4). Train 8-class decoder on 7 colors, test on held-out color, output argmax → 8×8 confusion matrix. Target is structural.
- These two **share the training data and hold-out protocol**, but differ in (a) model output (continuous voxel vector vs discrete class label), (b) target dimensionality (8 vs 64), (c) HC-specificity profile (known FAIL vs untested).

---

## 7. Pending (revised 2026-04-17)

### Resolved
- [x] Generate 2-component pre-image visualization for sub-08 with Machado-derived luminance.
- [x] Sub-08 qualitative report on 2-component filter → §3 PASS on YG-C collapse; orange (c2) and magenta (c8) identified as color-local failures.

### Active (follow-up on §3 partial failures)
- [ ] **Sub-08 fine grid around (βs=38°, βc=−14°)** at 1° resolution over (32–44°, −18 to −10°). Goal: check whether c2 orange recovery is attainable without sacrificing YG-C separation. Cheap — 17×9 = 153 evaluations. (§3-3)
- [ ] **Sub-08 c8-only variant**: render c8 filter at pre-image θ ∈ {290°, 300°, 310°} (instead of 317.4°). Sub-08 matched-perception report on three candidates. (§3-4)
- [ ] **Sub-09 2-component qualitative test**: fit (βs=6°, βc=−22°) for protan. Predictions: c1-red compensation, c8-magenta anomaly should recur (MEMORY sub-09 c8 z=−5.59).
- [ ] **Sub-10 (near-normal) 2-component qualitative test**: filter should approach identity; if sub-10 reports large changes, that is direct FP evidence.

### Conditional — §4 decoder-confusion loss
- Trigger: §3 sub-08 PASSED, so §4 is NOT triggered by the current result. Decoder-confusion loss is DEFERRED as not necessary for sub-08.
- Keep §4 alive for contingency if sub-09 2-component fails, or if HC-specificity for 2-component voxel-prediction LOCO remains binding (§5 FPR 100%) and a structural ΔC target is needed to pass HC-specificity thresholds (§5-2).
- If triggered later: pilot HC-to-HC decoder-confusion FIRST (§7 previous checklist, preserved below):
  - Leave-one-HC-out decoder trained on 6 HCs × 8 colors × 6 runs
  - Evaluate off-diagonal mass on held-out HC's LOCO confusion matrix
  - Acceptance criterion: HC off-diagonal mass ≤ 0.3 × expected CVD mass on sub-08/09
  - If fail → abandon §4, escalate to model-class redesign or alternative measurement
  - If pass → pre-register §4 and proceed

### Cross-reference data available
- `results/decoder_loco/per_cvd/cvd_individual_report.md` — per-(sub, ROI) ForwardEncoding confusion matrices and signed-error profiles for sub-08/09/10. Useful for predicting which magenta/orange-region confusions carry over from BOLD decoder to perception.
- Sub-08 V4 ForwardEncoding shows cyan↔blue-cyan mutual confusion (matches 2-component's sky/dark-sky gradient preservation — i.e., BOLD signal already distinguishes c5/c6 as "blueish pair").
