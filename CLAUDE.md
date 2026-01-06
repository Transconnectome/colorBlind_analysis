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

**Analyzable Subjects (as of 2026-01-05, original_v3 dataset):**

Based on preprocessing quality assessment (docs/0104_Preprocessing_Report.md):

**Tier 1: Excellent (100% pass, Dice ≥0.93)**
- **Subjects**: sub-01, sub-03, sub-04, sub-08, sub-09, sub-10 (6 subjects)
- **Usage**: Primary analyses, publications, group-level
- **Quality**: All 24 runs pass (Dice ≥0.80), minimal motion (<0.2mm)

**Tier 2: Good (83% pass, Dice ~0.82-0.92)**
- **Subjects**: sub-02, sub-05 (2 subjects)
- **Usage**: Individual-level and group-level (with caution)
- **Note**: 20/24 runs pass; consider excluding 4 bad runs (Dice <0.80)

**Tier 3: Partial (33% pass, Dice ~0.73-0.75)**
- **Subjects**: sub-06, sub-07 (2 subjects)
- **Usage**: Individual-level (good runs only); exclude from group-level
- **Issue**: High run-to-run variability, T1w mask over-extraction
- **Recommendation**: Supplementary analyses or case studies only

**Analysis Groups:**
- **Non-CVD (all)**: sub-01, 02, 03, 04, 05, 06, 07 (7 subjects)
- **CVD (all)**: sub-08, 09, 10 (3 subjects)
- **Tier 1+2 for group analysis**: sub-01, 02, 03, 04, 05, 08, 09, 10 (8 subjects)
- **HC for Procrustes**: sub-01, 02, 03, 04, 05 (5 Tier 1+2 non-CVD subjects)
- **CVD for testing**: sub-08, 09, 10 (3 CVD subjects)

**Data Paths (Current: original_v3 - 2026-01-05):**
```bash
# ✅ CURRENT DATASET (Use this for all new analyses)
FMRIPREP_OUT=/storage/connectome/haba6030/fmriprep_out_original_v3
EVENT_DIR=/storage/connectome/haba6030/bids_editted
DERIVATIVES=/scratch/connectome/haba6030/colorBlind/derivatives
```

**fMRIPrep original_v3 (CURRENT - USE THIS):**
- **Location**: `/storage/connectome/haba6030/fmriprep_out_original_v3/sub-{ID}/func/`
- **Key features**:
  - ✅ FreeSurfer removed (`--fs-no-reconall`)
  - ✅ BBR coregistration without surface-based alignment
  - ✅ Fieldmap applied
  - ✅ Quality: Dice 0.889 (mean), 83.3% pass rate, 0% ROI failure
- **BOLD files**: `sub-{ID}_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
- **Confounds**: `sub-{ID}_task-rsvp_run-X_desc-confounds_timeseries.tsv`
- **See**: `docs/0104_Preprocessing_Report.md` for quality metrics

**Event/Stimulus files:**
- **Location**: `/storage/connectome/haba6030/bids_editted/sub-{ID}/func/`
- **Files**: `sub-{ID}_task-rsvp_run-X_events.tsv`
- **Format**: BIDS-compliant (onset, duration, trial_type, color)

**Analysis outputs (derivatives):**
- **Location**: `/scratch/connectome/haba6030/colorBlind/derivatives/`
- **Structure**: `BH2009_{dataset}/{timestamp}/sm*_sub-{ID}_{ROI}_*/`

**Legacy datasets (DEPRECATED - DO NOT USE FOR NEW ANALYSES):**
```bash
# ⚠️ DEPRECATED: deoblique_v1 (fieldmap not applied)
/storage/connectome/haba6030/fmriprep_out_deoblique

