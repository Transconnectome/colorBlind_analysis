# Validated Preprocessing Results (C010 + Procrustes)

**Date**: 2026-02-09
**Pipeline**: C010 (2nd-level drift only) + Procrustes alignment
**Performance**:
- RDM Reliability: 0.487 ± 0.253
- Noise Ceiling: 0.613 ± 0.248
- Ceiling Utilization: **79%** (excellent)

## Directory Contents

### full_dataset_C010/
Complete validated preprocessing results for 40 subject-ROI pairs:
- 10 subjects × 4 ROIs (V1, V2, V3, V4)
- Raw amplitudes from C010 preprocessing
- Use with apply_procrustes_baseline.py for optimal performance

### analysis/
Summary statistics from validation experiments:
- Four-way comparison (Raw, Procrustes, Whitening orders)
- Procrustes improvement analysis
- Noise ceiling analysis
- CSV summaries for all conditions

### visualization/
Complete figure set documenting validation:
- RDM reliability comparisons
- Procrustes effects by ROI and group
- Quality metrics distributions
- Color space embeddings

### HRF_visualization/
HRF-specific validation for V2 ROI

## Usage

```python
# Load validated C010 data
amplitudes = load_amplitudes(subject, roi, from='full_dataset_C010/')

# Apply Procrustes (essential step)
python apply_procrustes_baseline.py --input full_dataset_C010/

# Expected performance:
#   RDM reliability: ~0.487
#   Noise ceiling: ~0.613
#   Ceiling utilization: ~79%
```

See parent README.md for complete pipeline documentation.
