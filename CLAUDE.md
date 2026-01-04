# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. Environment Setup

Before running any Python code, activate the nilearn conda environment:
```bash
conda activate nilearn
```

Most of the files are being ran in the remote server and directory named:
haba6030@node2:/scratch/connectome/haba6030/colorBlind
Also, most of the code is ran by using SLURM.
Therefore, for running a code to check it, suggest this procedure
(1) suggest code and sbatch modification -> (2) suggest scp CLI for uploading code -> (3) how to run code in the server -> (4) how to download from the server.

### 1-1. CRITICAL: Server Connection

**ALWAYS use `node2` for server connections:**

```bash
# ✅ CORRECT - Upload files
scp file.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# ✅ CORRECT - Download files
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/results.txt ./

# ✅ CORRECT - SSH connection
ssh haba6030@node2

# ❌ WRONG - Do NOT use IP address
scp file.py haba6030@node2:/scratch/...  # NEVER USE THIS
```

**Reason**: The server hostname `node2` is configured in SSH config and ensures correct node access.

### 1-2. SLURM Configuration (CRITICAL)

**CPU Jobs (node2) - 기본 배치 작업:**
```bash
#SBATCH --qos=shared               # ⚠️ REQUIRED: 노드 공유 필수!
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
```

**GPU Jobs (node3) - GPU 필요한 작업:**
```bash
#SBATCH --qos=shared_interactive   # ⚠️ CRITICAL: interactive 아님!
#SBATCH --nodelist=node3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
```

**NEVER include:**
```bash
#SBATCH --partition=normal         # ❌ Invalid partition error!
#SBATCH --partition=shared         # ❌ Invalid partition error!
#SBATCH --qos=interactive          # ❌ node3에서는 shared_interactive 사용!
```

**핵심 규칙:**
- **node2 (CPU)**: --qos=shared 필수
- **node3 (GPU)**: --qos=shared_interactive 필수
- **절대 금지**: --partition 지정 (서버가 자동 할당)

## 2. File Structure to fMRIPrep Output Check 
**Specific Information is in docs/GUIDE_to_fMRIprep**
- BIDS file, fMRIPrep Setting, Outcome Diagnose

**Subject Groups:**
- **Non-CVD subjects (all)**: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06, sub-07 (7 subjects)
- **CVD subjects (all)**: sub-08, sub-09, sub-10 (3 subjects)

**Analyzable Subjects (as of 2025-12-17):**
- **Non-CVD (individual-level)**: sub-01, sub-02, sub-03, sub-05, sub-06, sub-07 (6 subjects)
- **Non-CVD (group-level)**: sub-02, sub-03, sub-05, sub-06, sub-07 (5 subjects) - **sub-01 excluded**
- **CVD (analyzable)**: sub-08, sub-09, sub-10 (3 subjects)
- **Excluded from all**: sub-04 (No BOLD signal at V1 atlas location)

**Exclusion Reasons:**

**sub-04 (excluded from all analysis):**
- ROI alignment diagnostic (Job 67066+) revealed V1 atlas location has zero BOLD signal across all timepoints
- fMRIPrep functional brain mask excludes posterior visual cortex
- Unlike sub-03/09/10, BOLD data itself is zeros at V1 location (not just masked out)
- Root cause: Likely insufficient EPI coverage or signal dropout
- See: `logs/diagnostics/brain_mask_verification.txt` and `ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md`

**sub-01 (excluded from group-level analysis only):**
- Significantly fewer voxels after feature selection compared to other subjects
- V3 outlier: 3 voxels vs 58 voxels in others (5% of group median)
- Including sub-01 would discard 95% of V3 data from 5 good subjects
- Similar issues in V2 (80% of median) and V1 (95% of median)
- Individual-level decoding still valid, but problematic for group alignment
- See: `docs/SUB01_OUTLIER_DIAGNOSIS.md`