# ⚠️ DEPRECATED: deoblique_v2 (fieldmap applied but oblique issues)
/storage/connectome/haba6030/fmriprep_out_deoblique_v2
```

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

## 3. Project Overview and Analysis Pipeline
**Specific Information is in docs/GUIDE_to_classify_reconstruct and analysis/README.md**

This is a neuroimaging analysis project based on "final_IRB.pdf", modifying **Brouwer & Heeger (2009, J. Neurosci.)** color decoding pipeline. The project analyzes fMRI data to decode color information from visual cortex areas (V1-V4) using forward encoding models.

### Current Analysis Pipeline (original_v3 dataset)

**Phase 0: Baseline Decoding**
  1. **ROI Extraction**: Wang Atlas (2015) probabilistic ROIs → MNI space
  2. **Baseline Reconstruction & Classification**:
     - FIR-based HRF estimation (8 delays, 12s window)
     - Voxel selection: Top 50% by FIR R²
     - 2nd-level GLM with HRF + derivative
     - Forward encoding model (6 half-wave rectified channels)
     - Leave-one-run-out cross-validation
  3. **Feature Selection**: ANOVA F-test based voxel selection (optional)

**Phase 1: Representational Similarity Analysis (RSA)**
  4. **RDM Analysis**: Compute 8×8 Representational Dissimilarity Matrices
  5. **Inter-subject consistency**: Spearman correlation + Mantel test

**Phase 2: Procrustes Analysis & CVD-HC Comparison**
  6. **Procrustes Alignment**: Reference-based geometric alignment (sub-02 as reference)
  7. **HC Group Template**: Learn common decoder across aligned HC subjects
  8. **CVD Testing**: Apply Procrustes + HC decoder to CVD subjects
  9. **3D Characterization**: Magnitude, Sign/Baseline, Structure (RDM) differences

**Phase 3: Filter Learning (RQ3 - Neural-Guided Personalized Filter)**
  10. **3-Dimensional Loss Optimization**:
      - Loss = λ_mag × L_magnitude + λ_base × L_baseline + λ_rdm × L_RDM
      - Learn linear transformation F = Y @ A + b
      - Subject-specific filters for CVD→HC pattern mapping

**Next Research Questions (SRQs - Future Phases)**:
  - **SRQ1**: Shared Decoder Validation (completed via Procrustes)
  - **SRQ2**: Hyperalignment for HC Common Space (trial-aligned GPA)
  - **SRQ3**: Continuous Hue Interpolation (360° forward encoding)
  - **SRQ4**: CVD Filter Optimization via 360° Search

## 4. Preprocessing Settings

### 4.1 fMRIPrep Settings (original_v3)

**Key Parameters:**
```bash
--fs-no-reconall                    # FreeSurfer removed (critical fix)
--use-syn-sdc                       # Fieldmap-based distortion correction
--bold2t1w-dof 9                    # BBR with 9 DOF (no FreeSurfer surface)
--force-bbr                         # Force boundary-based registration
--dummy-scans 4                     # Remove first 4 volumes
--output-spaces MNI152NLin2009cAsym:res-2  # 2mm MNI space
```

**Quality Improvements (vs deoblique_v2):**
- Dice coefficient: 0.889 (vs 0.376 before, +136%)
- Pass rate (≥0.80): 83.3% (vs 0.0%, +83pp)
- ROI generation failure: 0.0% (vs 45.4%, complete resolution)

**Rationale:**
- `--fs-no-reconall`: FreeSurfer surface-based registration caused distortion in narrow visual cortex EPI
- BBR without surface constraints: Better T1w-BOLD alignment (Dice 0.889)
- See: `docs/0104_Preprocessing_Report.md`

### 4.2 Baseline Decoding Settings (Baseline32)

**Current Standard Configuration:**
```python
# Baseline32 configuration (determined via systematic review)
Smoothing:      0mm (no smoothing)
High-pass:      0.01 Hz
Motion:         cosine (6 cosine basis functions)
CompCor:        None
Drift:          none (handled by high-pass)
Standardize:    False (preserve raw beta values)
PCA:            30 components
```

**FIR GLM Parameters:**
```python
N_DELAYS = 8                    # 8 FIR delays (12s window at TR=1.5s)
VOXEL_SELECTION = 'top50'       # Top 50% voxels by FIR R²
HRF_MODEL = 'fir + derivative'  # 2nd-level GLM with HRF + temporal derivative
```

**Forward Encoding Model:**
```python
N_CHANNELS = 6                  # 6 half-wave rectified basis functions
CHANNEL_CENTERS = [0°, 60°, 120°, 180°, 240°, 300°]  # Equally spaced in hue space
CHANNEL_WIDTH = 60°             # FWHM of Gaussian basis functions
CROSS_VALIDATION = 'LORO'       # Leave-One-Run-Out
```

**Rationale:**
- **No smoothing**: Preserves fine-grained voxel patterns for MVPA
- **High-pass 0.01 Hz**: Removes slow drifts (100s period) while preserving task signal
- **Cosine motion**: Lightweight correction without removing task-related variance
- **No CompCor**: Avoids removing signal from visual cortex
- **PCA 30**: Computational efficiency while retaining 95%+ variance
- **FIR approach**: Model-free HRF estimation, no assumptions about HRF shape
- **Top 50% R²**: SNR-based voxel selection for robust signal

**See**: `docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md` for full systematic review (144 configurations tested)

## 5. Dependencies

Core packages (install via conda):
- nilearn: fMRI analysis
- nibabel: NIfTI file handling
- numpy, pandas: Data processing
- matplotlib: Visualization
- sklearn: Machine learning utilities
- scipy: Statistical functions
- torch: Deep learning (for Phase 3 filter learning)

## 6. File Outputs

Analysis creates:
- `derivatives/BH2009_{dataset}/{timestamp}/`: Baseline results per subject-ROI
- `derivatives/phase1_results/`: RDM analysis outputs
- `derivatives/phase2_procrustes/`: Procrustes alignment and CVD-HC comparison
- `derivatives/phase3_filters/`: Learned transformation filters
- Design matrices, beta maps, decoding accuracies
- Quality control figures and statistical summaries

## Systematic Preprocessing Review Analysis

**Primary document**: `SYSTEMATIC_PREPROCESSING_ANALYSIS.md`

This analysis systematically evaluated 144 preprocessing configurations (3 smoothing × 2 high-pass × 3 motion × 2 CompCor × 2 drift × 2 standardization) across 2 subjects and 4 ROIs (V1, V2, V3, hV4).