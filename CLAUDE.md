# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

Before running any Python code, activate the nilearn conda environment:
```bash
conda activate nilearn
```

Most of the files are being ran in the remote server and directory named:
haba6030@node2:/scratch/connectome/haba6030/colorBlind
Also, most of the code is ran by using SLURM.
Therefore, for running a code to check it, suggest this procedure
(1) suggest code and sbatch modification -> (2) suggest scp CLI for uploading code -> (3) how to run code in the server -> (4) how to download from the server.

## SLURM Configuration (CRITICAL)

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

## Project Overview

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
    - Planning to choose which file to use between these based on decoding performance. Trying to find best setting by integrating both.  
- `roi_build.py`: ROI mask construction utilities using Wang (2015) atlas
- `config.py`: Global configuration settings and file paths
- `combine_atlas.py`: Atlas combination utilities

## Subject Naming Convention (CRITICAL)

**Pilot vs Test subjects must be clearly distinguished:**

- **P01** = Pilot subject
  - fMRIPrep directory: `/storage/connectome/haba6030/fmriprep_out/sub-P01/`
  - File naming: `sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
  - Derivatives: `derivatives/sub-P01/` (to distinguish from test sub-01)
  - Color mapping: Irregular spacing (LABEL2HUE_DEG_PILOT)
  - Already preprocessed with res-2

- **01, 02, 03, 04** = Test subjects
  - fMRIPrep directory: `/storage/connectome/haba6030/fmriprep_out/sub-01/`, `sub-02/`, etc.
  - File naming: `sub-01_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
  - Derivatives: `derivatives/sub-01/`, `sub-02/`, etc.
  - Color mapping: Regular 45° spacing (LABEL2HUE_DEG_TEST)
  - Need preprocessing with identical res-2 settings as pilot

**NEVER confuse pilot P01 with test 01!**

## Data Structure

The project expects fMRIPrep preprocessed data in this structure:
- `/storage/connectome/haba6030/fmriprep_out/sub-{P01|01|02|03|04}/func/`: fMRIPrep BOLD files
- `/storage/connectome/haba6030/colorBlind_dataOct/sub-{P01|01|02|03|04}/func/`: Event files (.tsv)
- `derivatives/sub-{P01|01|02|03|04}/`: Analysis outputs (ROI masks, results)
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

The `BHAnalysisPipeline` class in `bh_anal.py` implements these stages:
1. `design`: Build FIR design matrices (8 colors + blank)
2. `deconv_glm`: Fit voxelwise FIR GLM per run
3. `roi_build`: Create V1-V4 masks from Wang atlas
4. `extract_roi`: Extract ROI data
5. `forward_model`: Six-channel encoding model with leave-one-run-out CV
6. `qc`: Quality control and visualization

## ROI Construction

ROIs are built from Wang (2015) atlas using mappings defined in `roi_build.py`:
- V1: roi1 (V1v) + roi2 (V1d)
- V2: roi3 (V2v) + roi4 (V2d)
- V3: roi5 (V3v) + roi6 (V3d)
- hV4: roi7

Also, for comparison, whole func BOLD will be used with ROI marked as BrainMask (sub-01_BrainMask_mask.nii.gz)

## Configuration

Key parameters in `config.py`:
- `TR = 1.5`: Repetition time
- `N_RUNS = 6`: Number of runs
- `N_COLORS = 8`: Color conditions
- `VOLS_TO_DROP = 4`: Volumes to discard at start

## Analysis Commands

Run the main analysis pipeline:
```python
from bh_anal import BHAnalysisPipeline
pipeline = BHAnalysisPipeline()

# Run specific stages
pipeline.run("design")
pipeline.run("deconv_glm")
pipeline.run("roi_build")
pipeline.run("extract_roi")
pipeline.run("forward_model")
pipeline.run("qc")
```

For HRF model comparison:
```python
exec(open('naive_analysis.py').read())
```

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