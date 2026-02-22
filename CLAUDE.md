# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. Environment Setup

Before running any Python code, activate the nilearn conda environment:
```bash
conda activate nilearn # if in server
conda activate srm # if in local
```

Most of the files are being ran in the remote server and directory named: haba6030@node3:/scratch/connectome/haba6030/colorBlind
(Note: Use `node3` for SSH/SCP access. SLURM jobs run on node2/node4 via sbatch.)
Also, most of the code is ran by using SLURM.
Therefore, for running a code to check it, follow this procedure:
1. suggest code and sbatch modification & bash file for required checking in interactive mode
2. suggest necessary memory monitoring method in background to prevent drain, OOM or other probs:
   ```bash
   # Profile actual resource usage before array jobs
   /usr/bin/time -v bash script.sh > output.log 2>&1
   # Check: Maximum resident set size (peak memory)
   # Check: Percent of CPU (actual CPU usage)
   ```
3. suggest scp CLI for uploading code **without line-breaking**
4. suggest how to run code in the server
5. suggest how to download from the server and run analysis code. 

### 1-2. SLURM Configuration (CRITICAL)

**CPU Jobs (node2) - 기본 배치 작업:**
```bash
#SBATCH --nodelist=node2
# ⚠️ --qos 지정하지 않음 (서버 기본값 사용)
```

**GPU Jobs (node3) - GPU 필요한 작업:**
```bash
#SBATCH --nodelist=node3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
# ⚠️ --qos 지정하지 않음 (서버 기본값 사용)
```

**NEVER include:**
```bash
#SBATCH --partition=normal         # ❌ Invalid partition error!
#SBATCH --partition=shared         # ❌ Invalid partition error!
#SBATCH --qos=shared               # ❌ 사용 금지!
#SBATCH --qos=shared_interactive   # ❌ 사용 금지!
#SBATCH --qos=interactive          # ❌ 사용 금지!
#SBATCH --qos=debug                # ❌ sbatch에서 qos 지정 금지!
```

**핵심 규칙:**
- **sbatch에서 --qos 지정하지 않음** (서버 기본값 자동 적용)
- **절대 금지**: --partition 지정, --qos 지정
- Set conda as below: 
```
source ~/.bashrc
conda activate nilearn
```
- **Don't use seaborn package in server**

**Guideline for Claude:**
- When suggesting scp commands, ALWAYS combine files going to the same destination
- Use wildcards (*.py, *.sbatch) when multiple files match pattern
- Only use separate scp commands when destinations differ
- Prefer 2-3 efficient commands over 10+ separate commands

### 1-4. SLURM Memory Limits (CRITICAL)

**Node2/Node4 Specs (Updated: 2026-01-19):**
```
Node2: 502GB total, ~450GB typically free
Node4: 514GB total, ~176GB typically free
```

**Safe Memory Formula for Array Jobs:**
```
memory_per_task × max_concurrent ≤ (available_memory × 0.8)
```

**Recommended Configs:**

**Node2 (CPU-intensive, typically less congested):**
```bash
# Conservative (safe for shared usage)
#SBATCH --array=1-10%5
#SBATCH --mem=16G
#SBATCH --nodelist=node2
# Total: 80GB ✓

# Aggressive (when node is idle)
#SBATCH --array=1-10%10
#SBATCH --mem=20G
#SBATCH --nodelist=node2
# Total: 200GB ✓ (if node is free)
```

**Node4 (may have other users):**
```bash
#SBATCH --array=1-10%4
#SBATCH --mem=16G
#SBATCH --nodelist=node4
# Total: 64GB ✓
```

**CRITICAL:** Always check actual free memory before large array jobs:
```bash
ssh node2 free -h  # Check available memory
squeue -w node2    # Check current jobs
```

## 2. File Structure to fMRIPrep Output Check 
**Specific Information is in docs/GUIDE_to_fMRIprep**
- BIDS file, fMRIPrep Setting, Outcome Diagnose

