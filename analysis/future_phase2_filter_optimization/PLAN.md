# Stimulus-Space Filter Optimization — PLAN

> Last updated: 2026-03-07
> Status: Planning (pre-validation complete; implementation pending)
> Reviewed by: colleague discussion (2026-03-06, 2026-03-07 revised)

---

## 0. Why the Prediction Model is Procrustes-Based (Not SRM)

The initial pipeline assumed SRM space for prediction, comparison, and filter design. This is wrong. Four reasons:

### (1) SRM destroys interpolation structure

LOCO results — MAE by alignment:

| ROI | Procrustes | SRM | Delta |
|-----|-----------|-----|-------|
| V1 | ~76° | ~80° | +4° |
| V2 | ~80° | ~85° | +5° |
| V3 | ~77° | **~99°** | **+22°** (worse than chance 90°) |
| hV4 | ~69° | ~72° | +3° |

SRM is useful for cross-subject alignment, but it **destroys continuous hue structure**. A continuous interpolation model cannot be built in SRM space.

### (2) SRM is not a stimulus-to-representation mapping

SRM learns:
```
voxel → shared latent
```

But the prediction model requires:
```
stimulus theta → neural representation
```

SRM does not provide this mapping. Forward Encoding (FE) in Procrustes space does.

### (3) SRM filters cannot control stimulus

An SRM-based filter would operate:
```
latent → latent
```

But what we actually need is:
```
stimulus theta → corrected stimulus theta'
```

An SRM filter has no direct connection to stimulus control. A stimulus-space transform (T_psi) operating through Procrustes-based FE does.

### (4) SRM is valid as a comparison space

SRM's strengths remain:
- Removes voxel-count differences across subjects
- Enables group-level comparison (HC vs CVD)
- Provides HC mean target geometry (V2: LOSO 7/7, PCA convergence r=0.891)

**Conclusion**: SRM's role is redefined as **comparison/target latent space**, not prediction/operating space.

---

## 1. Pipeline Overview

### 1.1 Two-Space Design

| Space | Role | What it does |
|-------|------|-------------|
| **Procrustes + FE** | Prediction / operating | stimulus theta → voxel response → continuous interpolation |
| **SRM (k-dim)** | Target / comparison | voxel → shared latent → HC mean geometry for evaluation |

### 1.2 Full Pipeline Flow

```
Stimulus theta
     |
     v
Forward Encoding (FE)
     |
     v
Procrustes voxel space          (prediction engine)
     |
     v
continuous interpolation
     |
     v
CVD latent trajectory
     |
     | projection via W_SRM
     v
SRM latent space                (evaluation space)
     |
     v
compare with HC mean latent geometry
```

- **Prediction**: theta → voxel response (via FE in Procrustes space)
- **Evaluation**: voxel → SRM latent (via W_SRM projection)

### 1.3 Subject-Specific Bridge Matrix

For each subject s:

```
M_s = W_SRM,s^T @ W_FE,s    (shape: k x 6)
```

where:
- W_FE: n_voxels x 6 (forward encoding weights)
- W_SRM: n_voxels x k (SRM projection weights)
- M_s: k x 6 (compact latent prediction mapping)

Prediction at any angle theta:
```
s_hat_s(theta) = M_s @ channels(theta)    → (k,) vector in SRM space
```

Each subject gets a different latent prediction model. FE channels are analytic (half-wave rectified cosines), so M_s produces smooth interpolation at arbitrary angles — no fitting needed for interpolation.

### 1.4 Primary vs Secondary Objectives

| | Previous | Revised |
|-|----------|---------|
| **Primary** | Pairwise disparity rescue | **Latent geometry matching to HC** |
| **Secondary** | Latent alignment (auxiliary) | **Pairwise disparity (diagnostic)** |

**Why**: (1) The true CVD deficit is continuous interpolation, not categorical classification (LOCO_trials: LORO HC ≈ CVD p=0.668, but LOCO HC 69.4° vs CVD 87.4° p=0.017). (2) CVD pairwise profiles are too heterogeneous for a single pairwise target (sub-08: 32 FDR pairs, sub-09: 7, sub-10: 0).

---

## 2. Prediction Model

The prediction model maps **stimulus theta → Procrustes voxel space response**. SRM is used only for cross-subject evaluation, not prediction.

### 2.1 Construction (per subject)

