# Group-Prior Prediction Model — PLAN

> Last updated: 2026-03-09
> Status: Implementation complete; awaiting server deployment
> Phase: Future Phase 1 — Forward Model (SRQ3)

---

## 0. Why Procrustes-Based Prediction (Brief)

Prediction must operate in **Procrustes voxel space**, not SRM. Four reasons:

1. **SRM destroys interpolation structure** — LOCO MAE comparison:

| ROI | Procrustes | SRM | Delta |
|-----|-----------|-----|-------|
| V1 | ~76° | ~80° | +4° |
| V2 | ~80° | ~85° | +5° |
| V3 | ~77° | **~99°** | **+22°** (worse than chance 90°) |
| hV4 | ~69° | ~72° | +3° |

2. **SRM maps voxel → latent**, not stimulus → representation. Prediction requires `theta → Y`.
3. **SRM filters operate latent → latent**, but we need `theta → theta'` (stimulus-space correction).
4. **SRM remains valid as a cross-subject alignment tool** — used here only for prior construction.

**SRM's role in this phase**: Prior-construction helper. Not prediction space, not evaluation space.

---

## 1. Notation

For each subject *s* and ROI *r*:

| Symbol | Shape | Meaning |
|--------|-------|---------|
| V_s | scalar | Number of voxels (varies per subject) |
| N | scalar | Number of conditions (= 8 colors × 6 runs, or 8 colors if averaged) |
| K | scalar | Number of basis channels (= 6) |
| Y_s | V_s × N | Procrustes-aligned voxel responses (`amplitudes_procrustes.npy`) |
| C | K × N | Color basis matrix (half-wave rectified cosine, Brouwer & Heeger 2009) |
| W_s | V_s × K | Subject-specific encoding weight (the thing we learn) |
| k | scalar | SRM latent dimension (V1=4, V2=4, V3=3, hV4=3) |
| R_s | V_s × k | SRM projection matrix for subject s (`srm.w_` from BrainIAK) |
| Z_i | k × N | Common-space response for HC subject i |
| A_i | k × K | Common-space encoding weight for HC subject i |
| A_g | k × K | Group prior (mean of A_i across HC) |
| W_{0,s} | V_s × K | Prior weight projected to target subject's voxel space |

**Prediction equation**:

```
Y_hat_s = W_s @ C
```

> **Transpose convention note**: Existing code (loco_baseline.py, group_prior.py) uses W ∈ R^{K×V_s} (channels × voxels). This document uses W_s ∈ R^{V_s×K} (voxels × channels). Implementation must transpose accordingly.

---

## 2. Why Direct Mixing Fails

The naive approach:

```
W_mix = alpha * W_group + (1-alpha) * W_subject
```

**does not work** because subjects have different voxel counts:

```
W_group   ∈ R^{V_g × K}
W_subject ∈ R^{V_s × K}
```

where V_g ≠ V_s in general. These matrices live in different spaces and cannot be directly combined.

> **Note**: The existing `group_prior.py` (`analysis/phase3_decoder_comparing/model_comparison_validation/scripts/`) sidesteps this by operating in SRM space (`amplitudes_srm.npy`), performing `W = λ·W_ind + (1-λ)·W_group` where both are K×k matrices. This violates the Procrustes principle — SRM space destroys interpolation structure (Section 0).

**Solution**: Construct the prior in a common space, project it to the target subject's voxel space, then fine-tune there.

---

## 3. Algorithm

### Step A: HC Common-Space Construction

For HC subjects i = 1, ..., M (M = 7), with Procrustes-aligned data:

```
Y_i ∈ R^{V_i × N}
```

Fit SRM (BrainIAK, HC-only training) to obtain projection matrices:

```
R_i ∈ R^{V_i × k}
```

Project to common space:

```
Z_i = R_i^T @ Y_i ∈ R^{k × N}
```

This maps all subjects to the same k-dimensional space regardless of voxel count.