**Data Paths (After Deoblique Preprocessing):**
```bash
INPUT_DIR=/storage/connectome/haba6030/colorBlind_data_deoblique
OUTPUT_DIR_V1=/storage/connectome/haba6030/fmriprep_out_deoblique      # Original (fieldmap not applied)
OUTPUT_DIR_V2=/storage/connectome/haba6030/fmriprep_out_deoblique_v2   # Improved (fieldmap applied)
WORK_DIR_V1=/storage/connectome/haba6030/fmriprep_work_deoblique_batch2
WORK_DIR_V2_B1=/storage/connectome/haba6030/fmriprep_work_deoblique_v2_batch1  # Sub-01~05
WORK_DIR_V2_B2=/storage/connectome/haba6030/fmriprep_work_deoblique_v2_batch2  # Sub-06~10
```

- **Event/Stimulus files**: `/storage/connectome/haba6030/colorBlind_data_deoblique/sub-{ID}/func/`

- **fMRIPrep outputs (v1 - DEPRECATED)**: `/storage/connectome/haba6030/fmriprep_out_deoblique/sub-{ID}/func/`
  - ⚠️ **Fieldmap not applied** (missing B0FieldIdentifier)
  - ⚠️ DO NOT use for new analysis

- **fMRIPrep outputs (v2 - RECOMMENDED)**: `/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-{ID}/func/`
  - ✅ **Fieldmap applied** (B0FieldIdentifier present)
  - ✅ Better registration (DOF 9, BBR forced, dummy scans removed)
  - ✅ All 10 subjects (01-10)
  - BOLD files: `sub-{ID}_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
  - Confounds: `sub-{ID}_task-rsvp_run-X_desc-confounds_timeseries.tsv`

- **Analysis outputs (derivatives)**: `/scratch/connectome/haba6030/colorBlind/derivatives/`

**Baseline Analysis Results Structure (CRITICAL for group-level scripts):**
```bash
# Path structure:
derivatives/BH2009_{dataset}/{timestamp}/sm*_sub-{ID}_{roi}_*/

# Example:
derivatives/BH2009_deoblique_v2/baseline81_deob_determin/sm6.0_hpYe_moCo_ccNo_drNo_stTr_sub-02_hV4_None/

# Contains:
amplitudes_z.npy          # (n_runs, n_colors, n_voxels) - z-scored channel amplitudes
classification_results.txt
roi_mask.nii.gz
# etc.
```

**Loading baseline results in Python:**
```python
from pathlib import Path
import glob

dataset = 'deoblique_v2'
timestamp = 'baseline81_deob_determin'
subject_id = '02'
roi = 'V1'

base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')
matches = glob.glob(pattern)
result_dir = Path(matches[0])
amplitudes = np.load(result_dir / 'amplitudes_z.npy')
```

**IMPORTANT**:
- **All analysis MUST use the most recent version suggested in `logs/GUIDE_to_fMRIprep`**
- **Group-level scripts MUST use the correct derivatives path structure above** 

## 3. Project Overview and Analysis
**Specific Information is in docs/GUIDE_to_classify_reconstruct**

This is a neuroimaging analysis project based on "final_IRB.pdf", modifying **Brouwer & Heeger (2009, J. Neurosci.)** color decoding pipeline. The project analyzes fMRI data to decode color information from visual cortex areas (V1-V4) using forward encoding models. 

### Guide
Procedure: 
  1. Preprocessing: Find out best preprocessing setting
  2. Baseline: Check baseline result (classification & reconstruction) of chosen preprocessing setting
  3. Feature Selection: Figure out the best feature selection method. 
  4. Group-level analysis: Across non-cvd participants (sub 01 ~ 07) make a common beta-map and conduct classification & reconstruction
  5. Try non-linear color reconstruction method

## Dependencies

Core packages (install via conda):
- nilearn: fMRI analysis
- nibabel: NIfTI file handling
- numpy, pandas: Data processing
- matplotlib: Visualization
- sklearn: Machine learning utilities
- scipy: Statistical functions

## File Outputs

Analysis creates:
- `derivatives/sub-{SUB_ID}/`: GLM results, ROI masks, extracted data
- Design matrices, beta maps, decoding accuracies
- Quality control figures and statistical summaries

## Systematic Preprocessing Review Analysis

**Primary document**: `SYSTEMATIC_PREPROCESSING_ANALYSIS.md`

This analysis systematically evaluated 144 preprocessing configurations (3 smoothing × 2 high-pass × 3 motion × 2 CompCor × 2 drift × 2 standardization) across 2 subjects and 4 ROIs (V1, V2, V3, hV4).