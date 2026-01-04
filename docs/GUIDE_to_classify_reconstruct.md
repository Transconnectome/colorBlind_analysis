# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) for below.
- Setup preprocessing settings
- Measure and summarize results of classification & reconstruction (leave-one-participant-out & leave-one-color-out) without feature selection (baseline)
- Try various options(ANOVA, RFE, PCA) for feature selection and find best config within/between them. 
- Try non-linear method for classification & reconstruction and compare with linear model
- When best setting for preprocessing, ROI, feature selection, model setting is made. Do 2nd-level analysis and find out
  (1) Common voxel activation for each color exist across participants
  (2) Each color has different tendency of common voxel activation
  (3) Whether such voxels can do classification, reconstruction by themselves
  (4) Whether (1) ~ (3) are different between CVD(08 ~ 10) and non-CVD(01~07)

## Settings
### **Environment Setup**

Before running any Python code, activate the nilearn conda environment:
```bash
conda activate nilearn
```

Most of the files are being ran in the remote server and directory named:
haba6030@node2:/scratch/connectome/haba6030/colorBlind
Also, most of the code is ran by using SLURM.
Therefore, for running a code to check it, suggest this procedure
(1) suggest code and sbatch modification -> (2) suggest scp CLI for uploading code -> (3) how to run code in the server -> (4) how to download from the server.

### **CRITICAL: Server Connection**

ALWAYS use `node2` for server connections:

```bash
# ✅ CORRECT - Upload files
scp file.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# ✅ CORRECT - Download files
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/results.txt ./

# ✅ CORRECT - SSH connection
ssh haba6030@node2

# ❌ WRONG - Do NOT use IP address
scp file.py haba6030@147.47.200.161:/scratch/...  # NEVER USE THIS
```

**Reason**: The server hostname `node2` is configured in SSH config and ensures correct node access.

### SLURM Configuration (CRITICAL)**

**All SBATCH files MUST include:**
```bash
#SBATCH --nodelist=node2  # ALWAYS specify node2
```

**NEVER include:**
```bash
#SBATCH --partition=normal  # DO NOT specify partition
```

### Subject Groups and Data Paths (CRITICAL - Updated 2025-12-12)

**Subject Groups:**
- **Non-CVD subjects (all)**: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06, sub-07 (7 subjects)
- **CVD subjects (all)**: sub-08, sub-09, sub-10 (3 subjects)

**Analyzable Subjects (as of 2025-12-12):**
- **Non-CVD (analyzable)**: sub-01, sub-02, sub-03, sub-05, sub-06, sub-07 (6 subjects)
- **CVD (analyzable)**: sub-08, sub-09, sub-10 (3 subjects)
- **Excluded from current analysis**: sub-04 (No BOLD signal at V1 atlas location - to be recovered in future)

**Note on sub-04**: ROI alignment diagnostic revealed V1 atlas location has zero BOLD signal across all timepoints. Unlike sub-03/09/10 where BOLD signal exists but was excluded by fMRIPrep functional brain mask, sub-04 has actual data zeros at V1 location. See `ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md` for details.

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

- **Analysis outputs**: `/scratch/connectome/haba6030/colorBlind/derivatives/`

## 1. Project Overview

This is a neuroimaging analysis project based on "final_IRB.pdf", modifying **Brouwer & Heeger (2009, J. Neurosci.)** color decoding pipeline. The project analyzes fMRI data to decode color information from visual cortex areas (V1-V4) using forward encoding models. 

For each step below, integrate the progress in a single md file to prevent too many md files. 
get and activate conda with : source ~/.bashrc

## 2. Analysis Guide
### Step 0: Preprocessing
- You are now an expert in Neuroimage preprocessing and neuro data analysis and decoding. Answer in korean even if I ask in English. 
- My current analysis in preprocessing are based on these standards, mainly focusing in voxel SNR, correlation and HRF consistency. Also, even though these metrics are bad, if  the classification or reconstruction (in both novel color or leave one run out), then I'll go with that option.

#### Criteria for evaluating settings
  - **Voxel SNR, correlation, HRF consistency 위주로 진행 계획 (Color 구분 + 안정성)**
      1. **Voxel-wise SNR: voxel의 color 표현 안정도**

          ```markdown
          signal = std(mean_amplitude_per_color) # Color 간 변동
          noise = mean(std_amplitude_per_color_across_runs) # Run 내 변동
          SNR = signal / noise
          ```

      2. **Voxel-wise amplitude의 Run-to-run correlation:**

          ```markdown
          각 run pair 간 amplitude pattern correlation
          - High correlation → 재현성 높음
          > 0.7: "✅ High reliability"
          > 0.5: "⚠ Moderate reliability"
          < 0.5: "🚨 Low reliability"
          ```

      3. **HRF variability & consistency: HRF의 대표성 및 run 간 안전성**

          ```markdown
          [Step 3] ROI average HRF : 개별 voxel과 얼마나 유사한가
          → mean(h_v for selected voxels)
          → numerical derivative
          ↓
          [Enhanced Analysis B] HRF variability: FIR ~ HRF
          → Correlation with ROI HRF
          → RMSE, representativeness

          HRF consistency: HRF for each run
          ```

      4. R² distribution: 각 FIR이 실제 voxel 반응을 얼마나 잘 설명하는가?
          - 활용 voxel 결정 시에만 활용

          ```markdown
          [Step 1] Voxel-wise FIR HRF estimation
          → color-ignored design matrix
          → h_v = pinv(X) @ y per voxel
          → r² 계산
          ```

      5. tSNR: 시간에 따른 각 voxel의 반응 수준 일정도
          - 데이터 품질 확인에 주요하나, 해당 분석에서는 큰 의미 없음

          ```markdown
          tSNR = mean(timeseries) / std(detrended_timeseries)

          예시:
          timeseries = [600, 610, 605, 615, 608, ...]
          mean = 610
          detrended = detrend([600, 610, 605, ...])
          std(detrended) = 15
          tSNR = 610 / 15 = 40.7
          ```