**Source**: SRM fitting uses `srm_alignment.py` (`analysis/phase2_SRM_across_between/utils/`). k values: V1=4, V2=4, V3=3, hV4=3 (confirmed via mean rank aggregation, Phase 2).

### Step B: Group Prior in Common Space

For each HC subject, learn the common-space encoding:

```
A_i = argmin_A ||Z_i - A @ C||_F^2 + lambda_A * ||A||_F^2
```

where A_i ∈ R^{k × K}.

Then average to form the group prior:

```
A_g = (1/M) * sum_{i=1}^{M} A_i
```

**Default**: Simple mean (omega_i = 1/M).

**Optional weighted variant**: omega_i = r_sh(i) / sum_j r_sh(j), where r_sh(i) is subject i's split-half RDM reliability for the current ROI. This downweights subjects with noisier representations.

**Recommendation**: Start with simple mean. With M=7, one noisy subject has limited influence on the average. Switch to weighted only if leave-one-out analysis shows one subject disproportionately degrades A_g quality.

### Step C: Project Prior to Target Subject Space

For target subject s with SRM projection R_s ∈ R^{V_s × k}:

```
W_{0,s} = R_s @ A_g ∈ R^{V_s × K}
```

Dimensions: R_s (V_s × k) @ A_g (k × K) → W_{0,s} (V_s × K).

**This is the key insight**: Despite different voxel counts, the common-space detour produces a prior W_{0,s} that lives in the target subject's own voxel space.

For new/CVD subjects, R_s is obtained via SVD-based projection (as in `rerun_loo_consistent.py` from Phase 2).

### Step D: Fine-Tune with Prior-Centered Ridge

Learn a single subject-specific weight matrix:

```
W_s = argmin_W ||Y_s - W @ C||_F^2 + lambda * ||W - W_{0,s}||_F^2
```

- First term: fit target subject's actual data
- Second term: stay close to group prior

**Closed-form solution** (normal equations):

```
W_s @ (C @ C^T + lambda * I) = Y_s @ C^T + lambda * W_{0,s}
```

Therefore:

```
W_s = (Y_s @ C^T + lambda * W_{0,s}) @ (C @ C^T + lambda * I)^{-1}
```

**lambda controls the prior-individual balance**:
- lambda = 0: pure subject-specific fit (OLS, no prior)
- lambda → ∞: W_s ≈ W_{0,s} (prior-only, zero-shot transfer)

---

## 4. Validation

All evaluation is in **Procrustes voxel space**, since the prediction itself is Y_hat = W_s @ C.

### A. LORO: Run Generalization

**Question**: Does prediction generalize to new runs of the same subject?

**Procedure**:
1. Train W_s using 5 of 6 runs
2. Predict held-out run: Y_hat = W_s @ C
3. Compare voxel patterns

**Metric**: r_LORO = corr(v_pred, v_real) per color, averaged across folds

### B. LOCO: Color Interpolation

**Question**: Can the model predict responses to unseen colors?

**Procedure**:
1. Hold out 1 of 8 colors
2. Train W_s using 7 remaining colors
3. Predict held-out color's voxel pattern

**Metrics**:
- r_LOCO = corr(v_pred, v_real) per held-out color
- MAE_LOCO = angular decoding error (circular mean absolute error)

This is the most directly relevant validation for the filter pipeline.

### C. LOSO: Subject Transfer

**Question**: How well does the group prior transfer to a new subject with limited/no data?

Three conditions:

| Condition | Formula | What it tests |
|-----------|---------|--------------|
| Zero-shot | W_s = W_{0,s} | Prior alone (lambda → ∞) |
| Few-shot / fine-tuned | argmin ||Y_s - WC||² + lambda·||W - W_{0,s}||² | Prior + subject data |
| Subject-only | argmin ||Y_s - WC||² | No prior (lambda = 0) |

### Metrics (ranked by priority)

