# Phase 1: Preprocessing & Baseline Decoding

**Status**: ✅ Validated (2026-02-09)
**Pipeline**: C010 (2nd-level drift) + Procrustes alignment
**Performance**: RDM reliability 0.487, Noise ceiling 0.613, 79% utilization

## Quick Start

### Validated Pipeline (Use This)

```python
# 1. C010 preprocessing
python run_full_dataset_C010.py --subject 01 --roi V1

# 2. Procrustes alignment
python apply_procrustes_baseline.py --input results/validated/full_dataset_C010/

# Expected performance:
#   - RDM reliability: ~0.487
#   - Noise ceiling: ~0.613
#   - Ceiling utilization: ~79%
```

## Core Configuration

### C010 Preprocessing
**Key Settings:**
- **1st-level GLM**: FIR basis (8 delays, 0-12s), no drift
- **2nd-level GLM**: 8 HRF + 8 HRF derivative + 12 per-run drift (linear + constant)
- **NO confounds**: No motion/tissue/WM regression
- **NO high-pass**: Drift regressors handle slow trends

**Rationale:**
- 2nd-level drift essential for session-wide trends
- Confounds remove signal (RDM -60% with C010+P3)
- HPF redundant with drift regressors

### Procrustes Alignment
**Essential step:** 16.4× improvement over raw data

**How it works:**
- Orthogonal transformation (rotation + reflection, no scaling)
- Aligns runs 1-5 to run 0 reference
- Removes geometric variance between runs

**Why essential:**
- Geometric variance 16× larger than signal
- Transforms negative noise ceilings to positive
- 100% of subject-ROI pairs improve

## Capabilities

- **Procrustes Alignment**: Remove geometric variance between runs
- **RDM Analysis**: Representational dissimilarity matrices
- **Noise Ceiling**: Upper bound on achievable performance
- **Forward Encoding**: 6-channel color-selective model
- **Cross-Validation**: LORO (Leave-One-Run-Out)

## Key Scripts

### Main Pipeline (Currently Used)
- `roi_pipeline_selected_1202used.py`: ROI extraction and preprocessing
- `apply_procrustes_baseline.py`: Procrustes alignment (Phase 2)
- `visualize_roi_overlay.py`: ROI visualization
- `create_permuted_amplitudes.py`: Permutation analysis

### Validation Tools
- `run_full_dataset_C010.py`: Run C010 on full dataset
- `analyze_c010_procrustes_effects.py`: Procrustes effect analysis
- `compute_noise_ceiling_analysis.py`: Noise ceiling computation
- `test_procrustes_improvement.py`: Validation testing
- `test_whitening_before_procrustes.py`: Four-way comparison

See EXECUTION_GUIDE.md for detailed usage.

## Performance Metrics

### Raw vs Procrustes

| Metric | Raw C010 | C010 + Procrustes | Improvement |
|--------|----------|-------------------|-------------|
| RDM Reliability | 0.028 | **0.487** | +1644% |
| Noise Ceiling | -0.038 | **0.613** | Negative→Good |
| Ceiling Utilization | N/A | **79%** | Excellent |
| Positive Pairs | 52.5% | **100%** | All positive |

### Comparison with Original Baseline32
- Original: 41% ceiling utilization
- Current: **79% ceiling utilization**
- **Improvement: +37.7 percentage points (nearly doubled)**

## Key Findings (Summary)

1. **C010 wins**: 2nd-level drift only, no confounds (RDM 0.039 vs -0.021 with confounds)
2. **Procrustes essential**: 16.4× improvement, 100% positive effect
3. **Whitening harmful**: -47% to -92% degradation regardless of order
4. **HPF redundant**: Zero benefit over drift regressors
5. **79% ceiling utilization**: Near-optimal performance

## Directory Structure

```
phase1_preprocess_decoding/
├── Main Scripts (currently used)
├── Validation Scripts (from preprocess_Check)
├── utils/validation/ (validation utilities)
├── scripts/past/ (archived old code)
├── results/
│   ├── validated/ (C010 + Procrustes - USE THIS)
│   └── past/ (historical experiments - reference only)
└── Detailed docs: preprocess_tests.md, updated_noise_procrustes.md
```

## Detailed Documentation

**For comprehensive details, see:**
- **preprocess_tests.md**: HPF/drift systematic tests, three-way confound comparison
- **updated_noise_procrustes.md**: Procrustes validation (16.4×), whitening tests
- **NOISE_CEILING_C010_PROCRUSTES.md**: Noise ceiling analysis
- **compare_with_previous.md**: Historical context, Baseline32 comparison

## What NOT to Do

1. ❌ **Use C010+P3**: Confounds degrade signal (-60%)
2. ❌ **Apply whitening**: Harmful regardless of order (-47% to -92%)
3. ❌ **Skip Procrustes**: Essential, 16× improvement
4. ❌ **Use high-pass filtering**: Zero benefit over drift regressors

## GLM Design

### FIR Basis Functions
- **N_DELAYS**: 8 time points (0-12s post-stimulus at TR=1.5s)
- **Voxel Selection**: Top 50% by FIR R²
- **HRF Model**: 2nd-level GLM with HRF + temporal derivative

### Forward Encoding Model
```python
N_CHANNELS = 6                  # 6 half-wave rectified basis functions
CHANNEL_CENTERS = [0°, 60°, 120°, 180°, 240°, 300°]  # Equally spaced in hue space
CHANNEL_WIDTH = 60°             # FWHM of Gaussian basis functions
CROSS_VALIDATION = 'LORO'       # Leave-One-Run-Out
```

## Output Structure

```
derivatives/BH2009_{dataset}/{timestamp}/
└── sm{smooth}_hpYe_mo{motion}_cc{compcor}_dr{drift}_st{stand}_sub-{ID}_{roi}_{extra}/
    ├── amplitudes.npy           # Channel weights (n_runs, n_colors, n_channels)
    ├── amplitudes_z.npy         # Z-scored channel weights
    ├── classification_results.txt
    ├── reconstruction_error.txt
    ├── channel_weights.npy      # W matrix (n_channels, n_voxels)
    ├── roi_mask.nii.gz
    └── figures/
        ├── channel_tuning.png
        └── reconstruction_wheel.png
```

## References

- **Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- **Wang, L., et al. (2015).** Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
