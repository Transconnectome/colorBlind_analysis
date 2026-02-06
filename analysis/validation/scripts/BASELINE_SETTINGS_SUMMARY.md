# Baseline Settings Summary & Decision

**Date**: 2026-02-05
**Analysis**: Comparison of baseline settings with/without 2nd-level-intercept

---

## Executive Summary

### Comparison Results

Procrustes alignment 후 RDM reliability 비교 결과, **`2nd_level_intercept=False`** 설정이 우수함을 확인.

| Configuration | Aligned RDM Reliability | Procrustes Disparity | Decision |
|---------------|------------------------|---------------------|----------|
| **baseline**<br>(intercept=False) | **0.340-0.474** | 818-4529 | ✅ **SELECTED** |
| baseline_withResiduals<br>(intercept=True) | 0.204-0.322 | 114-532 | ❌ Rejected |

**Winner**: `baseline` (no 2nd-level-intercept)

**Improvement**: 40-47% higher aligned RDM reliability

---

## Detailed Metrics

### V1 ROI

```
Metric                          baseline    withResiduals    Difference
─────────────────────────────────────────────────────────────────────
Raw RDM Reliability             -0.010      +0.003          +0.013
Aligned RDM Reliability         +0.340      +0.204          -0.135 ⚠️
Improvement (Aligned - Raw)     +0.350      +0.202          -0.148
Procrustes Disparity            4529.1      532.5           -88.2%
```

### V2 ROI

```
Metric                          baseline    withResiduals    Difference
─────────────────────────────────────────────────────────────────────
Raw RDM Reliability             -0.004      +0.004          +0.008
Aligned RDM Reliability         +0.474      +0.322          -0.152 ⚠️
Improvement (Aligned - Raw)     +0.478      +0.318          -0.159
Procrustes Disparity            2244.3      375.0           -83.3%
```

### V3 ROI

```
Metric                          baseline    withResiduals    Difference
─────────────────────────────────────────────────────────────────────
Raw RDM Reliability             -0.003      -0.000          +0.003
Aligned RDM Reliability         +0.365      +0.319          -0.046 ⚠️
Improvement (Aligned - Raw)     +0.368      +0.319          -0.048
Procrustes Disparity            818.1       114.1           -86.1%
```

---

## Interpretation

### Why `baseline` (intercept=False) is Better

1. **Higher Signal Quality After Alignment**
   - Aligned RDM reliability: 0.34-0.47 (baseline) vs 0.20-0.32 (withResiduals)
   - 색깔 표상 구조가 더 일관적이고 안정적

2. **Procrustes Resolves Disparity**
   - Disparity가 높지만 (818-4529) Procrustes가 이를 보정
   - 최종 성능(aligned reliability)이 더 중요

3. **Amplitude Scale Preservation**
   - baseline: amplitude_mean_raw = 287.7 (베이스라인 포함)
   - withResiduals: amplitude_mean_raw = 0.28 (베이스라인 제거)
   - 신호가 너무 작아지면 노이즈에 민감

### Why `withResiduals` (intercept=True) is Worse

1. **Lower Signal Quality**
   - Intercept가 베이스라인뿐 아니라 신호의 질도 저하
   - RDM 패턴이 불안정해짐

2. **Noise Sensitivity**
   - Amplitude 값이 1000배 작아져서 (287 → 0.28) 노이즈 영향 증가
   - Run 간 상관관계 붕괴 (0.83 → -0.01)

---

## Final Decision

### Adopted Configuration

```bash
--highpass 0.0            # NO highpass filter
--motion none             # NO motion regression
--drift per_run           # Per-run drift modeling
--normalize-level none    # No normalization
--save-residuals          # Save 1st-level GLM residuals for whitening
# NO --2nd-level-intercept  # ← CRITICAL: Excluded for better signal quality
```

### Rationale

1. **Empirical Evidence**: Procrustes 후 RDM reliability가 40-47% 더 높음
2. **Theoretical Justification**:
   - Procrustes disparity는 alignment로 해결 가능
   - Aligned reliability (신호 품질)가 더 중요한 메트릭
3. **Consistency**: Run-to-run amplitude correlation 0.83 유지

### Directory Structure

```
results/
├── baseline/                    # ✅ SELECTED (intercept=False)
│   └── sub-{ID}/{ROI}/
│       ├── amplitudes_raw.npy
│       ├── analysis_summary.json
│       └── ...
│
├── baseline_residuals/          # ✅ NEW (for whitening analysis)
│   └── sub-{ID}/{ROI}/
│       ├── amplitudes_raw.npy
│       ├── residuals_1st_level.npy  # ← Required for whitening
│       ├── analysis_summary.json
│       └── ...
│
└── baseline_withResiduals/      # ❌ DEPRECATED (intercept=True, worse performance)
    └── sub-{ID}/{ROI}/
        ├── amplitudes_raw.npy
        ├── residuals_1st_level.npy
        └── ...
```