| Priority | Metric | Formula | Purpose |
|----------|--------|---------|---------|
| 1st | Voxel prediction correlation | corr(v_pred, v_real) | Primary quality measure |
| 2nd | Explained variance | R² = 1 - ||v - v_hat||² / ||v - v_bar||² | Variance accounted for |
| 3rd | LOCO angular MAE | MAE_LOCO | Interpolation accuracy |
| 4th | Predicted vs real RDM correlation | corr(RDM_pred, RDM_real) | Geometry preservation |
| 5th | Normalized geometry fit | corr(RDM_pred, RDM_real) / RDM_ceiling | Ceiling-relative performance |

### Reliability-Aware Support Metrics

A reviewer will ask: "Is poor prediction due to a bad model, or noisy data?" Reliability metrics answer this by establishing the ceiling.

| Metric | Formula | Purpose |
|--------|---------|---------|
| RDM noise ceiling | Upper: corr(RDM_single_run, RDM_group_mean). Lower: corr(RDM_LOO_mean, RDM_full_mean) | Maximum achievable RDM correlation given measurement noise |
| Normalized fit | corr(RDM_pred, RDM_real) / RDM_ceiling | Model quality relative to data quality — enables fair ROI comparison |
| Split-half geometry reliability | corr(RDM_odd_runs, RDM_even_runs) | Data quality per subject × ROI |

**Why this matters**: Without a noise ceiling, ROI comparisons are confounded by data quality. V4 may appear better than V1 simply because its RDM is more reliable, not because the model is better. Normalized fit allows fair comparison across ROIs with different noise levels.

---

## 5. Encoding Basis Ablation

**Question**: Why 6-channel cosine tuning? Is it optimal, or would a different basis work better?

| Model | Stimulus basis | K | Description |
|-------|---------------|---|-------------|
| FE-6 | Half-wave rectified cosine | 6 | Brouwer & Heeger (2009), current default |
| LF-4 | Low-frequency Fourier | 4 | cos(θ), sin(θ), cos(2θ), sin(2θ) |
| LF-6 | Low-frequency Fourier | 6 | Up to 3rd harmonic |

All models predict the same target: `Y_hat_s = W_s @ C` where C differs per basis.

**Evaluation**: Same metrics as Section 4 (voxel correlation, R², LOCO MAE, RDM correlation, normalized fit) applied to each basis × each CV protocol.

**Key questions**:
- Is 6-channel tuning necessary, or is a 4-parameter model sufficient?
- Does CVD distortion predominantly affect low-frequency components?
- Does a Fourier basis better match the downstream filter parameterization (T_psi uses Fourier terms)?

### Recommended 2-Stage Design

**Stage 1 — Basis screening** (fixed model: Subject-only OLS):

|         | LORO r         | LOCO r         | LOCO MAE       |
|---------|----------------|----------------|----------------|
|         | V1  V2  V3  V4 | V1  V2  V3  V4 | V1  V2  V3  V4 |
| FE-6    |  .   .   .   . |  .   .   .   . |  .   .   .   . |
| LF-4    |  .   .   .   . |  .   .   .   . |  .   .   .   . |
| LF-6    |  .   .   .   . |  .   .   .   . |  .   .   .   . |

Values: mean ± SEM across 10 subjects. Bold = best per column.

**Stage 2 — Full model comparison** with winning basis from Stage 1.
→ Proceed to §6 comparison experiment.

**Rationale**: Full factorial (3 × 5 × 3 × 4 = 180 cells) is impractical to interpret with N=10. Two stages isolate the encoding-basis question before adding model complexity.

---

## 6. Comparison Experiment

**Design**: 5 models × 3 CV protocols × 4 ROIs (× 3 encoding bases optionally)

### Models

| Model | Regularization | W_s | Purpose |
|-------|---------------|-----|---------|
| Subject-only OLS | lambda = 0 | OLS fit, no regularization | Baseline |
| Standard Ridge | ||W||² (shrink to zero) | Ridge with GCV-selected alpha | Tests whether generic shrinkage suffices |
| Prior-only | lambda → ∞ | W_{0,s} = R_s @ A_g | Zero-shot group prior transfer |
| Prior + fine-tuning | ||W - W_{0,s}||² | Closed-form with optimal lambda | **Proposed method** |
| Standard Ridge + GCV | ||W||² with analytical alpha | GCV-selected (existing loco_ridge.py) | Strongest simple baseline |

