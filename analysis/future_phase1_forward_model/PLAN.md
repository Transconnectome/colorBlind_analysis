# Group-Prior Prediction Model — PLAN

> Last updated: 2026-03-11
> Status: Baseline complete; **ridge_gcv confirmed as final encoder** (smooth_tikh REJECTED — Section 9i)
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

### 9g. Prediction Improvement Methods (Q8 — NEW, 2026-03-10)

**Motivation**: HC LOCO ridge_gcv voxel_corr = 0.130 (V1), r²=0.017. Statistically significant (p=0.012) but practically weak. The forward model must predict well enough for Phase 2 filter to have room for improvement.

**Diagnosis**: df is NOT the bottleneck. Code uses 6 runs × 7 colors = 42 training samples for K=6 parameters (df=36). LF-4 (K=4, df=38) performing worse than FE-6 confirms this. Real bottlenecks: (1) low SNR of color signal in BOLD, (2) partial basis shape mismatch, (3) noise dimensions in W.

#### 9g-1. Reduced-Rank Ridge (RRR) — Priority: HIGH

**Method**: After ridge fit, SVD-truncate W to rank r:
```
W_ridge = (C^T@C + αI)^{-1} @ C^T @ X    # standard ridge
U, Σ, V^T = SVD(W_ridge)
W_RRR = U[:, :r] @ diag(Σ[:r]) @ V^T[:r, :]   # rank-r approximation
```

**Hyperparameter**: r ∈ {2, 3, 4}, selected via inner-CV (same LORO loop).

**Rationale**: Visual cortex color representation may have < 6 independent spatial patterns. Removing noise dimensions improves interpolation. Effective parameter reduction: 50% at r=3.

**Implementation**: One line of SVD truncation after existing ridge fit. Add `--rank` argument to validation script.

#### 9g-2. Channel-Smoothness Regularization (Circular Tikhonov) — Priority: HIGH

**Method**: Add circular smoothness penalty connecting adjacent FE channels:
```
min_W ||X - C @ W||²_F + α||W||²_F + β||D @ W||²_F
```

where D is 6×6 circular difference matrix:
```
D = [[ 1,-1, 0, 0, 0, 0],
     [ 0, 1,-1, 0, 0, 0],
     [ 0, 0, 1,-1, 0, 0],
     [ 0, 0, 0, 1,-1, 0],
     [ 0, 0, 0, 0, 1,-1],
     [-1, 0, 0, 0, 0, 1]]
```

**Closed-form**: `W = (C^T@C + αI + βD^T@D)^{-1} @ C^T @ X`

**Rationale**: "Ridge between basis functions" — a voxel tuned to green should have similar weights for adjacent yellow/cyan channels. Standard ridge shrinks each channel independently; this couples them.

**Hyperparameter**: α × β 2D grid (e.g., 5×5=25 combinations), inner-CV.

#### 9g-3. Elastic Net — Priority: LOW

**Method**: L1+L2 penalty for per-voxel channel sparsity.
```
min_W ||X - C @ W||²_F + α||W||₁ + β||W||²_F
```

**Implementation**: `sklearn.ElasticNetCV` per voxel. More complex than RRR/Smoothness.

#### 9g-4. Combined RRR + Smoothness — Priority: AFTER 9g-1 and 9g-2

If both methods individually help, combine: Circular Tikhonov fit → SVD truncation.

**Experimental design**: 2×2 factorial (±RRR × ±Smoothness) × 4 ROIs × 10 subjects.

### 9h. Prior Failure Investigation — LORO-LOCO Dissociation (Q9 — NEW, 2026-03-10)

**Motivation**: prior_ft wins LORO (V1: 0.315 vs ridge 0.201) but loses LOCO (V1: -0.056 vs ridge +0.130). The LORO-LOCO dissociation means the SRM group prior captures run-level variance structure but NOT color-specific tuning for interpolation. This section investigates WHY and tests structured alternatives.

**Root cause**: The prior-centered ridge `min ||X - CW||² + λ||W - W0||²` uses LORO-based nested CV to select λ. This biases λ HIGH (typically 10-100), keeping W close to W0. But for LOCO, what matters is the *curvature* of the individual's tuning — W0 (HC group average) smooths out exactly this curvature. Meanwhile, ridge_gcv's shrinkage toward ZERO is agnostic about channel structure: it regularizes magnitude without distorting shape, which is a better inductive bias for interpolation.

