# Comparative Analysis Framework

**Version**: 1.0
**Date**: 2025-01-20
**Purpose**: Dataset/Preprocessing comparison methodology for fMRI decoding analysis

---

## Table of Contents

1. [Overview](#overview)
2. [Framework Architecture](#framework-architecture)
3. [Dataset Comparison Methodology](#dataset-comparison-methodology)
4. [Implementation Guide](#implementation-guide)
5. [Analysis Pipeline](#analysis-pipeline)
6. [Extending the Framework](#extending-the-framework)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

This framework provides a systematic approach to compare different:
- **Datasets** (e.g., original vs deoblique preprocessing)
- **Feature selection methods** (e.g., probabilistic vs non-probabilistic ROI)
- **Preprocessing configurations** (e.g., smoothing, standardization)
- **Analysis parameters** (e.g., PCA components, voxel selection criteria)

### Key Features

- ✅ **Modular design**: Easy to add new datasets/configs
- ✅ **Reproducible**: All parameters explicitly defined
- ✅ **Scalable**: SLURM array jobs for parallel processing
- ✅ **Comprehensive**: Multiple performance metrics
- ✅ **Automated**: One-click compilation and visualization

### Current Application

Comparing feature selection methods:
- **Origin dataset** with `roi_pipeline_origin_Noprob` (non-probabilistic ROI)
- **Deoblique_v2 dataset** with `roi_pipeline_deob_Noprob` (non-probabilistic ROI)
- **Baseline configs**: Config 32 (no smooth, no standardize) vs Config 81 (6mm smooth, standardize)

---

## Framework Architecture

### Directory Structure

```
project/
├── fir_reconstruction_BH2009_system_clean.py   # Core analysis script
├── run_all_subjects_baseline{32,81}_{dataset}.sbatch  # SLURM batch files
├── analyze_baseline_results.py                 # Result compilation
├── visualize_baseline_results.py               # Visualization
├── run_baseline_analysis.sh                    # One-click pipeline
│
├── derivatives/
│   ├── BH2009_{dataset}/
│   │   └── {timestamp}/
│   │       └── {config}_sub-{ID}_{ROI}_{roi_config}/
│   │           ├── analysis_summary.json        # All metrics
│   │           ├── classification_results.csv
│   │           ├── reconstruction_results.csv
│   │           └── figures_*.png
│   │
│   └── sub-{ID}/
│       └── {roi_pipeline_dir}/
│           └── {ROI}_mask_{config}.nii.gz
│
└── logs/
    └── feature_selection/
        └── baseline{32,81}_{dataset}_sub-{ARRAY_ID}_{JOB_ID}.{out,err}
```

### Component Overview

| Component | Purpose | Input | Output |
|-----------|---------|-------|--------|
| `fir_reconstruction_BH2009_system_clean.py` | Core analysis | fMRIPrep data, ROI masks | Performance metrics, figures |
| `run_all_subjects_baseline*.sbatch` | Parallel execution | Analysis parameters | SLURM job array |
| `analyze_baseline_results.py` | Result compilation | Individual results | Comprehensive CSV |
| `visualize_baseline_results.py` | Visualization | CSV results | Publication figures |
| `run_baseline_analysis.sh` | Full pipeline | Downloaded results | All outputs |

---

## Dataset Comparison Methodology

### Step 1: Define Comparison Dimensions

Identify what you want to compare:

```python
COMPARISON_DIMENSIONS = {
    'dataset': ['original', 'deoblique_v2'],           # fMRIPrep versions
    'roi_pipeline': ['origin_Noprob', 'deob_Noprob'], # ROI construction methods
    'config': [32, 81],                                # Preprocessing configs
    'smooth': [0, 6],                                  # Smoothing FWHM
    'standardize': ['No', 'Yes']                       # Z-score standardization
}
```

### Step 2: Configure Dataset Paths

In `fir_reconstruction_BH2009_system_clean.py`:

```python
DATASET_CONFIGS = {
    'original': {
        'fmriprep': '/path/to/fmriprep_out_new',
        'events': '/path/to/events',
        'description': 'Original fMRIPrep output'
    },
    'deoblique_v2': {
        'fmriprep': '/path/to/fmriprep_out_deoblique_v2',
        'events': '/path/to/events_deoblique',
        'description': 'Deoblique v2 with fieldmap'
    }
}
```

### Step 3: Create SLURM Batch Files

**Template structure:**

```bash
#!/bin/bash
#SBATCH --job-name={config}_{dataset}
#SBATCH --nodelist=node2
#SBATCH --array=0-9          # For 10 subjects (0-9)
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32GB
#SBATCH --time=3:00:00
#SBATCH --output=logs/feature_selection/{config}_{dataset}_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/{config}_{dataset}_sub-%a_%j.err

# Configuration
DATASET="{dataset}"
ROI_PIPELINE_DIR="{roi_pipeline_dir}"
SMOOTH={smooth}
STANDARDIZE="{--standardize if yes else empty}"
TIMESTAMP="{config}_{dataset}"

# Subject mapping
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Execute for all ROIs
for ROI in V1 V2 V3 hV4; do
    python fir_reconstruction_BH2009_system_clean.py \
        --subject $SUBJECT \
        --roi $ROI \
        --dataset $DATASET \
        --roi-pipeline-dir $ROI_PIPELINE_DIR \
        --timestamp $TIMESTAMP \
        --smooth $SMOOTH \
        $STANDARDIZE \
        [other params...]
done
```

### Step 4: Analysis Execution Matrix

Create batch files for all combinations:

| Batch File | Dataset | ROI Pipeline | Config | Smooth | Standardize |
|------------|---------|--------------|--------|--------|-------------|
| `run_all_subjects_baseline32_origin.sbatch` | original | roi_pipeline_origin_Noprob | 32 | 0 | No |
| `run_all_subjects_baseline32_deob.sbatch` | deoblique_v2 | roi_pipeline_deob_Noprob | 32 | 0 | No |
| `run_all_subjects_baseline81_origin.sbatch` | original | roi_pipeline_origin_Noprob | 81 | 6 | Yes |
| `run_all_subjects_baseline81_deob.sbatch` | deoblique_v2 | roi_pipeline_deob_Noprob | 81 | 6 | Yes |

---

## Implementation Guide

### A. Core Analysis Script Modifications

**Add ROI pipeline directory parameter:**

```python
# In parse_args()
parser.add_argument('--roi-pipeline-dir', type=str, default='roi_pipeline',
                    help='ROI pipeline directory name')

# In ROI loading section
roi_pipeline_dir = args.roi_pipeline_dir
roi_path = f"derivatives/sub-{SUBJECT_ID}/{roi_pipeline_dir}/{ROI_NAME}_mask_{roi_config}.nii.gz"
```

**Add dataset-specific configurations:**

```python
DATASET_CONFIGS = {
    'dataset_name': {
        'fmriprep': '/path/to/fmriprep',
        'events': '/path/to/events',
        'description': 'Dataset description'
    }
}
```

### B. SLURM Batch File Creation

**Template for new comparison:**

```bash
#!/bin/bash
#SBATCH --job-name={unique_name}
#SBATCH --nodelist=node2
#SBATCH --array=0-{N_SUBJECTS-1}
#SBATCH --output=logs/{category}/{name}_sub-%a_%j.out

# Fixed configuration
DATASET="{dataset_name}"
ROI_PIPELINE_DIR="{roi_pipeline_directory}"
TIMESTAMP="{unique_timestamp}"

# Analysis parameters
SMOOTH={smooth_value}
HIGHPASS="--highpass {value}"
MOTION="{motion_type}"
STANDARDIZE="{--standardize or empty}"
USE_PCA="--use-pca"
N_COMPONENTS={n_components}

# Subject array
SUBJECTS=(01 02 03 05 06 07 08 09 10)  # Excluding sub-04
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# ROI loop
for ROI in V1 V2 V3 hV4; do
    python fir_reconstruction_BH2009_system_clean.py \
        --subject $SUBJECT \
        --roi $ROI \
        --dataset $DATASET \
        --roi-pipeline-dir $ROI_PIPELINE_DIR \
        --timestamp $TIMESTAMP \
        --smooth $SMOOTH \
        $HIGHPASS \
        --motion $MOTION \
        $STANDARDIZE \
        $USE_PCA \
        --n-components $N_COMPONENTS
done
```

**Important notes:**
- ⚠️ **Subject array**: Currently excluding sub-04 (no V1 signal)
- ⚠️ Update `#SBATCH --array` to match subject count (0-8 for 9 subjects)
- ✓ Use unique `TIMESTAMP` to avoid overwriting results
- ✓ Use descriptive job names for monitoring

### C. Result Compilation Script

**Configure analysis metadata:**

```python
CONFIGS = {
    'comparison_name': {
        'dataset': 'dataset_identifier',
        'timestamp': 'unique_timestamp',
        'config_num': 32,  # or unique identifier
        'smooth': 0,
        'standardize': 'No',
        # Add any other distinguishing parameters
    }
}
```

**Update result directory pattern:**

```python
def find_result_dir(dataset, timestamp, subject, roi):
    pattern = f"{RESULTS_BASE}/BH2009_{dataset}/{timestamp}/sm*_sub-{subject}_{roi}_*"
    matches = glob.glob(pattern)
    return matches[0] if matches else None
```

---

## Analysis Pipeline

### Phase 1: Server Execution

```bash
# 1. Upload analysis files
scp fir_reconstruction_BH2009_system_clean.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_all_subjects_*.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 2. SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# 3. Submit all comparison jobs
for config in baseline32_origin baseline32_deob baseline81_origin baseline81_deob; do
    sbatch run_all_subjects_${config}.sbatch
done

# 4. Monitor progress
watch -n 10 'squeue -u haba6030'

# 5. Check logs for errors
tail -f logs/feature_selection/baseline32_origin_sub-0_*.out
```

### Phase 2: Result Download

```bash
# Download all results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_* ./derivatives/

# Or download specific comparisons
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_original/baseline32_origin ./derivatives/BH2009_original/
```

### Phase 3: Local Analysis

```bash
# Activate environment
conda activate nilearn

# Run full pipeline
./run_baseline_analysis.sh

# Or step-by-step
python analyze_baseline_results.py      # Generate CSV
python visualize_baseline_results.py    # Create figures
```

### Phase 4: Result Interpretation

**Automated outputs:**
1. `baseline_results_summary.csv`: Full results table
2. `baseline_summary_stats.csv`: Statistical summary
3. Visualization figures (4 types)
4. Console output with comparison tables

**Manual inspection:**
```python
import pandas as pd

# Load results
df = pd.read_csv('baseline_results_summary.csv')
df_valid = df[df['summary_found'] == True]

# Quick comparison
for roi in ['V1', 'V2', 'V3', 'hV4']:
    print(f"\n{roi}:")
    roi_data = df_valid[df_valid['roi'] == roi]
    print(roi_data.groupby('config_name')['classification_accuracy'].mean())
```

---

## Extending the Framework

### Adding New Dataset

**1. Update Python script:**

```python
# In fir_reconstruction_BH2009_system_clean.py
DATASET_CONFIGS = {
    # ... existing configs ...
    'new_dataset': {
        'fmriprep': '/path/to/new/fmriprep',
        'events': '/path/to/new/events',
        'description': 'New dataset description'
    }
}
```

**2. Create SLURM batch file:**

```bash
# run_all_subjects_baseline32_newdataset.sbatch
DATASET="new_dataset"
ROI_PIPELINE_DIR="roi_pipeline_newdataset"
TIMESTAMP="baseline32_newdataset"
# ... rest of config ...
```

**3. Update compilation script:**

```python
# In analyze_baseline_results.py
CONFIGS = {
    # ... existing configs ...
    'baseline32_newdataset': {
        'dataset': 'new_dataset',
        'timestamp': 'baseline32_newdataset',
        'config_num': 32,
        'smooth': 0,
        'standardize': 'No'
    }
}
```

### Adding New Preprocessing Config

**Example: Add Config 144 (8mm smooth, CompCor, standardize)**

**1. Create batch file:**

```bash
# run_all_subjects_baseline144_deob.sbatch
SMOOTH=8
HIGHPASS="--highpass 0.01"
MOTION="cosine"
COMPCOR="--compcor"
DRIFT="none"
STANDARDIZE="--standardize"
USE_PCA="--use-pca"
N_COMPONENTS=30
TIMESTAMP="baseline144_deob"
```

**2. Add to compilation:**

```python
'baseline144_deob': {
    'dataset': 'deoblique_v2',
    'timestamp': 'baseline144_deob',
    'config_num': 144,
    'smooth': 8,
    'standardize': 'Yes',
    'compcor': 'Yes'  # Add new parameter
}
```

### Adding New ROI

**1. Generate ROI masks:**

```bash
# Run ROI pipeline for new ROI
python build_roi_masks.py --roi new_ROI --subjects 01 02 03 ...
```

**2. Update ROIS list:**

```bash
# In SLURM batch files
ROIS=(V1 V2 V3 hV4 new_ROI)
```

```python
# In analysis scripts
ROIS = ["V1", "V2", "V3", "hV4", "new_ROI"]
```

### Adding New Metric

**1. Compute in core script:**

```python
# In fir_reconstruction_BH2009_system_clean.py
new_metric = compute_new_metric(data)

# Add to results_summary
results_summary['new_category'] = {
    'new_metric': new_metric
}

# Save to output
np.save(f"{output_dir}/new_metric.npy", new_metric)
```

**2. Extract in compilation:**

```python
# In analyze_baseline_results.py, extract_metrics()
metrics['new_metric'] = summary.get('new_category', {}).get('new_metric', np.nan)
```

**3. Visualize:**

```python
# In visualize_baseline_results.py
def plot_new_metric(df):
    # Custom visualization for new metric
    pass
```

---

## Best Practices

### 1. Naming Conventions

**Timestamps:**
- Use descriptive names: `baseline{config}_{dataset}`
- Include key parameters: `smooth6mm_std_pca30_deob`
- Avoid special characters (use underscore)

**SLURM job names:**
- Short but informative: `b32_orig`, `b81_deob`
- Helps with `squeue` monitoring

**Output directories:**
- Automatically generated by script
- Format: `sm{X}_hp{X}_mo{X}_cc{X}_dr{X}_st{X}_sub-{ID}_{ROI}_{roi_config}`

### 2. Subject Handling

**Current exclusions (as of 2025-12-12):**
```python
# All subjects
ALL_SUBJECTS = [f"{i:02d}" for i in range(1, 11)]  # 01-10

# Analyzable subjects (exclude sub-04: no V1 signal)
ANALYZABLE_SUBJECTS = ['01', '02', '03', '05', '06', '07', '08', '09', '10']

# Use in SLURM
SUBJECTS=(01 02 03 05 06 07 08 09 10)  # 9 subjects
#SBATCH --array=0-8  # 0-indexed
```

**Important:**
- Always document exclusion reasons
- Update subject lists consistently across all scripts
- Check `CLAUDE.md` for current status

### 3. Resource Management

**SLURM settings:**
```bash
#SBATCH --cpus-per-task=8    # Sufficient for nilearn
#SBATCH --mem=32GB           # Adequate for most analyses
#SBATCH --time=3:00:00       # 3 hours per subject (all 4 ROIs)
```

**Parallel strategy:**
- **Array jobs**: One job per subject
- **Sequential ROIs**: Loop through ROIs within each job
- **Rationale**: Balance resource usage and monitoring

### 4. Error Handling

**Check for failures:**
```bash
# On server after jobs complete
cd /scratch/connectome/haba6030/colorBlind
for log in logs/feature_selection/baseline32_origin_sub-*_*.err; do
    if [ -s "$log" ]; then
        echo "Error in: $log"
        tail -20 "$log"
    fi
done
```

**Re-run failed subjects:**
```bash
# Edit batch file to run specific subject
#SBATCH --array=2  # For subject 03 (0-indexed)
sbatch run_all_subjects_baseline32_origin.sbatch
```

### 5. Data Validation

**Before compilation:**
```bash
# Check result directories exist
ls derivatives/BH2009_*/baseline*/sm*_sub-*_V1_*/analysis_summary.json | wc -l
# Expected: N_configs × N_subjects × 1 ROI
```

**During compilation:**
```python
# analyze_baseline_results.py prints:
# - Number of results found
# - Missing results warnings
# - Summary statistics

# Review console output for data quality
```

### 6. Version Control

**Track analysis versions:**
```bash
# Create analysis tag
git tag -a analysis_baseline_v1.0 -m "Initial baseline comparison"
git push origin analysis_baseline_v1.0

# Document in README
echo "## Analysis Versions" >> README.md
echo "- v1.0 (2025-01-20): Baseline dataset comparison" >> README.md
```

**Save configuration:**
```python
# Save exact parameters with results
config_record = {
    'analysis_date': '2025-01-20',
    'python_script': 'fir_reconstruction_BH2009_system_clean.py',
    'git_commit': '<commit_hash>',
    'parameters': { ... }
}
with open('analysis_config.json', 'w') as f:
    json.dump(config_record, f, indent=2)
```

---

## Troubleshooting

### Problem: Missing ROI masks

**Symptom:**
```
❌ ERROR: ROI mask file not found!
Expected path: derivatives/sub-02/roi_pipeline_deob_Noprob/V1_mask_*.nii.gz
```

**Solutions:**
1. Check ROI pipeline directory name matches `--roi-pipeline-dir`
2. Verify ROI config string matches actual file
3. Ensure ROI masks were generated for all subjects
4. Check file permissions

```bash
# Verify ROI masks exist
ls derivatives/sub-*/roi_pipeline_deob_Noprob/*_mask_*.nii.gz | wc -l

# Check specific subject
ls -la derivatives/sub-02/roi_pipeline_deob_Noprob/
```

### Problem: fMRIPrep file not found

**Symptom:**
```
FileNotFoundError: /storage/.../sub-02_task-rsvp_run-1_*.nii.gz
```

**Solutions:**
1. Verify dataset path in `DATASET_CONFIGS`
2. Check fMRIPrep output structure
3. Ensure files exist on server

```bash
# On server
ls /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-02/func/*preproc_bold.nii.gz
```

### Problem: SLURM job array mismatch

**Symptom:**
```
IndexError: list index out of range
```

**Solution:**
```bash
# Mismatch between --array and SUBJECTS array
# Wrong:
#SBATCH --array=0-9  # 10 jobs
SUBJECTS=(01 02 03 05 06 07 08 09 10)  # 9 subjects

# Correct:
#SBATCH --array=0-8  # 9 jobs
SUBJECTS=(01 02 03 05 06 07 08 09 10)  # 9 subjects
```

### Problem: Results not compiling

**Symptom:**
```
Warning: No results found for sub-02 V1
```

**Debug:**
```python
# Check expected path pattern
import glob
pattern = "derivatives/BH2009_deoblique_v2/baseline32_deob/sm*_sub-02_V1_*"
matches = glob.glob(pattern)
print(f"Found {len(matches)} matches")

# Check actual directory structure
import os
for root, dirs, files in os.walk("derivatives/BH2009_deoblique_v2/baseline32_deob"):
    if "sub-02" in root and "V1" in root:
        print(root)
        if "analysis_summary.json" in files:
            print("  ✓ Has summary")
```

### Problem: Visualization fails

**Symptom:**
```
KeyError: 'classification_accuracy'
```

**Solutions:**
1. Check CSV has expected columns
2. Verify data loaded correctly
3. Filter for valid results only

```python
# Debug data
import pandas as pd
df = pd.read_csv('baseline_results_summary.csv')
print(df.columns.tolist())
print(df['summary_found'].value_counts())
print(df[df['summary_found'] == True].head())
```

### Problem: Inconsistent results across runs

**Possible causes:**
1. Different random seeds
2. Data loading issues
3. Preprocessing differences

**Solutions:**
```python
# Set random seed in analysis script
np.random.seed(42)

# Log data checksums
import hashlib
with open(fmriprep_file, 'rb') as f:
    checksum = hashlib.md5(f.read()).hexdigest()
print(f"Data checksum: {checksum}")
```

---

## Summary

This framework provides:
- ✅ **Systematic comparison** of datasets/preprocessing
- ✅ **Reproducible pipeline** from data to publication figures
- ✅ **Scalable architecture** for multiple comparisons
- ✅ **Automated compilation** of heterogeneous results
- ✅ **Flexible extension** for new analyses

**Key principles:**
1. Explicit parameterization
2. Unique identifiers (timestamps)
3. Comprehensive logging
4. Automated compilation
5. Version control

**For new analyses:**
1. Define comparison dimensions
2. Create SLURM batch files
3. Execute on server
4. Download results
5. Compile and visualize

---

## References

- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- Project documentation: `CLAUDE.md`, `BASELINE_ANALYSIS_README.md`
- Preprocessing guide: `docs/GUIDE_to_fMRIprep`
- Classification guide: `docs/GUIDE_to_classify_reconstruct`
