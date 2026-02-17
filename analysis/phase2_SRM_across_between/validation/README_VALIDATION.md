# Phase 2 SRM Analysis - Validation Tests

This directory contains validation tests for the Phase2 SRM (Shared Response Model) between-subject analysis. The goal is to verify the robustness of the "scattered but parallel" CVD pattern finding.

## Background

### Current Findings (from RESULTS_SUMMARY.md)
- **V1/V2**: Significant CVD-HC separation (p<0.05) ✓
- **"Scattered but Parallel" Pattern**:
  - CVD-CVD disparity: 1.4-1.8× higher than HC-HC (spatial heterogeneity)
  - CVD-CVD RDM correlation: 0.591 in V2 (HIGHER than HC-HC 0.517!) ✅
  - Interpretation: CVD subjects occupy different spatial positions but preserve similar color relational structure

### Validation Goals

Test if these findings are robust against:
1. **Data leakage** - Is HC-only training correctly implemented?
2. **Sample instability** - Are patterns stable with n_CVD=3?
3. **"Scattered but parallel"** - Is the dual pattern (high disparity + high RDM correlation) reliable?

## Test Status

| Test | Purpose | Status | Critical Findings |
|------|---------|--------|-------------------|
| **1A** | Verify HC-only Training | ✅ COMPLETE | All checks passed, CVD/HC ratio 1.12-1.47× |
| **1B** | LOSO Stability | 🚧 READY (server) | Test fold-wise consistency |
| **1C** | Split-Half Reliability | 🚧 READY (server) | Test run-split stability |
| **1D** | Permutation Test | ✅ COMPLETE | V1 p=0.014, V2 p=0.036 significant; V3/hV4 n.s. as expected |
| **2A** | Individual ICC | ✅ COMPLETE | Mean r=0.475; 58% moderate, sub-08 best (hV4 r=0.71) |
| **2B** | RDM Consistency | ✅ COMPLETE | CVD ≥ HC in V1/V2 — "parallel" pattern CONFIRMED |
| **2C** | Optimal k Selection | 🚧 READY (server) | Cross-validate SRM dimensionality |
| **2D** | Alignment Comparison | 🚧 READY (server) | Compare Raw/Procrustes/SRM |

## Directory Structure

```
validation/
├── README_VALIDATION.md                    # This file
├── utils/
│   ├── __init__.py
│   ├── validation_metrics.py              # ICC, permutation, bootstrap
│   └── statistical_tests.py               # ANOVA, Bonferroni, effect sizes
│
├── 1A_verify_hc_only/
│   ├── verify_hc_only_simple.py           # ✅ COMPLETED
│   └── results/20260216_163108/
│       ├── settings.json
│       ├── results.json
│       └── verification_report.txt
│
├── 1B_loso_stability/                      # 🚧 Server job (7 folds)
├── 1C_split_half/                          # 🚧 Server job
├── 1D_permutation/                         # 🚧 Local execution
├── 2A_run_split_icc/                       # 🚧 Local execution
├── 2B_rdm_consistency/                     # 🚧 Local execution
├── 2C_optimal_k_selection/                 # 🚧 Server job (28 jobs)
└── 2D_alignment_comparison/                # 🚧 Server job
```

## Test Details

### Test 1A: Verify HC-only Training ✅

**Status**: COMPLETED

**Purpose**: Verify existing SRM results are internally consistent

**Method**: Check file structure, subjects, disparity patterns, statistics

**Results** (20260216_163108):
- ✅ All 4 ROIs passed verification
- ✅ Correct subjects: HC n=7, CVD n=3
- ✅ CVD-HC disparity > HC-HC for all ROIs
- ✅ V1: p=0.0242, V2: p=0.0253 (significant)
- ✅ V3: p=0.4434, hV4: p=0.4938 (non-significant)

**Key Finding**: CVD/HC disparity ratios:
- V1: 1.47× (0.5733 vs 0.3898)
- V2: 1.37× (0.5489 vs 0.3998)
- V3: 1.15× (0.5094 vs 0.4435)
- hV4: 1.12× (0.6413 vs 0.5749)

---

### Test 1B: Leave-One-Subject-Out (LOSO) Stability

**Status**: Scripts ready, needs server execution

**Purpose**: Test if HC-CVD separation is stable when leaving out individual HC subjects

**Method**:
- Leave out HC subject i ∈ {1..7}
- Train SRM on remaining 6 HC subjects
- Project left-out HC + 3 CVD to shared space
- Compute CVD-HC disparity for each fold
- Expected: Consistent separation across all 7 folds