**Three hypotheses**:

| ID | Hypothesis | If true... |
|----|-----------|-----------|
| H1 | **Shape mismatch** — W0 has the wrong voxel pattern direction for the individual | cosine_sim(W0_pred, X_true) is low; no amount of λ tuning can fix this |
| H2 | **Uncertainty blindness** — W0 is unreliable for some channels/voxels but treated uniformly | LOCO errors correlate with inter-subject A_i variance; per-element weighting helps |
| H3 | **Missing smoothness** — LOCO needs smooth interpolation, which is orthogonal to "match the group" | Structural smoothness (without any group prior) improves LOCO |

#### 9h-1. Diagnostic: Shape vs Magnitude Decomposition — Priority: HIGH

**Method**: For each LOCO fold c and each subject s:

```python
W0_pred = C[c] @ W0           # (1, V_s) — group prior predicted pattern
W_ridge_pred = C[c] @ W_ridge # (1, V_s) — ridge predicted pattern
X_true = amp[:, c, :].mean(0) # (V_s,) — actual pattern (run-averaged)

# Shape match (scale-invariant):
cos_prior = cosine_similarity(W0_pred, X_true)
cos_ridge = cosine_similarity(W_ridge_pred, X_true)
```

**Interpretation**:
- If W0 has correct SHAPE (high cosine) but low voxel_corr → magnitude/scaling issue → Model 9h-5 (shape-preserving) may help
- If W0 has WRONG shape (low cosine) → group average is fundamentally mismatched → favor pure smoothness (9g-2) or mixed model (9h-3)
- Compare cos_prior vs cos_ridge systematically across all folds × subjects

**Implementation**: Add to existing validation script as a diagnostic output. No new model fitting needed.

#### 9h-2. Diagnostic: Per-Color LOCO + Inter-Subject A_i Variance — Priority: HIGH

**Method**: Extends 9f-2 (per-color LOCO breakdown) with a causal analysis:

1. For each ROI, compute per-element variance of A_i across HC: `σ²_A[j, m] = Var(A_i[j, m])`
2. For each held-out color c, compute the "prior uncertainty" for that color:
   `prior_var(c) = ||C[c]||² ⊙ σ²_A` (how uncertain is the prior for this color?)
3. Correlate per-color prior_var with per-color LOCO error (prior_ft)

**Expected**: If H2 is correct, colors with high prior uncertainty should have worse prior_ft LOCO performance. This would support uncertainty-weighted Model 9h-4.

**Implementation**: Post-hoc analysis of existing A_i files (saved in `results/group_prior/{ROI}/sub-{ID}_A.npy`) and per-fold LOCO results.

#### 9h-3. Model: Mixed Regularization (Ridge + Prior) — Priority: HIGH

**Hypothesis tested**: H1 (partial shape match — prior is partially useful)

**Objective**:
```
min ||X - CW||² + α||W||² + λ||W - W0||²
```

**Closed-form solution**:
```
W = (C'C + (α+λ)I)^{-1} (C'X + λW0)
```

This is equivalent to shrinking toward a SCALED prior `λ/(α+λ) · W0` with total penalty `(α+λ)`. The data determines the optimal mixing:
- If optimal λ/(α+λ) ≈ 0 → prior is unhelpful (confirms ridge_gcv is sufficient)
- If optimal λ/(α+λ) ≈ 1 → current prior_ft is correct (contradicts baseline results)
- If 0 < λ/(α+λ) < 1 → prior is partially useful when combined with zero-shrinkage

**Hyperparameter selection**: 2D grid search via inner LOCO CV (hold out 1 of 7 remaining colors):
```
α_grid = [0.01, 0.1, 1, 10, 100]
λ_grid = [0, 0.01, 0.1, 1, 10, 100]
```
25 combinations per inner fold. Inner LOCO uses 6 colors for training (still determined for K=6 with regularization).

**Key methodological change**: Inner CV uses **LOCO** (color-held-out), not LORO (run-held-out). This directly optimizes for interpolation. With 7 training colors in the outer fold, inner LOCO holds out 1 → 6 training colors + regularization makes K=6 solvable.

**Implementation**: Modify `_inner_cv_lambda_loco()` to accept both α and λ grids. Wrap in `fit_model_loco()` as a new model type `mixed_ridge_prior`.

