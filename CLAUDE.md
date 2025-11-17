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

## 2. SLURM Configuration (CRITICAL)

**All SBATCH files MUST include:**
```bash
#SBATCH --nodelist=node2  # ALWAYS specify node2
```

**NEVER include:**
```bash
#SBATCH --partition=normal  # DO NOT specify partition
``` 

## logs Recording
For each conversation, make MD file, and record all of the prompting and your answer in that md file. 

## 3. Project Overview

This is a neuroimaging analysis project based on "final_IRB.pdf", modifying **Brouwer & Heeger (2009, J. Neurosci.)** color decoding pipeline. The project analyzes fMRI data to decode color information from visual cortex areas (V1-V4) using forward encoding models. 

### Step 1: Formation of color reconstruction method to evaluate color perception
When defining the forwarding function f:

- Consider prediction performance on Non-CVD individuals.
- Consider performance differences between Non-CVD and CVD mappings.
- Consider whether the visualized channel space preserves consistent distance between colors (i.e., perceptual spacing).

Choose the model type (deep learning vs. linear matrix W) based on:

- Model performance
- Model complexity

For the forward model, applying **Brouwer & Heeger (2009, J. Neurosci.)** is an option, and using Machine-Learning or Deep-Learning to replicate brain's nonlinearlity is the other option. 

### Step 2: Overview of filter design for this project
Formulation: 
CH_CVD = f_CVD(vox_CVD)
CH_NC = f_NC(vox_NC)
 → f_CVD represents how the weighted sum across channels appears for a CVD participant.

Goal: Find a function g(x) such that

    vox_NC = g(vox_CVD)

so that the decoding outputs in channel space (CH values) become equivalent
between CVD and NC individuals.

Assumptions: 
- For Non-CVD (NC) individuals, the mapping function f is similar or effectively identical.
- For CVD individuals, f is similar with that of NC individuals. However, their voxel activation pattern differs across people because each person shows a unique CVD pattern.

Neural response formulation: 
vox = V(color)

→ Therefore, we want to find g_CVD(color) such that:

    V( g_CVD(color) )

passes through f_CVD and becomes restored to behave like the normal (NC) case.

## Key Analysis Files

- `bh_anal.py`: Main analysis pipeline implementing B&H (2009) methodology
- `naive_analysis.py`: Alternative HRF model comparison analysis
- `fir_reconstruction_*.py`: Current best pipeline, using universal FIR, optimal delay and PCA
- `roi_build.py`: ROI mask construction utilities using Wang (2015) atlas
- `config.py`: Global configuration settings and file paths
- `combine_atlas.py`: Atlas combination utilities

## Subject Naming Convention (CRITICAL)

**Pilot vs Test subjects must be clearly distinguished:**

- **P01** = Pilot subject
  - fMRIPrep directory: `/storage/connectome/haba6030/fmriprep_out/pilot/sub-01/`
  - File naming: `sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
  - Derivatives: `derivatives/{timestamp}/pilot/sub-01/zScore/{ROI_NAME}_universal_hrf` (to distinguish from test files)
  - Color mapping: Irregular spacing (LABEL2HUE_DEG_PILOT)
  - Already preprocessed with res-2

- **01, 02, 03, 04** = Test subjects
  - fMRIPrep directory: `/storage/connectome/haba6030/fmriprep_out/sub-01/`, `sub-02/`, etc.
  - File naming: `sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
  - Derivatives: `derivatives/{timestamp}/sub-01/zScore/{ROI_NAME}_universal_hrf`, etc.
  - Color mapping: Regular 45° spacing (LABEL2HUE_DEG_TEST)
  - Already preprocessed with res-2

**NEVER confuse pilot P01 with test files**

## Data Structure

The project expects fMRIPrep preprocessed data in this structure:
- `/storage/connectome/haba6030/fmriprep_out/sub-{01|02|03|04}/func/`: fMRIPrep BOLD files
- `/storage/connectome/haba6030/colorBlind_dataOct/sub-{01|02|03|04}/func/`: Event files (.tsv)
- `derivatives/{timestamp}/sub-01|02|03|04/zScore/{ROI_NAME}_universal_hrf`: Analysis outputs (ROI masks, results)
- `ProbAtlas_v4/`: Wang et al. (2015) probabilistic visual area atlas

## fMRIPrep Configuration (CRITICAL)

**Must match pilot preprocessing settings exactly:**

Pilot was preprocessed with fMRIPrep 25.0.0 using these settings (from config.toml):
```bash
fmriprep /data /out participant \
  --participant-label 01 \
  --fs-license-file /opt/freesurfer/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --bold2t1w-dof 6 \
  --nthreads 16 \
  --mem-mb 16000 \
  -w /work
```

**Key settings from config.toml:**
- `output_spaces = "MNI152NLin2009cAsym:res-2"` - ONLY this space, with res-2
- `bold2anat_dof = 6` - MUST be 6 (same as pilot)
- `use_syn_sdc = false` - NO synthetic distortion correction (pilot used actual GRE fieldmap)
- `nprocs = 16`, `memory_gb = 16.0`
- Fieldmap: Phase-drift map with two consecutive GRE acquisitions

**For test subjects (01-04):**
- Use same `--output-spaces MNI152NLin2009cAsym:res-2`
- If fieldmap exists: let fMRIPrep auto-detect
- If no fieldmap: add `--use-syn-sdc` for fieldmap-less distortion correction

