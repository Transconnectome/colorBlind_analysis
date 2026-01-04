# Group-Level Analysis Guide
**Color Decoding Group Analysis: HC Consistency & HC-CVD Comparison**

---

## Overview

This guide outlines systematic group-level analyses to answer three fundamental questions:

1. **HC Consistency**: Do healthy controls (HC) share a common neural color encoding system?
2. **HC-CVD Transfer**: Can HC's color decoding model generalize to color vision deficiency (CVD) subjects?
3. **HC-CVD Differences**: Where and how do HC and CVD groups differ in neural color representation?

**Critical Hypothesis**: If HC and CVD use the same **neural representation → behavioral color mapping** (same voxels + same W matrix), then a color adjustment filter designed from HC patterns can correct CVD's behavioral deficits.

---

## Sample Characteristics

### Subjects
- **HC (Healthy Controls)**: sub-01, 02, 03, 05, 06, 07 (N=6)
  - Excluded: sub-04 (no BOLD signal at V1)
- **CVD (Color Vision Deficiency)**: sub-08, 09, 10 (N=3)
  - Type: Red-green color blindness (protanopia/deuteranopia)

### Statistical Power Considerations
⚠️ **Small sample size** (HC=6, CVD=3) limits confirmatory inference
- This is an **exploratory/pilot analysis**
- Focus on effect sizes and consistency patterns
- Results will guide future larger studies and filter design

---

## Preprocessing Configuration

**All analyses use a single, consistent preprocessing configuration:**

- **Config**: `anova_config32_determin`
- **Location**: `derivatives/BH2009_deoblique_v2/baseline32_deob_determin/`
- **Dataset**: `deoblique_v2` (fieldmap applied, improved registration)
- **Feature Selection**: Individual optimal K (from baseline analysis)
- **ROIs**: V1, V2, V3, hV4 (analyzed separately first)

**Rationale**: Consistent preprocessing eliminates confounds when comparing across subjects and groups.

---

## Phase 1: HC Consistency Analysis

**Goal**: Establish whether HC subjects share common neural color encoding mechanisms.

### 1A. Voxel Overlap Analysis

**Question**: Do HC subjects use anatomically consistent voxels for color encoding?

**Method**:
```
For each ROI (V1, V2, V3, hV4):
  1. Extract each subject's optimal K voxels (from baseline)
     - Based on individual feature selection (ANOVA F-test)
  2. Compute pairwise Jaccard index:
     J(sub_i, sub_j) = |voxels_i ∩ voxels_j| / |voxels_i ∪ voxels_j|
  3. Create 6×6 overlap matrix
  4. Define:
     - Common voxels = intersection of all 6 subjects
     - Union voxels = union of all 6 subjects
```

**Expected Outputs**:
```
derivatives/group_level/baseline32_deob_determin/{ROI}/voxel_overlap/
├── jaccard_matrix.csv              # 6×6 pairwise overlap
├── jaccard_heatmap.png
├── common_voxels_mask.nii.gz       # Intersection
├── common_voxels_indices.npy
├── union_voxels_mask.nii.gz        # Union
├── overlap_statistics.txt
└── voxel_locations_mni.png         # Scatter plot in MNI space
```

**Interpretation**:
- High Jaccard (>0.5): Strong anatomical consistency
- Low Jaccard (<0.3): High inter-subject variability
- Expected: V1 > V2 > V3 > hV4 (hierarchical decrease)

---

### 1B. Representational Similarity Analysis (RSA)

**Question**: Do HC subjects have similar color representation patterns (even if using different voxels)?

**Method**:
```
For common voxels (intersection from 1A):
  1. Extract amplitudes_z for each subject
     - Shape: (n_runs, n_colors=8, n_common_voxels)
  2. Compute Representational Dissimilarity Matrix (RDM) per subject:
     - Average across runs: (n_colors, n_voxels)
     - RDM[i,j] = 1 - Spearman_corr(beta_color_i, beta_color_j)
       across voxels
     - Shape: (8, 8) per subject
  3. Compare RDMs across subjects:
     - Spearman correlation: corr(RDM_sub_i, RDM_sub_j)
     - Mantel test for significance
  4. Average RDM across all HC subjects (group-level RDM)
```