#### Summarization method
- For summarizing the result of various preprocessing setting, do as below 
1. Make a csv file for each subject - ROI pair, and comprehensive file consist of all pairs. Such CSV file should be saved in derivatives/systematic_review_sumamry

2. The result should be summarized in "SYSTEMATIC_PREPROCESSING_ANALYSIS.md" file. Not making additional md file!
  - Append the date of latest update below the date of document initialization. 
  - In 1. Per subject-ROI Results, suggest top-3 preprocessing setting for each major metric - classification accuraty, reconstruction error, SNR. They should be suggested as table which consist of Rank, Config_name, Config Details, value of classification accuraty, reconstruction error, SNR. 
  - Also, suggest top config setting for each metric right below the heading of subject-roi pair. 

3. In Cross-ROI and Cross-Subject Patterns, 
  - Preprocessing factor: suggest each preprocessing setting's effect based on the results.  
  - Performance Metric relationships: relationships btw metrics
  - Subject Difference: Compare within non-CVD (sub 01, 02, 05, 06, 07) and within CVD(sub 03, 04) and between those groups. 

4. Then, suggest a "common" preprocessing setting based on reconstruction error, classification accuracy, and SNR. Consider in the given order (reconstruction first), however, don't suggest if either of error or accuracy is below by-chance level (90-degree or 12.5%)

### Step 1: Check baseline result(classification & reconstruction) of chosen preprocessing setting
Check
  - Classification accuracy
  - Reconstruction visualization & accuracy (22.5, 45 degree based)
    - Leave-one-run-out
    - Leave-one-color-out

#### 1. Utility Functions (CRITICAL - 2025-11-29)
**To prevent code duplication errors and ensure consistency across feature selection methods**, common utility functions have been extracted to:

- `utils_color_decoding.py`

This file contains shared functions for **ANOVA, RFE, and PCA** feature selection analyses:

**Color space utilities**:
- `circular_diff_deg()`: Circular distance calculation for hue angles
- `lab2rgb_accurate()`: CIELab → RGB conversion
- `get_stimulus_color_rgb()`: Retrieve actual stimulus colors

**Forward encoding model (B&H 2009)**:
- `create_basis_functions()`: 6-channel basis functions (half-wave rectified squared sinusoids)
- `evaluate_reconstruction()`: Complete reconstruction pipeline with leave-one-run-out CV
- `diag_linear_predict()`: Diagonal LDA prediction

**Quality metrics**:
- `compute_voxel_snr()`: Voxel-wise SNR calculation (signal/noise ratio)

**Visualizations**:
- `visualize_circular_color_space()`: B&H 2009 Figure 6 style polar plots
- `visualize_selected_voxels_brain()`: Brain visualization with feature values

#### 2. Execution
Use `fir_reconstruction_BH2009_system_clean.py` with sbatch files which use different preprocessing settings. They are `run_all_subjects_baseline32.sbatch` and `run_all_subjects_baseline81.sbatch`. 
You can merge those sbatch files into one file to try them in parallel.

#### 3. Results
For each subject, ROI, preprocessing setting, summarize results for each methods. 

#### Notes
- **Data normalization**: `amplitudes_z.npy` files are **already z-scored** (per run-voxel pair across 8 colors, see `fir_reconstruction_BH2009_system_clean.py:1424`). **NO additional StandardScaler should be applied** during reconstruction to avoid duplicate normalization.

-  **When modifying reconstruction logic**: Update `utils_color_decoding.py` only - changes will automatically propagate to all feature selection methods.

### Step 2: Feature Selection
- Objective: Figure out the best feature selection method. 
    - Best 1: Best classification & reconstruction result (especially for non-CVD group)
    - Best 2: Shows significant impairment in CVD group compared to non-CVD

- Progress
  1. Try several preprocessing settings (ANOVA, RPE, PCA). Within each setting, check best config. 
    - ANOVA: `run_all_subjects_anova.sbatch` to run `feature_selection_anova.py`
    - RFE: `run_all_subjects_rfe.sbatch` to run `feature_selection_rfe.py`
    - PCA: `run_pca_selection.sbatch` to run `feature_selection_pca.py`

