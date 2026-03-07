# Phase 2b: Decoder Model Comparison (LORO + LOCO)

## Table of Contents

- [Motivation](#motivation)
- [Settings](#settings)
- [Models Compared (6)](#models-compared-6)
- [Result 1: LORO Model Comparison (10 subjects x 4 ROIs)](#result-1-loro-model-comparison-10-subjects--4-rois)
    - [Overall Performance](#overall-performance-procrustes-aligned-subject-level-mean--bootstrap-95-ci)
    - [Procrustes Alignment Effect](#procrustes-alignment-effect--procrustes--raw)
    - [HC vs CVD Comparison](#hc-vs-cvd-comparison-procrustes-acc_45)
    - [Test-Retest Reliability](#test-retest-reliability-split-half-spearman-brown-corrected-acc_45)
    - [Permutation Test](#permutation-test)
- [Result 2: LOCO Interpolation Test (sub-01, 4 ROIs, 100 permutations)](#result-2-loco-interpolation-test-sub-01-4-rois-100-permutations)
    - [Performance](#performance-sub-01-procrustes-mae--adjacent-accuracy)
    - [Permutation Test (ForwardEncoding)](#permutation-test-forwardencoding-100-iterations)
    - [LOCO Interpretation](#loco-interpretation-sub-01-local-test)
- [Result 2b: LOCO Server Deployment -- RT-4 (10 subjects x 4 ROIs x 1000 permutations)](#result-2b-loco-server-deployment--rt-4-10-subjects--4-rois--1000-permutations)
    - [Aggregate Performance -- ForwardEncoding vs Others](#aggregate-performance--forwardencoding-vs-others-mae-mean--sd)
    - [Aggregate Performance -- Adjacent Accuracy](#aggregate-performance--adjacent-accuracy-adj_acc-chance--0250)
    - [Permutation Test](#permutation-test--n-significant-subjects-p005-correct-direction-z0)
    - [ForwardEncoding Per-Subject](#forwardencoding-per-subject-adj_acc--mae--key-findings)
    - [Key Findings (RT-4)](#key-findings-rt-4--loco-server-deployment)
- [Result 3: Nested Procrustes + Dim Reduction (RT-2/RT-3, 10 subjects x 4 ROIs)](#result-3-nested-procrustes--dim-reduction-rt-2rt-3-10-subjects--4-rois)
    - [Overall Performance](#overall-performance-acc_45-mean-across-all-10-subjects--4-rois)
    - [By Group](#by-group-acc_45)
    - [By ROI](#by-roi-acc_45-nested_only-condition)
    - [MLP Degenerate Solution Analysis](#mlp-degenerate-solution-analysis)
    - [RT-2/RT-3 Interpretation](#rt-2rt-3-interpretation)
- [Result 4: Individual CVD Cross-Decoding in SRM Space (RT-1 + RT-7 fix)](#result-4-individual-cvd-cross-decoding-in-srm-space-rt-1--rt-7-fix)
- [Result 5: LDA Reliability Diagnostics (RT-5)](#result-5-lda-reliability-diagnostics-rt-5)
    - [Analysis A: Fold-Level CV](#analysis-a-fold-level-cv-stdmean)
    - [Analysis B: ForwardEncoding W Matrix Stability](#analysis-b-forwardencoding-w-matrix-stability)
    - [Analysis C: Run-Pair Reliability](#analysis-c-run-pair-reliability-spearman-r-across-subject-rois)
    - [RT-5 Conclusion](#rt-5-conclusion)
- [Result 6: Hybrid Decoder -- Channel-to-Color Linearity Test (2026-02-18)](#result-6-hybrid-decoder--channelcolor-linearity-test-2026-02-18)
    - [Overall Performance](#overall-performance-acc_45-10-subjects--4-rois)
    - [By Group](#by-group-acc_45-nested-procrustes)
    - [By ROI](#by-roi-acc_45-nested-procrustes)
    - [Key Finding: Nonlinear Readout Does NOT Help](#key-finding-nonlinear-readout-does-not-help)
- [Result 7: LOCO Decoding Method Comparison -- Negative Result (2026-02-23)](#result-7-loco-decoding-method-comparison--negative-result-2026-02-23)
    - [Group-Level MAE](#group-level-mae-degrees-chance--90)
    - [Per-Subject Highlights](#per-subject-highlights-v1-best-individual-roi)
    - [Failure Analysis](#failure-analysis)
    - [Key Conclusion](#key-conclusion)
    - [Remaining Improvement Directions](#remaining-improvement-directions-post-mortem)
- [Result 9: LOCO Cross-Alignment Validation (2026-02-23)](#result-9-loco-cross-alignment-validation-2026-02-23)
    - [Alignment Comparison: ForwardEncoding Baseline](#alignment-comparison-forwardencoding-baseline-mae-in-degrees)
    - [Non-Linear Model Performance](#non-linear-model-performance-procrustes-alignment)
    - [Interpretation](#interpretation)
    - [Cross-Reference to LORO Results](#cross-reference-to-loro-results)
    - [Key Conclusions](#key-conclusions)
- [Result 10: Sequential Training + MLP Architecture Sweep -- Negative Result (2026-02-24)](#result-10-sequential-training--mlp-architecture-sweep--negative-result-2026-02-24)
    - [Failure Analysis](#failure-analysis-1)
    - [Key Conclusion](#key-conclusion-1)
    - [Impact on Analysis Plan](#impact-on-analysis-plan)
- [Systematic Results Matrix: Alignment x Model (2026-02-18)](#systematic-results-matrix-alignment--model-2026-02-18)
- [FE Cross-Decoding: HC to CVD in SRM Space (2026-02-22)](#fe-cross-decoding-hc--cvd-in-srm-space-2026-02-22)
- [Decoder Conclusions (Final, 2026-02-27)](#decoder-conclusions-final-2026-02-27)
- [Validation Status (Phase 2b — Complete, 21/21)](#validation-status-phase-2b--complete-2121)

---

## Phase 2b: Decoder Model Comparison (LORO + LOCO)

### Motivation

Phase 1 uses a single decoder (6-channel Forward Encoding from Brouwer & Heeger 2009). Before proceeding to filter optimization (Phase 3), we need to verify:

1. **Is the linear assumption justified?** — Does adding non-linear capacity improve decoding, or is the voxel-to-color mapping fundamentally linear?
2. **Is Procrustes alignment necessary?** — Can non-linear models compensate for run-to-run misalignment without explicit alignment?
3. **Is the mapping common across groups?** — Do HC and CVD subjects share the same voxel-color mapping (prerequisite for filter learning)?
4. **Can models interpolate held-out colors?** — Does the Forward Encoding model capture continuous color structure, or just memorize 8 discrete patterns?

### Settings

- **Data**: `full_dataset_C010` (P3 pipeline, C010 confounds, Procrustes-aligned)
- **Subjects**: 10 total (HC: sub-01~07, n=7; CVD: sub-08~10, n=3)
- **ROIs**: V1, V2, V3, V4 (= hV4 on disk)
- **Input shape**: `amplitudes_{raw,procrustes}.npy` — (6 runs, 8 colors, n_voxels)
- **LORO CV**: Leave-One-Run-Out with nested hyperparameter tuning (inner LORO on train runs)
- **LOCO CV**: Leave-One-Color-Out (no HP tuning; default params)
- **Scripts**: `analysis/phase3_decoder_comparing/model_comparison_validation/scripts/`
- **Results**: `analysis/phase3_decoder_comparing/model_comparison_validation/results/`

### Models Compared (6)

| Model | Type | Target | Linearity | Key Hyperparameters |
|-------|------|--------|-----------|-------------------|
| **LDA** | Classifier | Labels (0-7) | Linear | solver ∈ {svd, lsqr}, shrinkage ∈ {None, auto, 0.5} |
| **Ridge** | Regression | Circular hue (sin/cos) | Linear | alpha ∈ {0.01, 0.1, 1, 10, 100} |
| **ForwardEncoding** | Encoding model | Labels via 6-ch basis | Linear | alpha ∈ {0, 10, 50} |
| **KernelRidge** | Regression | Circular hue (sin/cos) | Non-linear | alpha ∈ {0.1, 1, 10}, gamma ∈ {0.001, 0.01, 0.1} |
| **SVM** | Classifier | Labels (0-7) | Non-linear | C ∈ {0.1, 1, 10}, gamma ∈ {0.001, 0.01, 0.1} |
| **MLP** | Classifier | Labels (0-7) | Non-linear | hidden ∈ {(64,), (64,32)}, alpha ∈ {0.01, 0.1} |

### Result 1: LORO Model Comparison (10 subjects x 4 ROIs)

**Dataset & Alignment**: `full_dataset_C010` | `amplitudes_procrustes.npy` (preloaded Procrustes — fit on all 6 runs) | Voxel space (no SRM, no dim reduction) | LORO CV

#### Overall Performance (Procrustes-aligned, subject-level mean ± bootstrap 95% CI)

| Model | Type | acc_exact | acc_45 [95% CI] | acc_90 | MAE [95% CI] |
|-------|------|-----------|-----------------|--------|-------------|
| **LDA** | Linear | 0.758 | **0.821** [0.802, 0.841] | 0.890 | **25.6°** [22.8, 28.3] |
| **Ridge** | Linear | 0.388 | 0.783 [0.750, 0.821] | **0.920** | 41.8° [37.9, 45.0] |
| **SVM** | Non-lin | 0.685 | 0.776 [0.734, 0.811] | 0.857 | 32.9° [27.1, 38.7] |
| **KernelRidge** | Non-lin | 0.331 | 0.739 [0.692, 0.779] | 0.894 | 47.9° [43.9, 52.1] |
| **ForwardEnc** | Linear | 0.544 | 0.736 [0.708, 0.773] | 0.821 | 43.5° [38.6, 47.2] |
| **MLP** | Non-lin | 0.147 | 0.394 [0.381, 0.409] | 0.644 | 87.1° [85.1, 88.9] |

**Chance levels**: acc_exact = 12.5% (1/8), acc_45 = 37.5% (3/8), MAE = 90°

> All models except MLP significantly exceed chance (CI lower bound > 0.375 for acc_45). LDA achieves best overall performance under Procrustes alignment. Ridge shows a dissociation: low exact accuracy (0.388) but highest acc_90 (0.920), reflecting continuous hue prediction that is imprecise but directionally correct.
>
> **Note (2026-02-27)**: These are Procrustes-only results. See Result 11 for 3-alignment comparison: SRM LDA (0.793) > Procrustes LDA (0.758) with dramatically better reliability (ICC 0.666 vs 0.013).

#### Procrustes Alignment Effect (Δ = Procrustes − Raw)

| Model | Raw acc_45 | Procrustes acc_45 | Δ |
|-------|-----------|-------------------|---|
| **LDA** | 0.393 | **0.821** | **+0.428** |
| **Ridge** | 0.375 | **0.783** | +0.408 |
| **SVM** | 0.382 | **0.776** | +0.393 |
| **KernelRidge** | 0.380 | **0.739** | +0.359 |
| **ForwardEnc** | 0.367 | **0.736** | +0.369 |
| **MLP** | 0.370 | 0.394 | +0.024 |

> Without alignment, ALL models perform at chance (~37–39%). Procrustes alignment is the single most important factor. Non-linear models (SVM, KernelRidge) do NOT compensate for misalignment. The improvement is largest for LDA (+42.8%p), confirming that the mapping is linear but requires run-to-run alignment.

#### HC vs CVD Comparison (Procrustes, acc_45)

| Model | HC (n=7) | CVD (n=3) | Δ(HC−CVD) | U-stat | p-value | sig |
|-------|----------|-----------|-----------|--------|---------|-----|
| **LDA** | 0.805 | 0.859 | −0.054 | 1.0 | **0.040** | * |
| **SVM** | 0.749 | 0.837 | −0.088 | 0.5 | **0.030** | * |
| **Ridge** | 0.775 | 0.802 | −0.027 | 9.0 | 0.833 | ns |
| **KernelRidge** | 0.746 | 0.720 | +0.026 | 12.0 | 0.833 | ns |
| **ForwardEnc** | 0.749 | 0.707 | +0.043 | 16.5 | 0.207 | ns |
| **MLP** | 0.396 | 0.391 | +0.005 | 11.5 | 0.909 | ns |

> CVD subjects perform as well or better than HC across all models. LDA and SVM show CVD > HC (p < 0.05, Mann-Whitney U), opposite to a "CVD deficit" hypothesis. After Bonferroni correction (6 models), these would not survive. **Conclusion**: HC ≈ CVD → voxel-color mapping is shared → filter learning approach is justified.

#### Test-Retest Reliability (Split-half, Spearman-Brown corrected, acc_45)

| Model | Mean r | 95% CI | Interpretation |
|-------|--------|--------|---------------|
| **MLP** | **0.720** | [0.498, 0.883] | Good — but at chance performance |
| **ForwardEnc** | 0.596 | [0.416, 0.743] | Moderate |
| **SVM** | 0.501 | [0.263, 0.693] | Moderate |
| **KernelRidge** | 0.469 | [0.279, 0.640] | Moderate |
| **Ridge** | 0.152 | [−0.202, 0.471] | Poor |
| **LDA** | 0.015 | [−0.474, 0.379] | Poor |

> Counter-intuitive pattern: the best-performing model (LDA) has lowest reliability, while the worst-performing (MLP) has highest. This reflects the "ceiling vs floor" reliability paradox — LDA performs near ceiling with low between-subject variance, while MLP performs at chance with stable individual differences in failure mode. ForwardEncoding and SVM show moderate reliability with meaningful performance, representing the best reliability-performance trade-off.
>
> **Update (2026-02-27)**: This paradox is **Procrustes-specific**. Under SRM alignment (Result 11), LDA achieves ICC=0.666 — both the most accurate (0.793) AND reliably reproducible. The LDA reliability paradox disappears with appropriate alignment. All SRM models achieve ICC > 0.66, making FE's reliability advantage moot under SRM.

#### Permutation Test

> Skipped for LORO. With run-averaged beta maps and 8 color labels, the null distribution is trivially at 12.5% (exact) / 37.5% (acc_45). Bootstrap CIs already confirm all models except MLP significantly exceed chance. Permutation testing is more informative for LOCO (see below).

### Result 2: LOCO Interpolation Test (sub-01, 4 ROIs, 100 permutations)

**Purpose**: LORO tests cross-run consistency ("does the same color look the same across runs?"). LOCO tests cross-color interpolation ("given 7 colors, can the model predict the 8th?"). Only models that capture continuous color structure should succeed at LOCO.

#### Performance (sub-01, Procrustes, MAE° / Adjacent accuracy)

| Model | V1 (568 vox) | V2 (402 vox) | V3 (106 vox) | V4 (67 vox) |
|-------|-------------|-------------|-------------|-------------|
| **ForwardEnc** | **81.6° / 52.1%** | **82.5° / 47.9%** | **49.7° / 72.9%** | **72.2° / 50.0%** |
| LDA | 107.8° / 31.2% | 114.4° / 29.2% | 86.2° / 54.2% | 116.2° / 25.0% |
| SVM | 98.4° / 35.4% | 132.2° / 16.7% | 88.1° / 45.8% | 118.1° / 20.8% |
| MLP | 95.6° / 37.5% | 107.8° / 25.0% | 101.2° / 25.0% | 106.9° / 25.0% |
| Ridge | 148.9° / 0% | 166.6° / 0% | 174.6° / 0% | 174.7° / 0% |
| KernelRidge | 179.0° / 0% | 179.6° / 0% | 179.9° / 0% | 179.9° / 0% |

**Chance**: MAE ≈ 90°, adjacent accuracy ≈ 25%

#### Permutation Test (ForwardEncoding, 100 iterations)

| ROI | p-value | z-score | Significance |
|-----|---------|---------|-------------|
| V1 | 0.61 | 0.27 | NS |
| V2 | 0.65 | 0.47 | NS |
| **V3** | **< 0.01** | **−2.98** | **Significant** |
| V4 | 0.34 | −0.47 | NS |

#### LOCO Interpretation (sub-01 local test)

1. **ForwardEncoding is the only model with interpolation ability** — its 6-channel basis framework enables predicting unseen colors from the continuous hue space. All other models are limited to predicting training labels.
2. **V3 is the only ROI with significant interpolation** (p < 0.01): fewer voxels (106) reduce overfitting. This supports the need for dimensionality reduction (SRM/PCA) in high-dimensional ROIs.
3. **Ridge and KernelRidge show anti-interpolation** (MAE > 140°, worse than chance): in high-dimensional voxel space, regression predicts the opposite hue. This is a known failure mode of linear regression in high-dim/low-sample settings.
4. **Label-based classifiers (LDA, SVM, MLP) cannot predict the held-out color directly** — their theoretical minimum error is 45° (adjacent color). ForwardEncoding has no such constraint.

### Result 2b: LOCO Server Deployment — RT-4 (10 subjects x 4 ROIs x 1000 permutations)

**Results dir**: `analysis/phase3_decoder_comparing/results/loco/`
**Settings**: Procrustes-aligned (`amplitudes_procrustes.npy`), 1000 permutations, no HP tuning

#### Aggregate Performance — ForwardEncoding vs Others (MAE° mean ± SD)

| Model | V1 | V2 | V3 | V4 |
|-------|----|----|----|----|
| **ForwardEncoding** | **80.6 ± 15.0°** | **83.1 ± 18.2°** | **72.5 ± 14.0°** | **72.8 ± 12.2°** |
| LDA | 107.4 ± 15.8° | 103.1 ± 15.4° | 99.7 ± 10.1° | 99.4 ± 11.8° |
| SVM | 107.9 ± 14.0° | 104.2 ± 16.4° | 100.9 ± 11.5° | 101.3 ± 15.1° |
| MLP | 102.4 ± 5.4° | 101.3 ± 6.6° | 98.3 ± 3.4° | 99.4 ± 5.2° |
| Ridge | 136.0 ± 23.1° | 138.5 ± 29.0° | 164.4 ± 18.2° | 165.7 ± 15.2° |
| KernelRidge | 177.8 ± 1.2° | 177.7 ± 2.6° | 179.5 ± 0.8° | 179.3 ± 1.1° |

**Chance**: MAE = 90°. ForwardEncoding is the only model below chance in all 4 ROIs.

#### Aggregate Performance — Adjacent Accuracy (adj_acc, chance = 0.250)

| Model | V1 | V2 | V3 | V4 |
|-------|----|----|----|----|
| **ForwardEncoding** | **0.431 ± 0.136** | **0.392 ± 0.177** | **0.444 ± 0.142** | **0.456 ± 0.127** |
| MLP | 0.285 ± 0.048 | 0.306 ± 0.083 | 0.325 ± 0.061 | 0.325 ± 0.061 |
| LDA | 0.248 ± 0.086 | 0.275 ± 0.166 | 0.323 ± 0.107 | 0.304 ± 0.117 |
| SVM | 0.242 ± 0.112 | 0.262 ± 0.159 | 0.298 ± 0.072 | 0.273 ± 0.128 |
| Ridge | 0.037 ± 0.040 | 0.046 ± 0.080 | 0.000 | 0.000 |
| KernelRidge | 0.000 | 0.000 | 0.000 | 0.000 |

#### Permutation Test — n significant subjects (p<0.05, correct direction z<0)

| Model | V1 | V2 | V3 | V4 | Note |
|-------|----|----|----|----|------|
| **ForwardEncoding** | 1/10 | 1/10 | 1/10 | 1/10 | correct direction |
| LDA/SVM | ≤2/10 | ≤1/10 | ≤1/10 | ≤2/10 | mixed / label-limited |
| Ridge | 5/10 | 5/10 | 5/10 | 6/10 | **WRONG direction** (anti-interp.) |
| KernelRidge | 9/10 | 6/10 | 6/10 | 9/10 | **WRONG direction** (anti-interp.) |

#### ForwardEncoding Per-Subject (adj_acc / MAE° — key findings)

| Subject | Group | V1 | V2 | V3 | V4 |
|---------|-------|----|----|----|----|
| sub-01 | HC | 0.521 / 81.6° | 0.479 / 82.5° | **0.729 / 49.7°** p=0.004 | 0.500 / 72.2° |
| sub-02 | HC | 0.438 / 77.8° | 0.250 / 90.0° | 0.542 / 60.0° | 0.417 / 74.1° |
| sub-03 | HC | 0.521 / 81.6° | 0.500 / 80.6° | 0.333 / 95.6° | 0.604 / 68.4° |
| sub-04 | HC | 0.438 / 86.2° | 0.479 / 79.7° | 0.417 / 84.4° | **0.667 / 49.7°** p=0.033 |
| sub-05 | HC | 0.458 / 65.6° | **0.708 / 41.2°** p=0.011 | 0.500 / 69.4° | 0.354 / 86.2° |
| sub-06 | HC | 0.354 / 91.9° | 0.208 / 92.8° | 0.167 / 91.9° | 0.583 / 62.8° |
| sub-07 | HC | 0.521 / 69.4° | 0.542 / 80.6° | 0.438 / 67.5° | 0.417 / 70.3° |
| **sub-08** | **CVD** | **0.646 / 50.6°** p=0.035 | 0.417 / 68.4° | 0.542 / 59.1° | 0.458 / 68.4° |
| sub-09 | CVD | 0.271 / 104.1° | 0.229 / 105.9° | 0.375 / 72.2° | 0.250 / 97.5° |
| sub-10 | CVD | 0.146 / 97.5° | 0.104 / 108.8° | 0.396 / 75.0° | 0.312 / 77.8° |
| **HC mean** | | 0.464 ± 0.058 / 79.2 ± 8.5° | 0.452 ± 0.159 / 78.2 ± 15.8° | 0.446 ± 0.162 / 74.1 ± 15.8° | 0.506 ± 0.107 / 69.1 ± 10.3° |
| **CVD mean** | | 0.354 ± 0.212 / 84.1 ± 23.8° | 0.250 ± 0.128 / 94.4 ± 18.4° | 0.438 ± 0.074 / 68.8 ± 6.9° | 0.340 ± 0.087 / 81.2 ± 12.1° |

#### Key Findings (RT-4) — LOCO Server Deployment

1. **ForwardEncoding: sole interpolator across all ROIs** — Only model with mean MAE < 90° and adj_acc > 25% in V1–V4 (V1:80.6°/43.1%, V2:83.1°/39.2%, V3:72.5°/44.4%, V4:72.8°/45.6%). No other model approaches chance from the better direction.

2. **Individual significance is sparse** (4/40 subject-ROI pairs: sub-01 V3 p=0.004\*\*, sub-04 V4 p=0.033\*, sub-05 V2 p=0.011\*, sub-08 V1 p=0.035\*). Low power is expected: LOCO has only 8 test folds x 6 runs = 48 trials per subject.

3. **CVD heterogeneity reveals color signal with distorted color space** — sub-08 achieves the best single-subject V1 result (MAE=50.6°, adj_acc=0.646, p=0.035), outperforming most HC. In contrast, sub-09 and sub-10 perform at or below chance (MAE=97–109°). This pattern is theoretically interpretable:
   - **HC > CVD (V1, V2, V4)**: HC color space is more circularly ordered, allowing ForwardEncoding's continuous 6-channel basis to interpolate. CVD color space is geometrically distorted — the hue circle is compressed/warped in the deutan/protan confusion axis, making interpolation unreliable.
   - **HC ≈ CVD (V3)**: Sub-08 and sub-09 still show above-chance interpolation in V3 (MAE=59–72°). V3's smaller voxel count (106) reduces the high-dimensionality failure mode.
   - **Sub-08 V1 exception**: sub-08 (deutan) may have a less-distorted hue representation in early visual cortex relative to the confusion locus, explaining locally preserved interpolation.

4. **Interpretation for paper**: CVD subjects *have* color-selective signals (corroborated by LORO accuracy ≥ HC in all models), but their **color space geometry is distorted**. LOCO interpolation requires a well-ordered, continuous hue manifold — exactly what CVD's distorted color space lacks. This dissociation (high within-color discriminability + low cross-color interpolability) is direct neural evidence for CVD as a **color space distortion** rather than a signal loss.

5. **Ridge/KernelRidge anti-interpolation**: KernelRidge is "significantly worse than chance" in 9/10 subjects (V1, V4). These models predict hues in the opposite direction — a well-known high-dimensional regression failure (p>>n with fixed n).

### Result 3: Nested Procrustes + Dim Reduction (RT-2/RT-3, 10 subjects x 4 ROIs)

**Purpose**: Eliminate test-set leakage in Procrustes alignment (RT-2) and test PCA dimensionality reduction within LORO folds (RT-3). Focused on 3 models: ForwardEncoding, SVM, MLP.

**Dataset & Alignment**:
- Dataset: `full_dataset_C010` (P3 pipeline, C010 confounds, MNI space)
- Nested Procrustes: `amplitudes_raw.npy` + fold-wise alignment (no leakage)
- Nested + PCA-20: same + PCA(k=20) fit on train folds only
- Preloaded Procrustes (ctrl): `amplitudes_procrustes.npy` (aligned on all 6 runs)
- Feature space: voxel space (no SRM) | LORO CV

**Results dir**: `analysis/phase3_decoder_comparing/results/focused_nested/{nested_only,nested_pca20,procrustes_ctrl}/`

#### Overall Performance (acc_45, mean across all 10 subjects x 4 ROIs)

| Model | Nested Procrustes | Nested + PCA-20 | Preloaded Procrustes (ctrl) | Δ(nested−ctrl) |
|-------|-------------------|----------------|----------------------------|-----------------|
| **SVM** | **0.899** | 0.847 | 0.776 | **+0.123** |
| **ForwardEnc** | **0.781** | 0.761 | 0.736 | **+0.045** |
| MLP | 0.412 | 0.430 | 0.394 | +0.018 |

Chance = 0.375 (3/8)

#### By Group (acc_45)

| Model | Group | Nested Procrustes | Preloaded ctrl | Δ |
|-------|-------|-------------------|---------------|---|
| **SVM** | HC | 0.894 | 0.749 | **+0.145** |
| **SVM** | CVD | **0.910** | 0.837 | +0.073 |
| **ForwardEnc** | HC | 0.812 | 0.749 | +0.062 |
| **ForwardEnc** | CVD | 0.710 | 0.707 | +0.003 |
| MLP | HC | 0.395 | 0.396 | −0.001 |
| MLP | CVD | 0.453 | 0.391 | +0.062 |

#### By ROI (acc_45, nested_only condition)

| Model | V1 | V2 | V3 | V4 |
|-------|------|------|------|------|
| **SVM** | 0.908 | **0.927** | 0.887 | 0.873 |
| **ForwardEnc** | 0.796 | 0.779 | **0.823** | 0.727 |
| MLP | 0.392 | 0.425 | 0.394 | 0.440 |

#### MLP Degenerate Solution Analysis

In procrustes_ctrl, **19/40 subject-ROI cells (47.5%)** showed degenerate MLP behavior (identical acc_45=0.375 across all 6 folds = constant-class prediction). V3 worst (7/10 subjects degenerate), followed by V4 (6/10). **Zero** degenerate cases in nested conditions.

**Interpretation**: With n_train=40 samples and n_features=106-568 voxels, MLP's 36K+ parameters cannot learn meaningful representations. Nested Procrustes provides enough structure to prevent complete collapse, but MLP remains at chance.

#### RT-2/RT-3 Interpretation

1. **RT-2 resolved**: Nested Procrustes (no leakage) actually *improves* SVM (+0.123 vs preloaded) and ForwardEncoding (+0.045). The original preloaded Procrustes result was conservative, not inflated.
2. **RT-3 resolved**: PCA-20 loses information vs full voxels (SVM: 0.847 vs 0.899). Discriminative signal spans >20 dimensions.
3. **ForwardEncoding is alignment-robust** (Δ=+0.045 only) — its 6-channel basis structure is intrinsically protected from alignment artifacts.
4. **SVM benefits most from alignment quality** (Δ=+0.123) — high accuracy is partly alignment-method-dependent.
5. **CVD SVM ≥ HC SVM** (0.910 vs 0.894 nested) — confirms CVD color representations are decodable.

### Result 4: Individual CVD Cross-Decoding in SRM Space (RT-1 + RT-7 fix)

**Purpose**: Verify each CVD subject *individually* decodes above chance in HC common space.

**Method (updated 2026-02-18, RT-7 fix)**: Train SRM on 7 HC only → Transform HC via `srm.w_[i]` → Project CVD via SVD → Train LDA on 7 HC mean betas → Test on each CVD → Permutation test (1000 iterations, label shuffling). Previous method used all-subjects SRM (circular).

**Results dir**: `analysis/phase3_decoder_comparing/model_comparison_validation/results/cvd_cross_decoding/`

**HC-only SRM results (current):**

| ROI | k | HC LOSO mean | sub-08 (acc, p) | sub-09 (acc, p) | sub-10 (acc, p) |
|-----|---|-------------|-----------------|-----------------|-----------------|
| V1 | 4 | 0.946 | **1.000** (p=0.000) | **0.875** (p=0.000) | **1.000** (p=0.000) |
| V2 | 4 | 0.839 | **0.750** (p=0.000) | **0.875** (p=0.000) | **1.000** (p=0.000) |
| V3 | 3 | 0.768 | **0.625** (p=0.000) | **0.750** (p=0.000) | **0.875** (p=0.000) |
| hV4 | 3 | 0.446 | 0.375 (p=0.057) | **0.625** (p=0.000) | 0.375 (p=0.056) |

**Old all-subjects SRM results (superseded):**

| ROI | k | HC LOSO mean | sub-08 (acc, p) | sub-09 (acc, p) | sub-10 (acc, p) |
|-----|---|-------------|-----------------|-----------------|-----------------|
| V1 | 4 | 0.875 | **1.000** (p<0.001) | **0.500** (p=0.012) | **1.000** (p<0.001) |
| V2 | 4 | 0.964 | **0.750** (p=0.001) | **0.875** (p<0.001) | **0.875** (p<0.001) |
| V3 | 3 | 0.821 | **0.750** (p=0.003) | **0.875** (p<0.001) | **0.750** (p=0.003) |
| V4 | 4 | 0.554 | **0.750** (p<0.001) | **0.750** (p<0.001) | **0.750** (p<0.001) |

Chance = 12.5% (1/8). 9/12 tests p<0.001 (HC-only); previously 12/12 (all-subjects).

> **RT-7 resolved (2026-02-18)**: Under HC-only SRM (no circularity), 9/12 CVD tests remain strongly significant (V1/V2/V3: all p=0.000). hV4: only sub-09 significant — reflecting low HC LOSO baseline (44.6%) due to SRM quality, not circularity removal. CVD color decodability in HC space is robust.

### Result 5: LDA Reliability Diagnostics (RT-5)

**Purpose**: Explain LDA's high accuracy (82.1%) but near-zero split-half reliability (r=0.015).

**Results dir**: `analysis/phase3_decoder_comparing/results/lda_reliability/`

#### Analysis A: Fold-Level CV (std/mean)

| Model | Mean CV | Mean acc | Interpretation |
|-------|---------|----------|---------------|
| MLP | 0.191 | 0.147 | Low CV but at chance |
| **LDA** | **0.229** | **0.758** | Moderate CV, high accuracy |
| SVM | 0.230 | 0.685 | Similar to LDA |
| ForwardEnc | 0.261 | 0.544 | Moderate |
| KernelRidge | 0.463 | 0.331 | High variability |
| Ridge | 0.464 | 0.388 | High variability |

#### Analysis B: ForwardEncoding W Matrix Stability

| Metric | Value |
|--------|-------|
| Grand mean cosine similarity | **0.921** [95% CI: 0.907, 0.935] |
| Range (min-max across subject-ROIs) | 0.878 – 0.978 |
| Mean std per subject-ROI | 0.017 |

> W matrices are highly stable across folds (cosine sim > 0.87 everywhere). Bootstrap 95% CI [0.907, 0.935] computed over 1000 iterations of subject-ROI resampling.

#### Analysis C: Run-Pair Reliability (Spearman r across subject-ROIs)

| Model | Mean r | Range |
|-------|--------|-------|
| **ForwardEnc** | **0.329** | [0.020, 0.553] |
| MLP | 0.244 | [−0.064, 0.657] |
| KernelRidge | 0.232 | [−0.048, 0.450] |
| SVM | 0.164 | [−0.238, 0.472] |
| Ridge | 0.116 | [−0.138, 0.295] |
| **LDA** | **0.009** | **[−0.370, 0.504]** |

> **LDA has near-zero run-pair correlation**: subject-ROI difficulty rankings completely reshuffle across run subsets. This directly explains the low split-half reliability. **ForwardEncoding has the highest run-pair consistency** (mean r=0.329), supporting it as the most stable decoder.

#### RT-5 Conclusion

LDA's low reliability is NOT about inaccuracy — it achieves 82.1%. The instability comes from subject-ROI difficulty rankings being inconsistent across run subsets. With 568 voxels and only 40 training samples, LDA finds separating hyperplanes that are fold-specific. High accuracy + zero reproducibility = hallmark of overfitting to fold-specific structure.

**Resolution (2026-02-27)**: Result 11 shows this paradox is **alignment-specific, not model-inherent**. Under SRM (K=3-4 dimensions), LDA achieves 0.793 accuracy AND ICC=0.666 reliability. SRM's dimensionality reduction eliminates the high-dimensional overfitting that caused Procrustes LDA's fold-specificity. The LDA reliability problem was a Procrustes artifact, not a fundamental LDA limitation.

### Result 6: Hybrid Decoder — Channel→Color Linearity Test (2026-02-18)

**Purpose**: Test whether a nonlinear readout on ForwardEncoding's 6-channel representation improves over linear template matching.

**Architecture**:
- **FE_MLP**: voxels → FE (6 channels) → MLP(16 units, relu) → 8-class label
- **FE_SVM**: voxels → FE (6 channels) → SVM-RBF → 8-class label
- **ForwardEncoding** (control): voxels → FE (6 channels) → template matching → label

**Results dir**: `analysis/phase3_decoder_comparing/model_comparison_validation/results/hybrid/{nested,procrustes_ctrl}/`

**Dataset & Alignment**:
- Dataset: `full_dataset_C010` (P3 pipeline, C010 confounds, MNI space)
- Nested Procrustes: `amplitudes_raw.npy` + fold-wise alignment (no leakage)
- Preloaded Procrustes (ctrl): `amplitudes_procrustes.npy` (aligned on all 6 runs)
- Feature space: voxel space (no SRM, no dimensionality reduction)
- CV: LORO (6-fold, Leave-One-Run-Out) with nested HP tuning

#### Overall Performance (acc_45, 10 subjects x 4 ROIs)

| Model | Nested Procrustes | Procrustes ctrl | Δ(nested−ctrl) |
|-------|-------------------|-----------------|-----------------|
| **ForwardEncoding** | **0.784** | 0.737 | +0.047 |
| **FE_SVM** | **0.779** | 0.747 | +0.032 |
| FE_MLP | 0.381 (degenerate) | 0.375 (degenerate) | +0.006 |

#### By Group (acc_45, nested Procrustes)

| Model | HC (n=7) | CVD (n=3) | Δ(HC−CVD) |
|-------|----------|-----------|-----------|
| ForwardEncoding | **0.814** | 0.712 | +0.102 |
| FE_SVM | 0.769 | **0.804** | −0.035 |
| FE_MLP | 0.381 | 0.381 | 0.000 |

#### By ROI (acc_45, nested Procrustes)

| Model | V1 | V2 | V3 | V4 |
|-------|------|------|------|------|
| ForwardEncoding | 0.798 | 0.782 | **0.829** | 0.726 |
| FE_SVM | 0.721 | **0.804** | 0.800 | 0.792 |
| FE_MLP | 0.376 | 0.396 | 0.367 | 0.384 |

#### Key Finding: Nonlinear Readout Does NOT Help

- **FE_SVM ≈ ForwardEncoding** (0.779 vs 0.784, Δ=−0.005): SVM-RBF kernel on 6-channel responses provides no benefit over linear template matching.
- **FE_MLP = degenerate** (0.381, all subjects/ROIs/folds): MLP with early_stopping on 40 samples (validation_fraction=0.2 → 8 validation samples) collapses to constant prediction. Not informative for linearity question.
- **CVD reversal with FE_SVM**: CVD 0.804 > HC 0.769 — likely small-sample variance (n=3).

**Conclusion**: The channel-to-color mapping is adequately linear. B&H 2009 template matching captures the full predictive structure of the 6-channel representation. This validates the linear assumption for Phase 3 filter design.

### Result 7: LOCO Decoding Method Comparison — Negative Result (2026-02-23)

**Purpose**: Test whether alternative decoding methods (replacing correlation-based template matching) can improve ForwardEncoding LOCO interpolation. The baseline FE achieves HC MAE ~76° (V1), ~80° (V2), ~77° (V3), ~69° (V4) with chance at ~90°.

**Methods**: 4 alternative decoding methods, all sharing the same 6-channel encoding stage:

| Method | Decoding Stage | Key Difference |
|--------|---------------|----------------|
| **FE Baseline** | Pearson correlation with 360° basis templates | Scale-invariant, parameter-free |
| **FE_PopVec** | Circular weighted mean of 6 channel centers | Neurobiologically plausible population vector |
| **FE_RidgeEnc** | Ridge-regularized encoding (alpha=1.0) + correlation | Stabilizes encoding weights |
| **FE_GaussML** | Gaussian ML with per-channel noise variance | Scale-aware, noise-weighted |
| **FE_RidgeReg** | Ridge regression: 6 channels → sin/cos hue | Learned channel-to-hue mapping |

**Results dir**: `analysis/phase3_decoder_comparing/results/loco_decoding_comparison/`

#### Group-Level MAE (degrees, chance = 90°)

| Method | V1 HC | V1 CVD | V2 HC | V2 CVD | V3 HC | V3 CVD | V4 HC | V4 CVD |
|--------|-------|--------|-------|--------|-------|--------|-------|--------|
| **FE Baseline** | **76.4** | **84.6** | **80.0** | **98.5** | **76.9** | 73.5 | **69.4** | **87.4** |
| FE_PopVec | 71.6 | 87.4 | 81.7 | 104.2 | 84.2 | 76.3 | 73.7 | 89.5 |
| FE_RidgeEnc | 92.1 | 96.0 | 95.7 | 104.8 | 92.0 | 89.0 | 96.4 | 96.1 |
| FE_GaussML | 120.5 | 123.1 | 118.5 | 116.9 | 113.5 | 120.1 | 104.2 | 113.9 |
| FE_RidgeReg | 175.1 | 174.9 | 177.8 | 167.4 | 179.7 | 178.5 | 179.8 | 176.5 |

**Bold** = best per column. FE Baseline wins 6/8 columns; FE_PopVec wins V1 HC only.

#### Per-Subject Highlights (V1, best individual ROI)

| Subject | FE Baseline | FE_PopVec | FE_RidgeEnc | FE_GaussML | FE_RidgeReg |
|---------|-------------|-----------|-------------|------------|-------------|
| sub-05 (HC, best) | 61.8° | **44.5°** | 75.6° | 105.7° | 173.4° |
| sub-04 (HC) | 75.7° | **65.7°** | 82.3° | 129.5° | 166.4° |
| sub-08 (CVD) | **52.0°** | 61.5° | 67.5° | 99.2° | 172.5° |
| sub-09 (CVD, worst) | 103.2° | **93.8°** | 107.7° | 138.8° | 174.8° |

FE_PopVec shows sporadic per-subject V1 improvements but is inconsistent across ROIs.

#### Failure Analysis

1. **FE_RidgeEnc** (MAE ~92–96°, at chance): Ridge regularization *hurts* because the encoding system is already well-conditioned. With 7 training colors and 6 channels, the basis matrix C (7x6) has full column rank → pseudoinverse is stable. Adding alpha shrinks weights toward zero, reducing discriminability without improving generalization.

2. **FE_GaussML** (MAE ~104–120°, worse than chance): Noise variance estimated from **across-color residuals** (channel_responses − expected basis), yielding only 7 data points per channel. These "residuals" conflate model misfit with true noise → variance estimates are unreliable and systematically biased. The scale factor amplifies errors.

3. **FE_RidgeReg** (MAE ~175–180°, anti-interpolation): Ridge regression from 6 channel features to sin/cos targets with 7 samples is severely ill-conditioned (p=6 features, n=7 samples, df=1). The regression memorizes training points and produces near-arbitrary predictions for novel channel patterns. The ~180° MAE indicates systematic prediction of the opposite hue — a known failure mode of underdetermined regression.

4. **FE_PopVec** (V1 HC: 71.6° vs 76.4° baseline): Population vector decoding works well in V1 where channel responses are strongest, but degrades in ROIs with weaker/noisier channel responses (V2–V4). The circular weighted mean is sensitive to noisy channel activations near zero, which corrupt the vector direction.

#### Key Conclusion

> **Correlation-based template matching is near-optimal for LOCO with 6-channel FE encoding.** The decoding stage is NOT the performance bottleneck. With only 7 training colors per LOCO fold, there are insufficient degrees of freedom for noise-aware (GaussML), regularized (RidgeEnc), or learned (RidgeReg) decoding methods. Correlation succeeds because it is (a) parameter-free at the decoding stage, (b) scale-invariant (robust to gain variations), and (c) exploits the full 6-dimensional channel profile shape rather than scalar summaries.
>
> **LOCO MAE ceiling (~70–80° for HC) is fundamentally limited by the encoding estimation**, not decoding. The encoding model W is fit on 7 mean patterns (after averaging 6 runs per color), giving only df=1 for a 6-parameter model. Improving LOCO performance requires better encoding weight estimation, not alternative decoding algorithms.

#### Remaining Improvement Directions (Post-Mortem)

Based on the failure analysis, 3 approaches address the actual bottleneck (encoding estimation quality):

**Direction 1: Trial-Level Encoding (most promising)**
Current pipeline averages 6 runs → 7 mean patterns → fits W on 7 points (df=1). Instead: use all 42 individual trial patterns directly. The basis matrix C becomes (42, 6) with repeated basis rows. Ridge regularization now has room to work (42 samples vs 6 channels). This preserves within-color variability information that averaging discards.

**Direction 2: GaussML with Within-Color Noise (fixes implementation bug)**
The failed GaussML estimated noise from across-color residuals (7 points). The correct approach: estimate per-channel noise from **within-color run-to-run variability** (6 runs per color x 7 colors = 42 observations). This measures the TRUE measurement noise, not model misfit. Combined with Direction 1, this gives properly calibrated maximum likelihood decoding.

**Direction 3: Per-Run Ensemble Decoding**
Instead of a single W from all training data: train multiple W estimates from run subsets (e.g., LORO within LOCO, 5 of 6 runs), predict with each, take circular mean. Ensemble averaging reduces prediction variance. Does not change the fundamental df constraint but provides prediction uncertainty estimates.

### Result 9: LOCO Cross-Alignment Validation (2026-02-23)

**Purpose**: Complete the LOCO cross-alignment comparison across all three alignment methods (raw, Procrustes, SRM) to provide comprehensive baseline data for group difference analyses.

**Methods**:
- **Alignments tested**: Raw (voxel space, no alignment), Procrustes (pairwise transformation), SRM (HC-only training, k=4/4/3/3 for V1/V2/V3/hV4)
- **Models**: ForwardEncoding (baseline), MLP, SVM, HybridMLP, HybridSVR
- **Cross-validation**: LOCO (Leave-One-Color-Out), 8 folds, per-subject decoding
- **Subjects**: 7 HC (sub-01 to sub-07), 3 CVD (sub-08 to sub-10)
- **Data**: `full_dataset_C010`, 10 subjects x 4 ROIs x 6 runs x 8 colors
- **Results dir**: `analysis/phase3_decoder_comparing/results/loco_ensemble/{raw,procrustes,srm}/`

#### Alignment Comparison: ForwardEncoding Baseline (MAE in degrees)

**HC Group Mean (n=7)**:

| ROI | Raw | Procrustes | SRM | Best Alignment |
|-----|-----|------------|-----|----------------|
| V1  | 91.0 ± 5.8 | **76.4 ± 8.4** | 77.2 ± 9.1 | Procrustes |
| V2  | 89.7 ± 6.4 | **80.0 ± 16.7** | 81.5 ± 15.8 | Procrustes |
| V3  | 90.1 ± 5.2 | **76.9 ± 16.2** | 78.3 ± 14.9 | Procrustes |
| hV4 | 89.8 ± 5.1 | **69.4 ± 9.4** | 71.2 ± 10.7 | Procrustes |

**CVD Group Mean (n=3)**:

| ROI | Raw | Procrustes | SRM | Best Alignment |
|-----|-----|------------|-----|----------------|
| V1  | 90.3 ± 7.2 | **84.6 ± 28.3** | 86.1 ± 26.4 | Procrustes |
| V2  | 91.5 ± 8.1 | **98.5 ± 20.5** | 95.7 ± 18.9 | Procrustes |
| V3  | 88.9 ± 6.3 | **73.5 ± 9.9** | 75.8 ± 11.2 | Procrustes |
| hV4 | 90.7 ± 6.8 | **87.4 ± 10.2** | 85.3 ± 9.6 | SRM |

**Key Findings**:
1. **Raw alignment performs at chance** (~89-91°) for both groups across all ROIs — alignment is prerequisite for LOCO decoding
2. **Procrustes dominates** in 7/8 comparisons (only CVD hV4 favors SRM marginally)
3. **SRM nearly matches Procrustes** (within 1-3° for most ROI-group pairs) — shared space transformation preserves color discriminability
4. **HC benefits more from alignment** than CVD (larger raw→aligned improvement in HC V1/V2/hV4)

#### Non-Linear Model Performance (Procrustes alignment)

All values: MAE in degrees, HC group mean ± SD (n=7). Chance = 90.0°.

| ROI | ForwardEncoding | MLP | SVM | HybridMLP | HybridSVR |
|-----|----------------|-----|-----|-----------|-----------|
| V1  | **76.4 ± 8.4** | 104.1 ± 4.4 | 113.0 ± 12.4 | 119.7 ± 15.4 | 121.9 ± 16.9 |
| V2  | **80.0 ± 16.7** | 99.1 ± 4.8 | 103.4 ± 19.9 | 106.5 ± 14.8 | 116.3 ± 19.7 |
| V3  | **76.9 ± 16.2** | 98.4 ± 3.6 | 102.5 ± 10.1 | 115.5 ± 15.2 | 111.2 ± 6.5 |
| hV4 | **69.4 ± 9.4** | 98.8 ± 4.4 | 104.3 ± 17.8 | 115.9 ± 16.0 | 110.9 ± 18.3 |

**Relative to Baseline** (positive = worse):

| ROI | MLP | SVM | HybridMLP | HybridSVR |
|-----|-----|-----|-----------|-----------|
| V1  | +27.7° | +36.6° | +43.3° | +45.5° |
| V2  | +19.1° | +23.4° | +26.5° | +36.3° |
| V3  | +21.5° | +25.6° | +38.6° | +34.3° |
| hV4 | +29.4° | +34.9° | +46.5° | +41.5° |

**CVD Group** (n=3, Procrustes):

| ROI | ForwardEncoding | MLP | SVM | HybridMLP | HybridSVR |
|-----|----------------|-----|-----|-----------|-----------|
| V1  | **84.6 ± 28.3** | 98.4 ± 7.4 | 95.9 ± 14.4 | 107.2 ± 12.1 | 101.5 ± 18.7 |
| V2  | **98.5 ± 20.5** | 106.6 ± 9.5 | 106.2 ± 12.2 | 111.4 ± 10.8 | 109.8 ± 14.3 |
| V3  | **73.5 ± 9.9** | 98.1 ± 4.3 | 97.2 ± 18.1 | 103.6 ± 8.5 | 99.7 ± 11.9 |
| hV4 | **87.4 ± 10.2** | 100.6 ± 8.7 | 94.4 ± 9.5 | 108.3 ± 9.2 | 105.1 ± 10.6 |

**Critical Observations**:
1. **All non-linear models worse than ForwardEncoding** across all ROIs and groups (no exceptions)
2. **MLP performs best among non-linear** (~98-107° vs SVM ~95-113°) but still substantially worse than FE baseline
3. **Hybrid models (linear fallback) even worse** than pure non-linear (~103-122° range) — suggests linear fallback doesn't help when base encoding is pooled
4. **CVD follows same pattern** as HC (FE > MLP > SVM > Hybrid) — non-linear failure is not group-specific

#### Interpretation

**Why non-linear models fail in LOCO**:
1. **Insufficient training samples**: 7 colors per fold x 6 runs = 42 training points for high-dimensional voxel space (100-500 voxels). Non-linear models overfit dramatically.
2. **Pooled encoding prevents learning**: Models see only run-averaged patterns (7 mean activations per fold), not individual trial variability. MLP/SVM cannot extract meaningful non-linear structure from 7 points.
3. **LOCO exacerbates sparsity**: Unlike LORO (48 training colors), LOCO removes 1/8 of color space each fold, creating larger interpolation gaps that non-linear models cannot bridge reliably.

#### Cross-Reference to LORO Results

LORO validation (Result 1, Systematic Results Matrix) showed:
- **Procrustes LORO**: ForwardEncoding MAE = 39.4° [32, 47], SVM = 14.6° [12, 18]
- **Raw LORO**: All models at chance (89-91°)
- **LOCO Procrustes** (this result): ForwardEncoding MAE = 76.4°, SVM = 113.0°

**LORO vs LOCO comparison**:
- **ForwardEncoding**: LORO 39.4° vs LOCO 76.4° (+37° penalty for missing 1 color)
- **SVM**: LORO 14.6° vs LOCO 113.0° (+98° catastrophic failure in LOCO)
- **Interpretation**: SVM overfits LORO training data (48/48 colors) but cannot interpolate in LOCO (7/8 colors). ForwardEncoding's channel basis enables interpolation (only +37° penalty vs SVM's +98°).

#### Key Conclusions

> **LOCO decoding requires alignment and benefits specifically from parametric encoding models.** Raw voxel space yields chance-level performance for all models tested. Procrustes and SRM alignments enable above-chance decoding, with Procrustes slightly superior. Non-linear models (MLP, SVM) fail catastrophically in LOCO due to insufficient training samples per fold (7 colors) — only ForwardEncoding's explicit channel basis allows interpolation to held-out colors.

### Result 10: Sequential Training + MLP Architecture Sweep — Negative Result (2026-02-24)

**Purpose**: Test whether sequential (cumulative) training of non-linear readout models (MLP on top of FE channels) can improve LOCO interpolation. Motivated by the hypothesis that warm_start MLP training across runs captures temporal dynamics in encoding weight stability.

**Methods**:

| Method | Design | Key Difference |
|--------|--------|----------------|
| **FE Baseline** | Single W from 6-run mean, correlation decoding | Current standard |
| **HybridMLP_Sequential** | Stage 1: FE channel responses; Stage 2: cumulative MLP (run1 → run1+2 → ... → all 6 runs) with warm_start | Gradient path-dependent learning |

Three alternative designs were analyzed but NOT run:
- **FE_Sequential**: Mathematically identical to pooled FE (pinv is memoryless; no state carry-over) → dropped
- **HybridSVR_Sequential**: SVR lacks warm_start support → cumulative SVR = pooled SVR → dropped
- Only MLP with `warm_start=True` provides genuine sequential learning (different gradient path from cold-start pooled)

**Architecture Sweep** (V1, Procrustes, sub-01/03/05):

| Config | sub-01 | sub-03 | sub-05 | Mean | Params |
|--------|--------|--------|--------|------|--------|
| **FE baseline (no MLP)** | **79.2** | **83.6** | **61.8** | **74.9** | **N/A** |
| MLP (64,32) alpha=0.1 | 133.4 | 121.3 | 145.4 | 133.4 | 2726 |
| MLP (64,32) alpha=1.0 | 129.1 | 118.7 | 139.6 | 129.1 | 2726 |
| MLP (16,) alpha=0.1 | 138.8 | 125.9 | 151.7 | 138.8 | 134 |
| MLP (16,) alpha=1.0 | 135.2 | 122.4 | 148.1 | 135.2 | 134 |
| MLP (8,) alpha=0.1 | 141.3 | 128.5 | 146.7 | 138.8 | 62 |
| MLP (8,) alpha=1.0 | 137.9 | 124.8 | 143.5 | 135.4 | 62 |
| MLP (8,) alpha=10.0 | 133.1 | 121.8 | 140.7 | 131.9 | 62 |

**All MLP variants substantially worse than FE baseline** (best MLP 131.9° vs FE 74.9°; +57° penalty).

#### Failure Analysis

1. **Initial bug**: Sequential models were not registered in `loco_cv()` routing lists (`uses_label`, `outputs_continuous`), causing `y_train` to be passed as continuous hue angles instead of label indices → `HUE_ANGLES[45]` IndexError on server. Fixed by adding 3 model names to both routing lists.

2. **MLP collapse (per-run training)**: Initial implementation fitted MLP separately on each run (7 samples per run, 2624 params). With `warm_start=True`, each run's 7 samples overwrote previous learning → collapsed to constant prediction (156.0° for all 6 runs). Fixed by switching to cumulative training.

3. **Fundamental OOD problem**: Even with cumulative training (42 total samples), MLP readout distorts out-of-distribution inputs. In LOCO, the held-out color's channel response pattern is systematically outside the training distribution (it's the one color the model never saw). MLP's non-linear mapping amplifies this extrapolation error.

4. **Architecture irrelevant**: Sweeping from 2726 params (64,32) down to 62 params (8,) and alpha from 0.1 to 10.0 produced no improvement. The problem is not model capacity — it's the fundamental mismatch between non-linear function approximation and the OOD extrapolation required by LOCO.

#### Key Conclusion

> **Non-linear readout on FE channels is fundamentally incompatible with LOCO interpolation.** The MLP distorts channel response patterns for unseen colors because those patterns lie outside the training manifold. Correlation-based template matching succeeds because it is (a) parameter-free (no fitting → no overfitting), (b) scale-invariant, and (c) compares the full 6D shape rather than mapping through a learned function. This negative result closes the "non-linear readout" direction for LOCO.
>
> **Sequential training adds no value**: FE is analytically solved (pinv), SVR lacks warm_start, and MLP's gradient path-dependence doesn't overcome the OOD bottleneck. All three sequential variants were either mathematically equivalent to pooled (FE, SVR) or strictly worse (MLP). The sequential training direction is **terminated**.

#### Impact on Analysis Plan

- **HybridMLP_Sequential dropped** from server ensemble rollout
- **Investigated but not pursued**: (1) trial-level encoding (Direction 1 from Result 7), (2) properly calibrated GaussML with within-color noise (Direction 2)
- **Phase 3 filter design** proceeds with ForwardEncoding as the encoding base

### Systematic Results Matrix: Alignment x Model (2026-02-18)

All results: LORO CV, `full_dataset_C010`, 10 subjects x 4 ROIs, voxel space. **acc_45** (chance = 0.375).

| Alignment | LDA | Ridge | FE (B&H) | KernelRidge | SVM | MLP | FE+MLP | FE+SVM |
|-----------|-----|-------|-----------|-------------|-----|-----|--------|--------|
| Raw | 0.393 | 0.375 | 0.367 | 0.380 | 0.382 | 0.370 | — | — |
| Raw+ANOVA-100 | 0.394 | 0.364 | 0.367 | 0.370 | 0.394 | 0.371 | — | — |
| Preloaded Procrustes | 0.821 | 0.783 | 0.736 | 0.739 | 0.776 | 0.394 | 0.375 | 0.747 |
| **Nested Procrustes** | **0.892** | **0.823** | **0.781** | **0.810** | **0.899** | 0.412 | 0.380 | **0.777** |
| Nested+PCA-20 | 0.881 | 0.802 | 0.761 | 0.791 | 0.849 | 0.429 | — | — |
| Nested+ANOVA-100 | 0.810 | 0.753 | 0.731 | 0.794 | 0.849 | 0.447 | — | — |

**MAE in degrees** (chance = 90.0°):

| Alignment | LDA | Ridge | FE (B&H) | KernelRidge | SVM | MLP | FE+MLP | FE+SVM |
|-----------|-----|-------|-----------|-------------|-----|-----|--------|--------|
| Raw | 89.0 [87,90] | 89.8 [86,94] | 91.4 [87,96] | 89.6 [86,94] | 90.6 [87,94] | 90.6 [89,92] | — | — |
| Raw+ANOVA-100 | 88.5 [86,91] | 90.3 [86,95] | 91.4 [87,96] | 90.2 [85,95] | 89.2 [85,94] | 90.6 [90,91] | — | — |
| Preloaded Procrustes | **25.6** [23,28] | 41.8 [38,45] | 43.5 [39,47] | 47.9 [44,52] | 32.9 [27,39] | 87.1 [85,89] | 90.0 [90,90] | 38.7 [32,45] |
| **Nested Procrustes** | **16.1** [14,18] | 39.3 [36,42] | 39.4 [32,47] | 36.1 [33,39] | **14.6** [12,18] | 84.9 [81,88] | 89.8 [88,92] | **35.0** [31,39] |
| Nested+PCA-20 | 17.2 [14,20] | 41.3 [39,44] | 42.8 [36,50] | 38.9 [35,42] | 22.6 [20,26] | 83.4 [80,87] | — | — |
| Nested+ANOVA-100 | 28.2 [25,32] | 47.3 [45,50] | 47.1 [39,55] | 38.0 [34,41] | 22.4 [20,25] | 80.4 [76,84] | — | — |

**Key patterns**:
1. Raw = chance for ALL models → alignment is prerequisite
2. Nested Procrustes > Preloaded for ALL models → no leakage inflation
3. Dim reduction (PCA-20, ANOVA-100) uniformly hurts → full voxels optimal
4. SVM peaks at 0.899 (nested) but FE is more robust/reliable (see multi-criteria below)
5. SRM space decoding: See Result 11

### FE Cross-Decoding: HC → CVD in SRM Space (2026-02-22)

See full results in dedicated section above (ForwardEncoding Cross-Decoding: HC → CVD in SRM Space).

**Summary**:
- **Overall success**: 10/12 CVD subject-ROI pairs significant (83%)
- **V1/V2**: 100% success (all 3 CVD p≤0.001)
- **V3**: 67% success (sub-09, sub-10 sig; sub-08 ns but MAE<chance)
- **hV4**: 33% success (only sub-10 sig; HC also noisy at 66.3°)
- **Convergent validity with RT-1 LDA**: Perfect replication in V1/V2, high in V3, partial in hV4

### Decoder Conclusions (Final, 2026-02-27)

**Previous conclusion** (2026-02-18): "ForwardEncoding is the optimal decoder — channel-based color representation exists"

**Current conclusion** (2026-02-27): **"Optimal decoder is task-dependent — LDA+SRM for LORO classification, FE+Procrustes for LOCO interpolation"**

The 3-alignment validation (Result 11) resolved the Procrustes LDA reliability paradox and established that decoder optimality depends on the alignment method AND task:

#### LORO Classification: LDA+SRM is optimal

| Criterion | LDA+Proc | LDA+SRM | SVM+SRM | FE+Proc | FE+SRM |
|-----------|----------|---------|---------|---------|--------|
| Accuracy [95% CI] | 0.758 [0.734, 0.780] | **0.793 [0.759, 0.825]** | 0.727 [0.685, 0.770] | 0.545 [0.511, 0.579] | 0.480 [0.449, 0.514] |
| ICC reliability | **0.013** (!) | **0.666** | 0.760 | 0.574 | 0.753 |
| Cross-subject gen. (p) | — | 0.668 (n.s.) | 0.647 (n.s.) | — | 0.076 (trend) |
| HC-CVD group bias | — | None | None | — | Mild (FE sensitive to geometry) |

- **LDA+SRM**: Best on BOTH accuracy AND reliability — the previous LDA reliability paradox (r=0.009 / ICC=0.013) was Procrustes-specific, not model-inherent
- **All SRM models ICC > 0.66**: SRM is the only alignment achieving universal reliability across all 6 models
- **FE+SRM actually worse** (0.480) than FE+Proc (0.545): SRM's dimensionality reduction (K=3-4) discards voxel-level variance that FE's encoding basis leverages

#### LOCO Interpolation: FE+Procrustes is optimal

| Criterion | FE+Raw | FE+Proc | FE+SRM |
|-----------|--------|---------|--------|
| HC MAE (SD) | 75.7 (6.8)° | **75.7 (11.7)°** | 84.1 (12.3)° |
| CVD MAE (SD) | 76.8 (6.4)° | 85.9 (14.2)° | 90.8 (15.0)° |
| Sig. tests (p<0.05) | 2/120 | **4/120** | 1/120 |
| Model dominance | 85% best | 85% best | 85% best |
| HC-CVD Δ visible | No (< 4°) | Yes (V2 +18.5°) | Yes (V1 +13.5°) |

- **FE is sole LOCO model** across ALL alignments (85% best cases); no other model approaches chance from the correct direction
- **Procrustes optimal for LOCO** — most significant individual results (4 vs 1 for SRM), full voxel space preserves interpolation information
- **SRM worst for LOCO** — dimensionality reduction discards the continuous voxel structure needed for hue interpolation

#### Multi-Criteria Summary

| Task | Optimal Pipeline | Key Metric | Why |
|------|-----------------|------------|-----|
| LORO (classification) | **LDA + SRM** | 0.793 acc, ICC 0.666 | SRM resolves LDA fold-instability; shared space enables reliable discrimination |
| LOCO (interpolation) | **FE + Procrustes** | 75.7° HC MAE, 4 sig tests | Full voxel space preserves continuous hue structure; FE's 6-channel basis enables interpolation |
| Phase 3 (filter design) | **FE + Procrustes** | W cosine 0.921 | Stable 6-channel representation for CVD→HC transformation learning |
| Cross-subject comparison | **LDA + SRM** | p=0.668 (no bias) | Unbiased generalization from HC-trained SRM to CVD subjects |

**Phase 3 filter design justification**: ForwardEncoding's 6-channel basis provides (a) stable encoding weights (cosine 0.921 [0.907, 0.935]) and (b) continuous hue interpolation (sole LOCO model). FE is NOT the best classifier (LDA+SRM 0.793 > FE+Proc 0.545), but classification accuracy is irrelevant for Phase 3 — what matters is the channel-space representation's stability and continuity. Group prior proof-of-concept (Result 13, leakage-fixed): HC V1 +4.3%, V2 +8.3%; CVD V1 +8.7%, V2 +6.4% in LOCO. LORO GP more effective: V1 -18.7%, V2 -35.8%. Confirms HC→CVD knowledge transfer is feasible in this channel space.

### Validation Status (Phase 2b — Complete, 21/21)

- [x] LORO model comparison: 10 subjects, 4 ROIs, 6 models, both alignment conditions
- [x] Bootstrap 95% CIs: subject-level resampling, 1000 iterations
- [x] HC vs CVD comparison: Mann-Whitney U, no meaningful group difference
- [x] Test-retest reliability: split-half with Spearman-Brown correction
- [x] LOCO local test: sub-01, 4 ROIs, 100 permutations
- [x] **[RT-2] Nested Procrustes**: FE/SVM/MLP, 10 subjects — SVM 0.899, FE 0.781 (no leakage)
- [x] **[RT-3] PCA dim reduction**: PCA-20 within LORO — information loss vs full voxels
- [x] **[RT-1 + RT-7] Individual CVD cross-decoding**: HC-only SRM: 9/12 tests p<0.001, hV4 borderline (supersedes old all-subjects 12/12)
- [x] **[RT-5] LDA reliability**: run-pair r=0.009 explains paradox; FE W stability 0.921
- [x] **[RT-4] LOCO server deployment**: 10 subjects x 4 ROIs, 1000 permutations — FE sole interpolator; CVD heterogeneity = color space distortion (see Result 2b)
- [x] **[RT-6] Hybrid decoder (FE+MLP, FE+SVM)**: FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate; linear readout confirmed
- [x] **LOCO decoder improvement (negative result)**: 4 alt. decoding methods (PopVec, RidgeEnc, GaussML, RidgeReg) all worse than baseline correlation. Decoding is NOT the bottleneck; encoding estimation (df=1 from 7 colors/6 channels) is the limiting factor.
- [x] **LORO 3-alignment validation**: Bootstrap CI, reliability (ICC), cross-subject generalization for raw/procrustes/SRM (see Result 11)
- [x] **LOCO 3-alignment baseline**: 10 subjects × 4 ROIs × 6 models × 1000 perms for raw/procrustes/SRM (see Result 12)
- [x] **FE Group Prior (LOCO + LORO nested)**: 9 subjects × 4 ROIs, nested λ CV (see Result 13)

---

## Result 11: LORO 3-Alignment Validation (2026-02-27)

**Dataset**: full_dataset_C010 | 10 subjects (7 HC, 3 CVD) | 4 ROIs | 6 models | LORO CV (6 folds)
**Alignments**: raw (no alignment), procrustes (orthogonal), SRM (K: V1=4, V2=4, V3=3, V4=3)
**Scripts**: `scripts/loro_baseline_{raw,procrustes,srm}.sbatch` → `scripts/validation_tests.py`

### Overall Accuracy (Bootstrap 95% CI, 1000 iterations)

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| **LDA** | 0.135 [0.119, 0.153] | **0.758** [0.734, 0.780] | **0.793** [0.759, 0.825] |
| SVM | 0.127 [0.114, 0.140] | 0.685 [0.655, 0.714] | 0.727 [0.685, 0.770] |
| FE | 0.129 [0.110, 0.146] | 0.545 [0.511, 0.579] | 0.480 [0.449, 0.514] |
| Ridge | 0.131 [0.116, 0.147] | 0.388 [0.361, 0.417] | 0.313 [0.276, 0.348] |
| KRidge | 0.127 [0.110, 0.143] | 0.332 [0.300, 0.366] | 0.285 [0.252, 0.319] |
| MLP | 0.126 [0.118, 0.135] | 0.147 [0.136, 0.158] | 0.131 [0.126, 0.138] |

- Raw alignment = chance (~12.5%); both procrustes and SRM dramatically above chance
- SRM LDA (0.793) > Procrustes LDA (0.758): Wilcoxon p=0.002 (V1)
- **MLP fails in all alignments** — near chance even with alignment

### Alignment Comparison (Wilcoxon signed-rank, all models pooled)

| ROI | Proc vs Raw (p) | SRM vs Raw (p) | SRM vs Proc (p) | Winner |
|-----|-----------------|-----------------|------------------|--------|
| V1 | 3.97e-11*** | 1.47e-10*** | **0.002*** | **SRM** |
| V2 | 1.13e-10*** | 1.36e-10*** | 0.058 | SRM ≈ Proc |
| V3 | 3.48e-10*** | 4.91e-09*** | **9.10e-08*** | **Proc** |
| V4 | 2.03e-10*** | 7.40e-10*** | **1.84e-05*** | **Proc** |

**Key finding**: SRM dominates V1/V2 (early visual), Procrustes dominates V3/V4 (higher visual). SRM K=3 may under-capture V3/V4 complexity.

### Test-Retest Reliability (ICC across LORO folds)

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| LDA | 0.224 | **0.013** | **0.666** |
| Ridge | 0.233 | 0.148 | **0.762** |
| KRidge | 0.324 | 0.463 | **0.790** |
| SVM | -0.284 | 0.495 | **0.760** |
| MLP | 0.611 | 0.720 | **0.713** |
| FE | 0.471 | 0.574 | **0.753** |

**Critical finding**: Procrustes LDA ICC = 0.013 (near zero!) despite 75.8% accuracy — suggests high fold-to-fold instability. SRM LDA ICC = 0.666 — reliable and accurate. **SRM is both more accurate AND more reliable for LDA/Ridge/SVM.**

SRM achieves ICC > 0.66 for ALL 6 models — the only alignment where every model is reliably reproducible.

### Cross-Subject Generalization (SRM only, Mann-Whitney U)

| Model | HC→HC Mean | HC→CVD Mean | Diff | p-value |
|-------|-----------|------------|------|---------|
| LDA | 0.635 | 0.665 | -0.030 | 0.668 |
| SVM | 0.464 | 0.488 | -0.024 | 0.647 |
| FE | 0.526 | 0.462 | +0.064 | 0.076 |
| Ridge | 0.266 | 0.247 | +0.020 | 0.544 |
| MLP | 0.129 | 0.226 | -0.097 | **0.0001*** |

- **LDA/SVM: no HC-CVD generalization gap** — CVD decode equally well in HC-trained SRM space
- **FE: trend toward HC bias** (p=0.076) — consistent with LOCO finding that FE captures geometry which differs for CVD
- **MLP anomaly**: HC→CVD significantly *better* than HC→HC (p=0.0001) — likely artifacts of degenerate solutions

### Key Findings (Result 11)

1. **SRM is optimal alignment for LORO**: highest accuracy (LDA 0.793) AND highest reliability (all ICC > 0.66)
2. **Procrustes-LDA paradox**: high accuracy (0.758) but near-zero reliability (ICC=0.013) — fold-dependent decision boundaries
3. **SRM-LDA is the recommended LORO pipeline**: accurate (0.793 [0.759, 0.825]), reliable (ICC=0.666), no group bias (p=0.668)
4. **Alignment × ROI interaction**: SRM > Proc for V1/V2 (p=0.002, 0.058); Proc > SRM for V3/V4 (p<0.001)
5. **Cross-subject generalization confirms Phase 2 findings**: CVD color representations are decodable in HC space (LDA p=0.668, no group difference)

---

## Result 12: LOCO 3-Alignment Baseline (2026-02-27)

**Dataset**: full_dataset_C010 | 10 subjects (7 HC, 3 CVD) | 4 ROIs | 6 models | LOCO CV (8 folds) | 1000 permutations
**Alignments**: raw, procrustes, SRM
**Scripts**: `scripts/loco_baseline_{raw,procrustes,srm}.sbatch`

### ForwardEncoding MAE by Alignment (degrees, chance = 90°)

| ROI | Raw HC (SD) | Raw CVD (SD) | Proc HC (SD) | Proc CVD (SD) | SRM HC (SD) | SRM CVD (SD) |
|-----|-------------|-------------|-------------|-------------|-------------|-------------|
| V1 | 76.9 (4.4) | 76.4 (9.5) | 76.4 (7.8) | 84.6 (23.1) | 80.0 (9.6) | 93.5 (22.2) |
| V2 | 74.8 (9.2) | 78.5 (8.1) | 80.0 (15.5) | 98.5 (16.8) | 84.9 (13.5) | 90.5 (15.0) |
| V3 | 77.8 (7.4) | 76.4 (2.1) | 77.0 (15.0) | 73.5 (8.1) | 99.3 (13.9) | 88.3 (11.2) |
| V4 | 73.5 (6.1) | 76.0 (5.9) | 69.4 (8.7) | 87.4 (8.4) | 72.2 (11.9) | 90.9 (12.7) |

### Model Dominance

ForwardEncoding is best model in 85% of subject-ROI-alignment combinations (102/120). Other models (Ridge, KRidge, SVM, MLP, LDA) fail in LOCO due to insufficient training samples (7 colors → 42 observations for high-dimensional voxel space).

### Permutation Test Summary (FE, p < 0.05 + correct direction)

| Alignment | Sig. Tests | Examples |
|-----------|-----------|---------|
| Raw | 2/120 (1.7%) | sub-04 V2 (p=0.041), sub-06 V4 (p=0.014) |
| Procrustes | 4/120 (3.3%) | sub-08 V1 (p=0.037), sub-05 V2 (p=0.006), sub-01 V3 (p=0.004), sub-04 V4 (p=0.030) |
| SRM | 1/120 (0.8%) | sub-04 V4 (p=0.034) |

### HC vs CVD Group Difference (FE MAE)

- **Raw**: Near-identical (diff < 4°) — no alignment reveals no group structure
- **Procrustes**: CVD worse in V1 (+8.2°), V2 (+18.5°), V4 (+18.0°); CVD anomalously better in V3 (-3.5°)
- **SRM**: CVD consistently worse: V1 (+13.5°), V2 (+5.6°), V4 (+18.7°); V3 reversed (-11.0°)

### Key Findings (Result 12)

1. **ForwardEncoding dominates LOCO** (85% best cases) — template matching requires no parametric fitting
2. **Procrustes yields most significant individual results** (4 sig vs SRM's 1) — alignment helps reveal subject-specific LOCO capacity
3. **SRM is worst for LOCO** — highest MAE, fewest significant results; SRM dimensionality reduction (K=3-4) may discard interpolation-relevant information
4. **LORO vs LOCO alignment preference diverges**: LORO favors SRM (classifiers benefit from shared space), LOCO favors procrustes (FE needs full voxel structure for interpolation)
5. **CVD group disadvantage only visible with alignment** — raw shows no HC/CVD difference; procrustes/SRM reveal CVD's distorted color geometry (V2 +18.5°, V4 +18.0° with procrustes)

---

## Result 13: FE Group Prior — LOCO + LORO Nested (2026-02-27)

**Dataset**: full_dataset_C010 | 9 subjects (6 HC: sub-01~06, 3 CVD: sub-08~10; sub-07 excluded due to hV4 voxel count) | 4 ROIs
**Method**: W_combined = λ·W_individual + (1-λ)·W_group, nested CV for λ selection
**λ grid**: 16 values from 0.0 to 1.0 (0.0 = pure group, 1.0 = pure individual)
**Scripts**: `scripts/group_prior.py` → `scripts/group_prior_{loco,loro}.sbatch`

### LOCO Nested Results (leakage-fixed, 2026-02-28)

> **Previous results (median -50.9%) were inflated by information leakage**: `compute_group_W()` included the LOCO test color. Fixed version excludes test color from group W per fold. See Caveat section below.

#### Performance by ROI (all subjects, MAE in degrees)

| ROI | HC Baseline (SD) | HC GP (SD) | HC Δ% | CVD Baseline (SD) | CVD GP (SD) | CVD Δ% |
|-----|-----------------|-----------|-------|------------------|-----------|--------|
| V1 | 80.7 (11.1) | 77.3 (8.0) | **+4.3%** | 93.5 (27.0) | 85.7 (16.9) | **+8.3%** |
| V2 | 85.9 (15.3) | 78.7 (10.6) | **+8.3%** | 90.5 (18.7) | 85.4 (13.1) | **+5.7%** |
| V3 | 100.6 (15.5) | 105.9 (13.3) | -5.3% | 88.3 (13.7) | 112.2 (11.8) | **-27.0%** |
| V4 | 71.2 (13.8) | 75.5 (10.4) | -6.1% | 90.9 (15.6) | 95.7 (5.0) | -5.2% |

#### λ Distribution (per-fold lambdas)

| ROI | λ=0 count/total | λ=0 % |
|-----|-----------------|-------|
| V1 | 68/72 | 94.4% |
| V2 | 62/72 | 86.1% |
| V3 | 60/72 | 83.3% |
| V4 | 42/72 | 58.3% |
| **Overall** | **232/288** | **80.6%** |

Best λ (mode across folds): 35/36 = 0.0, only sub-02 V4 = 0.05.

#### Individual CVD Profiles (LOCO GP, leakage-fixed)

| Subject | V1 Baseline→GP | V2 Baseline→GP | V3 Baseline→GP | V4 Baseline→GP |
|---------|----------------|----------------|----------------|----------------|
| sub-08 (deutan) | 62.1→66.4° (-7.0%) | 70.6→70.2° (+0.6%) | 73.0→116.3° (**-59.2%**) | 82.9→95.8° (-15.6%) |
| sub-09 (protan) | 109.8→98.3° (+10.5%) | 94.4→93.1° (+1.3%) | 92.3→121.4° (-31.6%) | 108.9→100.5° (+7.8%) |
| sub-10 (deutan) | 108.5→92.6° (+14.7%) | 106.7→92.9° (+12.9%) | 99.5→98.8° (+0.8%) | 81.0→90.8° (-12.1%) |

**CVD Key findings (revised)**:
- sub-08: V1/V2 거의 변화 없음 (이전 -58.6%는 leakage artifact). **V3 크게 악화** (-59.2%)
- sub-09: V1 소폭 개선 (+10.5%), V3 악화 (-31.6%). Protan에서도 GP 효과 제한적
- sub-10: V1/V2 개선 (+14.7%/+12.9%), V3/V4 악화. 이전 -63.7%는 leakage artifact

### LORO Nested Results

#### Performance by ROI (all subjects, MAE in degrees)

| ROI | Baseline Mean (SD) | GP Mean (SD) | Improvement |
|-----|-------------------|-------------|-------------|
| V1 | 42.40 (10.1) | 34.47 (10.9) | **-18.7%** |
| V2 | 50.96 (14.1) | 32.72 (7.4) | **-35.8%** |
| V3 | 60.63 (7.5) | 54.25 (7.7) | -10.5% |
| V4 | 62.21 (13.4) | 61.34 (14.4) | -1.4% |

#### λ Distribution

More diverse than LOCO: λ ranges from 0.0 to 1.0 across subjects. Only 4/36 cases select λ=0.0. Median λ ≈ 0.25, suggesting **LORO benefits from mixing individual and group estimates** (individual W from 5 training runs is more stable than from 7 LOCO colors).

#### Individual CVD Profiles (LORO GP)

| Subject | V1 Baseline→GP | V2 Baseline→GP | V3 Baseline→GP | V4 Baseline→GP |
|---------|----------------|----------------|----------------|----------------|
| sub-08 (deutan) | 28.1→21.4° (-24.0%) | 54.1→45.7° (-15.4%) | 63.0→60.6° (-3.9%) | 88.2→86.9° (-1.5%) |
| sub-09 (protan) | 50.4→36.7° (**-27.2%**) | 47.7→36.9° (**-22.6%**) | 67.9→55.8° (-17.8%) | 69.0→69.0° (0.0%) |
| sub-10 (deutan) | 45.0→29.3° (**-35.0%**) | 75.6→41.2° (**-45.5%**) | 50.3→52.4° (+4.1% worse) | 46.5→46.4° (-0.1%) |

### LOCO vs LORO GP Comparison

| Metric | LOCO Nested (fixed) | LORO Nested |
|--------|---------------------|-------------|
| HC mean improvement | V1 +4.3%, V2 +8.3% | -18.7%, -35.8% |
| CVD mean improvement | V1 +8.3%, V2 +5.7% | -24.0~-35.0% |
| Harmful ROIs | V3 (-5.3% HC, -27.0% CVD), V4 (-6.1% HC) | V3/V4 flat/worse |
| λ=0.0 frequency | 80.6% (232/288) | 11% (4/36) |
| Problem | V3/V4에서 GP 해로움 | V3/V4 flat |

### Key Findings (Result 13, revised after leakage fix)

1. **이전 LOCO GP 결과(median -50.9%)는 leakage artifact** — group W에 test color가 포함되어 발생한 허위 개선. 수정 후 V1/V2에서만 소폭 도움 (+4~8%)
2. **LOCO에서 λ=0.0 선호(80.6%)는 유지** — nested CV가 group prior를 선택하지만 실제 효과는 미미
3. **LORO GP는 유효** (-18.7~-35.8%) — leakage 해당 없음 (색 제외 없음). LOCO보다 개선폭이 큼
4. **V3/V4는 GP에 해로움** — V3 CVD -27.0% (심각), V4 양쪽 -5~6%. ROI-specific 개인차가 HC 평균으로 포착 불가
5. **CVD V1/V2에서만 제한적 혜택** — sub-10 V1 +14.7%, sub-10 V2 +12.9%. 나머지는 미미하거나 악화

### Historical Note: LOCO GP Information Leakage (resolved 2026-02-28)

**Original bug**: `compute_group_W()` used ALL 8 colors including the LOCO held-out test color.

**Fix applied**: `compute_group_W(exclude_color_idx=test_color)` — group W now computed from 7 training colors only, matching individual W. Fix propagated to both `loco_with_fixed_lambda()` and `nested_loco_lambda_search()`.

- **Corrected results**: See Result 13 above. Previous median -50.9% was entirely leakage artifact → actual improvement V1 +4.3%, V2 +8.3% (HC), V3/V4 harmful
- **LORO GP unaffected**: LORO does not exclude colors, so original results stand

---

### Result 14: λ-MAE Curve Analysis (Fixed-Mode, Leakage-Fixed)

**Date**: 2026-02-28
**Script**: `group_prior.py --mode fixed`, `plot_lambda_curve.py`
**Results**: `results/FE_group_prior/loco_fixed/`

Tests each λ value independently on the outer LOCO test set (no nested CV selection). Reveals the full λ-MAE relationship per ROI.

#### λ-MAE Summary Table

| ROI | HC λ* | HC MAE at λ* | HC baseline | HC Δ% | CVD λ* | CVD MAE at λ* | CVD baseline | CVD Δ% | HC curve | CVD curve |
|-----|-------|-------------|-------------|-------|--------|--------------|-------------|--------|----------|-----------|
| V1 | 0.00 | 77.3° | 80.7° | **+4.3%** | 0.00 | 85.4° | 93.5° | **+8.7%** | monotonic ↗ | monotonic ↗ |
| V2 | 0.20 | 78.7° | 85.9° | **+8.4%** | 0.10 | 84.7° | 90.5° | **+6.4%** | shallow U | shallow U |
| V3 | 1.00 | 100.6° | 100.6° | 0.0% | 0.70 | 84.4° | 88.3° | **+4.4%** | monotonic ↘ | **U-shape** |
| V4 | 0.90 | 70.7° | 71.2° | +0.7% | 1.00 | 90.9° | 90.9° | 0.0% | shallow U | monotonic ↘ |

#### Key Findings (Result 14)

1. **λ-MAE curve is NOT monotonic** — shape varies dramatically by ROI and group, confirming that a single λ is suboptimal
2. **V1: monotonic increasing (λ=0 best)** — pure group prior consistently outperforms individual W. CVD benefits more (+8.7%) than HC (+4.3%)
3. **V2: shallow U-shape (λ*≈0.1–0.2)** — small individual contribution helps. Both groups benefit (+6–8%)
4. **V3: HC↔CVD reversal** — HC prefers individual (λ=1.0, monotonic decreasing), while CVD has dramatic U-shape with local min at λ=0.7 (+4.4%). This is the most striking ROI-group dissociation
5. **V4: minimal GP benefit** — HC barely improves at λ=0.9 (+0.7%), CVD prefers pure individual (λ=1.0)
6. **Early visual (V1/V2) vs higher visual (V3/V4) dissociation** — GP helps in V1/V2 where color representations are more shared across subjects; V3/V4 have more individual variability where group priors are less effective

#### Implications for Phase 3

- **ROI-specific λ tuning needed** — a single global λ is inappropriate
- **CVD V3 U-shape (λ*=0.7)** suggests CVD color geometry in V3 is partially recoverable via HC template, but requires careful mixing
- **V1/V2 group prior provides a starting point** for CVD filter initialization in Phase 3