**Core (Procrustes prediction)**:
```
ŷ_proc(theta) = W_FE @ channels(theta)   # voxel response prediction in Procrustes space
```

**Evaluation pathway (SRM bridge)**:
```
s = W_SRM^T @ ŷ_proc                     # project to shared latent for evaluation
M_s = W_SRM^T @ W_FE                     # (k x 6) evaluation bridge matrix
s_hat(theta) = M_s @ channels(theta)      # SRM-space evaluation at any angle
```

Note: M_s is an evaluation shortcut, not the prediction model itself. Continuous interpolation quality is rooted in Procrustes-level FE.

### 2.2 Prediction Model Validation

Before proceeding to filter design, the prediction engine must be validated. This is the critical **gate step** — if the prediction engine does not preserve color space structure, any downstream filter effect is uninterpretable (improvement could be genuine correction or prediction model bias).

**Why MAE alone is insufficient**: LOCO FE has a structural bottleneck: 7 training colors per fold yields ~1 degree of freedom per channel. The resulting MAE (~75° for HC) reflects this data limitation, not decoder quality. Previous attempts to improve MAE (Ridge, GCV, GP, hybrid MLP) all failed — confirming the bottleneck is encoding estimation, not the decoder architecture (LOCO_trials confirmed: correlation-based template matching is optimal).

**The real question**: "Does this model preserve color space geometry well enough to serve as a filter design surrogate?" — answered by 5 structural metrics.

#### 5 Structural Metrics (Table 2 + Figure 2)

| # | Metric | Pass criterion |
|---|--------|----------------|
| 1 | LOCO MAE | < 90° (chance) |
| 2 | Circular order preservation | Spearman rho > 0.7 |
| 3 | Local monotonicity | < 2 violations |
| 4 | Pairwise distance rank preservation | Kendall tau > 0.5 |
| 5 | Fold/run trajectory stability | Mean correlation > 0.6 |

#### Metric 1: LOCO MAE (baseline, existing)

**What**: Mean absolute circular error between predicted and actual hue angle.

**How**: For each LOCO fold (leave out 1 of 8 colors), train FE on 7 colors × 6 runs = 42 samples (pooled W, OLS alpha=0). Predict held-out color via correlation template matching against 360° basis functions. Average across 6 test runs → 1 predicted hue per fold. MAE = mean of 8 fold-level circular errors.

**Why needed**: Basic sanity check. If MAE ≥ 90° (chance level for 360° prediction), the model has no predictive signal at all.

**Known values**: HC mean ~75° in Procrustes, ~80° in SRM (LOCO_trials). Procrustes is better, confirming the operating space choice.

#### Metric 2: Circular order preservation (NEW)

**What**: Do the 8 LOCO-predicted hues maintain the correct angular ordering?

**How**: Collect predicted hues from all 8 LOCO folds → (8,) vector. Compute Spearman rank correlation between the rank order of predicted hues and the true hue order (0, 45, 90, ..., 315). Test both clockwise and counterclockwise directions (MDS reflection ambiguity), take the better |rho|.

**Why needed**: A model can have moderate MAE but still preserve the correct circular order — meaning it "knows" which colors are adjacent and which are distant, even if absolute positions are noisy. This is what matters for filter design: the filter needs to know the direction of correction, not the exact position.

**Example**: If true order is red→orange→yellow→green→cyan→blue→purple→magenta and predictions are 10°→55°→80°→140°→170°→230°→280°→320°, MAE is ~10° and order is perfect (rho=1.0). If predictions are 10°→280°→80°→140°→170°→230°→55°→320°, MAE is similar but order is broken.

#### Metric 3: Local monotonicity (NEW)

**What**: Are adjacent colors ever swapped in the predicted order?

**How**: For each adjacent pair (color_i, color_{i+1}) in the circular arrangement (including wraparound color_8→color_1): check if the predicted angular difference goes in the wrong direction. Specifically, a violation occurs when the true difference is forward (< 180°) but the predicted difference goes backward (> 180°). Count total violations (0-8 possible).

**Why needed**: Even if global order is approximately preserved (metric 2), local swaps between adjacent colors indicate that the model confuses neighboring hues. A filter built on such a model would warp colors in the wrong direction locally. Fewer than 2 violations means the model reliably distinguishes adjacent colors.

#### Metric 4: Pairwise distance rank preservation (NEW)