- Validation
To validate the choice btw PCA and voxel selection, we can do voxel-wise SNR measuring and check the distribution of such SNR. 
  
- **Report Results** 
The main metrics are 
- (1) Classification (2) Run Reconstruction (3) Novel color Reconstruction (4) SNR of selected voxels

Current two config setting of preprocessing are below
- (1) Config 81 : SM = 6, high-pass = 0.01, motion = cosine, Standardize = True
- (2) Config 32 : SM = 0, high-pass = 0.01, motion = cosine, Standardize = False
Therefore, each feature selection (ANOVA, RFE, PCA) results would be given for both configs.

The results of implementing each selection method should be as below. 
1. All results of selection should be in one md file "SYSTEMATIC_SELECTION_ANALYSIS.md"
    - Such file will include results from:
      - Individual level ANOVA, RFE, PCA
      - Group level ANOVA, RFE, PCA
2. For individual level, Summarize each method's results as a table consist of metrics in row and subject-voxel in column:
    - ANOVA based results: 
    |   | sub-01 V1 | Sub-01 V2 |...| sub-02 V1 | .... |
    |Classification|
    |Run Recon|
    |Color Recon|
    |SNR mean|
    - Before the table, explain the method and how it is implemented as a code. With directly quoting the code of python file. 
2. For group level, To be added...
3. Report the best classification & Reconstruction result for each subject. Insert the image file. If it doesn't exist, put pseudo-image file link for the user to insert
4. Compare with the result without selection method.
5. 위 분석 중 실패한 게 있다면, 실패함 표시 후 각주로 에러 이유를 간단히 작성해주세요. 

### Step 3. Group-level analysis
Across non-cvd participants (sub 01 ~ 07) make a common beta-map to find out common color-encoding voxels. 
  - With individaul & group level beta-map, try several feature selection (PCA, ANOVA based, RFE) to compress the large dimension consisting of several voxels in each ROI. 
  - Use the same file for feature selection with the previous step. 
  
#### 1. PCA
Assuming that information is spread across voxels, we would need to concatenate all participants & runs and conduct PCA. 
However, when validating the model, we would need to do PCA for each train set. 

    #### Example
    pca = PCA()
    pca.fit(X_train)
    X_pcatrain = pca.transform(X_train)
    pca.saveAs(..pickle)

    - Test에 학습된 차원 적용 for consistency
    X_pcaTest = pca.transform(X_test)

    - 학습 시 concatenate (PCA 시 필요할 것 - 공부해보기)
    train data = 
    concate(X_run1 ~ X_run6)
    concate(X_sub1run1 ~ X_sub5run6)

#### 2. ANOVA and RFE
To use ANOVA or RFE, assuming information is mainly in certain voxels. 
We would need to do group-level (2nd level) GLM and run ANOVA or RFE to choose common voxels to extract. 
When validating the model, we would need to choose which voxel to extract and extract it from the test data.

#### Important NOTE
Before all these group-level procedure, we must check whether they are in same MNI space, or whether we need to conduct non-linear warping. 


### Step 4: Formation of non-linear color reconstruction method
When defining the forwarding function f:

- Consider prediction performance on Non-CVD individuals.
- Consider performance differences between Non-CVD and CVD mappings.
- Consider whether the visualized channel space preserves consistent distance between colors (i.e., perceptual spacing).

Choose the model type (deep learning vs. linear matrix W) based on:

- Model performance
- Model complexity

For the forward model, applying **Brouwer & Heeger (2009, J. Neurosci.)** is an option, and using Machine-Learning or Deep-Learning to replicate brain's nonlinearlity is the other option. 

## Figures 
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

## File Outputs

Analysis creates:
- `derivatives/sub-{SUB_ID}/`: GLM results, ROI masks, extracted data
- Design matrices, beta maps, decoding accuracies
- Quality control figures and statistical summaries

## Systematic Preprocessing Review Analysis

**Primary document**: `SYSTEMATIC_PREPROCESSING_ANALYSIS.md`

This analysis systematically evaluated 144 preprocessing configurations (3 smoothing × 2 high-pass × 3 motion × 2 CompCor × 2 drift × 2 standardization) across 2 subjects and 4 ROIs (V1, V2, V3, hV4).

### Analysis Workflow

1. **Parse results from log files**:
   ```bash
   python parse_systematic_results.py
   ```
   - Input: `logs/systematic_review/*.out`
   - Output: `derivatives/systematic_review_summary/sub-{ID}_{ROI}_results.csv`

2. **Review comprehensive analysis**:
   - Read `SYSTEMATIC_PREPROCESSING_ANALYSIS.md` for:
     - Per subject-ROI results and baseline selection
     - Preprocessing factor effects
     - Feature selection methods (ANOVA, RFE)
     - ML classifier recommendations (SVM, Random Forest)

3. **Next steps** (implement in this order):
   - **Step 3**: Linear/RBF SVM classifier (Section 5.1)
   - **Step 4**: Random Forest classifier (Section 5.2)
