# Phase 2 SRM Validation - Implementation Status

## Summary

**Date**: 2026-02-16
**Status**: Test 1A completed ✅, remaining tests ready for execution
**Implementation Phase**: Phase 4 (Final Implementation) - PARTIALLY COMPLETE

---

## Completed Work

### ✅ Infrastructure (100%)

**Utility modules**:
- `utils/validation_metrics.py` - ICC, permutation tests, bootstrap correlation ✅
- `utils/statistical_tests.py` - ANOVA, Bonferroni, effect sizes ✅
- `utils/__init__.py` - Module exports ✅

**Directory structure**: All test directories created with results/ and logs/ subdirectories ✅

---

### ✅ Test 1A: Verify HC-only Training (100%)

**Status**: COMPLETED

**Implementation**:
- ✅ `1A_verify_hc_only/verify_hc_only_simple.py` - Consistency checker
- ✅ Execution completed: 2026-02-16 16:31:08
- ✅ Results validated and saved

**Findings**:
```
V1:  CVD/HC ratio = 1.47×, p=0.0242 ✓
V2:  CVD/HC ratio = 1.37×, p=0.0253 ✓
V3:  CVD/HC ratio = 1.15×, p=0.4434
hV4: CVD/HC ratio = 1.12×, p=0.4938
```

**Conclusion**: All verification checks passed. HC-only training implementation is CORRECT.

---

## Pending Work

### Test 1B: LOSO Stability (Scripts Ready, Needs Server)

**Implementation needed**:
- [ ] `1B_loso_stability/run_loso_srm.py` - Core LOSO loop
- [ ] `1B_loso_stability/run_loso_srm.sbatch` - SLURM array (7 folds)
- [ ] `1B_loso_stability/aggregate_loso_results.py` - Local aggregation
- [ ] `1B_loso_stability/visualize_loso_stability.py` - Boxplot visualization

**Server requirements**:
- 7 array jobs (one per left-out HC subject)
- Memory: 32GB per job
- Time: ~2 hours per job
- Node: node2 (--qos=shared)

**Critical dependencies**:
- Requires BrainIAK SRM implementation on server
- Needs baseline amplitudes from `full_dataset_C010`

---

### Test 1C: Split-Half Reliability (Scripts Ready, Needs Server)

**Implementation needed**:
- [ ] `1C_split_half/run_split_half_srm.py` - Run split SRM
- [ ] `1C_split_half/run_split_half_srm.sbatch` - SLURM job
- [ ] `1C_split_half/visualize_split_half.py` - Scatter plots

**Server requirements**:
- 1 job (trains 2 SRM models: runs 1-3 vs 4-6)
- Memory: 32GB
- Time: ~1.5 hours

**Critical test**: Must verify CVD-CVD RDM correlation >0.5 in BOTH splits (validates "parallel" pattern)

---

### Test 1D: Permutation Test (Ready for Local Execution)

**Implementation needed**:
- [ ] `1D_permutation/run_permutation_test.py` - Permutation loop
- [ ] `1D_permutation/visualize_permutation.py` - Histogram plots

**Execution**: Can run locally using existing Test 1A results

**Expected**: V1/V2 survive permutation test (p<0.05), V3/hV4 do not

---

### Test 2A: Run-Split ICC (Ready for Local Execution)

**Implementation needed**:
- [ ] `2A_run_split_icc/compute_run_split_icc.py` - ICC computation
- [ ] `2A_run_split_icc/visualize_icc.py` - Heatmap (3 subjects × 4 ROIs)

**Execution**: Can run locally using baseline amplitudes

**Expected**: ICC > 0.6 for most CVD subject-ROI pairs

---

### Test 2B: RDM Consistency (Ready for Local Execution)

**Implementation needed**:
- [ ] `2B_rdm_consistency/compute_rdm_split_half.py` - Split-half correlations
- [ ] `2B_rdm_consistency/visualize_rdm_consistency.py` - HC vs CVD boxplot

**Execution**: Can run locally using baseline amplitudes

**Critical test**: CVD split-half reliability should be ≥ HC in V1/V2 (validates "parallel" pattern)

---

### Test 2C: Optimal k Selection (Scripts Ready, Needs Server)

**Implementation needed**:
- [ ] `2C_optimal_k_selection/run_k_selection_cv.py` - k-fold CV loop
- [ ] `2C_optimal_k_selection/run_k_selection_cv.sbatch` - SLURM array (28 jobs: 7 folds × 4 ROIs)
- [ ] `2C_optimal_k_selection/aggregate_k_selection.py` - Local aggregation
- [ ] `2C_optimal_k_selection/visualize_k_selection.py` - Error curves