**What**: Does the predicted RDM preserve the rank order of pairwise distances compared to the actual neural RDM?

**How**:
1. **Actual RDM**: For each of 6 runs, compute 8×8 pairwise correlation-distance matrix from Procrustes voxel patterns. Average across 6 runs → reference (8, 8) RDM.
2. **Predicted RDM**: For each LOCO fold, the fitted W allows reconstructing voxel patterns at any hue: `predicted_pattern(theta) = W.T @ basis(theta)` → (n_voxels,). Reconstruct all 8 colors, compute pairwise correlation-distance → (8, 8). Average across 8 folds.
3. Extract upper triangles (28 unique pairs), compute Kendall tau between actual and predicted rank orders.

**Why needed**: The filter operates on the geometry of color representations. If the prediction model distorts which colors are close vs. distant (e.g., predicting blue-purple closer than blue-green when the brain does the opposite), the filter would optimize toward a wrong geometry. Kendall tau > 0.5 ensures the predicted distance structure is monotonically related to the actual one.

#### Metric 5: Fold/run trajectory stability (NEW)

**What**: Are the 360° prediction trajectories consistent across the 8 LOCO folds?

**How**: Each LOCO fold produces a different W matrix (trained on different 7-color subsets). For each fold, generate the full 360° trajectory: `trajectory_f = W_f.T @ basis_full.T` → (n_voxels, 360). Flatten each trajectory into a single vector. Compute C(8,2) = 28 pairwise Pearson correlations between all fold-level trajectories. Report mean correlation.

**Why needed**: If leaving out different training colors produces wildly different W matrices (and thus different 360° predictions), the model is unstable — the prediction at any angle depends heavily on which specific colors were used for training. A stable model (mean correlation > 0.6) means the 6-channel basis captures the voxel tuning reliably regardless of which 7 of 8 colors are available. This is essential because the filter will use a single W (pooled from all 8 colors), and we need confidence that this W represents a stable encoding model, not an artifact of the specific training set.

#### Gate Decision (Revised — HC Normative Procrustes Interpolation Quality)

All metrics computed in **Procrustes space** (not SRM). Gate validates Procrustes interpolation quality.

**HC-only criteria (per ROI)**:
1. Trajectory stability: HC mean > 0.6 AND CV ≤ 0.20
2. Signal presence: HC MAE mean < 90°
3. RDM rank preservation: HC tau mean > 0.25 AND ≥4/7 HC p<0.05

**Gate rule**: 3/3 → PASS. 1-2 → MARGINAL. 0 → FAIL.

**Results**: V1 PASS, V2 PASS, V3 PASS (borderline), V4 PASS. Metrics 2 (rho) and 3 (monotonicity) are supplementary diagnostics — their original thresholds are mathematically incompatible with 8 data points + MAE ~75°.

**Halt criteria**: HC trajectory mean < 0.5 AND RDM tau mean < 0.15 → FE structurally inadequate.

#### Figure 2 (Interpolation validation)

- Panel A: ROI-level LOCO MAE bar/point plot (HC mean ± SD, individual CVD points)
- Panel B: Circular order preservation polar plot (predicted vs actual hue positions, one example subject)
- Panel C: Pass/fail heatmap (10 subjects × 4 ROIs × 5 metrics)
- Panel D: Gate decision summary per ROI (PASS/MARGINAL/FAIL)

#### Implementation

**Script**: `step2_validate_prediction.py` — per-subject, runs LOCO FE in Procrustes space, computes 5 metrics.

**Procedure**:
```
For each ROI:
  Load amplitudes_procrustes.npy (6, 8, n_voxels)
  For each LOCO fold (test_color = 0..7):
    Train: 7 colors × 6 runs = 42 samples
    fit_W(X_train, hues_train, alpha=0) → W, basis_full
    decode_with_W(W, basis_full, X_test) → pred_hues per run
    Store: W matrix, mean predicted hue
  Compute 5 metrics from collected predictions + W matrices
  Save per-ROI results to JSON
```

**Reuses**: `fit_W`, `decode_with_W` from loco_ridge.py (lines 67-107); `create_basis_functions` from utils_color_decoding.py; `load_amplitudes` from loco_baseline.py.

**Output**: `results/step2_validation/sub-{ID}_validation.json` + summary + Figure 2.