#### 9h-4. Model: Bayesian Uncertainty-Weighted Prior — Priority: HIGH

**Hypothesis tested**: H2 (uncertainty blindness)

**Principle**: Replace scalar λ with per-element precision derived from inter-subject spread. Trust the prior MORE where HC subjects agree, LESS where they disagree.

**Construction of per-element variance**:

For target subject s with projection R_s:
```python
# Project each HC's individual A_i into the target subject's voxel space
for h in HC_subjects:
    W_h = (R_s @ A_h).T          # (K, V_s) — HC h's encoding in subject s's space

W0 = mean(W_h)                   # (K, V_s) — group prior (same as current)
σ²[m, v] = Var(W_h[m, v])        # (K, V_s) — inter-subject spread per element
```

**Objective (scaled form)**:
```
min ||X - CW||² + γ · Σ_{m,v} (W[m,v] - W0[m,v])² / σ²[m,v]
```

where γ > 0 is a global scaling hyperparameter that controls overall prior trust. The **relative** weighting across elements is fixed by the inter-subject data; γ controls the **absolute** level.

**Per-voxel closed form** (K×K solve, trivially fast):
```python
Λ_v = diag(γ / σ²[:, v])         # (K, K) diagonal precision matrix per voxel
w_v = (C'C + Λ_v)^{-1} @ (C'x_v + Λ_v @ w0_v)
```

**Bayesian interpretation**:
- Prior: `p(W[m,v]) = N(W0[m,v], σ²[m,v] / γ)`
- Likelihood: `p(X | W) = N(CW, noise_var · I)`
- Posterior MAP: the weighted ridge solution above

**Hyperparameter**: γ ∈ [0.01, 0.1, 1, 10, 100], selected via inner LOCO CV.

**Why γ is necessary**: Without γ, the precision is fully determined by inter-subject spread, which may not be calibrated against the noise level of the individual's data. γ rescales the prior variance relative to the data likelihood:
- γ >> 1: tight prior (trust group even for uncertain elements)
- γ << 1: loose prior (only trust group where subjects strongly agree)
- γ = 1: prior variance equals inter-subject variance (default Bayesian)

**Numerical safeguard**: Floor σ² at a small value (e.g., `max(σ², 1e-6)`) to avoid infinite precision for elements where HC subjects happen to agree exactly.

**Implementation**: New function `compute_prior_precision(A_list, R_s)` in `utils_forward_model.py`. Returns (K, V_s) precision matrix. New model type `bayes_prior` in validation script.

#### 9h-5. Model: Smooth + Prior Hybrid — Priority: MEDIUM (after 9h-3 and 9h-4)

**Hypothesis tested**: H2 + H3 combined

**Objective**:
```
min ||X - CW||² + α||DW||² + λ||W - W0||²
```

where D is the 6×6 circular difference matrix from §9g-2.

**Closed-form**:
```
W = (C'C + αD'D + λI)^{-1} (C'X + λW0)
```

**Rationale**: Gets structural smoothness from D (helps interpolation) and starting-point guidance from W0 (helps when individual data is sparse). Tests whether the prior becomes helpful when combined with the right structural constraint.

**Hyperparameter**: Joint (α, λ) grid via inner LOCO CV.

**Implementation**: Combine existing smooth Tikhonov (9g-2) with prior_ridge machinery. New model type `smooth_prior`.

#### 9h-6. Evaluation Protocol

**All models evaluated on the same LOCO (8-fold) protocol** with clean prior recomputation (excluding held-out color from A_g for prior-based models). This ensures fair comparison with existing baseline results.

**Comparison table** (target output):

| Model | Type | λ selection | V1 HC | V2 HC | hV4 HC | V3 HC |
|-------|------|------------|-------|-------|--------|-------|
| ridge_gcv | baseline | GCV | 0.130 | 0.150 | 0.183 | 0.023 |
| prior_ft | baseline | LORO inner | -0.056 | -0.060 | 0.169 | -0.101 |
| mixed (9h-3) | new | LOCO inner (α,λ) | ? | ? | ? | ? |
| bayes_prior (9h-4) | new | LOCO inner (γ) | ? | ? | ? | ? |
| smooth_tikh (9g-2) | new | LOCO inner (α,β) | ? | ? | ? | ? |
| smooth+prior (9h-5) | new | LOCO inner (α,λ) | ? | ? | ? | ? |