**Expected Outputs**:
```
derivatives/group_level/baseline32_deob_determin/{ROI}/rsa/
├── rdm_per_subject.npz             # 6 RDMs (8×8 each)
├── rdm_similarity_matrix.csv       # 6×6 inter-subject correlation
├── rdm_similarity_heatmap.png
├── group_average_rdm.png           # Mean RDM
├── rdm_visualization_grid.png      # All 6 RDMs side-by-side
└── mantel_test_results.txt
```

**Interpretation**:
- High RDM correlation: Similar representational geometry
- Cluster analysis: Do some HC subjects form sub-groups?

---

### 1C. Cross-Subject Decoding (Leave-One-Subject-Out) ⭐⭐ **PRIORITY 1**

**Question**: Can a decoder trained on some HC subjects accurately decode color from other HC subjects?

**Critical Hypothesis**: If HC share common encoding, then:
1. Same voxels should be informative across subjects
2. Same W matrix (channel weights) should generalize

**Method**:
```
Leave-One-Subject-Out Cross-Validation:

For each test_subject in [sub-01, 02, 03, 05, 06, 07]:

  # Training phase (on 5 other HC subjects)
  1. Select voxels:
     - Option A: Union of training subjects' top-K voxels
     - Option B: Intersection (more conservative)
     - Recommended: Union (maximizes information)

  2. Pool training data:
     - amplitudes_z from 5 subjects
     - Shape: (5 subjects × ~8 runs × 8 colors, n_union_voxels)
     - Total: ~40 runs × 8 colors = 320 training samples

  3. Train 6-channel forward encoding model:
     - Build basis set: 6 channels (0°, 60°, 120°, 180°, 240°, 300°)
     - Learn W matrix: (n_voxels, 6 channels)
     - W = pinv(C_train) @ amplitudes_train
       where C_train = predicted channel responses (320, 6)

  # Testing phase (on held-out subject)
  4. Extract test subject's amplitudes at SAME voxels
     - Important: Use exact same voxel indices

  5. Reconstruction with SAME W matrix:
     - C_pred = amplitudes_test @ W
     - Reconstruct hue from C_pred

  6. Evaluate:
     - Classification accuracy (8-way)
     - Reconstruction error (circular mean absolute error)
     - Per-color confusion matrix

# Baseline comparison
For same test_subject:
  - Train decoder on own data (within-subject)
  - Compare: ACC_within vs ACC_cross_subject
  - Metric: ΔACC = ACC_within - ACC_cross_subject
```

**Expected Outputs**:
```
derivatives/group_level/baseline32_deob_determin/{ROI}/cross_subject/
├── loso_performance.csv
│   Columns: test_subject, train_subjects, n_voxels_used,
│            ACC_cross, ACC_within, ΔACC,
│            MSE_cross, MSE_within, ΔMSE
├── loso_summary_statistics.txt
├── w_matrices/
│   ├── fold1_train_sub02-03-05-06-07.npy  # W matrix for fold 1
│   ├── fold2_train_sub01-03-05-06-07.npy  # etc.
│   └── ...
├── figures/
│   ├── cross_vs_within_accuracy.png       # Bar plot
│   ├── cross_vs_within_mse.png
│   ├── per_fold_confusion_matrix.png      # 6 panels
│   ├── per_fold_circular_reconstruction.png
│   └── voxel_usage_across_folds.png       # Which voxels selected
└── performance_breakdown/
    ├── fold1_detailed_results.npz
    └── ...
```

**Interpretation**:
- **ΔACC < 10%**: Strong generalization → HC share common system
- **ΔACC > 20%**: Weak generalization → Subject-specific encoding
- **Per-color analysis**: Which colors generalize well vs. poorly?

**Code Reuse**:
- Decoder from `fir_reconstruction_BH2009_system_clean.py`
- Data loading from `group_level_common_voxels.py`

---

## Phase 2: HC-CVD Comparison

**Goal**: Test whether HC's color decoding model can be applied to CVD subjects.

### 2A. Voxel Domain Differences

**Question**: Do HC and CVD differ in voxel selection (number, location, overlap)?

