## Data collection
### Participants 

### fMRI experiment pipeline (First & Second)
Stimuli
Rapid Serial Visual Presentation(RSVP) task
Protocol

## Preprocessing 
### Spatial Normalizations
Ezbids, MNI space, MI coregistration

### Wang Atlas ROI definition (V1, V2, V3, hV4)
ROI definitions
Regions of Interest (ROI; V1, V2, V3, hV4) were defined using the Wang probabilistic atlas (Wang et al., 2015) in MNI space at 2mm resolution. Bilateral ROIs were thresholded at 50% atlas probability and intersected with each individual’s BOLD brain mask. Voxel counts varied across ROIs (V1: 655 +/- 214; V2: 451 +/- 145; V3: 103 +/- 29; hV4: 63 +/- 22; all mean +/- SD across subjects)

### FIR-based response estimation (two-stage GLM)
1st-level: voxel-wise FIR deconvolution (8 delays)
Voxel selection (top 50% by R²)
2nd-level: HRF + derivative amplitude estimation

### Within-subject procrustes alignment (orthogonal, no scaling)

### Quality Control


Supplementary - quality control
Registration quality was evaluated by computing the intersection between the Wang Atlas ROIs (V1, V2, V3, hV4) and the BOLD brain mask in MNI space. Across 10 subjects, mean ROI coverage was 84.3% (SD = 21.7%), and GLM valid ratio (percentage of ROI voxels with reliable stimulus-evoked responses) was 99.6%. We evaluated all subjects’ data suitable for downstream analysis, though sub-07 showed reduced coverage (30.8%) due to individual anatomical variability.

Supplementary - Voxel counts range

## Functional Alignment and shared representational space
### Shared Response Model (SRM, k-selection)
Cross subject alignment, K value for generalizability. 


### CVD projection (SVD-based)
Projection of CVD, Disparity

### Individual case analysis (Crawford & Howell)
Individual CVD case vs HC distribution — directly motivated by N=3 CVD

## Color decoding and voxel response prediction model
### Forward encoding model
Basis function design (6 half-wave rectified Gaussians, Brouwer & Heeger 2009)
- Feature space definition (basis) and mapping (W) from brouwer and heeger

Encoding (ridge-GCV, voxel weight matrix W)


Group prior construction (HC-mean A_g via SRM)


### Cross-Validation and Evaluation
LORO (run generalization — classification)
LOCO (color interpolation — novel color prediction)
LOSO (zero-shot transfer — group prior validity)

MAE
Voxel correction

### Group comparison (permutation tests)
Permutation,

## Behavioral-neural concordance

### Behavioral task pipeline
Pairwise Just Noticeable Difference(JND) task

### Color identifying task


## Behavioral-neural concordance

## Filter design
### Cone-gain model
### Fitting Criteria
Loss function & Validation
### Evaluation
- Permutation test


## Statistical Analysis

## References