> **Why standard ridge is critical**: If prior-centered ridge (||W - W_{0,s}||²) does not beat standard ridge (||W||²) by a meaningful margin, the SRM-mediated prior construction adds complexity without benefit. This comparison isolates the prior's contribution from generic regularization.

### CV Protocols

| Protocol | Held-out | Train set |
|----------|----------|-----------|
| LORO | 1 run | 5 runs (same subject, all 8 colors) |
| LOCO | 1 color | 6 runs × 7 colors (same subject) |
| LOSO | 1 subject | All HC data (group prior transfer) |

### Expected Outcomes

- **Prior-only > Subject-only OLS** when subject data is scarce (LOSO)
- **Prior + fine-tuning >= Standard Ridge** in all conditions (prior provides structured regularization beyond generic shrinkage)
- **Prior + fine-tuning >> Subject-only OLS** for CVD subjects (group prior regularizes noisy individual estimates)
- **Standard Ridge > Subject-only OLS** in LOCO (small training set benefits from regularization)

---

## Implementation

### Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `utils_forward_model.py` | Shared utilities (constants, basis, fitting, metrics) | **DONE** |
| `step_a_fit_srm.py` | SRM on HC subjects → R_i matrices | **DONE** |
| `check_rs_stability.py` | R_s split-half stability check (gate before Steps B-D) | **DONE** |
| `step_b_group_prior.py` | Common-space encoding A_i → group prior A_g | **DONE** |
| `step_c_project_prior.py` | W_{0,s} = R_s @ A_g for each target subject | **DONE** |
| `step_d_finetune.py` | Prior-centered ridge → W_s per subject | **DONE** |
| `validate_loro_loco_loso.py` | LORO + LOCO evaluations for 4 models | **DONE** |
| `run_step1_srm.sbatch` | SLURM wrapper: Step A + stability gate | **DONE** |
| `run_step2_prior.sbatch` | SLURM wrapper: Step B + C | **DONE** |
| `run_step3_finetune.sbatch` | SLURM wrapper: Step D (array 1-10) | **DONE** |
| `run_step4_validate.sbatch` | SLURM wrapper: validation (array 1-10) | **DONE** |
| `run_all.sh` | Sequential SLURM dependency orchestrator | **DONE** |

### Data Dependencies

| Data | Path (server) | Shape | Source |
|------|--------------|-------|--------|
| Procrustes amplitudes | `derivatives/full_dataset_C010/{sub}/{ROI}/amplitudes_procrustes.npy` | (6, 8, V_s) | Phase 1 |
| SRM projection matrices | To be saved by step_a | (V_s, k) per subject | Step A |
| Color basis | Generated by `create_basis_functions()` | (K, N) | `utils/utils_color_decoding.py` |

### Directory Structure

```
future_phase1_forward_model/
├── PLAN.md                          # This document
├── notion.md                        # Algorithm documentation (Korean)
├── README.md                        # Phase overview
├── scripts/
│   ├── step_a_fit_srm.py
│   ├── check_rs_stability.py
│   ├── step_b_group_prior.py
│   ├── step_c_project_prior.py
│   ├── step_d_finetune.py
│   ├── validate_loro_loco_loso.py
│   └── run_comparison.sbatch
└── results/
    ├── srm_projections/             # R_i matrices
    ├── group_prior/                 # A_g per ROI
    ├── subject_weights/             # W_s per subject-ROI
    └── validation/                  # LORO/LOCO/LOSO results
```

### lambda Selection

- **Nested CV**: Within each outer fold, inner loop selects lambda from grid [0, 0.01, 0.1, 1, 10, 100, 1000]
- **Alternative**: Analytical GCV (generalized cross-validation) if applicable
- Report optimal lambda per ROI and per subject