**Decision rules**:
- If smooth_tikh > ridge_gcv: H3 confirmed, smoothness is the key inductive bias
- If bayes_prior > prior_ft: H2 confirmed, uncertainty-weighting rescues the prior
- If mixed with λ/(α+λ) ≈ 0: prior is truly unhelpful, ridge suffices
- If smooth+prior > smooth_tikh: prior provides value when combined with smoothness
- If nothing > ridge_gcv: current baseline is already optimal; strong evidence for paper

**Secondary analysis**: HC-CVD group comparison (Welch t-test) and individual CVD profiles (Crawford-Howell) using the best model from this comparison. Compare effect sizes against baseline ridge_gcv.

#### 9h-7. Implementation Plan

| Step | Script | Depends on | Priority |
|------|--------|-----------|----------|
| 1 | `diagnose_prior_failure.py` — 9h-1 + 9h-2 diagnostics | Existing results | **FIRST** |
| 2 | Add `compute_prior_precision()` to `utils_forward_model.py` | A_i files, R_s | HIGH |
| 3 | Add models `mixed_ridge_prior`, `bayes_prior`, `smooth_prior` to `validate_loro_loco_loso.py` | Step 2 | HIGH |
| 4 | `run_step4_prior_investigation.sbatch` — run all new models | Steps 1-3 | HIGH |
| 5 | `analyze_prior_investigation.py` — comparison table + decision | Step 4 results | HIGH |

**Key change from baseline**: Inner CV for hyperparameter selection switches from **LORO** (run-held-out) to **LOCO** (color-held-out) for all new models. This directly optimizes for interpolation, addressing the original observation that LORO-based λ selection biases toward the prior.

### 9h-8. smooth_tikh Permutation Result (2026-03-11)

**FAILED all ROIs** — but paradoxically, RDM improvements are genuine. See `ANALYSIS_smooth_tikh_paradox.md` for detailed analysis.

| ROI | Observed | Null Mean | Null 95% CI | p_perm | Verdict |
|-----|----------|-----------|-------------|--------|---------|
| V1 | 0.189 | 0.187 | [0.179, 0.197] | 0.331 | FAIL |
| V2 | 0.216 | 0.212 | [0.202, 0.223] | 0.188 | FAIL |
| V3 | 0.125 | 0.128 | [0.115, 0.144] | 0.613 | FAIL |
| hV4 | 0.239 | 0.241 | [0.230, 0.252] | 0.613 | FAIL |

**Root cause:** voxel_corr captures shared spatial structure (covariance baseline) + color-discriminative signal. Smoothness penalty (β=100) amplifies the shared baseline → high null mean (~0.19-0.24). Two fixable issues:
1. **No condition-centering**: Model Y=WC lacks intercept → W absorbs shared voxel pattern → smoothness penalty amplifies it
2. **Fixed hyperparams in permutation**: (α=0.01, β=100) were selected on real data but used for all 10K shuffles → biased null

**Key insight:** voxel_corr is NOT the wrong metric — it's the standard in the field. The problems are (a) missing intercept in the model and (b) biased permutation procedure. Fix both → smooth_tikh should pass voxel_corr permutation.

**Resolution:** See §9i for condition-centering and re-optimized permutation fixes.

### 9i. smooth_tikh Investigation — RESOLVED (REJECTED, 2026-03-11)

**Original motivation**: smooth_tikh showed apparent improvements (RDM +0.5, HC-CVD d=3.43) but failed voxel_corr-based permutation. Three rescue attempts were tested.

---

#### 9i-1. Permutation Test — Fixed Params (DONE — ALL FAIL)

| ROI | Observed | Null Mean | p_perm |
|-----|---------|-----------|--------|
| V1 | 0.189 | 0.187 | 0.331 |
| V2 | 0.216 | 0.212 | 0.188 |
| V3 | 0.125 | 0.128 | 0.613 |
| V4 | 0.239 | 0.241 | 0.613 |

---

#### 9i-2. Rescue: Condition-Centering (DONE — FAILED)

Per-run centering (subtracting mean across 8 colors within each run) **commutes with color label shuffle**: `mean(amp[:, perm, :], axis=1) == mean(amp, axis=1)`. Cannot change the permutation test by construction. Confirmed empirically.

---

#### 9i-3. Rescue: Re-Optimized Permutation (DONE — FAILED)