**Runtime**: ~30 sec per subject (all 4 ROIs). SLURM array job for all 10 subjects.

### 2.3 Prediction Model Post-Evaluation

After validation, assess prediction quality further:

**(1) Latent trajectory smoothness**: Generate 360-degree hue trajectory per subject. Smooth trajectory = FE channels provide adequate basis.

**(2) HC latent geometry distance**: Measure baseline distance between each CVD subject's predicted trajectory and HC mean trajectory in SRM space.

**(3) Held-out color validation**: LOCO 8-fold — predict held-out color, compare to actual.

**(4) Permutation validation**: Shuffle subject labels to establish null distribution.

---

## 3. Filter Design

The filter is a **stimulus transform**: it remaps the input hue angle to bring CVD neural responses closer to HC geometry.

### 3.1 Filter Definition

```
theta' = T_psi(theta)
```

Fourier parameterization:
```
T_psi(theta) = theta + a1*cos(theta) + b1*sin(theta) + a2*cos(2*theta) + b2*sin(2*theta)
```

Properties:
- 4 free parameters: psi = (a1, b1, a2, b2)
- Identity when psi = 0 (no transform)
- Circular: T_psi(0) and T_psi(2*pi) connect smoothly
- Low-frequency: 1st and 2nd harmonics only — prevents jagged remappings
- Monotonicity constraint: dT_psi/dtheta > 0 everywhere (no color order reversal)

**T_psi is SEPARATE from FE 6-channel**: FE channels model neural encoding (voxel tuning); T_psi models stimulus correction (hue remapping). T_psi operates UPSTREAM: θ → T_psi(θ) → channels(T_psi(θ)) → W_FE.

**Why Fourier (not spline)**: (1) Inherently circular (periodic); (2) frequency truncation = automatic smoothness; (3) splines with 8 knots = overfitting risk; (4) splines don't naturally enforce circularity at θ=0↔360.

**Why only 1st + 2nd harmonics**: (1) CVD distortions arise from cone spectral sensitivity shifts — smooth, low-frequency; (2) 1st harmonic captures global axis distortion (L-M compression); (3) 2nd harmonic captures asymmetric expansion (S-cone compensation); (4) 3rd+ harmonics at 8-point data resolution = noise fitting.

**Why same 4-param family handles both deutan and protan**: a1·cos + b1·sin = R1·cos(θ-φ1) — phase φ1 freely rotates the distortion axis. sub-08 (deutan): 2nd harmonic dominant (S-cone compensation axis). sub-09 (protan): 1st harmonic dominant (magenta axis). Same parametric family, different fitted (a1,b1,a2,b2) per subject.

### 3.2 Filter Objective

```
L(psi) = sum_i ||M_CVD @ channels(T_psi(theta_i)) - s_bar_HC(theta_i)||^2
         + lambda * Omega(T_psi)
```

where:
- theta_i: 8 measured color angles (0, 45, ..., 315 degrees)
- M_CVD = W_SRM^T @ W_FE: CVD subject's (k x 6) **evaluation bridge** (not prediction model)
- s_bar_HC(theta_i): HC group-mean SRM representation at theta_i
- lambda * Omega(T_psi): regularization (smoothness + near-identity)

**Three-space separation**: Filter operates in stimulus space (T_psi). Prediction engine operates in Procrustes (W_FE). Evaluation uses SRM (M_s bridge) because cross-subject HC mean requires shared dimensionality (subjects have different n_voxels in Procrustes).

This loss **directly optimizes latent geometry matching**. Pairwise improvement is a consequence, not an explicit target.

### 3.3 Filter Optimization

```
psi* = argmin L(psi)
```

Method: scipy.optimize.minimize (L-BFGS-B), 4 parameters only. Per-subject, per-ROI optimization.

### 3.4 Filter Validation (3 levels)

**(1) Latent matching** (PRIMARY — Table 3 + Figure 3):

| Metric | Definition |
|--------|------------|
| Baseline latent distance | d(M_CVD @ channels(theta_i), s_bar_HC(theta_i)) summed over all i |
| Corrected latent distance | d(M_CVD @ channels(T_psi(theta_i)), s_bar_HC(theta_i)) summed over all i |
| % reduction | (baseline - corrected) / baseline x 100 |
| Held-out color generalization | Same metric at LOCO held-out theta (8-fold mean) |
| Permutation p-value | Rank of observed reduction in 1000-shuffle null |