**Files**:
- `run_loso_srm.py` - Main script
- `run_loso_srm.sbatch` - SLURM array job (7 folds)
- `aggregate_loso_results.py` - Combine fold results (local)
- `visualize_loso_stability.py` - Generate plots (local)

**Expected Results**:
- ICC > 0.7 (good consistency across folds)
- V1/V2 show p<0.05 in ALL 7 folds
- Mean disparity similar to original (0.55-0.57 for CVD-HC)

---

### Test 1C: Split-Half Reliability

**Status**: Scripts ready, needs server execution

**Purpose**: Test if SRM learned from different run subsets produces consistent CVD patterns

**Method**:
- Set A: Average runs 1-3 → (n_subjects, 8, n_voxels)
- Set B: Average runs 4-6 → (n_subjects, 8, n_voxels)
- Train separate SRM models on each set (HC only)
- Compute CVD-HC disparities for both sets
- Spearman correlation between Set A and Set B disparities

**Files**:
- `run_split_half_srm.py` - Main script
- `run_split_half_srm.sbatch` - SLURM job
- `visualize_split_half.py` - Generate plots (local)

**Expected Results**:
- Spearman r > 0.7 (high correlation between run splits)
- **CRITICAL**: CVD-CVD RDM correlation >0.5 in BOTH sets (validates "parallel" pattern)
- Disparity patterns stable across run splits

---

### Test 1D: Label Permutation Test

**Status**: Scripts ready, local execution only

**Purpose**: Test if observed CVD-HC disparity difference is larger than chance

**Method**:
- Load existing disparity results from Test 1A
- Compute observed t-statistic: (CVD-HC mean - HC-HC mean) / SE
- Permutation loop (n=10,000):
  - Shuffle group labels (HC-HC vs CVD-HC)
  - Recompute t-statistic
- P-value: P(t_null ≥ t_obs)

**Files**:
- `run_permutation_test.py` - Main script
- `visualize_permutation.py` - Histogram plots

**Expected Results**:
- V1/V2: p < 0.05 (survives permutation test)
- V3/hV4: p > 0.05 (expected, underpowered)

---

### Test 2A: Run-Split Individual Stability (ICC)

**Status**: Scripts ready, local execution only

**Purpose**: Test if individual CVD patterns are stable across run splits

**Method**:
- For each CVD subject (sub-08, sub-09, sub-10):
  - Compute disparity using runs 1-3 average
  - Compute disparity using runs 4-6 average
  - Calculate ICC(3,1) with bootstrap 95% CI

**Files**:
- `compute_run_split_icc.py` - Main script
- `visualize_icc.py` - Heatmap generation

**Expected Results**:
- ICC > 0.6 for most subject-ROI pairs (good stability)
- Validates individual-level reliability

---

### Test 2B: RDM Consistency (Split-Half Correlation)

**Status**: Scripts ready, local execution only

**Purpose**: Test if color RDMs are consistent within subjects across run splits

**Method**:
- For each subject (all 10):
  - Compute RDM from runs 1-3
  - Compute RDM from runs 4-6
  - Spearman correlation between upper triangles (28 values)
- Compare HC vs CVD split-half reliability

**Files**:
- `compute_rdm_split_half.py` - Main script
- `visualize_rdm_consistency.py` - Boxplot comparison

**Expected Results**:
- HC split-half r > 0.5
- **CRITICAL**: CVD split-half r should be **comparable or higher** in V1/V2 (validates "parallel" pattern)
- Low CVD reliability would challenge current findings

---

### Test 2C: Cross-Validation for Optimal k Selection

**Status**: Scripts ready, needs server execution

**Purpose**: Select optimal k based on generalization performance via LOSO CV

**Method**:
- For each HC subject i ∈ {1..7}:
  - For each k ∈ [2, 3, 4, 5, 6, 8]:
    - Train SRM on remaining 6 HC subjects
    - Project left-out subject to k-dimensional space
    - Reconstruct and compute MSE
- Select k* = argmin(mean_error)

**Files**:
- `run_k_selection_cv.py` - Main script
- `run_k_selection_cv.sbatch` - SLURM array (7 folds × 4 ROIs = 28 jobs)
- `aggregate_k_selection.py` - Combine results (local)
- `visualize_k_selection.py` - Error curves (local)

**Expected Results**:
- Optimal k* close to current values (V1=4, V2=4, V3=3, hV4=4)
- Reconstruction error decreases with k up to optimal point