**Expected output files (matching pilot):**
```
sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_boldref.nii.gz
sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz
sub-01_task-rsvp_run-X_desc-confounds_timeseries.tsv  # No space/res in confounds
```

**Resolution:** 97×115×97 (2mm MNI space with res-2)

**DO NOT add T1w or fsaverage spaces** - pilot only has MNI152NLin2009cAsym:res-2

## Main Analysis Pipeline

### 1. ROI Mask construction & overlaying
#### ROI Construction
ROIs are built from Wang (2015) atlas using mappings defined in `roi_build.py`:
- V1: roi1 (V1v) + roi2 (V1d)
- V2: roi3 (V2v) + roi4 (V2d)
- V3: roi5 (V3v) + roi6 (V3d)
- hV4: roi7

Also, for comparison, whole func BOLD will be used with ROI marked as BrainMask (sub-01_BrainMask_mask.nii.gz)

#### ROI Mask construction
ROI Masks for each participants are built with `roi_pipeline_comprehensive.py`:
- Match affine with reference anatomical & functional data to `MNI152NLin2009cAsym`
- Parameters: 
  - `threshold` = 50
  - `interpolation` = `nearest`
  - `binarize` = False
  - `brain_mask` = `func`
  - `use_gm_probseg` = 0.35

### 2. GLM & Preprocessing for extracting voxel responses
#### Configuration
- `TR = 1.5`: Repetition time
- `N_RUNS = 6`: Number of runs
- `N_COLORS = 8`: Color conditions
- `VOLS_TO_DROP = 4`: Volumes to discard at start

Planning to use `config.py`

#### Procedure
The `fir_reconstruction_*.py` files implements these stages:
1. `load_roi_mask`: load ROI mask 
2. `load_data`: load functional data and events, compounds
- Drop first four scans for stability
3. `design`: Build FIR design matrices (8 colors + blank)
4. `deconv_glm`: Fit voxelwise FIR GLM per run
5. `optimal_delay`: Determine optimal delay and universal HRF via selecting maximum absolute values.
6. `z-score`: Extract Z-score Estimates and create Z-maps from contrast maps of each color
- If `voxelChoice`: Extract voxels whose max_z is larger than threshold

### 3. Classification, Reconstruction
The `fir_reconstruction_*.py` files implements these stages:
1. `PCA`: From (Chosen) Z-score voxels, apply PCA for components = 6
2. `Classification`: with diagonal LDA, use one-run-out-cross validation
3. `Reconstruction`: Six-channel encoding model with leave-one-run-out & leave-one-color-out CV

### 4. Visualization
The `fir_reconstruction_*.py` files implements these stages:

#### Settings
- Visualize via actual stimulus colors in CIELab
- For circular graph, increase degree in anticlock wise, with middle-right being 0-degree

#### Figures 
1. Visualize Mean HRF from FIR: 
  - Extract FIR response for each color at all delays
  - Plot HRF with universal HRF highlighted
  - Plot universal HRF (bold) with annotating optimal delay
2. Z-Map Matrix Visualization:
  - Full Z-Score Matrix Heatmap (unsorted): 
    - Raw matrix (all voxels × colors) 
    - Sorted by peak color preference
    - Per-color z-score distribution
    - Voxel selectivity statistics: Count voxels with significant response (|z| > 2.3) for each color
  - Detailed per-color z-score heatmaps (top 100 voxels):
    - Get top voxels for this color
    - Show z-scores across all colors for these top voxels
  - Voxel-wise color preference wheel
    - Map color indices to hue angles, For each voxel, plot its preferred color direction weighted by z-score magnitude
3. PCA Component Visualization
  - Store results from each fold
  - Fit PCA for each fold independently
  1. Component × Color Matrix Heatmap with Robustness
    - Top-left: Mean matrix (colors × components)
    - Top-right: Std matrix (robustness check)
    - Bottom-left: Explained variance per component with error bars
    - Bottom-right: Per-color component variance with robustness
  2. Top Components per Color
  3. Component Loadings (top 5 components) - Mean across folds
  4. Subplot: cumulative variance with error bars + recommendation numbers
  5. PCA Color Space Visualization (B&H 2009 Figure 6 style)
    - Combination of PC1, PC2, PC3
4. Visualization: Reconstruction Results
  1. True vs Reconstructed Hues (Leave-One-Run-Out)
  2. Confusion Matrix Visualization
  3. Circular Color Space Visualization (naive_analysis style with colored markers)
    - Left: Training colors reconstruction 
    - Right: Novel colors reconstruction
    - Plot true colors at border and predictions inside

## Dependencies

Core packages (install via conda):
- nilearn: fMRI analysis
- nibabel: NIfTI file handling
- numpy, pandas: Data processing
- matplotlib: Visualization
- sklearn: Machine learning utilities
- scipy: Statistical functions

## Analysis Methodology

The forward encoding model uses:
- Six idealized color channels (half-wave rectified & squared sinusoids)
- Ordinary least squares estimation (not ridge regression)
- Leave-one-run-out cross-validation
- Two-tailed permutation testing (1000 iterations) for significance

## File Outputs

Analysis creates:
- `derivatives/sub-{SUB_ID}/`: GLM results, ROI masks, extracted data
- Design matrices, beta maps, decoding accuracies
- Quality control figures and statistical summaries