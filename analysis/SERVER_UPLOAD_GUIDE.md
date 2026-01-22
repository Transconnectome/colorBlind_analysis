# Server Upload Guide

**Updated: 2026-01-22**

Complete guide for uploading the entire analysis directory to the server with the new structure supporting method3_header_mi dataset.

## Overview

The new structure uses:
- **Shared ROI masks**: `analysis/roi_masks/{dataset}/`
- **Phase-specific results**: `analysis/{phase}/{dataset}/results/`
- **Phase-specific logs**: `analysis/{phase}/{dataset}/logs/`
- **Common utilities**: `analysis/utils/` (path management, data loading)

## Quick Upload - Complete Analysis Directory (RECOMMENDED)

### One-Line Upload (모든 스크립트 한번에)

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Upload entire analysis directory (excluding results/logs)
rsync -av --exclude='results/' --exclude='logs/' --exclude='*.nii.gz' --exclude='*.npy' --exclude='*.npz' --exclude='__pycache__/' analysis/ haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/
```

**What gets uploaded:**
- ✓ All Python scripts (`.py`)
- ✓ All SLURM scripts (`.sbatch`)
- ✓ All utilities (`utils/`)
- ✓ All phase directories (phase1, phase2, phase3, prep_trials, etc.)
- ✓ README and documentation files

**What does NOT get uploaded (automatically excluded):**
- ✗ `results/` directories
- ✗ `logs/` directories
- ✗ `.nii.gz`, `.npy`, `.npz` files (data)
- ✗ `__pycache__/` directories

### Alternative: SCP Upload (Simple but slower)

```bash
# Upload all directories with scripts
scp -r analysis/{utils,phase1_preprocess_decoding,phase2_*,phase3_*,prep_trials,comprehensive,group_level,future_phase*}/*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/
scp -r analysis/comprehensive/*.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/comprehensive/
```

## What Gets Created Automatically on Server

The scripts will automatically create these directories when they run:

```
/scratch/connectome/haba6030/colorBlind/analysis/
├── roi_masks/
│   └── method3_header_mi/
│       └── sub-{01-10}/          # Created by roi_pipeline scripts
├── phase1_preprocess_decoding/
│   └── method3_header_mi/
│       ├── results/
│       │   └── baseline_decoding/  # Created by fir_reconstruction
│       └── logs/                    # Created by sbatch --output
├── phase2_procrustes_cvd_hc/
│   └── method3_header_mi/
│       ├── results/                 # Created by procrustes scripts
│       └── logs/
├── phase3_procrustes_filter/
│   └── method3_header_mi/
│       ├── results/                 # Created by filter learning
│       └── logs/
└── prep_trials/
    └── method3_header_mi/
        ├── results/                 # Created by prep trials
        └── logs/
```

## Complete Analysis Directory Structure

After upload, your analysis directory will contain:

```
analysis/
├── utils/                            # ✓ Uploaded
│   ├── output_paths.py              # Path management
│   ├── data_loader.py               # Data loading utilities
│   └── utils_color_decoding.py      # Color decoding utilities
├── phase1_preprocess_decoding/       # ✓ Uploaded
│   ├── *.py                         # All preprocessing scripts
│   ├── *.sbatch                     # SLURM batch files
│   ├── grid_search/*.py             # Grid search scripts
│   └── feature_selection/*.py       # Feature selection
├── phase2_baseline_comparing/        # ✓ Uploaded
│   └── *.py                         # RSA and comparison scripts
├── phase2_procrustes_cvd_hc/        # ✓ Uploaded
│   ├── *.py                         # Procrustes analysis
│   └── visualization/*.py           # Visualization scripts
├── phase3_procrustes_filter/         # ✓ Uploaded
│   └── *.py                         # Filter learning
├── prep_trials/                      # ✓ Uploaded
│   ├── scripts/*.{py,sbatch,sh}     # Preprocessing trials
│   └── README.md
├── comprehensive/                    # ✓ Uploaded
│   └── *.sbatch                     # Complete pipeline runners
├── group_level/                      # ✓ Uploaded
│   ├── *.py                         # Group-level analyses
│   └── *.sbatch                     # Group-level runners
├── future_phase*/                    # ✓ Uploaded
│   └── *.py                         # Future development phases
└── *.md                             # ✓ Documentation files
```

## Running the Pipeline on Server

### Step 1: SSH to Server

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
```

### Step 2: Activate Conda Environment

```bash
conda activate nilearn
```

### Step 3: Verify Upload

```bash
# Check if files are uploaded correctly
ls -la analysis/phase1_preprocess_decoding/*.py
ls -la analysis/comprehensive/*.sbatch
ls -la analysis/utils/*.py
```

### Step 4: Run Pipeline

#### Option A: Full Pipeline (All Phases)

```bash
# Run complete analysis (sequential, 80-130h)
sbatch analysis/comprehensive/comprehensive_first_analysis.sbatch
```

#### Option B: Phase by Phase