---

### Test 2D: Alignment Method Stability Comparison

**Status**: Scripts ready, needs server execution

**Purpose**: Compare split-half reliability of Raw vs Procrustes vs SRM alignment

**Method**:
- For each method (Raw, Procrustes, SRM):
  - Compute split-half RDM correlation (same as Test 2B)
  - Average across subjects
- Repeated-measures ANOVA (method × ROI)

**Files**:
- `compare_alignment_stability.py` - Main script
- `compare_alignment_stability.sbatch` - SLURM job
- `visualize_alignment_comparison.py` - Barplot (local)

**Expected Results**:
- SRM shows higher stability than Raw (validates dimensionality reduction)
- Post-hoc: SRM > Procrustes > Raw

---

## Execution Guide

### Local Tests (No Server Needed)

**Test 1A**: Already completed ✅

**Test 1D, 2A, 2B**: Can be run locally once baseline data is available

```bash
# Test 1D: Permutation test
cd 1D_permutation
python run_permutation_test.py

# Test 2A: Individual ICC
cd 2A_run_split_icc
python compute_run_split_icc.py

# Test 2B: RDM consistency
cd 2B_rdm_consistency
python compute_rdm_split_half.py
```

### Server Tests (Require SLURM)

**Upload scripts**:
```bash
# From local validation/ directory
scp 1B_loso_stability/run_loso_srm.py 1B_loso_stability/run_loso_srm.sbatch \
    1C_split_half/run_split_half_srm.py 1C_split_half/run_split_half_srm.sbatch \
    2C_optimal_k_selection/run_k_selection_cv.py 2C_optimal_k_selection/run_k_selection_cv.sbatch \
    2D_alignment_comparison/compare_alignment_stability.py 2D_alignment_comparison/compare_alignment_stability.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/

# Upload utilities
scp utils/*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/utils/
```

**Submit jobs**:
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation

# Test 1B: LOSO (7 folds)
sbatch 1B_loso_stability/run_loso_srm.sbatch

# Test 1C: Split-half
sbatch 1C_split_half/run_split_half_srm.sbatch

# Test 2C: Optimal k (28 jobs)
sbatch 2C_optimal_k_selection/run_k_selection_cv.sbatch

# Test 2D: Alignment comparison
sbatch 2D_alignment_comparison/compare_alignment_stability.sbatch

# Monitor
squeue -u haba6030
```

**Download results**:
```bash
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/*/results/ \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between/validation/
```

---

## Success Criteria

### Critical Validation of "Scattered but Parallel" Pattern

**High CVD-CVD disparity** (Tests 1A-1C):
- ✅ Test 1A: Confirmed 1.12-1.47× ratio
- [ ] Test 1B: Stable across LOSO folds
- [ ] Test 1C: Stable across run splits

**High CVD-CVD RDM correlation** (Tests 1C, 2B):
- [ ] Test 1C: >0.5 in BOTH run splits for V1/V2
- ✅ Test 2B: CVD ≥ HC in V1 (+0.200) and V2 (+0.123) — "parallel" CONFIRMED

**Statistical robustness** (Tests 1B, 1D):
- [ ] Test 1B: All 7 folds show p<0.05 for V1/V2
- ✅ Test 1D: V1 p=0.014, V2 p=0.036 — survives permutation test

**Individual stability** (Tests 2A, 2B):
- ⚠️ Test 2A: Mean r=0.475 (moderate); 1/12 good, 7/12 moderate, 4/12 poor — sub-08 strongest
- ✅ Test 2B: High within-subject consistency (CVD r=0.53-0.71 across ROIs)

**Methodological validation** (Tests 2C, 2D):
- [ ] Test 2C: Optimal k matches current choices
- [ ] Test 2D: SRM outperforms raw alignment

---

## References

### Related Documents
- `../RESULTS_SUMMARY.md` - Current Phase2 findings
- `../../phase1_preprocess_decoding/README.md` - Baseline preprocessing
- `/Users/jinilkim/.claude/projects/.../36e2501a-7b27-499b-a838-2a267e0b8a47.jsonl` - Full planning transcript

### Key Papers
- Chen et al. (2015). A Reduced-Dimension fMRI Shared Response Model. NIPS.
- Nastase et al. (2019). Keep it real: rethinking the primacy of experimental control in cognitive neuroscience. NeuroImage.

---

Last updated: 2026-02-17 (Tests 1D, 2A, 2B completed locally)