**Method**:
```
1. Optimal K comparison:
   - Extract each subject's optimal K (from baseline)
   - HC: mean ± std across 6 subjects
   - CVD: mean ± std across 3 subjects
   - Two-sample t-test: K_HC vs K_CVD

2. Voxel overlap (HC common vs CVD individual):
   - HC_common: intersection from Phase 1A
   - For each CVD subject:
     - Jaccard(HC_common, CVD_individual_top_K)

3. Anatomical location (center of mass):
   - Compute center of mass in MNI coordinates
   - Distance: ||COM_HC - COM_CVD||

4. Spatial distribution:
   - Variance of voxel coordinates
   - Are CVD voxels more dispersed?
```

**Expected Outputs**:
```
derivatives/group_level/baseline32_deob_determin/{ROI}/voxel_comparison/
├── optimal_k_comparison.csv
│   Columns: subject, group, optimal_k, accuracy_at_optimal_k
├── optimal_k_boxplot.png           # HC vs CVD
├── voxel_overlap_hc_cvd.csv
│   Columns: cvd_subject, jaccard_with_hc_common,
│            center_distance_mm, spatial_variance
├── voxel_locations_mni_overlay.png  # HC (blue) vs CVD (red)
└── statistics_summary.txt
```

**Interpretation**:
- If K_CVD > K_HC: CVD needs more voxels for same accuracy (noisier representation?)
- If Jaccard < 0.3: Anatomical divergence
- If center distance > 5mm: Different cortical regions engaged

---

### 2B. Decoder Transfer (HC→CVD) ⭐⭐ **PRIORITY 2**

**Question**: Can HC's decoder (voxels + W matrix) accurately decode CVD's neural activity?

**Critical Test**: This directly tests whether HC and CVD use the **same neural→color mapping**.

**Method**:
```
# Step 1: Train HC group decoder
1. Pool ALL 6 HC subjects' data
   - Voxels: HC common voxels (intersection or union)
   - amplitudes_z: (6 subjects × ~8 runs × 8 colors, n_voxels)
   - Total: ~48 runs × 8 colors = 384 training samples

2. Train 6-channel forward encoding model:
   - Build basis set C (384 samples, 6 channels)
   - Learn W_HC: (n_voxels, 6 channels)
   - W_HC = pinv(C_train) @ amplitudes_HC

# Step 2: Test on CVD subjects
For each CVD subject (sub-08, 09, 10):

  3. Extract CVD's amplitudes at SAME voxel locations:
     - Critical: Use HC voxel indices in CVD's data
     - Check: Do these voxels exist in CVD's ROI mask?
     - If missing: Report and use nearest neighbors

  4. Reconstruction using HC's W_HC matrix:
     - C_pred = amplitudes_CVD @ W_HC
     - Reconstruct hue from C_pred
     - NO retraining, NO voxel reselection

  5. Compare to CVD's individual decoder:
     - Train on CVD's own data (within-subject)
     - W_CVD from CVD's optimal voxels

  6. Metrics:
     - ΔACC_CVD = ACC_HC_decoder - ACC_CVD_individual
     - ΔMSE_CVD = MSE_HC_decoder - MSE_CVD_individual
     - Per-color breakdown: Which colors fail?

# Step 3: Test HC K on CVD (generalization of voxel number)
7. Force CVD to use K_HC_mean voxels:
   - Select top K_HC_mean from CVD by F-value
   - Train CVD decoder with this K
   - Compare to CVD's individual optimal K

# Step 4: Identify failure modes
8. Per-color error analysis:
   - Which colors have highest reconstruction error?
   - Hypothesis: Red-green axis (90° vs 270°) most affected
9. Confusion pattern:
   - Which colors are confused (e.g., red→green)?
```