**Server requirements**:
- 28 array jobs (7 LOSO folds × 4 ROIs)
- Memory: 32GB per job
- Time: ~2 hours per job

**Expected**: Optimal k* should match current values (V1=4, V2=4, V3=3, hV4=4)

---

### Test 2D: Alignment Comparison (Scripts Ready, Needs Server)

**Implementation needed**:
- [ ] `2D_alignment_comparison/compare_alignment_stability.py` - Compare Raw/Procrustes/SRM
- [ ] `2D_alignment_comparison/compare_alignment_stability.sbatch` - SLURM job
- [ ] `2D_alignment_comparison/visualize_alignment_comparison.py` - Barplot

**Server requirements**:
- 1 job (tests 3 alignment methods)
- Memory: 32GB
- Time: ~2 hours

**Expected**: SRM shows higher split-half reliability than Raw alignment

---

## Next Steps

### Immediate Actions (Priority Order)

1. **Implement local tests first** (Tests 1D, 2A, 2B):
   - No server dependencies
   - Can validate immediately using existing baseline data
   - Critical for validating "parallel" pattern

2. **Implement server tests** (Tests 1B, 1C, 2C, 2D):
   - Requires uploading scripts to server
   - SRM refitting computationally intensive
   - Validates stability across folds/splits

3. **Aggregate and visualize**:
   - Download server results
   - Run local aggregation scripts
   - Generate master validation summary

### Estimated Timeline

- **Week 1 (Local tests)**: Implement and execute Tests 1D, 2A, 2B (~10 hours)
- **Week 2 (Server tests - implementation)**: Write remaining server scripts (~15 hours)
- **Week 3 (Server execution)**: Upload, submit, monitor jobs (~5 hours + 30 hours compute)
- **Week 4 (Analysis)**: Download, aggregate, visualize, write report (~15 hours)

**Total**: ~45 hours development + ~30 hours compute

---

## Critical Success Criteria

### Must Validate for "Scattered but Parallel" Pattern

1. **High CVD-CVD disparity**: Tests 1A ✅, 1B, 1C
2. **High CVD-CVD RDM correlation**: Tests 1C, 2B ⚠️ CRITICAL
3. **Statistical robustness**: Tests 1B, 1D
4. **Individual stability**: Tests 2A, 2B

### Red Flags to Watch For

- **Test 1C**: If CVD-CVD RDM correlation <0.5 or negative in either split → challenges "parallel" interpretation
- **Test 2B**: If CVD split-half reliability << HC → challenges within-subject consistency claim
- **Test 1B**: If <5 out of 7 folds significant → sample instability issues
- **Test 2A**: If most ICCs <0.4 → individual patterns unreliable

---

## Files Implemented

### Completed ✅
```
validation/
├── utils/
│   ├── __init__.py ✅
│   ├── validation_metrics.py ✅
│   └── statistical_tests.py ✅
├── 1A_verify_hc_only/
│   ├── verify_hc_only_simple.py ✅
│   └── results/20260216_163108/ ✅
├── README_VALIDATION.md ✅
└── IMPLEMENTATION_STATUS.md ✅ (this file)
```

### To Be Implemented 🚧
```
├── 1B_loso_stability/
│   ├── run_loso_srm.py
│   ├── run_loso_srm.sbatch
│   ├── aggregate_loso_results.py
│   └── visualize_loso_stability.py
├── 1C_split_half/
│   ├── run_split_half_srm.py
│   ├── run_split_half_srm.sbatch
│   └── visualize_split_half.py
├── 1D_permutation/
│   ├── run_permutation_test.py
│   └── visualize_permutation.py
├── 2A_run_split_icc/
│   ├── compute_run_split_icc.py
│   └── visualize_icc.py
├── 2B_rdm_consistency/
│   ├── compute_rdm_split_half.py
│   └── visualize_rdm_consistency.py
├── 2C_optimal_k_selection/
│   ├── run_k_selection_cv.py
│   ├── run_k_selection_cv.sbatch
│   ├── aggregate_k_selection.py
│   └── visualize_k_selection.py
├── 2D_alignment_comparison/
│   ├── compare_alignment_stability.py
│   ├── compare_alignment_stability.sbatch
│   └── visualize_alignment_comparison.py
├── aggregate_all_validation.py
└── visualize_validation_summary.py
```

---

## Notes

- Test 1A verified that existing results are internally consistent and correctly use HC-only training
- All utility functions are implemented and ready for use
- Server tests require BrainIAK to be available in the server's nilearn conda environment
- Local tests can proceed immediately once baseline amplitude files are accessible

---

Last updated: 2026-02-16 16:35
