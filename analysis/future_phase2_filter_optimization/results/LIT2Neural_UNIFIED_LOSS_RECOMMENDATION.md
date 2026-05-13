# Unified Neural-Only Loss — Recommendation

**Date**: 2026-05-13
**Status**: Empirical sweep complete (sub-08, sub-09)
**Scripts**: `scripts/neural_only_deep_sweep.py`, `scripts/neural_only_unified_loss.py`
**Output dir**: `results/neural_only_unified/`

---

## 1. Unified Loss Formulation (identical for both subjects)

```
L(β_s, β_c | subject) =
      w_s · ((β_s − β_s^{V1ΔRDM}[subject]) / σ_s)²
    + w_c · ((β_c − β_c^{V4LOCO2c}[subject]) / σ_c)²
    + λ  · L_RDM_cos(vuln_sim, vuln_cvd)            ← V4 landscape, per-cell

Defaults: w_s = w_c = 1, σ_s = 10°, σ_c = 15°, λ = 0.5
```

**Same formulation, per-subject neural extraction**: the anchors β_s^{V1ΔRDM} and
β_c^{V4LOCO2c} are computed from each subject's own data using identical pipelines
(V1 ΔRDM bootstrap + V4 LOCO 2-component fit).

---

## 2. Empirical Result

| Subject | Anchors (β_s^{V1ΔRDM}, β_c^{V4LOCO2c}) | Argmin (β_s, β_c) | P2a | exact | dist→P2a-max | ‖β‖ |
|---|---|---|---:|---:|---:|---:|
| sub-08 deutan | (+20°, −14°) | (20°, −14°) | 0.263 | 1/8 | **48.4°** | 24.4° |
| sub-09 protan | (+23°, −22°) | (22°, −22°) | **0.887** | 6/8 | **2.8°** | 31.1° |

### Hyperparameter stability (sub-09)
Argmin is **invariant** to σ_s ∈ {5, 10, 20}, σ_c ∈ {8, 15, 25}, λ ∈ {0, 0.5, 2},
and w_s/w_c weights (β_s+β_c anchors dominate). Removing one anchor degrades P2a
(β_s only → 0.787; β_c only → 0.675; shape only → 0.400).

### Hyperparameter stability (sub-08)
Argmin is identically (20, −14) across all settings. **No hyperparameter** in
the unified formulation steers sub-08 toward the P2a-max region (26, +34).

---

## 3. Per-Component Neural Source + Literature Anchor

| Component | Neural source | Subject value | Literature anchor | Citation |
|---|---|---|---|---|
| β_s anchor | V1 ΔRDM bootstrap on voxel-space RDM differences (HC mean − subject); β_s decomposed via 2-component basis | sub-08: 20°<br>sub-09: 23° | Emery 2021 NT→AT B-Y rotation ≈ 21.4°; Machado 2009 severity | Tregillus et al. 2020 (fMRI compensation, paperId `0a8595382d…`); Webster et al. 2010 (paperId `aae36c2977…`); Parkes et al. 2009 V1 hue MVPA (paperId `a9f4083c09…`, n=157 cits) |
| β_c anchor | V4 LOCO 2-component fit on hV4 ridge_gcv decoder failures; β_c = cortical confusion-axis amplitude | sub-08: −14°<br>sub-09: −22° | Brettel, Viénot & Mollon 1997 confusion-axis sign | Brettel et al. 1997 (paperId `bd7a98c1ea…`, n=412 cits); Bannert & Bartels 2018 V4 perceptual hub (paperId `9370270…`, n=44 cits) |
| L_RDM_cos (shape) | V4 landscape per-cell vuln_sim ↔ vuln_cvd RDM cosine (scale-invariant) | (per-cell) | Kriegeskorte 2008 RSA framework; Brouwer & Heeger 2009 V4 color decoding | Brouwer & Heeger 2009 (paperId `7777f6e5a1…`, n=540 cits) |

All three components are **neural-derivable from this study's own data**. No
literature constants enter the loss.