**Expected Outputs**:
```
derivatives/group_level/baseline32_deob_determin/{ROI}/decoder_transfer/
├── hc_group_decoder/
│   ├── w_matrix_hc.npy              # HC group W matrix
│   ├── voxel_indices_hc.npy         # Which voxels used
│   ├── training_performance_hc.csv
│   └── channel_weights_visualization.png
│
├── cvd_transfer_results/
│   ├── transfer_performance.csv
│   │   Columns: cvd_subject,
│   │            ACC_hc_decoder, ACC_cvd_individual, ΔACC,
│   │            MSE_hc_decoder, MSE_cvd_individual, ΔMSE,
│   │            n_voxels_hc, n_voxels_cvd_optimal
│   ├── per_subject_breakdown/
│   │   ├── sub08_confusion_hc_decoder.png
│   │   ├── sub08_confusion_cvd_decoder.png
│   │   ├── sub08_circular_reconstruction_hc.png
│   │   ├── sub08_circular_reconstruction_cvd.png
│   │   └── ... (repeat for sub09, sub10)
│   └── per_color_error_hc_vs_cvd.png
│
├── k_generalization/
│   ├── k_forced_results.csv
│   │   Columns: cvd_subject, k_hc_mean, k_cvd_optimal,
│   │            ACC_at_k_hc, ACC_at_k_optimal, ΔACC
│   └── k_sensitivity_curves.png     # Accuracy vs K
│
└── failure_analysis/
    ├── red_green_axis_error.png     # 90° vs 270° specifically
    ├── error_vs_hue.png             # Circular error plot
    └── voxel_mismatch_report.txt    # Missing voxels in CVD
```

**Interpretation**:
- **If ΔACC_CVD < 10%**: HC decoder works for CVD → **Same mapping!**
  - Filter design is feasible: adjust colors to match HC representation
- **If ΔACC_CVD > 30%**: HC decoder fails on CVD → **Different mapping**
  - Need CVD-specific filter, or mapping is fundamentally different
- **Red-green axis**: Expected to show largest errors in CVD

**Code Reuse**:
- HC decoder from Phase 1C
- CVD data loading from baseline results

---

### 2C. Beta Amplitude Differences

**Question**: In common voxels, do HC and CVD show different activation magnitudes?

**Method**:
```
1. Define common voxels:
   - HC_common (from Phase 1A) ∩ CVD_individual
   - Or: Use HC_common and extract from CVD

2. Extract beta amplitudes (z-scored):
   - HC: (6 subjects, 8 colors, n_common_voxels)
   - CVD: (3 subjects, 8 colors, n_common_voxels)
   - Average across runs

3. Statistical tests:
   - Per-color t-test: t-test(HC, CVD) for each color
   - Per-voxel ANOVA: Which voxels differ most?
   - Variance test: F-test(var_HC, var_CVD)

4. Effect size:
   - Cohen's d per color
   - Which colors show largest differences?
```

**Expected Outputs**:
```
derivatives/group_level/baseline32_deob_determin/{ROI}/beta_comparison/
├── beta_amplitude_stats.csv
│   Columns: color, mean_hc, std_hc, mean_cvd, std_cvd,
│            t_value, p_value, cohens_d
├── beta_heatmap_hc_vs_cvd.png      # Colors × Subjects
├── per_color_boxplots.png          # HC vs CVD per color
├── variance_comparison.png
└── per_voxel_anova_results.npz
```

---

## Phase 3: 2nd-Level GLM (Random Effects Model)

**Goal**: Estimate group-level parameters using proper hierarchical modeling.

**Challenge**: Small sample (N=6) is suboptimal for random effects, but implementable.

### Method 1: Nilearn Second-Level Model

```python
from nilearn.glm.second_level import SecondLevelModel

# Step 1: Prepare first-level contrast maps
For each subject:
  - Create contrast maps: beta_color_i vs baseline (8 maps per subject)
  - Save as NIfTI: sub-XX_color_i_beta.nii.gz

# Step 2: Second-level GLM
design_matrix = pd.DataFrame({
    'subject': [1, 1, ..., 2, 2, ..., 6, 6, ...],  # Subject ID
    'color': [0, 1, ..., 0, 1, ..., 0, 1, ...]      # Color ID
})

second_level_model = SecondLevelModel()
second_level_model.fit(
    second_level_input=contrast_maps,  # List of NIfTI files
    design_matrix=design_matrix
)

# Step 3: Group-level contrasts
- Color 1 vs baseline (across all subjects)
- Color i vs Color j (pairwise)
- Group-level activation map (FDR corrected)

# Step 4: Extract group-level betas
- Group beta map per color (8 maps)
- Use for reconstruction on CVD
```

### Method 2: Mixed-Effects Model (Statsmodels)