### Existing Code Reuse

| Function | Source | Reuse |
|----------|--------|-------|
| `create_basis_functions(n_channels=6)` | `analysis/utils/utils_color_decoding.py` | Basis matrix C |
| SRM fitting | `analysis/phase2_SRM_across_between/utils/srm_alignment.py` | Step A |
| `fit_W()` | `analysis/phase3_decoder_comparing/LOCO_trials/scripts/loco_ridge.py` | Reference for OLS/ridge fitting |
| SVD projection for new subjects | `rerun_loo_consistent.py` (Phase 2) | R_s for CVD subjects |

---

## 7. Gate Criteria

An ROI is considered **usable for downstream filter design** if it satisfies three independent conditions:

| Criterion | Metric | Threshold | Purpose |
|-----------|--------|-----------|---------|
| Geometry reliability | Split-half RDM correlation | > 0.3 | Data quality sufficient for model fitting |
| Prediction quality | Normalized geometry fit (pred RDM corr / ceiling) | > 0.3 | Model captures available structure |
| Interpolation stability | LOCO voxel correlation (prior+finetune model) | > 0 (above chance, p < 0.05 by permutation) | Generalization to unseen colors |

**Gate rule**: All 3 criteria must pass. Failure on criterion 1 (reliability) means the data is too noisy — no model can help. Failure on criteria 2-3 means the model is inadequate.

**Advantage over previous gate**: The old gate used absolute thresholds on 5 structural metrics (MAE < 90°, trajectory r > 0.6, etc.), which mixed data quality with model quality. This gate separates them: reliability tells us about the data, normalized fit tells us about the model.

### Failure Analysis Protocol

When an ROI fails the gate, diagnose *why*:

| Gate failure | Interpretation | Diagnostic |
|---|---|---|
| Criterion 1 (reliability < 0.3) | Data too noisy | No model fix possible — need better data or more runs |
| Criterion 2 (normalized fit < 0.3) | Model captures little structure | Per-channel encoding quality: corr(W_s[:,k] @ C[k,:], Y_s) per channel k — identifies which basis channels fail |
| Criterion 3 (LOCO r ≤ 0) | Interpolation fails | Residual analysis: is (Y_s - W_s @ C) structured or random? Structured residual → systematic encoding failure; random → voxel noise exceeds signal |

This separates **encoding model inadequacy** from **measurement noise**.

---

## 8. Relationship to Filter Pipeline

The best W_s from this phase feeds directly into Phase 2 as the **prediction engine**:

```
theta → C(theta) → W_s @ C(theta) = Y_hat_s(theta)
```

Phase 2 designs T_psi (stimulus-space filter) that operates **upstream** of W_s:

```
theta → T_psi(theta) → C(T_psi(theta)) → W_s @ C(T_psi(theta))
```

**SRM is no longer required for filter evaluation**. Since W_s produces predictions in Procrustes voxel space, filter quality can be assessed by voxel-level metrics (correlation, R²) without projecting to SRM. SRM may optionally be used for cross-subject comparison, but it is not part of the core prediction or evaluation path.

This is a fundamental simplification from the previous M_s bridge approach.

> **Critical constraint**: Prediction model W_s is frozen before filter optimization begins. Filter T_ψ operates only in stimulus space — it does not modify, retrain, or fine-tune W_s. The optimization objective is min_ψ L(W_s @ C(T_ψ(θ)), Y_target) with W_s fixed.

### Filter Family Ablation (Phase 2 scope, referenced here)

The filter itself is designed in Phase 2, but the prediction model must support comparison across filter families:

| Filter | Parameters | Description |
|--------|-----------|-------------|
| Identity | 0 | No correction (baseline) |
| Fourier-4 | 4 | a1·cos(θ) + b1·sin(θ) + a2·cos(2θ) + b2·sin(2θ) |
| Fourier-6 | 6 | Up to 3rd harmonic |
| GP (optional) | nonparametric | Gaussian process baseline |