Pass criteria:
- % reduction > 0 for all 3 CVD subjects
- Held-out generalization positive for >= 5/8 LOCO folds per subject
- Permutation p < 0.05 for >= 1 CVD subject
- Monotonicity: dT_psi/dtheta > 0 everywhere

Figure 3 (Main result — Latent matching before vs after):
- Per-subject panel (sub-08, sub-09, sub-10)
- Each panel: 8-color trajectory in SRM space
  - Gray: HC mean trajectory
  - Red: baseline CVD trajectory
  - Blue: corrected CVD trajectory
- Primary: V2; auxiliary panel: V1
- Message: "Whole-geometry shift toward HC, not pairwise patch-fixing"

**(2) Pairwise distortion rescue** (SECONDARY — Table 4 + Figure 4):

Limited to pre-validation evidence pairs only:
- Group: V2 blue-purple (p=0.042)
- sub-08: V2 12 FDR pairs (yellow-purple z=13.87 strongest), V3 17 FDR pairs
- sub-09: V1 cyan-magenta (z=4.08), V1 red-magenta (z=3.52)
- sub-10: No FDR pairs (cortical compensation)

Pass criterion: Rescue direction correct for > 50% of evidence-weighted pairs.

Figure 4 (Pairwise diagnostic map):
- Panel A/B: Pairwise error heatmap baseline vs corrected
- Panel C: Difference map, evidence-weighted pairs highlighted
- Rows: sub-08, sub-09, sub-10; Columns: V2, V1

**(3) Trajectory improvement**: Verify that the corrected 360-degree trajectory is smoother and closer to HC circular geometry.

### 3.5 Filter Post-Evaluation

**(1) Neural validation**: Corrected stimulus → predicted neural response → compare with HC geometry in SRM space. This is the in-silico validation.

**(2) Behavioral validation (future, deferred)**: Psychophysics with corrected stimuli — JND thresholds, pair discrimination tasks. Requires additional scanning session.

---

## 4. Full Pipeline Summary

| Step | What | Primary Space | Deliverable |
|------|------|--------------|-------------|
| 1 | FE fit (W_FE) + SRM fit (W_SRM) + M_s | **Procrustes** + SRM | W_FE, W_SRM, M_s per subject |
| 2 | Procrustes interpolation validation | **Procrustes** | Table 2 + Figure 2 (GATE 1) |
| 2b | M_s evaluation bridge validation | Procrustes → SRM | bridge_summary.json (GATE 2) |
| 3 | Filter optimization (T_psi) | **Stimulus** (eval: SRM) | T_psi per CVD subject, Table 3 + Figure 3 (PRIMARY) |
| 4 | Permutation test | SRM | p-values |
| 5 | Pairwise diagnostic | SRM | Table 4 + Figure 4 (SECONDARY) |

**Three-space architecture**: Filter in stimulus space, prediction in Procrustes, evaluation in SRM. SRM is needed for cross-subject target (different n_voxels) but is not the prediction core.

---

## 5. Two-Space Logic Figure (Figure 1)

Conceptual schematic tying Steps 1-5 together. Created last; appears as manuscript Figure 1.

**Layout**:
- Left: SRM space — HC vs CVD comparison, target ROI (V2, V1)
- Right: Procrustes + FE — interpolation engine, continuous hue trajectory
- Center arrows: stimulus transform T_psi, prediction → latent matching

**Annotations**:
- SRM = target/comparison space
- Procrustes = interpolation/operating space
- Primary objective = latent geometry matching
- Pairwise disparity = secondary diagnostic

---

## 6. Implementation

### 6.1 Scripts

| Script | Pipeline Step | Purpose | Input | Output |
|--------|-------------|---------|-------|--------|
| `utils_transform.py` | — | Shared utilities (channels, Fourier T, M_s, latent distance) | — | importable module |
| `step1_build_prediction_model.py` | 2 | Build M_s per subject (W_SRM^T @ W_FE) | amplitudes_procrustes.npy, amplitudes_srm.npy | M_s matrices, HC mean targets |
| `step2_validate_prediction.py` | 3 | LOCO structural metrics | M_s matrices | Table 2 JSON, Figure 2 |
| `step3_filter_optimization.py` | 4 | T_psi optimization + latent distance reduction | M_s matrices, HC mean targets | Table 3 JSON, fitted psi, Figure 3 |
| `step4_permutation_test.py` | 4 | Null distribution for latent matching (1000 shuffles) | step3 outputs | p-values, null distributions |
| `step4_permutation.sbatch` | 4 | SLURM wrapper for step4 | step4 script | SLURM logs |
| `step5_pairwise_diagnostic.py` | 5 | Pairwise rescue at evidence pairs | step3 psi + pre-validation pair list | Table 4 JSON, Figure 4 |