Re-selecting (α, β) via inner LOCO-CV within each permutation. Result (5 perms, sub-02 hV4):
- Null selects β=1000 in 45% of shuffles (most common) — smoothness helps fit ANY data
- Observed score drops: 0.172 (vs 0.239 fixed)
- Delta ≈ -0.007 — still not significant

---

#### 9i-4. RDM Structure Inspection (DONE — REINTERPRETATION)

| RDM Comparison | V1 | V2 | hV4 |
|---------------|------|------|------|
| Actual vs Ideal (Spearman) | -0.008 | +0.044 | +0.004 |
| smooth_tikh Predicted vs Ideal | **-0.624** | **-0.580** | **-0.442** |

- **Actual data has NO ideal circular hue structure** (all ρ ≈ 0)
- **smooth_tikh predicted RDM anti-correlated with ideal** (ρ ≈ -0.5)
- RDM distances extremely compressed (0.06-0.23 vs actual 0.66-1.49)
- **rdm_pearson "improvement" was noise pattern-matching**, not color geometry preservation

---

#### 9i-5. Final Conclusion

**smooth_tikh REJECTED.** Root cause: β=100 forces near-rank-1 W → predictions dominated by single shared spatial pattern → ALL "improvements" (voxel_corr, rdm_pearson, HC-CVD separation) driven by spatial covariance, not color signal.

| "Improvement" | Reality |
|----------------|---------|
| Higher voxel_corr | Shared spatial pattern (high null baseline proves it) |
| Higher rdm_pearson | Compressed RDM matching noise structure |
| Stronger HC-CVD d | Group differences in spatial covariance |

**The permutation test was correct.** ridge_gcv confirmed as final encoder.

---

### 9j. hV4-Informed Multi-ROI Prior (Q11 — NEW, 2026-03-11)

**Motivation:** Current model works for HC hV4 (p=0.044 permutation) but fails for V1/V2 and all CVD subjects. Use hV4's robust color representation to inform V1/V2 encoding.

**Hypothesis:** hV4 maintains color structure that V1/V2 should be consistent with. Use hV4 as "color axis reference" for lower visual areas.

---

#### 9j-1. Cross-ROI Prior Projection

**Method 1: RDM-Constrained Fitting**

```python
# Step 1: Compute target RDM from hV4
W_hV4 = fit_W_ridge(C, X_hV4, alpha)  # hV4 encoder (works for both HC/CVD)
RDM_target = compute_rdm(W_hV4 @ basis_full)  # hV4's color geometry

# Step 2: Fit V1 weights with RDM constraint
def fit_W_rdm_constrained(C, X_V1, RDM_target, lambda_rdm):
    """
    min ||X - CW||^2 + lambda_rdm * ||RDM(W@C_full) - RDM_target||^2
    """
    # Iterative optimization (RDM is non-linear in W)
```

**Method 2: Shared Color Subspace**

```python
# Assumption: V1/V2/hV4 share a common COLOR subspace (despite different spatial maps)

# Step 1: Learn hV4 color subspace (via PCA or ICA on W_hV4)
color_components = PCA(W_hV4.T, n_components=3)  # 3D color subspace

# Step 2: Constrain V1 weights to this subspace
W_V1_constrained = W_V1_free @ color_components.T @ color_components
```

**Advantage:**
- Leverages hV4's validated color signal
- Single framework for HC and CVD (if hV4 works for CVD)

**Challenge:**
- Cross-ROI projection is non-trivial (different voxel spaces)
- May overconstraint V1/V2 if hV4 structure differs

**Priority:** MEDIUM — after §9i RDM validation confirms hV4's role

---

#### 9j-2. hV4-Adaptive Basis Initialization

**Idea:** Use hV4 to infer subject's color space distortion, initialize V1/V2 basis centers accordingly.

```python
# Step 1: Fit adaptive basis for hV4 (§9k)
centers_hV4 = fit_adaptive_basis(X_hV4)  # Per-subject hV4 centers

# Step 2: Initialize V1/V2 basis from hV4
centers_V1_init = centers_hV4  # Assume V1 follows hV4 color axes

# Step 3: Fine-tune V1/V2 centers (allow small deviations)
centers_V1 = fit_adaptive_basis(X_V1, centers_init=centers_V1_init,
                                lambda_deviation=10)  # Penalty for deviating from hV4
```