Key questions for filter ablation:
- Is correction actually necessary? (Identity vs Fourier-4)
- Are 4 parameters sufficient? (Fourier-4 vs Fourier-6)
- Does a more flexible model overfit? (Fourier-6 vs GP)

---

## 9. Planned Ablations and Open Questions

> Added: 2026-03-09. Items to run **after** baseline pipeline (Steps 1-4) produces initial results.

### 9a. Prior Source Ablation (Q1)

The baseline pipeline uses SRM-mediated group prior (A_g → W_{0,s} = R_s @ A_g). The question: **is this the best way to construct a prior?**

| Prior variant | Construction | What it tests | Priority |
|---------------|-------------|---------------|----------|
| No prior (OLS) | lambda = 0 | Already in baseline 4-model comparison | Covered |
| Standard ridge (shrink to zero) | ||W||² penalty | Already in baseline | Covered |
| **SRM-mediated A_g** (proposed) | R_s @ mean(A_i) | Already in baseline | Covered |
| **Lambda sweep** | Vary lambda across wider range | Sensitivity of prior weight | **After baseline** |
| **Cross-ROI prior** | Use V4's A_g to inform V1, etc. | Does ROI-specific prior matter? | **After baseline** |
| **Weighted A_g** | omega_i = reliability / sum(reliability) | Downweight noisy HC subjects | **After baseline, if prior_finetune wins** |

**Decision rule**: Only pursue alternative priors if `prior_finetune > ridge_gcv` in baseline. If standard ridge already matches prior_finetune, the prior construction method is moot regardless of source.

### 9b. Per-Protocol Model Conclusions (Q2)

Each CV protocol answers a distinct question. Results reporting must emphasize **which model wins per protocol**, not just overall:

| Protocol | Question | Expected winner | Report format |
|----------|----------|-----------------|---------------|
| **LORO** | Run generalization | prior_finetune or ridge_gcv | Best model per ROI × subject group |
| **LOCO** | Color interpolation | prior_finetune (prior regularises sparse training) | Best model per ROI × subject group |
| **LOSO** | Group prior transfer | prior_only (by definition, no subject data) | HC-only: LOO consistency check |

If the same model wins across all three protocols, that strengthens the case. If different models win for different protocols, this is informative — e.g., prior_finetune winning LOCO but not LORO suggests the prior specifically helps interpolation (the target use case).

### 9c. Encoding Basis Channel Ablation (Q3)

Already described in Section 5. Additional detail:

**Specific hypothesis**: 4-channel Fourier basis (LF-4) may match or exceed 6-channel FE for LOCO interpolation, because:
- Fewer parameters = less overfitting with 7 training colors per fold
- Fourier basis aligns with the filter parameterization (T_psi uses cos/sin terms)

**Test**: Compare FE-6 vs LF-4 in OLS-only LOCO (simplest model, isolates basis effect). If LF-4 ≥ FE-6, adopt LF-4 as default and rerun full model comparison.

**Implementation**: `create_basis_matrix()` already accepts `n_channels`. Add `--n_channels` and `--basis_type` arguments to validation script.

### 9c-result. Basis Ablation Result (RESOLVED 2026-03-09)

**Result**: FE-6 > LF-4 > LF-6. Paired t-test (LOCO OLS, n=10): V1 p=0.045, V2 p=0.042, hV4 p=0.016. Half-wave rectified cosine better captures peaked neural tuning. **FE-6 confirmed as default.**

### 9f. LOCO Metric Reinforcement (Q7 — NEW, 2026-03-09)

**Motivation**: HC LOCO ridge_gcv voxel_corr = 0.130 (V1). While statistically significant (p=0.012), r²=0.017 means only 1.7% variance explained. Reviewers will challenge whether this is meaningful. Four reinforcement analyses planned:

#### 9f-1. Permutation Test (Priority: HIGH)

**Problem**: One-sample t-test with n=7 assumes normality — risky with small samples.

