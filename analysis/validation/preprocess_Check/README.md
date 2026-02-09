# Preprocessing Validation: Complete Results

**Date**: 2026-02-09
**Status**: ✅ COMPLETE - All experiments finished, optimal pipeline validated

---

## Overview

This directory contains comprehensive preprocessing validation work to optimize the fMRI analysis pipeline for color representation analysis. Multiple systematic experiments were conducted to identify the best preprocessing configuration and post-processing steps.

**Final Validated Pipeline**:
```
Raw BOLD → C010 (2nd-level drift only) → Procrustes alignment → RDM analysis
```

**Performance**: RDM reliability = 0.487, Noise ceiling = 0.613, Ceiling utilization = **79%**

---

## What Was Tested

### 1. HPF/Drift Systematic Test (Preliminary)
**Goal**: Test 2×2×2 factorial design of high-pass filtering and drift regressors

**Configurations**:
- C000-C111: 8 configurations testing HPF (bit 1), 1st-level drift (bit 2), 2nd-level drift (bit 3)
- Example: C010 = 2nd-level drift only, C111 = all three

**Result**: **C010 (2nd-level drift only)** wins
- 2nd-level drift essential for session-wide trends
- 1st-level drift insufficient
- HPF redundant with 2nd-level drift regressors

### 2. Three-Way Confound Comparison (Full Dataset)
**Goal**: Test confound regression effects on C010 baseline

**Configurations**:
- C010: Drift only (12 regressors)
- C010+P3: + Motion/Tissue (12) + WM aCompCor (5) = 29 regressors
- C011+P3: + High-pass filter

**Result**: **C010 (drift only)** wins
- RDM reliability: 0.039 (C010) vs -0.021 (C010+P3)
- Confounds remove signal, not just noise
- HPF has zero effect (identical to C010+P3)

### 3. Procrustes Alignment Validation
**Goal**: Measure improvement from orthogonal alignment to common reference

**Result**: **Essential, 16.4× improvement**
- RDM reliability: 0.028 (raw) → 0.487 (aligned)
- Noise ceiling: -0.038 → 0.613
- All 40 pairs become positive (21/40 → 40/40)
- Geometric variance 16× larger than signal, removed by Procrustes

### 4. Whitening Tests (Two Orders)
**Goal**: Test whitening before and after Procrustes alignment

**Configurations**:
- Raw → Whitening → Procrustes (literature-recommended)
- Raw → Procrustes → Whitening (alternative)

**Result**: **Both orders FAIL**
- Before Procrustes: -92% vs Procrustes-only
- After Procrustes: -47% vs Procrustes-only
- Covariance estimated from amplitudes (signal + noise), not residuals (noise only)
- Whitening removes signal correlations instead of noise

---

## Key Findings

### 1. Confounds Remove Signal
- C010+P3 degrades RDM reliability 60% (0.039 → -0.021)
- Motion/tissue/WM confounds correlated with task
- 19 confound regressors too aggressive for weak color signal

### 2. HPF is Redundant
- C010+P3 and C011+P3 identical (0.000 difference)
- 2nd-level per-run drift regressors already capture slow trends
- No additional benefit from HPF on top of drift regressors

### 3. Procrustes is Essential
- 16.4× improvement (largest single effect)
- Transforms negative to positive noise ceilings
- Removes between-run geometric variance (rotation, reflection)
- Essential for extracting color signal

### 4. Whitening is Harmful
- Degrades performance regardless of order
- Estimates total covariance (signal + noise), not noise-only
- Removes spatial structure of color representations
- Not worth the complexity and risk

### 5. Already Near Optimal
- Ceiling utilization: 79% (excellent)
- Compared to original Baseline32: 41% (nearly doubled!)
- Little room for improvement without major changes

---

## Final Validated Pipeline

### Configuration

**Preprocessing (C010)**:
```python
# 1st-level GLM (per run):
#   - Basis: FIR (16 time points, 0-32s)
#   - Drift: None
#   - Output: Beta maps per color per timepoint

# 2nd-level GLM (across runs):
#   - 8 HRF regressors (colors)
#   - 8 HRF derivative regressors
#   - 12 per-run drift regressors:
#       * 6 linear (one per run, centered)
#       * 6 constant (one per run, DC offset)
#   - NO motion/tissue confounds
#   - NO WM aCompCor
#   - NO high-pass filtering
```