```python
from statsmodels.regression.mixed_linear_model import MixedLM

# Step 1: Prepare long-format data
For each voxel:
  - Stack all subjects' betas: (6 subjects × 8 colors = 48 rows)
  - Columns: subject_id, color_id, beta_value

# Step 2: Fit mixed model per voxel
For voxel_idx in range(n_voxels):
    data = prepare_voxel_data(voxel_idx)

    # Fixed effect: color (categorical)
    # Random effect: subject (intercept + slope)
    model = MixedLM.from_formula(
        'beta_value ~ C(color_id)',
        data=data,
        groups=data['subject_id'],
        re_formula='1'  # Random intercept
    )
    result = model.fit()

    # Extract group-level coefficients
    group_betas[voxel_idx, :] = result.fe_params

# Step 3: Use group_betas for reconstruction
- Same as individual betas but from group model
```

### Data Augmentation Strategy (If Needed)

**⚠️ Use with caution - statistically questionable but exploratory**

```
If model fitting fails due to small N:

Option A: Bootstrap resampling
  - Resample subjects with replacement
  - Create 100 bootstrap samples
  - Estimate group betas from bootstrap distribution
  - Caveat: Inflates degrees of freedom artificially

Option B: Run concatenation (within-subject)
  - Treat each run as pseudo-subject
  - 6 subjects × 8 runs = 48 "subjects"
  - Caveat: Violates independence assumption
  - Use only if Method 1/2 completely fail

Option C: Bayesian hierarchical model
  - Use PyMC or Stan
  - Prior on subject-level variance
  - Can handle small N better than frequentist
```

### Expected Outputs

```
derivatives/group_level/baseline32_deob_determin/{ROI}/second_level_glm/
├── method/
│   └── nilearn/  or  statsmodels/  or  bayesian/
│
├── group_level_betas/
│   ├── group_beta_color1.nii.gz    # 8 beta maps
│   ├── ...
│   └── group_beta_color8.nii.gz
│
├── group_statistics/
│   ├── t_maps_color_vs_baseline.nii.gz
│   ├── f_map_color_effect.nii.gz
│   ├── fdr_corrected_mask.nii.gz
│   └── group_anova_results.csv
│
├── group_decoder/
│   ├── w_matrix_group_glm.npy       # From group betas
│   └── performance_group_decoder.csv
│
├── comparison_with_phase1c/
│   ├── group_glm_vs_pooled_performance.csv
│   │   Comparing: 2nd-level GLM vs simple pooling (Phase 1C)
│   └── method_comparison.png
│
└── model_diagnostics/
    ├── residual_plots.png
    ├── random_effects_estimates.csv  # Subject-level deviations
    └── convergence_warnings.txt
```

### Interpretation

**Compare 3 approaches**:
1. **Pooled data** (Phase 1C): Treats all HC runs equally
2. **2nd-level GLM** (Phase 3): Accounts for subject-level variance
3. **Individual average** (Phase 1B): Each subject weighted equally

**Expected**:
- If subject variance is small: All 3 methods similar
- If subject variance is large: GLM provides better group estimates
- GLM should give more conservative (wider) confidence intervals

**Validation**:
- Test group decoder on held-out HC (leave-one-subject-out)
- Compare to Phase 1C results
- If similar: Pooling was sufficient
- If better: Random effects improved generalization

---

## Code Organization

### Directory Structure

```
colorBlind_analysis/
├── analysis/
│   ├── __init__.py
│   ├── group_level/
│   │   ├── __init__.py
│   │   │
│   │   # Phase 1: HC Consistency
│   │   ├── phase1_voxel_overlap.py          # 1A
│   │   ├── phase1_rsa.py                    # 1B
│   │   ├── phase1_cross_subject_loso.py     # 1C ⭐⭐ PRIORITY 1
│   │   │
│   │   # Phase 2: HC-CVD Comparison
│   │   ├── phase2_voxel_comparison.py       # 2A
│   │   ├── phase2_decoder_transfer.py       # 2B ⭐⭐ PRIORITY 2
│   │   ├── phase2_beta_comparison.py        # 2C
│   │   │
│   │   # Phase 3: 2nd-Level GLM
│   │   ├── phase3_second_level_glm.py       # Option C
│   │   │
│   │   # Utilities
│   │   └── utils_group.py                   # Shared functions
│   │
│   └── utils/
│       ├── data_loader.py                   # Extract from existing code
│       └── decoder_utils.py                 # Reusable decoder class
│
├── run_phase1_analysis.sbatch               # SLURM: Phase 1
├── run_phase2_analysis.sbatch               # SLURM: Phase 2
├── run_phase3_analysis.sbatch               # SLURM: Phase 3
│
└── docs/
    ├── GUIDE_GROUP_LEVEL.md                 # This file
    └── GUIDE_GroupLevel.md                  # Original (keep for reference)
```