**Method**: For each of 10,000 iterations:
1. Within each subject, shuffle color labels across the 8 conditions (preserving run structure)
2. Refit ridge_gcv W on shuffled labels
3. Compute LOCO voxel_corr under shuffled model
4. Build null distribution of mean(HC LOCO_r) under H0: no color structure

**Output**: Non-parametric p-value = fraction of null ≥ observed. If permutation p < 0.05 when parametric p = 0.012, the result is robust.

**Implementation**: Add `--permutation_test --n_perms 10000` to `validate_loro_loco_loso.py`. Save null distribution for plotting.

#### 9f-2. Per-Color LOCO Breakdown (Priority: HIGH)

**Question**: Is the average LOCO driven by a few easy colors, or is it uniform?

**Method**: Report LOCO voxel_corr for each of 8 held-out colors, averaged across HC subjects.

**Expected patterns**:
- Colors with close neighbors on the hue circle (e.g., red-orange, 45° apart) should interpolate better
- Colors opposite to many training colors (e.g., cyan, 180° from red) may interpolate worse
- If 2-3 colors drive the entire mean, the "continuous representation" claim weakens

**Output**: 8-color bar plot per ROI. Test: is the per-color distribution uniform (Friedman test)?

**Implementation**: Already available in per-fold LOCO results — just need aggregation script.

#### 9f-3. Residual Structure Analysis (Priority: MEDIUM)

**Question**: Is the prediction error (Y - W@C) systematic or random?

**Method**:
1. Compute residuals R = Y - W_ridge @ C for each subject × ROI
2. Compute RDM of residuals across 8 colors
3. Test: corr(RDM_residual, RDM_original) — if high, model misses systematic structure
4. Test: corr(RDM_residual, ideal_circular_RDM) — if high, residuals retain color geometry

**Interpretation**:
- Random residuals → model captures all available structure (noise ceiling reached)
- Structured residuals → model misses something → room for improvement (but may need more data/channels)

#### 9f-4. Ridge Alpha Stability (Priority: LOW)

**Question**: Is the GCV-selected regularization strength stable across folds?

**Method**: Report distribution of selected alpha across 8 LOCO folds × 7 HC subjects per ROI.

**Interpretation**: High variance → model is sensitive to training data composition → less trustworthy. Low variance → robust model selection.

### 9d. Native Voxel-Space Inverse Transform (Q4)

**Motivation**: Current metrics are computed in Procrustes space. A reviewer may ask: "Does the model actually predict activity in the subject's native voxel space, or does the Procrustes alignment itself create an artifactual structure?"

**Approach**: Apply inverse Procrustes transform to predicted patterns, then compute voxel correlation in native space.

```
Y_hat_native = P_s^{-1} @ Y_hat_procrustes
Y_native = P_s^{-1} @ Y_procrustes
r_native = corr(Y_hat_native, Y_native)
```

where P_s is the subject's Procrustes rotation matrix (orthogonal → P^{-1} = P^T).

**Implementation requirements**:
1. Load Procrustes transform parameters from Phase 1 output
2. Apply P_s^T to both predicted and actual patterns
3. Compute voxel correlation in native space
4. Compare r_native vs r_procrustes — they should be similar (Procrustes is orthogonal, preserves inner products)

**Expected result**: r_native ≈ r_procrustes (since Procrustes rotation preserves correlations). If they diverge, investigate whether Procrustes scaling (not just rotation) introduces systematic bias.

**Priority**: Enhancement for paper, not a blocker. Run after baseline validation.

### 9e. Gate Threshold Justification (Q6)

Current gate thresholds (Section 7) may appear arbitrary. Two principled alternatives:

**Option A — Noise-ceiling normalization** (preferred):
```
normalized_fit = observed_metric / noise_ceiling
```
Gate: normalized_fit > 0.3 (model captures ≥30% of achievable signal). This automatically adapts to data quality — noisy ROIs have lower ceilings, so a lower absolute metric can still pass.

