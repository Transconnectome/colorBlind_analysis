# Cone Shift Pipeline

## Background

The previous W0+T_psi filter pipeline (Steps 3-5 in `scripts/`) failed due to identifiability:
R_new (the CVD subject's SRM projection) absorbed both retinal shifts and cortical
differences, making T_psi redundant. This redesigned pipeline uses **W_HC (pure HC encoding,
fixed)** with **delta_theta as the sole free variable**.

## Core Design Principle

All fitting criteria use HC-derived encoding weights (pre-computed, never re-optimized).
The only free variable is the hue distortion delta_theta, parameterized by one of 5
distortion models.

| Criterion | W Source | R_new? | Prediction Space |
|-----------|----------|:------:|------------------|
| 1a (Voxel RDM) | HC per-subject ridge_gcv | No | Voxel |
| 1b (SRM RDM) | A_g (group prior) | Target only | SRM common |
| 2 (LORO) | A_g in SRM space | Target only | SRM common |
| 3 (LOCO sim) | HC per-subject ridge_gcv | No | Voxel |
| W constraint | ridge_gcv(Y_CVD, C(theta)) | No | Voxel |

**Key**: R_new is never on the model side. Where used (1b, 2), it projects CVD
observations into shared space and is fixed (not optimized).

## Distortion Models

| Model | df | Parameters | Biological Interpretation |
|-------|----|------------|--------------------------|
| cone_1way | 1 | |delta_lambda| (nm) | Single affected cone shift magnitude |
| cone_3way | 3 | delta_L, delta_M, delta_S (nm) | Independent 3-cone shifts |
| fourier | 4 | a1, b1, a2, b2 (degrees) | Smooth circular distortion (k=1,2) |
| per_color | 8 | delta_1..delta_8 (degrees) | Per-color free shift |
| fourier_8 | 8 | a1..a4, b1..b4 (degrees) | Smooth circular (k=1..4) |

## Fitting Criteria

### Criterion 1a: Voxel-Space RDM (no R_new)
For each HC subject: W_i = ridge_gcv(Y_HC_i, C(theta)). Predict RDM with
C(theta+delta) @ W_i. Average predicted RDM across 7 HC. Match to CVD voxel-space RDM.

### Criterion 1b: SRM-Space RDM
Model: Z_model = A_g @ C(theta+delta)^T. Target: Z_CVD = R_new^T @ beta_CVD^T.
Compare RDMs in k-dimensional space. Also includes 1a->1b transfer test.

### Criterion 2: SRM-Space LORO
6-fold run-level validation. Predict Z_pred = A_g @ C(theta+delta)^T,
compare to Z_CVD_r = R_new^T @ Y_CVD_r^T per run.

### Criterion 3: LOCO Simulation
Apply delta_theta to HC subjects' LOCO procedure. Train W with C(theta), predict
with C(theta+delta). Match resulting per-color vulnerability to CVD's actual pattern.

## W Constraint Verification
W_free = ridge_gcv(Y_CVD, C(theta)) vs W0 (HC group prior). Tests cortical equivalence.
Crawford & Howell test against HC W distribution.

## Data Dependencies

| Data | Local Path | Shape |
|------|-----------|-------|
| Amplitudes | `../../phase1_preprocess_decoding/results/full_dataset_C010/sub-{ID}/{ROI}/amplitudes_procrustes.npy` | (6,8,V_s) |
| A_g | `../../future_phase1_forward_model/results/group_prior/{ROI}/A_g.npy` | (k,K) |
| Shared response | `../../future_phase1_forward_model/results/srm_projections/{ROI}/shared_response.npy` | (k,8) |
| LOCO results | `../../future_phase1_forward_model/results/validation/sub-{ID}_loco.json` | per-fold |
| Legacy W0 | `../results/step1_model/{ROI}/sub-{CVD}/W0.npy` | (K,V_s) |

## Execution

```bash
# Phase A: Foundations (local)
conda activate srm
python scripts/step1_validate_cone_mapping.py

# Phase B: Fitting (local)
python scripts/step2_fit_rdm.py
python scripts/step3_fit_loro.py
python scripts/step3_fit_loco.py
python scripts/step3_verify_w_constraint.py

# Phase C: Integration (local)
python scripts/step4_cross_validate.py
python scripts/plot_summary.py

# Phase D: Server permutation test
scp scripts/step5_hc_replication_null.py haba6030@node3:...
sbatch sbatch/run_step5.sbatch
```

## Notation

| Symbol | Shape | Definition |
|--------|-------|-----------|
| C(theta) | (8,K) | Design matrix, FE-6 basis at 8 hue angles |
| A_g | (k,K) | Group encoding matrix (HC mean) |
| R_new | (V_s,k) | CVD SRM projection (orthonormal) |
| Z_i | (k,8) | Subject i common-space response |
| W_i | (K,V_s) | Per-subject ridge_gcv weight |
| delta_theta | varies | Distortion parameters (sole free variable) |