### Shared Utilities (`utils_group.py`)

**Extract from existing code**:
```python
# From group_level_common_voxels.py
- load_subject_amplitudes()
- load_all_subjects()
- validate_group_data_consistency()

# From group_level_anova_selection.py
- compute_anova_f_values()

# From fir_reconstruction_BH2009_system_clean.py
- build_6channel_basis_set()
- train_encoding_model()
- reconstruct_hue()
- evaluate_reconstruction()
```

### Decoder Class (`decoder_utils.py`)

```python
class ColorDecoder:
    """
    6-channel forward encoding model for color reconstruction

    Reusable across:
    - Within-subject decoding
    - Cross-subject decoding (Phase 1C)
    - HC→CVD transfer (Phase 2B)
    - 2nd-level GLM decoder (Phase 3)
    """

    def __init__(self, n_channels=6):
        self.n_channels = n_channels
        self.W = None  # Weight matrix (n_voxels, n_channels)
        self.voxel_indices = None

    def train(self, amplitudes_train, hues_train):
        """
        Train encoding model

        Args:
            amplitudes_train: (n_samples, n_voxels) z-scored beta
            hues_train: (n_samples,) stimulus hues in degrees

        Returns:
            self.W: (n_voxels, n_channels) weight matrix
        """
        # Build channel basis set
        C_train = self.build_channel_responses(hues_train)

        # Learn weights: W = pinv(C_train) @ amplitudes_train
        self.W = np.linalg.pinv(C_train.T) @ amplitudes_train.T

        return self.W

    def predict(self, amplitudes_test):
        """
        Reconstruct hue from neural activity

        Args:
            amplitudes_test: (n_samples, n_voxels)

        Returns:
            hues_pred: (n_samples,) reconstructed hues
        """
        # Estimate channel responses: C_pred = amplitudes @ W
        C_pred = amplitudes_test @ self.W.T

        # Reconstruct hue from channel profile
        hues_pred = self.reconstruct_hue_from_channels(C_pred)

        return hues_pred

    def transfer_to(self, amplitudes_new, voxel_indices_new):
        """
        Apply trained W matrix to new data

        Critical for Phase 1C and 2B:
        - Same voxels must be used
        - Same W matrix applied

        Args:
            amplitudes_new: (n_samples, n_voxels_all)
            voxel_indices_new: Indices to extract (must match training)

        Returns:
            hues_pred: (n_samples,) reconstructed hues
        """
        # Extract same voxels
        amplitudes_selected = amplitudes_new[:, voxel_indices_new]

        # Apply trained W
        return self.predict(amplitudes_selected)
```

---

## Implementation Priority

**⚡ AGGRESSIVE TIMELINE: 2 DAYS TOTAL**

**Rationale**: Validate assumptions (Phase 1A, 1B) → Test generalization (Phase 1C) → Build group model (Phase 3) → Test on CVD (Phase 2B)

---

### Day 1: Assumptions + Cross-Subject Decoding

**Morning (3h): Setup + Phase 1A**
- 09:00-10:00: Create directory structure + extract utils
- 10:00-11:00: Implement Phase 1A (Voxel Overlap)
- 11:00-12:00: Run Phase 1A (4 ROIs in parallel on server)
  - Quick check: Jaccard index

**Afternoon (4h): Phase 1B + Decision**
- 13:00-15:00: Implement Phase 1B (RSA - RDM + Mantel test)
- 15:00-16:00: Run Phase 1B (4 ROIs in parallel)
  - Quick check: RDM correlation
- 16:00-17:00: **Decision Point**: Proceed if Phase 1A, 1B show consistency