**Option B — HC percentile-based**:
```
threshold = HC_5th_percentile(metric)
```
Gate: CVD metric > HC 5th percentile. This asks "is the CVD prediction within the HC range?" rather than using a fixed number.

**Implementation**: Both options use data already computed by `compute_reliability()` in `validate_loro_loco_loso.py`. The noise ceiling (upper/lower bounds) is saved in the reliability JSON. Post-hoc analysis can derive normalized fits without rerunning the pipeline.

**Current status**: Noise ceiling is computed. Normalized fit is reported as a derived metric. Absolute thresholds (LOCO r > 0, split-half RDM > 0.3) serve as first-pass gates; normalized fits provide nuance in interpretation.

---

## 10. Risk and Contingency

**Core risk**: If LOCO voxel correlation ≈ 0 across ROIs, the continuous interpolation claim collapses, and filter optimization has no prediction engine to build on.

**Why this could happen**:
- 8 training colors may be too sparse for continuous encoding (especially in higher visual areas)
- SRM-mediated prior may inject noise rather than signal (red team criticism 1)

**Mitigations**:
1. Gate criterion 3 catches this explicitly — pipeline stops before filter stage
2. Template-matching LOCO already works (MAE: V1 ~76°, hV4 ~69°), so a model-based approach should at minimum match template matching performance
3. R_s split-half stability check (Execution Step 1b) catches prior-projection failure early

**Contingency**: If model-based LOCO fails but template matching succeeds, revert to template-matching-based prediction for filter evaluation. This is less elegant (no closed-form gradient for filter optimization) but functional.

---

## 11. Execution Priority

Strict sequential dependency — each step gates the next.

| Step | Script(s) | Output | Gate |
|---|---|---|---|
| 1a | `step_a_fit_srm.py` | R_i per HC subject | — |
| **1b** | **`check_rs_stability.py`** | **R_s split-half cosine similarity** | **cosine > 0.5 per ROI → proceed; else redesign prior approach** |
| 2a | `step_b_group_prior.py` | A_i, A_g per ROI | — |
| 2b | `step_c_project_prior.py` | W_{0,s} per subject | — |
| 3 | `step_d_finetune.py` | W_s per subject (lambda via nested CV) | — |
| **4** | **`validate_loro_loco_loso.py`** | **LORO r, LOCO r, LOCO MAE** | **LOCO r > 0 (p < 0.05) → proceed; else STOP** |
| 5 | Encoding-basis ablation (Stage 1) | Basis comparison table | Pick best basis |
| 6 | Full model comparison (Stage 2) | 5 models × 3 CV × 4 ROI table | Identify best model |
| 7 | Phase 2 filter design | T_ψ optimization | — |

**Step 1b is from red team criticism 1** — verifies R_s projection reliability before investing in Steps 2-4.

**Step 4 is the critical go/no-go gate** — if prediction model fails LOCO, everything downstream is blocked.

---

## 12. Updated Pipeline Summary

```
Phase 1. Prediction Model
├── 1. Base model: forward encoding (FE-6 default)
├── 2. Encoding basis ablation: FE-6 / LF-4 / LF-6
├── 3. Group prior + subject adaptation (Steps A-D)
├── 4. Validation: LORO / LOCO / LOSO
├── 5. Model comparison: OLS / Standard Ridge / Prior-only / Prior+finetune
├── 6. Metrics: voxel corr, R², LOCO MAE, RDM corr, normalized fit, reliability
└── 7. Gate: reliability + predictability + interpolation

Phase 2. Filter Optimization
├── Filter families: identity / Fourier-4 / Fourier-6 / optional GP
├── Evaluation: geometry improvement, held-out validation, permutation, pairwise diagnostics
└── Individual-level analysis (Crawford & Howell per CVD subject)

Phase 3. Behavioral Validation
└── Neural correction → perceptual improvement prediction
```

**Structural principle**: Prediction model의 과학적 타당성을 먼저 확실히 만들고, 그 위에서 filter를 논의한다.
