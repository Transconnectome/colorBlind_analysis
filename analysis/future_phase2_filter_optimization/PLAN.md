# Stimulus-Space Filter Optimization — PLAN (Revised: RDM-Matching)

> Last updated: 2026-03-16
> Status: Implementation complete; ready for server execution
> Previous version: M_s bridge + latent geometry (2026-03-07, superseded)
> Pivot reason: Cone shift angle correction FAILED experimentally; per-color patterns already match (W_HC @ C(θ_original) ≈ HC mean). Deficit is in inter-color geometry (pairwise RDM structure).

---

## 0. Context and Pivot

### What failed (Approach A: angle substitution)
All CVD subjects showed **worse** predictions after angle substitution. Key finding: `W_HC @ C(θ_original)` already predicts CVD hV4 per-color patterns well (sub-09 baseline=0.495 ≈ HC mean 0.492). The deficit is NOT in per-color patterns but in **inter-color geometry** (pairwise RDM structure).

### What changed
- **Previous plan**: M_s bridge matrix (W_SRM^T @ W_FE) + latent geometry matching in SRM space
- **New plan**: Direct RDM-level optimization using W₀ (HC group prior) in Procrustes voxel space
- **Why**: SRM bridge adds unnecessary complexity. The filter question can be answered directly: "Does remapping θ → T_ψ(θ) improve predicted pairwise distances toward HC?"

### Primary outcome
Either (A) T_ψ improves CVD→HC geometry = filter works, or (B) T_ψ* ≈ identity at RDM level too = stimulus-space filter insufficient, cortical locus confirmed. **Both are publishable.**

---

## 1. Architecture: Two-Level Estimation

### Level 1: Pattern-Level (confirmation)
```
L_pattern(ψ) = Σ_i || W₀ @ C(T_ψ(θ_i)) − Ȳ_CVD(θ_i) ||²
```
- Expected: T_ψ* ≈ 0. Per-color patterns already match.

### Level 2: RDM-Level (the real test)
```
L_RDM(ψ) = Σ_{i<j} w_ij · (d^ψ_ij − μ_HC_ij)²
```
where:
- `d^ψ_ij = corr_dist(W₀ @ C(T_ψ(θ_i)), W₀ @ C(T_ψ(θ_j)))` — predicted pairwise distance after transform
- `μ_HC_ij` — mean HC pairwise distance for pair (i,j)
- `w_ij` — optional weighting from pre-validation FDR z-scores (default: uniform)

### T_ψ Parameterization (Fourier)
```
T_ψ(θ) = θ + a₁cos(θ) + b₁sin(θ) + a₂cos(2θ) + b₂sin(2θ)   [4 params]
```
Monotonicity constraint: `dT_ψ/dθ > 0` everywhere.

### Nested Model Comparison
| Model | Params | Description |
|-------|--------|-------------|
| **Model 0** | 1 (Δλ) | Cone shift: T₀(θ) = θ + δθ(θ; Δλ) from Stockman physics |
| **Model A** | 4 (a₁,b₁,a₂,b₂) | Fourier: T_ψ(θ) = θ + Σ harmonics |
| **Model B** | 8 (δ₁..δ₈) | Per-color free shift: T(θ_i) = θ_i + δ_i |

Compare via F-test (nested) and AICc. Model 0 ⊂ A ⊂ B.

---

## 2. Pipeline Steps

### Step 1: Build Model — W₀ + HC Reference RDMs
**Script**: `scripts/step1_build_model.py`
**SLURM**: `sbatch/run_step1.sbatch` (single job, node2, 8G, ~1 min)

Constructs:
- W₀ = (R_new @ A_g).T — HC group prior projected into CVD voxel space
- Ȳ_CVD = amp.mean(axis=0) — mean CVD response per color
- HC mean RDM — target geometry
- Baseline predicted RDM — identity transform reference

**Outputs** → `results/step1_model/{ROI}/sub-{CVD}/`:
- `W0.npy`, `Y_mean.npy`, `baseline_rdm.npy`, `cvd_rdm.npy`
- `hc_rdm_mean.npy`, `hc_rdm_per_subject.npy`
- `results.json`, `config.json`

### Step 2: Validate Prediction (ALREADY DONE)
Gate passed: all 4 ROIs PASS on trajectory stability, MAE, and RDM rank preservation.
Results at: `results/step2_validation/`

### Step 3: Filter Estimation — Core Two-Level T_ψ + Nested Models
**Script**: `scripts/step3_filter_estimation.py`
**SLURM**: `sbatch/run_step3.sbatch` (array 1-3, node2, 8G, ~5 min each)

For each CVD subject × ROI (hV4, V2, V1):
1. **Level 1**: Pattern-level optimization → confirm T_ψ* ≈ identity
2. **Level 2**: RDM-level optimization with multi-start L-BFGS-B
3. **Model 0**: Evaluate cone-shift angles (no optimization)
4. **Model A**: 4-param Fourier with monotonicity penalty
5. **Model B**: 8-param free shift
6. **Nested comparison**: F-test + AICc

**Outputs** → `results/step3_filter/sub-{CVD}_filter_results.json`

### Step 4: Validation — LOCO + Permutation
**Script**: `scripts/step4_validation.py`
**SLURM**: `sbatch/run_step4.sbatch` (array 1-3, node2, 16G, ~30 min each)

- **LOCO (8-fold)**: Train on 21 pairs (7 colors), test on 7 held-out pairs. ≥5/8 folds positive = robust.
- **Permutation (1000 shuffles)**: Randomly reassign HC/CVD labels, rebuild everything, fit filter. p < 0.05 = systematic effect.

**Outputs** → `results/step4_validation/sub-{CVD}_loco_validation.json`