**Evening (5h): Phase 1C**
- 17:00-19:00: Implement Phase 1C (LOSO cross-subject decoding)
- 19:00-22:00: Run Phase 1C (4 ROIs, **overnight jobs**)
  - V1, V2: ~2h each
  - V3, hV4: ~1h each

**Overnight**: Phase 1C running (~6h total)

---

### Day 2: GLM + CVD Application

**Morning (3h): Phase 1C Analysis + Phase 3**
- 09:00-10:00: Analyze Phase 1C results (ΔACC, visualizations)
- 10:00-11:00: Implement Phase 3 (2nd-level GLM - nilearn only)
- 11:00-12:00: Run Phase 3 (4 ROIs in parallel)

**Afternoon (4h): Phase 3 Analysis + Phase 2B**
- 13:00-14:00: Analyze Phase 3 (group betas, compare with Phase 1C)
- 14:00-16:00: Implement Phase 2B (HC→CVD decoder transfer)
- 16:00-17:00: Run Phase 2B (4 ROIs, 3 CVD subjects)

**Evening (3h): Results + Report**
- 17:00-19:00: Analyze all results
  - HC consistency (1A, 1B)
  - Cross-subject generalization (1C)
  - Group model (3)
  - HC→CVD transfer (2B)
- 19:00-20:00: Summary report + next steps

---

### Parallelization Strategy

**Run 4 ROIs simultaneously for maximum speed:**

```bash
# Day 1 Morning: Phase 1A
sbatch run_phase1a.sbatch --roi V1 &
sbatch run_phase1a.sbatch --roi V2 &
sbatch run_phase1a.sbatch --roi V3 &
sbatch run_phase1a.sbatch --roi hV4 &

# Day 1 Afternoon: Phase 1B
sbatch run_phase1b.sbatch --roi V1 &
sbatch run_phase1b.sbatch --roi V2 &
sbatch run_phase1b.sbatch --roi V3 &
sbatch run_phase1b.sbatch --roi hV4 &

# Day 1 Evening: Phase 1C (overnight)
sbatch run_phase1c.sbatch --roi V1 --time 4:00:00 &
sbatch run_phase1c.sbatch --roi V2 --time 4:00:00 &
sbatch run_phase1c.sbatch --roi V3 --time 2:00:00 &
sbatch run_phase1c.sbatch --roi hV4 --time 2:00:00 &

# Day 2 Morning: Phase 3
sbatch run_phase3_glm.sbatch --roi V1 &
sbatch run_phase3_glm.sbatch --roi V2 &
sbatch run_phase3_glm.sbatch --roi V3 &
sbatch run_phase3_glm.sbatch --roi hV4 &

# Day 2 Afternoon: Phase 2B
sbatch run_phase2b.sbatch --roi V1 &
sbatch run_phase2b.sbatch --roi V2 &
sbatch run_phase2b.sbatch --roi V3 &
sbatch run_phase2b.sbatch --roi hV4 &
```

---

### Simplified Scope (2-Day Focus)

**Core Analyses (MUST DO)**:
- ✅ Phase 1A: Voxel Overlap
- ✅ Phase 1B: RSA
- ✅ Phase 1C: Cross-Subject Decoding
- ✅ Phase 3: 2nd-Level GLM (nilearn only)
- ✅ Phase 2B: Decoder Transfer (HC→CVD)

**Deferred (Optional)**:
- ⏸️ Phase 2A: Voxel Comparison (can derive from 1A + 2B)
- ⏸️ Phase 2C: Beta Comparison (supplementary)
- ⏸️ Phase 3: Alternative GLM methods (statsmodels, Bayesian)
- ⏸️ Extensive visualizations (focus on key metrics)

**Deliverables (End of Day 2)**:
1. HC consistency metrics (Jaccard, RDM correlation)
2. Cross-subject ΔACC (does HC model generalize?)
3. Group decoder (2nd-level GLM betas + W matrix)
4. HC→CVD transfer results (ΔACC_CVD, failure modes)
5. Summary report answering:
   - Do HC share common encoding?
   - Does HC model work on CVD?
   - Is filter design feasible?

---

### Critical Success Factors