**Post-processing**:
```python
# Procrustes alignment:
#   - Method: Orthogonal Procrustes (scipy)
#   - Reference: Run 0
#   - Transformation: Rotation + reflection only (no scaling)
#   - Per-run: Align runs 1-5 to run 0 independently
```

**NO Whitening**: Harmful regardless of order

### Performance Metrics

| Metric | Raw C010 | C010 + Procrustes | Improvement |
|--------|----------|-------------------|-------------|
| **RDM Reliability** | 0.028 | **0.487** | **+1644%** |
| **Noise Ceiling** | -0.038 | **0.613** | Negative → Good |
| **Ceiling Utilization** | N/A | **79%** | Excellent |
| **Method Difference** | 0.262 | **0.097** | **-63%** |
| **Positive Pairs** | 52.5% | **100%** | All positive |

**Comparison with Original Baseline32**:
- Original: RDM/Ceiling = 0.154-0.256 / 0.434-0.609 = 35.5-44.4% (41.3% average)
- Current: RDM/Ceiling = 0.487 / 0.613 = **79.4%**
- **Improvement: +37.7 percentage points (nearly doubled ceiling utilization)**

### Quality Distribution (Post-Procrustes)

- **Excellent** (RDM rel > 0.70): 35% of pairs (14/40)
- **Good** (0.50-0.70): 25% of pairs (10/40)
- **Moderate** (0.30-0.50): 27.5% of pairs (11/40)
- **Low** (< 0.30): 12.5% of pairs (5/40)

**60% good-excellent** quality ✅

---

## Documentation

### Comprehensive Documents (Read These)

**1. [`preprocess_tests.md`](./preprocess_tests.md)**
- HPF/drift systematic test details (C000~C111)
- Three-way confound comparison (C010 vs C010+P3 vs C011+P3)
- Complete configuration details, results, and analysis
- Why C010 wins, why confounds hurt, why HPF has no effect

**2. [`updated_noise_procrustes.md`](./updated_noise_procrustes.md)**
- Procrustes alignment validation (16.4× improvement)
- Whitening after Procrustes test (47% degradation)
- Whitening before Procrustes test (92% degradation)
- Why whitening fails, why Procrustes is essential
- Four-way comparison (Raw, R→P, R→W→P, R→P→W)

### Quick Start: Using the Validated Pipeline

**For new analyses**, use C010 + Procrustes:

```python
import numpy as np
from scipy.linalg import orthogonal_procrustes

# 1. Load C010 amplitudes (from preprocessing)
amplitudes_raw = load_amplitudes(subject, roi)  # (n_runs, n_colors, n_voxels)

# 2. Apply Procrustes alignment
reference = amplitudes_raw[0]  # Run 0 as reference
aligned = []

for run_idx in range(len(amplitudes_raw)):
    Q, scale = orthogonal_procrustes(amplitudes_raw[run_idx].T, reference.T)
    aligned_run = amplitudes_raw[run_idx].T @ Q
    aligned.append(aligned_run.T)

amplitudes_aligned = np.array(aligned)

# 3. Compute RDMs and analyze
# Expected performance:
#   - RDM reliability: ~0.487
#   - Noise ceiling: ~0.613
#   - Ceiling utilization: ~79%
```

**Do NOT**:
- ❌ Use C010+P3 (confounds degrade signal)
- ❌ Use C011+P3 (HPF has no effect)
- ❌ Apply whitening (harmful regardless of order)
- ❌ Skip Procrustes (essential, 16× improvement)

---

## File Organization

### Essential Files (Keep)

**Documentation**:
```
README.md                           # This file (overview)
preprocess_tests.md                 # Preprocessing configurations (comprehensive)
updated_noise_procrustes.md        # Procrustes and whitening (comprehensive)
```