**Advantage:**
- Reduces V1/V2 optimization DOF (6 centers → small deviations)
- Respects hierarchy (hV4 informs V1/V2)

**Priority:** HIGH (if adaptive basis §9k is implemented)

---

### 9k. Adaptive Basis Optimization (Q12 — NEW, 2026-03-11)

**Motivation:** CVD subjects have distorted color axes → fixed FE-6 basis at [0°, 60°, ...] may be misaligned. Optimize basis centers per subject to match individual color geometry.

**Goal:** Make model work for BOTH HC and CVD by respecting individual color spaces.

---

#### 9k-1. Subject-Specific Basis Centers

**Method:**

```python
def fit_adaptive_basis(X, n_channels=6, lambda_spacing=1.0):
    """
    Optimize basis function centers to maximize LOCO cross-validation.

    Args:
        X: (n_runs, n_colors, V_s) voxel responses
        n_channels: number of basis channels (default 6)
        lambda_spacing: regularization for even spacing

    Returns:
        centers_opt: (n_channels,) optimized centers [deg]
        W_opt: (n_channels, V_s) encoding weights
    """
    from scipy.optimize import minimize

    # Initial centers (FE-6 default)
    centers_init = np.linspace(0, 360, n_channels, endpoint=False)

    def objective(centers):
        # Rebuild basis
        C = create_basis_matrix(HUE_ANGLES, centers=centers)

        # Fit weights
        W = fit_W_ridge(C, X, alpha=gcv_alpha(C, X))

        # LOCO cross-validation score
        loco_score = -evaluate_loco_rdm_corr(W, C, X)  # Use RDM (§9i)

        # Regularization: penalize uneven spacing
        c_sorted = np.sort(centers)
        spacing = np.diff(c_sorted, append=c_sorted[0] + 360)
        spacing_penalty = lambda_spacing * np.var(spacing)

        return loco_score + spacing_penalty

    # Constrained optimization
    bounds = [(0, 360)] * n_channels
    result = minimize(objective, centers_init, method='L-BFGS-B', bounds=bounds)

    centers_opt = result.x % 360
    return centers_opt
```

**Expected outcomes:**
- **HC subjects:** centers ≈ [0°, 60°, 120°, 180°, 240°, 300°] (symmetric)
- **Deutan CVD:** compressed green-red axis, e.g. [0°, 55°, 110°, 180°, 250°, 305°]
- **Protan CVD:** compressed red-green axis differently

**Validation:**
1. Within-subject LOCO (test generalization with optimized basis)
2. Compare CVD vs HC center patterns (interpret distortion)
3. Test: Does adaptive basis rescue CVD LOCO (currently negative)?

---

#### 9k-2. Hierarchical Adaptive Basis (hV4-Informed)

**Combine §9j and §9k:**

```python
# Use hV4 to initialize V1/V2 basis optimization
centers_hV4_CVD = fit_adaptive_basis(X_hV4_CVD)
centers_V1_init = centers_hV4_CVD  # hV4 as prior

centers_V1 = fit_adaptive_basis(X_V1_CVD,
                                centers_init=centers_V1_init,
                                lambda_prior=10)  # Stay close to hV4
```

**Advantage:**
- hV4 constrains search space (reduces overfitting)
- Respects anatomical hierarchy

**Priority:** HIGH (after hV4 validation)

---

#### 9k-3. Implementation Plan

| Step | Script | Output | Priority |
|------|--------|--------|----------|
| 1 | `fit_adaptive_basis.py` | Per-subject × ROI optimized centers | **HIGH** |
| 2 | `validate_adaptive_loco.py` | LOCO with adaptive basis vs fixed basis | **HIGH** |
| 3 | `analyze_cvd_centers.py` | HC vs CVD center comparison, distortion quantification | MEDIUM |
| 4 | `fit_hierarchical_adaptive.py` | hV4-informed V1/V2 (§9k-2) | MEDIUM |

**Validation criteria:**
- Success = CVD LOCO > 0 in at least 2 ROIs with adaptive basis
- Interpret = CVD center patterns reveal perceptual distortion

---

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

## 11. Execution Priority (Updated 2026-03-11)

### Phase 1a: Baseline (COMPLETE ✅)