```bash
# Phase 1a: ROI Pipeline (all subjects)
sbatch analysis/phase1_preprocess_decoding/run_roi_fixed_all_subjects.sbatch

# Phase 1b: Baseline Decoding (single subject-ROI)
cd analysis/phase1_preprocess_decoding
python fir_reconstruction_BH2009_system_clean.py \
    --subject 01 \
    --roi V1 \
    --dataset method3_header_mi \
    --smooth 0 \
    --highpass 0.01 \
    --motion cosine \
    --use-pca \
    --n-components 30
```

## Monitoring Execution

### Check Job Status

```bash
# View running jobs
squeue -u haba6030

# View specific job details
squeue -j <job_id>

# View all jobs on node2
squeue -w node2
```

### Check Logs

```bash
# View latest log file
tail -f analysis/phase1_preprocess_decoding/method3_header_mi/logs/complete_pipeline_*.out

# Check for errors
tail -f analysis/phase1_preprocess_decoding/method3_header_mi/logs/complete_pipeline_*.err

# View ROI pipeline logs
ls -lth analysis/phase1_preprocess_decoding/method3_header_mi/logs/

# Follow specific log
tail -f analysis/phase1_preprocess_decoding/method3_header_mi/logs/job_12345.out
```

### Check Results

```bash
# ROI masks (shared resource)
ls -lh analysis/roi_masks/method3_header_mi/sub-01/

# Baseline decoding results
ls -lh analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/

# Check specific subject-ROI
ls -lh analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/20260122_*/sub-01/V1/
```

## Downloading Results

### Download Specific Results

```bash
# Download ROI masks
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/roi_masks/method3_header_mi/sub-01/ ~/Downloads/

# Download baseline decoding results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/ ~/Downloads/

# Download logs
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/logs/ ~/Downloads/
```

### Download Everything

```bash
# Download entire analysis directory (WARNING: large)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/ ~/Downloads/colorBlind_analysis_results/
```

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'utils.output_paths'"

**Solution:** Make sure you uploaded the utils directory:
```bash
scp analysis/utils/*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/utils/
```

### Problem: "ROI mask not found"

**Solution:** Check if ROI pipeline has been run first:
```bash
# Check shared ROI location
ls analysis/roi_masks/method3_header_mi/sub-01/

# If empty, run ROI pipeline first
sbatch analysis/phase1_preprocess_decoding/run_roi_fixed_all_subjects.sbatch
```

### Problem: "Permission denied" or directory not created

**Solution:** Create directories manually:
```bash
mkdir -p analysis/phase1_preprocess_decoding/method3_header_mi/{results,logs}
mkdir -p analysis/roi_masks/method3_header_mi
mkdir -p analysis/utils
```

### Problem: SLURM job fails immediately

**Solution:** Check the error log:
```bash
# Find the error file
ls -lt analysis/phase1_preprocess_decoding/method3_header_mi/logs/*.err | head -1

# View the error
cat <error_file>
```

## File Organization Summary

### What to Upload (Code)
```
analysis/
├── utils/
│   └── output_paths.py ✓
├── phase1_preprocess_decoding/
│   ├── roi_pipeline_selected_1202used.py ✓
│   ├── fir_reconstruction_BH2009_system_clean.py ✓
│   ├── visualize_roi_overlay.py ✓
│   ├── run_roi_fixed_all_subjects.sbatch ✓
│   └── grid_search/
│       ├── roi_pipeline_comprehensive.py ✓
│       └── grid_search_preprocessing.py ✓
└── comprehensive/
    ├── comprehensive_first_analysis.sbatch ✓
    └── comprehensive_first_analysis_node4.sbatch ✓
```

### What Gets Created (Results)
```
analysis/
├── roi_masks/method3_header_mi/
│   └── sub-{01-10}/              # Auto-created ✓
│       └── V1_mask_*.nii.gz
├── phase1_preprocess_decoding/method3_header_mi/
│   ├── results/                  # Auto-created ✓
│   │   └── baseline_decoding/
│   └── logs/                     # Auto-created ✓
│       └── job_*.{out,err}
└── phase2_procrustes_cvd_hc/method3_header_mi/
    ├── results/                  # Auto-created ✓
    └── logs/                     # Auto-created ✓
```

## Memory Management

**IMPORTANT:** Monitor memory usage to prevent OOM errors:

```bash
# Check memory before running
ssh node2 free -h

# Check current memory usage
watch -n 5 free -h

# Check specific job memory
sstat -j <job_id> --format=JobID,MaxRSS,MaxVMSize

# Profile a script before batch submission
/usr/bin/time -v python script.py
```

## Batch vs Interactive

**Batch (Recommended):**
```bash
sbatch script.sbatch
```

**Interactive (Debug only):**
```bash
# Request interactive session
srun --nodelist=node2 --qos=shared --cpus-per-task=4 --mem=16G --time=2:00:00 --pty bash

# Run commands
conda activate nilearn
cd /scratch/connectome/haba6030/colorBlind
python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py ...
```

---

**See also:**
- `DIRECTORY_STRUCTURE.md` - Directory layout explanation
- `README.md` - Analysis pipeline overview
- `CLAUDE.md` - Development guide
- `utils/output_paths.py` - Path management utilities

**Last Updated:** 2026-01-22