---

## 4. Sub-09 — Literature Validation (P2a-max recovered)

Argmin (22°, −22°) lands at distance **2.8°** from P2a-max (24°, −20°) and meets
**all three** literature anchors simultaneously:

| Anchor | Recovered value | Literature target | Δ |
|---|---|---|---|
| Emery β_s | 22° | 21.4° | 0.6° |
| Tregillus norm (overshoot) | ‖β‖=31.1° | 28° (21.4×1.3) | +3.3° |
| Brettel protan β_c sign | −22° (negative) | negative for protan (OLD axis 150°) | sign OK |

**Interpretation**: For sub-09 protan, V1 ΔRDM (cone-shift level) and V4 LOCO
(cortical confusion axis) jointly recover Brettel/Emery/Tregillus geometry
without any literature constants in the loss. Sub-09 is a textbook case where
neural signal → literature-anchored filter → P2a-restoration target converge.

---

## 5. Sub-08 — Honest Dissociation (P2a-max NOT recovered)

Argmin (20°, −14°) is **48.4°** from P2a-max (26°, +34°). The P2a-max is
unreachable from any neural-only formulation because:

| Neural source for sub-08 | β_c estimate |
|---|---|
| V1 ΔRDM bootstrap | −18° (CI excl. 0) |
| V4 LOCO 2-component | −14° |
| V1 LOCO 2-component | −14° |
| **All three agree: β_c < 0.** | |
| P2a-max behavioral target | **β_c = +34** (opposite sign) |

**This is a real, reproducible neural–verbal-report dissociation.** It is not
solved by:
- changing σ_s/σ_c/λ/weights (verified above)
- switching axis convention (Stockman 150° vs CIELab 175.7° — both give β_c<0)
- switching ROI (V1 and V4 agree)
- switching bootstrap measure (ΔRDM and LOCO 2-comp agree)

### Possible explanations to investigate further
1. **Verbal-report noise/anchoring**: sub-08's `SUB08_ORIGINAL_HC_EQUIV` was
   derived from verbal "이것은 분홍색이다" reports under specific instructions.
   Verbal reports may carry semantic biases distinct from neural representation.
2. **Post-V4 cortical processing**: sub-08 may have additional transformation
   downstream of V4 not captured by V1/V4 LOCO/ΔRDM.
3. **Axis convention 180° flip**: would change β_c sign for sub-08; needs
   independent test using fresh axis derivation.
4. **Atypical CVD profile**: sub-08 may be a non-standard deutan whose
   neural signature does not follow the canonical Brettel deuteranopia confusion-axis sign.

---

## 6. Recommended Reporting Strategy

### A. Primary claim (strong)
> "A unified neural-only loss combining V1 ΔRDM β_s anchor, V4 LOCO 2-component
> β_c anchor, and V4 RDM-cosine shape consistency recovers the P2a-restoration
> filter target within 3° for sub-09 protan, with simultaneous convergence to
> Emery (β_s), Tregillus (‖β‖), and Brettel (β_c sign) literature predictions.
> No literature constants enter the loss; all three components are independently
> extracted from each subject's neural data using identical pipelines."

### B. Secondary finding (honest)
> "The same unified loss applied to sub-08 deutan lands 48° from the P2a-max
> target, with β_c sign opposing the behavioral target. This neural–behavioral
> dissociation is consistent across V1/V4 ROIs and ΔRDM/LOCO methods, and
> suggests a post-V4 transformation or atypical confusion-axis structure for
> this subject. Further targeted experiments (per §5 candidates 1–4) needed."

### C. Why this beats the Bayesian framework
- **Bayesian** (α=0.3, w_Emery=0.5, w_Tregillus=0.5, w_Brettel=0.3) inserts
  literature constants directly into the loss. Sub-08 BEST (22, +18) is
  literature-pulled, not neurally-supported (Brettel prior overrides V1/V4
  evidence). Risk: literature anchoring can mask real neural dissociation.