**Analysis Scripts**:
```
run_full_dataset_C010.py           # C010 full dataset analysis
test_procrustes_improvement.py     # Procrustes validation
test_whitening_before_procrustes.py  # Four-way comparison
test_whitening_on_procrustes.py    # Whitening after Procrustes
```

**Batch Scripts**:
```
run_C010_with_residuals.sbatch     # SLURM job for C010
run_four_way_comparison.sbatch     # SLURM job for four-way test
```

**Results**:
```
four_way_comparison_summary.json
four_way_comparison_detailed.json
procrustes_improvement_summary.json
procrustes_improvement_detailed.json
whitening_improvement_summary.json
whitening_improvement_detailed.json
```

**Visualizations**:
```
visualization/
  ├── procrustes_improvement_visualization.png
  ├── whitening_effect_visualization.png
  ├── four_way_comparison.png
  └── three_way_comparison.png
```

### Data Directories (In .gitignore)

**Raw Data** (subject-level, not version controlled):
```
full_dataset_C010/          # C010 amplitudes (40 pairs)
full_dataset_P3/            # C010+P3 amplitudes
full_dataset_P3_C011/       # C011+P3 amplitudes
phase2_results/             # Phase 2 confound tests
*_results/                  # Other result directories
```

These directories contain subject data and are excluded from git for ethical/privacy reasons.

---

## Next Steps

### Immediate: Use Validated Pipeline

1. ✅ **Use C010 preprocessing** for all new analyses
2. ✅ **Apply Procrustes alignment** before RDM computation
3. ✅ **Expect performance**: RDM rel ≈ 0.487, NC ≈ 0.613

### Downstream Analyses (Ready to Proceed)

1. **CVD vs HC comparison**: Use Procrustes-aligned C010 data
2. **SRM (Shared Response Model)**: Between-subject alignment
3. **Geometric analysis**: RDM structure, MDS, clustering

### Not Recommended (Tested and Failed)

1. ❌ **Whitening**: Degrades performance 47-92%
2. ❌ **Confound regression**: Removes signal, 60% degradation
3. ❌ **High-pass filtering**: Zero benefit over drift regressors

### Optional Long-Term (Low Priority)

**Only if major pipeline overhaul is justified**:

1. **GLMsingle**: Voxel-wise HRF estimation
   - Expected: +0.20-0.30 improvement
   - Cost: High complexity, long compute time
   - Priority: Low (current performance already excellent)

2. **Proper whitening** (requires residuals):
   - Estimate covariance from GLM residuals (noise-only)
   - Whiten raw amplitudes → Procrustes
   - Expected: +0.06-0.11 improvement (marginal)
   - Cost: Pipeline overhaul, uncertain benefit
   - Priority: Very low (79% utilization already excellent)

3. **More data**: Additional runs or subjects
   - Expected: Modest improvement in noise ceiling
   - Cost: New data collection
   - Priority: Depends on scientific goals

---

## Summary

**Main Achievement**: Identified optimal preprocessing pipeline that nearly doubles ceiling utilization (41% → 79%) compared to original Baseline32 pipeline.

**Key Innovation**: Adding 2nd-level drift regressors (C010) removes session-wide temporal trends that were limiting the original pipeline.

**Critical Step**: Procrustes alignment removes geometric variance (16× larger than signal), revealing color signal structure.

**Failed Approaches**: Confound regression and whitening both degrade performance by removing task-related signal.

**Current Performance**: 79% ceiling utilization indicates near-optimal extraction of color signal from fMRI data. Further improvements would require fundamental changes (new models, more data) rather than preprocessing tweaks.

---

## Key Insight

> "The optimal preprocessing pipeline is surprisingly simple: 2nd-level drift regressors (C010) + Procrustes alignment. This achieves 79% noise ceiling utilization—nearly double the 41% of the original pipeline. More aggressive approaches (confounds, whitening) degrade performance by removing signal along with noise. When signal is weak, simplicity and careful alignment matter more than aggressive denoising."

---

**Status**: ✅ COMPLETE - All experiments finished, documentation consolidated, pipeline validated

**Contact**: See `CLAUDE.md` for project information and analysis pipeline documentation