### Step 5: Pairwise Diagnostic — FDR Pair Rescue
**Script**: `scripts/step5_pairwise_diagnostic.py`
**SLURM**: `sbatch/run_step5.sbatch` (single job, node2, 8G, ~1 min)

Cross-references step3 filter effect with pre-validation FDR pairs. For each FDR-significant pair, checks whether filter reduces distance error toward HC.

**Outputs** → `results/step5_pairwise/sub-{CVD}_pairwise_diagnostic.json`

---

## 3. ROI Strategy

| ROI | Role | Rationale |
|-----|------|-----------|
| **hV4** | Primary | Phase 1 gate ROI (perm p=0.044), only ROI exceeding LOCO permutation null |
| **V2** | Validation | Best SRM structure, independent FDR pairs |
| **V1** | Exploratory | Discrimination-only, expect no filter effect |

## 4. Subject Strategy

| Subject | Type | FDR pairs | Role |
|---------|------|-----------|------|
| **sub-08** | Deutan | 28 | Primary proof-of-concept |
| **sub-09** | Protan | 8 | Boundary case |
| **sub-10** | Deutan | 1 | Negative control |

---

## 5. Execution Order

```
Step 1 → Step 3 → Step 4 → Step 5
(Step 2 already done)
```

---

## 6. Scripts and Files

### 6.1 Implementation

| File | Type | Purpose |
|------|------|---------|
| `scripts/utils_filter.py` | Shared utilities | T_ψ transforms, loss functions, nested model comparison |
| `scripts/step1_build_model.py` | Build model | W₀ + HC RDMs for all ROIs/subjects |
| `scripts/step3_filter_estimation.py` | Core script | Two-level filter estimation + nested models |
| `scripts/step4_validation.py` | Validation | LOCO cross-validation + permutation test |
| `scripts/step5_pairwise_diagnostic.py` | Diagnostic | FDR pair rescue analysis |
| `sbatch/run_step1.sbatch` | SLURM | Single job wrapper |
| `sbatch/run_step3.sbatch` | SLURM | Array 1-3 wrapper |
| `sbatch/run_step4.sbatch` | SLURM | Array 1-3 wrapper |
| `sbatch/run_step5.sbatch` | SLURM | Single job wrapper |

### 6.2 Existing (unchanged)

| File | Purpose |
|------|---------|
| `scripts/utils_transform.py` | Step 2 structural metrics (4 functions) |
| `scripts/step2_validate_prediction.py` | Step 2 validation (DONE) |
| `scripts/step2_summarize.py` | Step 2 local summarization |
| `pre_validation/` | Pre-validation results (FDR pairs, z-scores) |

### 6.3 Critical Reuse (from Phase 1)

| Function | Source | Used in |
|----------|--------|---------|
| `fit_srm_all_hc()` | `cone_shift_loco.py` | step1 |
| `build_Ag_all_hc()` | `cone_shift_loco.py` | step1 |
| `build_W_HC_for_cvd()` | `cone_shift_loco.py` | step1 |
| `load_amplitudes()` | `utils_forward_model.py` | step1, step4 |
| `create_basis_full()` | `utils_forward_model.py` | step3, step4 |
| `compute_rdm()`, `rdm_upper_tri()` | `utils_forward_model.py` | all steps |
| `predict_patterns()` | `utils_forward_model.py` | step1 |

### 6.4 Directory Structure

```
future_phase2_filter_optimization/
├── PLAN.md              # This document
├── README.md
├── pre_validation/      # Existing pre-validation results
├── figures/
├── scripts/
│   ├── utils_transform.py       # Step 2 metrics (existing)
│   ├── utils_filter.py          # NEW: filter utilities
│   ├── step1_build_model.py     # NEW: build W₀ + HC RDMs
│   ├── step2_validate_prediction.py  # Existing (DONE)
│   ├── step2_summarize.py       # Existing
│   ├── step2b_validate_bridge.py    # Existing (superseded)
│   ├── step3_filter_estimation.py   # NEW: core filter estimation
│   ├── step4_validation.py          # NEW: LOCO + permutation
│   └── step5_pairwise_diagnostic.py # NEW: FDR pair rescue
├── sbatch/
│   ├── run_step1.sbatch    # NEW
│   ├── run_step3.sbatch    # NEW
│   ├── run_step4.sbatch    # NEW
│   └── run_step5.sbatch    # NEW
└── results/
    ├── step1_model/
    ├── step2_validation/   # Existing (DONE)
    ├── step3_filter/
    ├── step4_validation/
    └── step5_pairwise/
```

---

## 7. Success Criteria

| Criterion | Threshold |
|-----------|-----------|
| Pattern T_ψ* ≈ 0 | ‖ψ*‖ < 5° max shift (EXPECTED) |
| RDM improvement > 0 | ≥1 CVD subject |
| LOCO generalization | ≥5/8 folds positive |
| Permutation p < 0.05 | ≥1 CVD subject |
| Monotonicity | dT/dθ > 0 everywhere |
| Model A > Model 0 | F-test p < 0.05 |
| FDR pair rescue > 50% | For sub-08 |

**Null result**: RDM T_ψ* ≈ 0 → "CVD inter-color metric distortion cannot be corrected by stimulus remapping alone" — cortical locus confirmed.

---

## 8. Verification Checklist

1. **step1**: W₀ baseline voxel_corr should match cone_shift_loco.py results
2. **step3**: L_pattern ψ*≈0 confirms cone_shift_loco negative result; check Model 0/A/B AIC ordering
3. **step4**: LOCO improvement distribution + permutation null histogram
4. **step5**: Cross-reference with pre-validation FDR pairs