- **Unified neural-only** (this proposal) reports the neural ground truth.
  When neural converges with literature (sub-09), both are validated. When
  they diverge (sub-08), the divergence is itself a finding rather than a
  forcing target.

---

## 7. Caveats / Open issues

1. **V1 ΔRDM β_s for sub-09 has CI (sub-09 β_s=23° [2°, 36°])** — bootstrap CI
   wide. Anchor is a point estimate; loss uses point estimate, not CI weighting.
2. **V4 LOCO 2-comp β_c for sub-09 CI not in MEMORY** — needs explicit
   re-extraction with bootstrap CI for full Bayesian-equivalent reporting.
3. **σ_s=10°, σ_c=15°, λ=0.5 hyperparameters** chosen by amplitude-matching
   convention; not learned. Sensitivity to these is empirically null at the
   neural anchor (verified §3). Defensible as standard quadratic-anchor form.
4. **L_RDM_cos λ=0.5** is contributing essentially nothing at the anchor
   (sub-08 dist invariant; sub-09 dist invariant). Could be set to 0 with no
   change in argmin. Kept for shape-consistency reporting only.

---

## 8. Next experimental steps

| Step | Goal | Cost |
|---|---|---|
| (a) Bootstrap V4 LOCO 2-comp β_c CI on sub-08, sub-09 — confirm sign stability | Strengthen anchor reliability | 1 day |
| (b) Axis 180° flip test on sub-08 — re-extract β_c under both axis polarities, check Brettel-consistent solution exists | Resolve possible sign-convention artifact | half day |
| (c) Sub-08 c8-only variant fit — does isolating magenta resolve dissociation? | Localize dissociation to specific colors | half day |
| (d) Bayesian-vs-unified specificity comparison via HC-permutation null | Confirm unified loss is at least as specific | 1 day |
| (e) Independent psychophysics for sub-08 — measure P2a directly w/o verbal report | Resolve behavioral target source | weeks |

Recommended execution order: **(a) → (b) → (d)** before any new Bayesian
parameter tuning. Steps (c) and (e) are slower follow-ups.

---

## References (Semantic Scholar paperIds)

- Brettel H, Viénot F, Mollon JD (1997). *Computerized simulation of color
  appearance for dichromats.* J Opt Soc Am A. paperId `bd7a98c1eaf3d7f83335629e80040138f0eecfc4`
- Brouwer GJ, Heeger DJ (2009). *Decoding and Reconstructing Color from Responses
  in Human Visual Cortex.* J Neurosci. paperId `7777f6e5a13aaf197b89964723d2ec8eb87cc200`
- Parkes L, Marsman J, Oxley DC, Goulermas JY, Wuerger S (2009). *Multivoxel
  fMRI analysis of color tuning in human primary visual cortex.* J Vis. paperId `a9f4083c09025f06be964d134cf7c672dc3871d4`
- Webster M, Juricevic I, McDermott K (2010). *Simulations of adaptation and
  color appearance in observers with varying spectral sensitivity.* paperId `aae36c29779796f7f93baad667441a76648c6c2e`
- Bannert M, Bartels A (2018). *Human V4 Activity Patterns Predict Behavioral
  Performance in Imagery of Object Color.* J Neurosci. paperId `93702704ab3f43bf88427627e3f5a9f9c2714519`
- Tregillus KEM, Isherwood ZJ, Vanston JE, Engel S, MacLeod D, Kuriki I, Webster M (2020).
  *Color compensation in anomalous trichromats assessed with fMRI.* Curr Biol. paperId `0a8595382de8f3ed776e62577749905c443ad99e`
- Basim F, Goddard E, Yang Y, Webster MA (2025). *Color contrast adaptation
  and compensation in color deficiencies.* paperId `f4b253bb6e1325aa655b08f2d3b01b9b7581cfa6`
- Shimakura H, Sakata K (2022). *Color Compensatory Mechanism of Chromatic
  Adaptation at the Cortical Level.* paperId `13b03df6d99737d37c3888b417d6ccab402ea96c`