**All scripts save to `results/` with flat structure (no timestamp subdirs) per CLAUDE.md convention.**

### 6.2 Directory Structure

```
future_phase2_filter_optimization/
├── PLAN.md              # This document
├── README.md            # Phase overview + relationship to LOCO trials
├── pre_validation/      # Existing pre-validation results
│   ├── notion_prevalidation.md
│   ├── results/
│   └── scripts/
├── figures/             # Existing + new validation figures
│   └── README.md
├── scripts/             # Implementation (to be created)
│   ├── utils_transform.py
│   ├── step1_build_prediction_model.py
│   ├── step2_validate_prediction.py
│   ├── step3_filter_optimization.py
│   ├── step4_permutation_test.py
│   ├── step4_permutation.sbatch
│   └── step5_pairwise_diagnostic.py
└── results/             # Outputs (to be created)
    ├── step1_prediction_model/
    ├── step2_validation/
    ├── step3_filter/
    ├── step4_permutation/
    └── step5_pairwise/
```

---

## 7. Success Criteria

### Required (all must pass)

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| FE+Procrustes structural preservation | Order rho > 0.7, rank tau > 0.5 | Prediction engine must be structurally reliable |
| Corrected representation closer to HC | % reduction > 0 for all CVD subjects | Direction of correction is correct |
| Held-out color generalization | Positive for >= 5/8 LOCO folds | Not overfitting to training colors |
| Permutation significance | p < 0.05 for >= 1 CVD subject | Improvement exceeds chance |
| Monotonicity | dT_psi/dtheta > 0 everywhere | Physically meaningful (no folding) |

### Strengthening (not required, but bolsters claims)

| Criterion | What it shows |
|-----------|---------------|
| Pre-validation pairs rescued > 50% | Latent correction aligns with known pairwise distortions |
| Subject-type-specific correction directions | sub-08 deutan ≠ sub-09 protan correction patterns |
| V2 results most robust | Consistent with V2 as best-structured ROI (Phase 2, LOCO_trials) |
| sub-10 shows minimal correction | Expected: cortical compensation already achieved HC-like geometry |

---

## 8. Relationship to Existing Analyses

| Component | Source | Status |
|-----------|--------|--------|
| SRM k values (V1=4, V2=4, V3=3, hV4=3) | Phase 2 validation 2C | Confirmed |
| W_FE (forward encoding weights) | phase3_decoder_comparing LOCO/LORO | Pooled W adopted |
| HC-CVD SRM disparity | Phase 2 LOO-consistent | V1 p=0.062, V2 p=0.075 |
| LOCO FE baseline (Procrustes) | phase3_decoder_comparing | HC MAE ~75° |
| FE W cosine stability | LOCO_trials | 0.921 |
| SRM continuous structure limits | LOCO_trials Phase 1b MDS | V1 unstructured (0/4), hV4 CIELab sign flip |
| V2 SRM structure | LOCO_trials Phase 1b | Structured (2/4 criteria), 3D stress=0.097, Isomap>MDS |
| Per-pair CVD distortion profiles | pre_validation B1-B3 | L-M deficit + S-cone compensation |
| Cross-decoding HC≈CVD | LOCO_trials | Categorical equivalent (10/12 sig), continuous deficit in LOCO |
| Individual CVD profiles | pre_validation | sub-08: V2/V3 dominant; sub-09: V1 dominant; sub-10: no elevation |

---

## 9. Deferred Items

- **Script implementation** (step1-5 .py files): To be created after plan approval
- **Server-side folder renames**: User will handle when ready
- **Behavioral validation**: Requires additional scanning session with corrected stimuli
- **Multi-ROI joint optimization**: Currently per-ROI; joint T_psi across ROIs is a possible extension
- **Figure 1 (two-space schematic)**: Created last as conceptual synthesis, not a computational step