| Step | Script(s) | Output | Status |
|---|---|---|---|
| 1a | `step_a_fit_srm.py` | R_i per HC subject | ✅ DONE |
| 1b | `check_rs_stability.py` | R_s split-half cosine similarity | ✅ DONE (all PASS) |
| 2a | `step_b_group_prior.py` | A_i, A_g per ROI | ✅ DONE |
| 2b | `step_c_project_prior.py` | W_{0,s} per subject | ✅ DONE |
| 3 | `step_d_finetune.py` | W_s per subject (nested CV) | ✅ DONE |
| 4 | `validate_loro_loco_loso.py` | LORO/LOCO/LOSO (4 models) | ✅ DONE |
| 5 | Basis ablation | FE-6 vs LF-4 vs LF-6 | ✅ DONE (FE-6 wins) |
| 6 | Extended models (§9g, §9h) | smooth_tikh + prior variants | ✅ DONE |

**Current encoder:** ridge_gcv (hV4 permutation-validated, p=0.044)

---

### Phase 1b: HC Model Refinement (IN PROGRESS 🎯)

**Goal:** Fix smooth_tikh permutation failure via condition-centering + re-optimized permutation. Keep voxel_corr as primary metric.

| Priority | Step | Script | Expected Outcome | Gate |
|----------|------|--------|------------------|------|
| **1 (HIGHEST)** | **§9i-1+2: Condition-center + re-optimized perm** | `permutation_test_centered.py` | smooth_tikh passes voxel_corr perm | If PASS → adopt smooth_tikh |
| 2 (MEDIUM) | Quick test: centered LOCO (no perm) | Modify `utils_forward_model.py` | Verify centering improves LOCO scores | Sanity check before full perm |
| 3 (SUPPORTING) | RDM as secondary metric | Existing scripts | Independent geometry evidence | Complementary |

**Decision point:**
- ✅ If centered permutation passes → **smooth_tikh adopted** (voxel_corr primary, RDM secondary)
- ❌ If still fails → **ridge_gcv retained** (hV4 only validated ROI)
- → **Proceed to Phase 2 with HC-validated encoder**

---

### Phase 1c: CVD Model Development (PLANNED 📋)

**Goal:** Make encoder work for CVD subjects (currently LOCO ≤ 0 for most ROIs).

**Prerequisite:** HC model finalized (§9i decision made).

| Priority | Step | Script | Goal | Target |
|----------|------|--------|------|--------|
| **1 (HIGH)** | **§9k-1: Adaptive basis** | `fit_adaptive_basis.py` | Optimize basis centers per subject | CVD LOCO > 0 in 2+ ROIs |
| **2 (HIGH)** | **§9k-1 validation** | `validate_adaptive_loco.py` | Test adaptive vs fixed basis | Significant improvement |
| 3 (MEDIUM) | §9k-2: hV4-informed adaptive | `fit_hierarchical_adaptive.py` | Use hV4 to constrain V1/V2 | Reduce overfitting |
| 4 (MEDIUM) | §9j-1: hV4 RDM constraint | `fit_rdm_constrained.py` | V1/V2 match hV4 geometry | Alternative to adaptive |
| 5 (LOW) | §9k-3: CVD distortion analysis | `analyze_cvd_centers.py` | Quantify color axis compression | Interpretability |

**Decision criteria:**
- **Minimum bar:** CVD LOCO > 0 in at least 2 ROIs (adaptive basis)
- **Target:** CVD LOCO within HC range (e.g., CVD > HC 5th percentile)
- **Stretch:** Unified HC-CVD model (same algorithm, different hyperparameters)

**Gate for Phase 2:**
- ✅ HC encoder validated (§9i complete)
- ✅ CVD encoder shows positive LOCO OR explicitly treat CVD as exploratory
- → **Proceed to filter optimization**

---

### Timeline Recommendation

**Week 1-2 (HC focus):**
1. Implement condition-centering in `utils_forward_model.py` + quick LOCO test — 1 day
2. Implement re-optimized permutation (`permutation_test_centered.py`) — 1-2 days
3. Run centered permutation on server (10K iters) — 1-2 days
4. Analyze results, make encoder decision — 1 day
5. Document final HC encoder in RESULTS.md

**Week 3-4 (CVD focus):**
1. Implement adaptive basis optimization (§9k-1) — 3-4 days
2. Run on all subjects (HC + CVD), validate LOCO — 1-2 days
3. If successful → implement hV4-informed variant (§9k-2)
4. If fails → document limitation, proceed with HC-only Phase 2