**Subject Groups:**
- **Non-CVD subjects (all)**: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06, sub-07 (7 subjects)
- **CVD subjects (all)**: sub-08, sub-09, sub-10 (3 subjects)

**Data Paths (Current: method3_header_mi - 2026-01-22):**
```bash
FMRIPREP_OUT=/storage/connectome/haba6030/fmriprep_out_method3_header_mi
EVENT_DIR=/storage/connectome/haba6030/bids_editted
DERIVATIVES=/scratch/connectome/haba6030/colorBlind/derivatives
```

**fMRIPrep method3_header_mi (CURRENT - USE THIS):**
- **Location**: `/storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-{ID}/func/`
- **BOLD files**: `sub-{ID}_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
- **Confounds**: `sub-{ID}_task-rsvp_run-X_desc-confounds_timeseries.tsv`
- **Registration method**: MI-based coregistration with header optimization
- **See**: `analysis/prep_trials/README.md` for registration quality comparison

**Event/Stimulus files:**
- **Server (BIDS format)**: `/storage/connectome/haba6030/bids_editted/sub-{ID}/func/`
  - Files: `sub-{ID}_task-rsvp_run-X_events.tsv`
  - Format: BIDS-compliant (onset, duration, trial_type, block, trial, target_presented)
- **Local (Original)**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_data/logs/sub-{ID}/`
  - Files: `ses-1_rsvp_run-X_events.tsv`
  - Same content as server, different filename format

**CRITICAL - trial_type values**:
```python
# Color trials (8 colors)
color_trials = ['color_1', 'color_2', 'color_3', 'color_4',
                'color_5', 'color_6', 'color_7', 'color_8']

# Non-color trials
other_trials = ['blank']

# Color mapping (for reference, not in file):
# color_1 = red, color_2 = orange, color_3 = yellow, color_4 = green
# color_5 = cyan, color_6 = blue, color_7 = purple, color_8 = magenta
```

**Analysis outputs (derivatives):**
- **Location**: `/scratch/connectome/haba6030/colorBlind/derivatives/`
- **Structure**: `BH2009_{dataset}/{timestamp}/sm*_sub-{ID}_{ROI}_*/`

## 3. Analysis Pipeline
### Current Analysis Pipeline (original_v3 dataset)

Follow phase 1~3 and then future_phase 1~3 in `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis`

## 4. Preprocessing Settings

### 4.1 fMRIPrep Settings 
Check `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/README.md`

### 4.2 Baseline Decoding Settings (Baseline32)
Check `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/README.md`

## 5. File Outputs

Analysis creates:
- `derivatives/BH2009_{dataset}/`: Baseline results per subject-ROI
- `derivatives/phase1_results/`: RDM analysis outputs
- `derivatives/phase2_procrustes/`: Procrustes alignment and CVD-HC comparison
- `derivatives/phase3_filters/`: Learned transformation filters

**Output Convention (CRITICAL — no timestamp subdirectories):**
- Save results **directly** into `--output_dir` (flat structure, no `{date_time}/` subdirs)
- Per-subject files: `sub-{ID}_*.json` (e.g., `sub-01_performance_raw.json`, `sub-01_loco.json`)
- **`config.json`**: One per output_dir. Records date, parameters, data paths, settings. Safe to overwrite (identical across subjects in same batch).
- Manage result grouping via directory names (e.g., `results/loco/`, `results/nested_procrustes/raw_ctrl/`)
- **WHY**: SLURM array jobs start simultaneously → identical timestamps → overwrites and data loss

## 7. Future Phases Development (SRQ2-4)

**Development workspace**: `prediction_model_workspace/`
**TODO tracking**: `prediction_model_workspace/MASTER_PLAN.md`

### Phase Directories

- **Future Phase 1**: `analysis/future_phase1_hyperalignment/` - HC common space (SRQ2)
- **Future Phase 2**: `analysis/future_phase2_forward_model/` - 360° hue encoder (SRQ3)
- **Future Phase 3**: `analysis/future_phase3_filter_optimization/` - CVD filter optimization (SRQ4)