**To finish in 2 days**:
1. ⚡ **Reuse code maximally**: Extract decoder from existing files
2. 🔧 **Minimal visualization**: Focus on metrics, not pretty plots
3. 🚀 **Parallel execution**: All 4 ROIs simultaneously
4. 📊 **Quick checks**: Don't wait for full analysis between phases
5. 🌙 **Overnight runs**: Phase 1C (longest) runs while sleeping
6. 🎯 **Skip optionals**: No Phase 2A, 2C, alternative GLM methods

---

## Expected Outcomes

### Success Criteria (HC Consistency)

**Strong Evidence**:
- Phase 1A: Jaccard index > 0.5 (V1), > 0.4 (V2-hV4)
- Phase 1B: RDM correlation > 0.7 across subjects
- Phase 1C: ΔACC < 10% (cross-subject vs within-subject)

**Moderate Evidence**:
- Phase 1A: Jaccard 0.3-0.5
- Phase 1B: RDM correlation 0.5-0.7
- Phase 1C: ΔACC 10-20%

**Weak Evidence** (subject-specific encoding):
- Phase 1A: Jaccard < 0.3
- Phase 1B: RDM correlation < 0.5
- Phase 1C: ΔACC > 20%

### Success Criteria (HC→CVD Transfer)

**Filter Design Feasible** (same mapping):
- Phase 2B: ΔACC_CVD < 15% (HC decoder on CVD vs CVD individual)
- Red-green axis error < 30° (circular MAE)
- Phase 2A: Jaccard(HC, CVD) > 0.4

**Filter Design Challenging**:
- Phase 2B: ΔACC_CVD 15-30%
- Red-green axis error 30-60°
- Requires mapping correction + color adjustment

**Different Mapping** (filter may not work):
- Phase 2B: ΔACC_CVD > 30%
- Red-green axis error > 60°
- Phase 2A: Jaccard(HC, CVD) < 0.2

---

## Next Steps After Analysis

### If HC Model Generalizes to CVD

**Filter Design Strategy**:
1. Use HC group W matrix as target mapping
2. For each CVD subject:
   - Measure their actual W_CVD
   - Compute transformation: T = W_HC @ pinv(W_CVD)
   - Design filter: Color_adjusted = T @ Color_input
3. Test: Does adjusted color improve CVD's behavioral discrimination?

### If HC Model Does NOT Generalize

**Alternative Approaches**:
1. CVD-specific filter:
   - Use CVD's own W_CVD
   - Enhance discriminability along red-green axis
2. Mapping correction + filter:
   - First: Train CVD neural response → match HC
   - Second: Apply color filter
3. Behavioral training:
   - If neural mapping is fundamentally different
   - Train CVD to use different decision boundaries

---

## Technical Notes

### Data Compatibility

**Critical Checks**:
1. **Voxel correspondence**:
   - All subjects must use same ROI atlas (ProbAtlas_v4)
   - Same MNI space (MNI152NLin2009cAsym)
   - Same resolution (2mm)

2. **Run numbers**:
   - Validate n_runs per subject (may vary)
   - Handle missing runs appropriately

3. **Preprocessing version**:
   - Ensure all use `anova_config32_determin`
   - Check: `derivatives/BH2009_deoblique_v2/baseline32_deob_determin/`

### Computational Requirements

**Phase 1C & 2B** (most intensive):
- Memory: ~16GB per ROI
- Time: ~2-4 hours per ROI (V1 longest)
- Storage: ~10GB per ROI for all outputs

**Recommended SLURM**:
```bash
#SBATCH --nodelist=node2
#SBATCH --mem=32G
#SBATCH --time=6:00:00
#SBATCH --cpus-per-task=4
```

---

## References

**Methods**:
- Brouwer & Heeger (2009, J. Neurosci.): 6-channel forward encoding model
- Kriegeskorte et al. (2008, Frontiers): Representational Similarity Analysis
- Mumford & Nichols (2009, NeuroImage): Group-level GLM

**Validation**:
- Compare results with OHBM abstract findings
- Expected: HC and CVD both show color decoding (confirmed)
- New question: **Same mechanism** or **different mechanisms**?

---

**Document Version**: 1.0
**Date**: 2025-12-16
**Author**: Claude Code (with user guidance)
**Status**: Ready for implementation