**Week 5+ (Phase 2):**
- Filter optimization with validated encoder
- Separate HC and CVD evaluation if needed

---

### Critical Dependencies

**§9i (Centered permutation) blocks:**
- Encoder decision (smooth_tikh vs ridge_gcv)
- Voxel_corr remains primary metric; RDM as secondary

**§9k-1 (Adaptive basis) blocks:**
- CVD model viability
- Unified vs separate HC-CVD encoding

**Both can run in parallel** — different questions, independent implementations.

---

## 12. Updated Pipeline Summary (2026-03-11)

```
Phase 1. Prediction Model (HC Focus First)
├── 1. Base model: forward encoding (FE-6 default)                  ← DONE
├── 2. Encoding basis ablation: FE-6 / LF-4 / LF-6                 ← DONE (FE-6 wins)
├── 3. Group prior + subject adaptation (Steps A-D)                 ← DONE (ridge_gcv retained)
├── 4. Validation: LORO / LOCO / LOSO                               ← DONE (hV4 passes permutation)
├── 5. Model comparison: 4 baseline models                          ← DONE (ridge_gcv best LOCO)
├── 6. Extended models (§9h): prior-based + smooth_tikh             ← DONE (smooth_tikh RDM↑, voxel_corr perm FAIL)
├── 7. Metrics: voxel corr, R², LOCO MAE, RDM corr, NC-normalized  ← DONE
├── 8. Gate (HC): hV4 PRIMARY GO (perm p=0.044); V1/V2 CONDITIONAL ← DONE
│
├── 9i. Model & permutation fixes (condition-centering + re-opt)    ← PLANNED
│   ├── 9i-1. Condition-centering (add intercept to model)          ← **HIGHEST PRIORITY**
│   ├── 9i-2. Re-optimized permutation (hyperparams per shuffle)    ← **HIGH PRIORITY**
│   └── 9i-3. Combined: centered + re-opt perm test                 ← **RECOMMENDED**
│
├── 9j. hV4-informed multi-ROI prior (cross-ROI constraints)        ← PLANNED
│   ├── 9j-1. RDM-constrained V1/V2 fitting                         ← MEDIUM (after 9i)
│   └── 9j-2. hV4-adaptive basis initialization                     ← HIGH (if 9k implemented)
│
└── 9k. Adaptive basis optimization (CVD-HC unified model)          ← PLANNED
    ├── 9k-1. Subject-specific basis centers                         ← **HIGH PRIORITY**
    ├── 9k-2. Hierarchical adaptive (hV4-informed V1/V2)            ← HIGH (after 9k-1)
    └── 9k-3. Validation: CVD LOCO > 0 target                        ← HIGH

Phase 1.5. CVD Model Development (After HC Validation)
├── Apply §9i strategies to CVD subjects
├── Test adaptive basis (§9k) on CVD → target: LOCO > 0 in 2+ ROIs
└── If successful → unified HC-CVD encoder for Phase 2

Phase 2. Filter Optimization
├── Encoder: Best HC model from Phase 1 (smooth_tikh if centered perm passes, else ridge_gcv)
├── Filter families: identity / Fourier-4 / Fourier-6 / optional GP
├── Evaluation metric: voxel_corr (primary) + RDM correlation (secondary)
├── Validation: geometry improvement, held-out, permutation, pairwise diagnostics
└── CVD individual-level analysis (Crawford & Howell)

Phase 3. Behavioral Validation
└── Neural correction → perceptual improvement prediction
```

**Structural principle**:
1. **HC model validation first** (hV4 confirmed, V1/V2 pending model/permutation fix)
2. **Fix smooth_tikh** via condition-centering + re-optimized permutation (§9i) — keep voxel_corr as primary metric
3. **Extend to CVD** via adaptive basis (§9k) and hV4 constraints (§9j)
4. **Unified framework** for Phase 2 filter optimization

**Current status (2026-03-11):**
- ✅ HC baseline complete (ridge_gcv, hV4 permutation-validated)
- ✅ smooth_tikh shows promise (RDM↑, HC-CVD separation↑) but perm fails due to missing intercept + biased null
- 🎯 **Next: Condition-centering + re-optimized permutation (§9i-1+2)** — fixes model & test
- 🎯 **Parallel: Adaptive basis development (§9k-1)** — for CVD model
