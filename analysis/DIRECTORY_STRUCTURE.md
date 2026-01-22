# Analysis Directory Structure

**Updated: 2026-01-22**

## Overview

Standardized output structure for colorBlind analysis pipeline with shared resources and phase-specific results.

## Directory Structure

```
analysis/
├── roi_masks/{dataset}/              # SHARED: ROI masks (used by all phases)
│   ├── sub-01/
│   │   ├── V1_mask_*.nii.gz
│   │   ├── V2_mask_*.nii.gz
│   │   ├── V3_mask_*.nii.gz
│   │   ├── hV4_mask_*.nii.gz
│   │   ├── results_summary.csv
│   │   └── figures/
│   ├── sub-02/
│   └── ...
│
├── phase1_preprocess_decoding/{dataset}/
│   ├── results/
│   │   └── baseline_decoding/        # FIR reconstruction & forward encoding
│   │       ├── {timestamp}/
│   │       │   ├── sub-01/
│   │       │   │   ├── V1/
│   │       │   │   │   ├── amplitudes_z.npy
│   │       │   │   │   ├── classification_results.txt
│   │       │   │   │   ├── reconstruction_results.txt
│   │       │   │   │   └── figures/
│   │       │   │   ├── V2/
│   │       │   │   ├── V3/
│   │       │   │   └── hV4/
│   │       │   ├── sub-02/
│   │       │   └── ...
│   └── logs/
│       ├── roi_pipeline_{jobid}.out
│       ├── baseline_decoding_{jobid}.out
│       └── ...
│
├── phase2_procrustes_cvd_hc/{dataset}/
│   ├── results/
│   │   ├── alignment_quality_metrics.txt
│   │   ├── hc_common_decoder_{ROI}.npz
│   │   ├── cvd_procrustes_results_sub-{08,09,10}_{ROI}.npz
│   │   └── figures/
│   └── logs/
│
├── phase3_procrustes_filter/{dataset}/
│   ├── results/
│   │   ├── patterns/
│   │   ├── models/
│   │   └── training_curves/
│   └── logs/
│
├── prep_trials/{dataset}/
│   ├── results/
│   │   ├── dice_scores.csv
│   │   ├── registration_comparison.csv
│   │   └── diagnostic_figures/
│   └── logs/
│
└── utils/
    └── output_paths.py               # Shared path management utility
```

## Design Principles

### 1. Shared Resources vs Phase-Specific Results

**Shared Resources** (`analysis/roi_masks/{dataset}/`):
- Used by multiple phases
- Dataset-specific but phase-independent
- Examples: ROI masks, atlases, common preprocessed data

**Phase-Specific Results** (`analysis/{phase}/{dataset}/results/`):
- Unique to each phase
- Contains analysis outputs specific to that phase
- Examples: baseline decoding amplitudes, Procrustes transformations

### 2. Dataset Organization

Each dataset (e.g., `method3_header_mi`, `original_v3`) has its own directory to:
- Isolate different preprocessing methods
- Allow easy comparison across datasets
- Prevent cross-contamination of results

### 3. Results vs Logs Separation

**results/** - Analysis outputs
- Permanent analysis results
- Figures, metrics, trained models
- Version controlled outputs

**logs/** - Execution logs
- SLURM job outputs (.out, .err)
- Runtime information
- Debug information
- Not version controlled

## Path Usage Examples

### Python Scripts

```python
from utils.output_paths import get_roi_paths, get_baseline_paths

# Get ROI mask paths (shared resource)
roi_paths = get_roi_paths(
    dataset='method3_header_mi',
    subject_id='01'
)
# Returns: analysis/roi_masks/method3_header_mi/sub-01/

# Get baseline decoding paths (phase-specific)
baseline_paths = get_baseline_paths(
    dataset='method3_header_mi',
    subject_id='01',
    roi='V1',
    timestamp='20260122_120000'
)
# Returns: analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/20260122_120000/sub-01/V1/
```

### SBATCH Scripts

```bash
#SBATCH --output=analysis/phase1_preprocess_decoding/method3_header_mi/logs/job_%j.out
#SBATCH --error=analysis/phase1_preprocess_decoding/method3_header_mi/logs/job_%j.err

DATASET="method3_header_mi"
PHASE="phase1_preprocess_decoding"

# Shared ROI masks
ROI_DIR="analysis/roi_masks/${DATASET}"

# Phase-specific results
RESULTS_DIR="analysis/${PHASE}/${DATASET}/results"
LOGS_DIR="analysis/${PHASE}/${DATASET}/logs"
```

## Migration from Old Structure

**Old structure:**
```
derivatives/V3_Comprehensive/
├── ROI_mask/sub-{ID}/roi_pipeline/
└── BH2009_{dataset}/{timestamp}/sub-{ID}/{ROI}/
```

**New structure:**
```
analysis/
├── roi_masks/{dataset}/sub-{ID}/
└── phase1_preprocess_decoding/{dataset}/results/baseline_decoding/{timestamp}/sub-{ID}/{ROI}/
```

**Migration advantages:**
1. ✅ Phase-agnostic shared resources
2. ✅ Clear separation of concerns
3. ✅ Better scalability for future phases
4. ✅ Consistent naming conventions
5. ✅ Easier to understand and navigate

## Server Deployment

When deploying to server, upload only the `analysis/` folder:

```bash
# Upload scripts and utilities
scp -r analysis/phase1_preprocess_decoding/*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/
scp -r analysis/utils/*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/utils/

# Upload sbatch files
scp analysis/comprehensive/*.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/comprehensive/

# Results and logs directories will be created automatically
```

---

**See also:**
- `utils/output_paths.py` - Path management utilities
- `README.md` - Pipeline overview
- `CLAUDE.md` - Development guide
