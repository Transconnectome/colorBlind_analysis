# README for Figures
## Storyline
methods → distortion exists (SRM) → distortion affects interpolation not discrimination (decoding) → neural distortion predicts behavior (JND) → filter corrects it

## Lists
### Methods
#### Fig1. Task, Stimuli, and Analysis Pipeline
- Fig1a. fMRI & behavioral Experiment Pipeline (Stimuli, task pipeline)
- Fig1b. ROI locations in inflated brain
- Fig1c. Pipeline overview: preprocessing → SRM alignment → encoding → decoding

#### Fig2. Encoding-Decoding model and Filter pipeline
- Fig2a. Encoding-Decoding pipeline with ForwardEncoding model
- Fig2b. Cone-shift based filter model pipeline

- SuppleFig. Description of computing Relative Difference Measure(RDM) 

### Results - SRM 
#### Fig3. SRM reveals distorted color geometry in CVD
- Fig3a. Baseline RDM matrix of HC group
- Fig3b. RDM significance Matrix sub-08 (V1, V2 and others in supple)
- Fig3c. RDM significance Matrix sub-09
- Fig3d. summary metric across ROIs

- Supple Table. validation, mean activation results, noise ceiling

### Results - Decoding
#### Fig4. Interpolation fails where distinguish succeds
- Fig4a. Barplot comparison of decoded color estimation in LORO task  between two groups
- Fig4b. Barplot comparison  of decoded color estimation in LOCO task between two groups

- Table. Model comparison (supple: validation)

### Results - Behavioral Task
#### Fig5. Match between Neural analysis and behavioral task results
- Fig5a. Summary of JND task in both HC group and individuals with CVD 
- Fig5b. Relationship between the results of behavioral task and previous analyses

### Results -  Prediction Model
#### Fig6. Voxel-response prediction results for synthetic data
- Fig6. Summary of group results in voxel-response prediction for LORO, LOCO task
- Table. Model comparison, permutation test

### Results - Filter optimization
#### Fig7. Cone-shift filter optimization
- Fig7a. Comparison between original and filtered color stimuli
- Fig7b. Comparison of SRM RDM results between original and filter condition
- Fig7c. Comparison of LOCO results between original and filter condition
- Fig7d. Comparison of behavioral task results between original and filter condition

## Style
- As a single paper style config
- Make it in a single file for each figure, for reproducibility and modifiability 