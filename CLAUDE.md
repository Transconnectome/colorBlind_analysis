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

## Data Structure

The project expects fMRIPrep preprocessed data in this structure:
- `output/pilot/sub-{SUB_ID}/func/`: fMRIPrep BOLD files
- `pilot/sub-{SUB_ID}/func/`: Event files (.tsv)
- `derivatives/sub-{SUB_ID}/`: Analysis outputs
- `ProbAtlas_v4/`: Wang et al. (2015) probabilistic visual area atlas

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