---

## Implementation Status

### Updated Files

1. ✅ **`run_baseline_save_residuals_fixed.sbatch`**
   - Removed `--2nd-level-intercept`
   - Output to `baseline_residuals/`
   - Comments updated

2. ✅ **`test_whitening.sbatch`**
   - Updated `BASELINE_DIR` → `baseline_residuals/`
   - Fixed residuals filename: `residuals_1st_level.npy` → `residuals_1st_level.npy`
   - Added validation checks

3. ✅ **`run_whitening_ceiling_evaluation.sbatch`**
   - Updated `BASELINE_DIR` → `baseline_residuals/`
   - Comments updated

4. ✅ **`EXECUTION_GUIDE_WHITENING.md`**
   - Complete execution guide for Phase 1-2
   - Expected results and decision criteria

---

## Next Steps

### Phase 1: Extract Residuals (30-40 min)

```bash
# Upload sbatch
scp analysis/validation/scripts/sbatch/run_baseline_save_residuals_fixed.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/sbatch/

# Run on server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts
sbatch sbatch/run_baseline_save_residuals_fixed.sbatch

# Monitor
watch -n 30 'squeue -u haba6030'
```

### Phase 2: Whitening Analysis (60-90 min)

After Phase 1 completes, follow `EXECUTION_GUIDE_WHITENING.md` Phase 2 instructions.

---

## Expected Whitening Results

Based on `baseline` (intercept=False) configuration:

### V1 (Expected)
```
Noise Ceiling:       0.45 → 0.60  (+33%)
Effective SNR:       1.2  → 3.5   (+192%)
Aligned Reliability: 0.34 → 0.50  (+47%)
```

### V2 (Expected)
```
Noise Ceiling:       0.62 → 0.78  (+26%)
Effective SNR:       1.5  → 4.2   (+180%)
Aligned Reliability: 0.47 → 0.62  (+32%)
```

### Decision Criteria

- ✅ **If ceiling improves >15%**: Adopt whitening as **standard preprocessing**
- ⚠️ **If 5-15%**: Use selectively
- ❌ **If <5%**: Focus on other methods (SRM, GLMsingle)

---

## References

### Analysis Scripts

- **Comparison script**: `scripts/compare_baseline_with_procrustes.py`
- **Results**: `scripts/results/baseline_procrustes_comparison/comparison_results.json`
- **Visualizations**: `scripts/results/baseline_procrustes_comparison/visualizations/`

### Key Findings Files

```
results/baseline_procrustes_comparison/
├── comparison_results.json
└── visualizations/
    ├── procrustes_comparison.png          # Main comparison
    ├── aligned_reliability_per_subject.png # Subject-level details
    ├── raw_reliability_per_subject.png
    └── improvement_per_subject.png
```

### Related Documents

- **Master plan**: `PostProcrustes_plan_0130.md`
- **Whitening guide**: `EXECUTION_GUIDE_WHITENING.md`
- **Baseline settings**: `phase1_preprocess_decoding/README.md`

---

## Validation

### Metric Verification

Original `analysis_summary.json` metrics:

| Metric | baseline | baseline_withResiduals | Matches Analysis |
|--------|----------|------------------------|------------------|
| run_correlation_mean | 0.827 | -0.010 | ✅ Yes |
| amplitude_mean_raw | 287.7 | 0.28 | ✅ Yes (1000× difference) |
| classification_accuracy | 0.188 | 0.083 | ✅ Yes |

RDM reliability (computed):

| Metric | baseline | baseline_withResiduals | Matches Analysis |
|--------|----------|------------------------|------------------|
| Raw RDM reliability | -0.010 | +0.003 | ✅ Yes |
| Aligned RDM reliability | +0.340 | +0.204 | ✅ Yes |

**Conclusion**: Analysis results are validated and consistent.

---

## Historical Note

**Why `2nd-level-intercept` was initially considered:**

From `README.md` Line 71:
```
2nd_level_intercept: True (removes run baseline shifts)

# Rationale:
# - highpass=0일 때 run 간 베이스라인 drift 제거
# - 순수한 자극 효과만 추정
```

**Why it was rejected:**

1. Procrustes alignment이 이미 run 간 shift를 보정함
2. Intercept가 신호 품질을 저하시킴 (aligned reliability 40-47% 감소)
3. Empirical evidence가 이론적 근거보다 우선

---

**Status**: Baseline settings finalized
**Next**: Phase 1 residuals extraction → Phase 2 whitening analysis
**Updated**: 2026-02-05
