# Phase 2: SRM Between-Subject Group Comparison

**Research Question**: Do CVD subjects show systematically different color representations from HC in SRM shared space?

**Status**: Analysis complete + Robustness validated ✅
**Canonical script**: `rerun_loo_consistent.py`

---

## Overview

This phase uses **Shared Response Model (SRM)** to align subjects into a common low-dimensional space and compare HC (n=7) vs CVD (n=3) color representations.

**Key Methodology**:
- **HC-only SRM**: Trained on 7 HC subjects; CVD projected via SVD
- **LOO-consistent disparity**: HC sub-i vs mean of other 6 HC; CVD vs same LOO references
- **Three bias fixes**: (1) HC-only training, (2) LOO for HC, (3) same LOO refs for CVD
- **Individual CVD tests**: Crawford & Howell (1998) modified t-test
- **Robustness**: 3 independent metrics (A3/A4/A5) triangulate SRM results
- **SRM components (k)**: V1=4, V2=4, V3=3, hV4=3 (validated via mean rank aggregation)

---

## Key Findings (Updated 2026-02-18)

### Main Results: HC-CVD Group Comparison (LOO-consistent)

| ROI | HC LOO [95% CI] | CVD LOO [95% CI] | Separation [95% CI] | p (perm) | g [95% CI] |
|-----|----------------|-----------------|---------------------|----------|------------|
| **V1** | 0.453 [0.397, 0.512] | 0.590 [0.457, 0.761] | 0.137 [−0.005, 0.301] | **0.062** | 1.16 [−0.06, 3.98] |
| **V2** | 0.486 [0.418, 0.559] | 0.606 [0.505, 0.718] | 0.120 [0.001, 0.244] | **0.075** | 1.04 [0.02, 3.18] |
| V3 | 0.540 [0.476, 0.608] | 0.564 [0.404, 0.738] | 0.023 [−0.137, 0.194] | 0.395 | 0.18 |
| hV4 | 0.700 [0.617, 0.796] | 0.677 [0.444, 0.855] | −0.023 [−0.244, 0.172] | 0.559 | −0.14 |

### Individual CVD Tests (Crawford & Howell 1998)

| Subject | V1 (t, p) | V2 (t, p) | V3 (t, p) | hV4 (t, p) |
|---------|-----------|-----------|-----------|------------|
| **sub-09** | **t=3.5, p=0.007** | t=1.0, p=0.181 | t=0.1, p=0.466 | t=1.1, p=0.150 |
| **sub-08** | t=1.1, p=0.157 | **t=2.1, p=0.040** | t=1.9, p=0.052 | t=0.2, p=0.411 |
| sub-10 | t=0.0, p=0.483 | t=0.2, p=0.433 | t=−1.3, p=0.884 | t=−1.9, p=0.945 |

### LOSO Color-Dependency (CVD disparity depends on true color labels)

| ROI | CVD score p | CVD pairwise p | HC held-out p | Interpretation |
|-----|------------|---------------|--------------|----------------|
| V1 | 0.427 | 0.077 | 0.364 | Not color-specific |
| **V2** | **0.033** | **0.035** | 0.894 | **CVD color-dependent** |
| **V3** | **0.009** | **0.046** | 0.437 | **CVD color-dependent** |
| **hV4** | **0.028** | **0.031** | 0.325 | **CVD color-dependent** |

### Robustness Triangulation (A3/A4/A5)

| Metric | Method | Key result | Convergent validity (pooled) |
|--------|--------|------------|------------------------------|
| A4 Crossnobis | Native voxel space, SRM-independent | V1 p=0.051 | **r=0.486, p=0.001** |
| A5 PCA-only | Alternative alignment | Group ns | **r=0.742, p<0.001** |
| A5 PCA-CCA | Alternative alignment | Group ns | **r=0.472, p=0.002** |
| A3 VE (LOSO) | SRM reconstruction quality | CVD VE ≥ HC; V2 g=−1.68 | r=−0.246, ns |

**Interpretation**:
- Group-level effects trend but do not reach p<0.05 (n=3 CVD limitation)
- Individual CVD tests reveal region-specific dissociations: sub-09=V1, sub-08=V2
- CVD color-dependency confirmed via LOSO (V2/V3/hV4) — strongest evidence
- **Convergent validity is key**: SRM disparity correlates with crossnobis (r=0.486) and PCA distance (r=0.742), confirming SRM captures genuine neural differences, not alignment artifacts
- CVD VE ≥ HC = "strong signal, different structure" (not noisy, but anisotropic)

---

## Key Scripts

### A. Within-Subject Analysis (SRM vs Procrustes)

#### 1. `evaluate_srm_vs_procrustes.py`

**Purpose**: Core comparison of SRM vs Procrustes alignment

**Method**:
- Beta-based SRM: Average runs → (n_colors × n_voxels) per run
- Leave-one-run-out cross-validation
- Test k values: [2, 3, 4, 5, 6, 8] (constrained by n_colors=8)

**Metrics**:
- RDM correlation (Spearman)
- Decoding accuracy (LDA 8-way classification)
- Optimal k selection per ROI

**Output**:
```python
results/srm_evaluation/{TIMESTAMP}/
├── sub-{ID}_{ROI}_srm_results.json
└── sub-{ID}_{ROI}_srm_k_tuning.png
```

**Statistical Test**:
- Paired t-test (SRM vs Procrustes)
- Threshold: p<0.05 and improvement >5%

---

#### 2. `aggregate_srm_results.py`

**Purpose**: Aggregate individual results across subjects

**Functions**:
- Summarize by ROI (mean ± SD across subjects)
- Identify optimal k per ROI
- Generate recommendations (Use SRM / Use Procrustes)

**Output**:
```python
results/srm_evaluation/{TIMESTAMP}/
├── summary_by_roi.json
├── optimal_k_recommendations.json
└── summary_all_subjects.json
```

**Example Summary**:
```
V1 (n=10 subjects)
----------------------------------------
Procrustes Baseline:
  RDM correlation: 0.174 ± 0.144

SRM (optimal k=50):
  RDM correlation: 0.185 ± 0.150
  Improvement: +0.011 (+6.3%)
  Improved subjects: 7/10 (70.0%)

Statistical Test:
  RDM: t=2.134, p=0.0412 *

Recommendation: Use SRM
```

---

#### 3. `visualize_srm_comparison.py`

**Purpose**: Generate publication-quality comparison figures

**Plots**:
1. **Performance comparison**: SRM vs Procrustes by ROI (boxplots)
2. **Feature tuning curves**: RDM vs k for each ROI
3. **Improvement distribution**: Histogram of subject-level improvements
4. **Optimal k recommendations**: Bar chart of best k per ROI
5. **Winner summary**: Decision flowchart (SRM vs Procrustes)

**Output**:
```python
results/srm_evaluation/{TIMESTAMP}/visualizations/
├── srm_vs_procrustes_performance_by_roi.png
├── feature_tuning_curves_all_rois.png
├── improvement_distribution_by_roi.png
├── optimal_k_recommendations.png
└── srm_winner_summary.png
```

---

### B. Between-Subject Analysis (HC vs CVD)

#### 4. `evaluate_srm_between_subject.py`

**Purpose**: Main between-group HC-CVD comparison in SRM shared space

**Method**:
- Learn shared space from HC subjects (n=6, excluding sub-07)
- Project CVD subjects (n=3) to shared space
- Compare Procrustes disparities: CVD-to-HC vs HC-to-HC

**Metrics**:
1. **Procrustes Disparity**: ||CVD_aligned - HC||_F / sqrt(n_colors × n_features)
   - HC-to-HC: Internal HC consistency
   - CVD-to-HC: Group difference
   - CVD-to-CVD: Internal CVD consistency

2. **RDM Similarity**: Spearman correlation between 8×8 RDMs
   - HC-HC pairs (n=15)
   - CVD-CVD pairs (n=3)
   - HC-CVD pairs (n=18)

**Statistical Tests**:
- Independent t-test: HC vs CVD disparities
- Comparison: CVD-CVD vs CVD-HC (tests internal consistency)
- Effect size: Cohen's d

**Output**:
```python
results/srm_between_subject/{TIMESTAMP}/
├── {ROI}_srm_between_subject_results.json
├── {ROI}_aligned_amplitudes.npy
├── {ROI}_hc_cvd_disparity_comparison.png
└── {ROI}_rdm_similarity_matrix.png
```

---

#### 5. `evaluate_srm_c010_between_subject.py`

**Purpose**: C010 dataset variant of between-subject analysis

**Differences from main script**:
- Uses C010 dataset (different preprocessing)
- May have different subject inclusions
- Alternative validation dataset

**Use Case**: Cross-dataset validation of HC-CVD findings

---

#### 6. `visualize_srm_c010_between_subject.py`

**Purpose**: Visualizations specific to C010 between-subject results

**Plots**:
- C010-specific disparity comparisons
- RDM similarity matrices
- Color space projections

---

#### 7. `visualize_c010_color_space.py`

**Purpose**: MDS projections of 8-color RDMs for C010 dataset

**Method**:
- Multidimensional Scaling (MDS) on 8×8 RDMs
- 2D projection of color representation geometry

**Output**:
- HC vs CVD average color space comparison
- Per-subject color space variations

---

#### 8. `visualize_color_space_per_subject.py`

**Purpose**: Individual subject MDS color space plots

**Output**:
```python
{ROI}_color_space_all_subjects.png  # Grid of all subjects
{ROI}_hc_vs_cvd_color_space_comparison.png  # Group averages
```

**Key Observations**:
- High variability in color space structure across subjects
- Some subjects: circular arrangements
- Others: linear/clustered patterns
- No consistent HC-CVD pattern in color geometry

---

### C. Individual Disparity Analysis

#### 9. `summarize_individual_disparities.py`

**Purpose**: Subject-level disparity summaries

**Metrics**:
- Disparity to each HC reference
- Mean, median, range of disparities
- Rank subjects by similarity to HC

**Use Case**: Identify which CVD subjects are most different from HC

---

#### 10. `visualize_individual_disparities.py`

**Purpose**: Visualize subject-specific disparity patterns

**Plots**:
- Heatmaps: Subject × HC reference disparities
- Distribution plots: Disparity histograms per subject
- Ranking plots: Sort subjects by mean disparity

**Insight**: Reveals CVD heterogeneity (Sub-08 vs Sub-09 with same genotype)

---

### D. Utilities

#### 11. `utils/srm_alignment.py`

**Purpose**: Beta-based SRM implementation wrapper

**Key Functions**:

```python
def apply_srm_alignment(amplitudes_dict, n_features=50):
    """
    Apply SRM to align subjects in shared response space.

    Args:
        amplitudes_dict: {subject: (n_runs, n_colors, n_voxels)}
        n_features: k shared features (k ≤ 8 for beta-based)

    Returns:
        aligned_amplitudes: {subject: (n_runs, n_colors, n_features)}
        srm_model: Trained SRM object
        transformations: {subject: W_i}
    """
```

**Beta-Based Approach**:
1. Average across runs → (n_voxels, n_colors) per subject
2. Fit SRM on averaged patterns
3. Transform individual runs using learned W matrices
4. Constraint: k ≤ n_colors (8)

**References**:
- BrainIAK SRM implementation
- Chen et al. (2015) - SRM paper

---

## Methods

### SRM Algorithm

**Standard SRM**:
```python
# Given: X_i (n_voxels_i × n_samples) for i subjects
# Find: Shared response S (k × n_samples), transformations W_i

# Objective:
minimize ||X_i - W_i @ S||^2  over all i subjects

# Constraint:
S.T @ S = I_k  (orthonormal shared response)
```

**Beta-Based Modification**:
```python
# For limited samples (8 colors):
# 1. Average across runs
X_avg_i = mean(X_i, axis=runs)  # (n_voxels_i, 8)

# 2. Fit SRM on averaged patterns
srm.fit([X_avg_1.T, X_avg_2.T, ...])

# 3. Apply to individual runs
X_aligned_i = X_i @ W_i  # (n_runs, 8, k)
```

**Key Parameters**:
- `n_features` (k): Number of shared dimensions
- `n_iter`: EM iterations (default=10)
- `features_axis`: BrainIAK convention (1 for voxels)

---

### Metrics

#### 1. RDM Correlation (Spearman)

**Purpose**: Measure structural similarity of color representation

```python
# Compute RDMs
RDM_i = pdist(pattern_i, metric='correlation')  # 8×8 → 28 unique pairs

# Similarity
rdm_correlation = spearmanr(RDM_1, RDM_2).correlation
```

**Range**: -1 to +1 (higher = more similar structure)

---

#### 2. Procrustes Disparity

**Purpose**: Quantify alignment quality

```python
# After optimal rotation R, scaling s, translation c
disparity = ||P - Q||_F / sqrt(n_colors × n_features)
```

**Interpretation**:
- Lower disparity = better alignment
- Normalized by matrix size
- HC-HC baseline: Internal group consistency
- CVD-HC: Group difference

---

#### 3. Decoding Accuracy (LDA)

**Purpose**: Task-relevant performance metric

```python
# 8-way classification of colors
lda = LinearDiscriminantAnalysis()
accuracy = cross_val_score(lda, X_aligned, color_labels, cv=6).mean()
```

**Chance Level**: 12.5% (1/8)
**Typical Range**: 30-70%

---

### Statistical Testing

#### Within-Subject (SRM vs Procrustes)

**Test**: Paired t-test (each subject has both SRM and Procrustes results)

```python
t, p = ttest_rel(rdm_srm, rdm_procrustes)
```

**Decision**: Use SRM if p<0.05 AND improvement >5%

---

#### Between-Subject (HC vs CVD)

**Test**: Independent t-test

```python
# HC disparities: n=15 (all HC-HC pairs)
# CVD disparities: n=18 (all CVD-HC pairs)
t, p = ttest_ind(cvd_hc_disparities, hc_hc_disparities)
```

**Interpretation**:
- p<0.05: CVD significantly different from HC
- Cohen's d: Effect size

---

## Execution Guide

### Prerequisites

**Required**:
- Phase 1 baseline results completed
- BrainIAK installed: `conda install -c brainiak -c conda-forge brainiak`
- Python environment: nilearn conda environment

**Data Paths** (auto-detected):
- **Server**: `/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline`
- **Local**: `/Users/jinilkim/.../analysis/phase1_preprocess_decoding/results/baseline`

---

### Running on Server

#### Step 1: Upload Scripts

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Create directories
ssh haba6030@node2 'mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/{utils,sbatch,logs,results}'

# Upload all scripts (consolidated per CLAUDE.md guidelines)
scp analysis/phase2_SRM_across_between/{evaluate_srm_vs_procrustes.py,evaluate_srm_between_subject.py,aggregate_srm_results.py,visualize_srm_comparison.py,evaluate_srm_c010_between_subject.py,visualize_srm_c010_between_subject.py,visualize_c010_color_space.py,visualize_color_space_per_subject.py,summarize_individual_disparities.py,visualize_individual_disparities.py} haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/

# Upload utilities and sbatch
scp analysis/phase2_SRM_across_between/utils/srm_alignment.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/utils/
scp analysis/phase2_SRM_across_between/sbatch/*.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/sbatch/
```

---

#### Step 2: Submit Array Job (Within-Subject)

```bash
# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between

# Submit array job (40 subject-ROI pairs: 10 subjects × 4 ROIs)
sbatch sbatch/run_srm_evaluation.sbatch

# Check job status
squeue -u haba6030

# Monitor progress
watch -n 10 'squeue -u haba6030 | grep srm_eval | wc -l'

# Check completed tasks
ls results/srm_evaluation/*/sub-*_srm_results.json | wc -l
# Expected: 40 when all jobs complete
```

**Job Configuration** (from sbatch file):
```bash
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --array=1-40%10
#SBATCH --mem=32G
#SBATCH --time=04:00:00
```

**Expected Runtime**: ~3 hours total (parallel execution)

---

#### Step 3: Aggregate Results

```bash
# On server (after all 40 jobs complete)
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between

# Find results directory
RESULTS_DIR=$(ls -d results/srm_evaluation/20* | tail -1)

# Aggregate
python aggregate_srm_results.py \
    --results-dir "${RESULTS_DIR}" \
    --output-dir "${RESULTS_DIR}"

# Generate visualizations
python visualize_srm_comparison.py \
    --summary-dir "${RESULTS_DIR}" \
    --output-dir "${RESULTS_DIR}/visualizations"
```

---

#### Step 4: Between-Subject Analysis

```bash
# On server
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between

# Run for each ROI
for ROI in V1 V2 V3 hV4; do
    echo "Processing ${ROI}..."
    python evaluate_srm_between_subject.py \
        --roi "${ROI}" \
        --output-dir "results/srm_between_subject/$(date +%Y%m%d_%H%M%S)" \
        2>&1 | tee "logs/srm_between_${ROI}.log"
done

# Expected runtime: ~30 min per ROI (2 hours total)
```

---

#### Step 5: Download Results

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between

# Download entire results directory
TIMESTAMP=20260206_143022  # Replace with actual timestamp
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/results/srm_evaluation/${TIMESTAMP} ./results/

# Or download only summaries
scp haba6030@node2:/scratch/.../results/srm_evaluation/${TIMESTAMP}/summary_*.json ./results/
scp -r haba6030@node2:/scratch/.../results/srm_evaluation/${TIMESTAMP}/visualizations ./results/
```

---

### Running Locally (Test)

**Quick test scripts**:
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between

# Test single subject-ROI
python evaluate_srm_vs_procrustes.py \
    --subject sub-01 \
    --roi V1 \
    --output-dir results/test/

# Test between-subject (single ROI)
python evaluate_srm_between_subject.py \
    --roi V1 \
    --output-dir results/test/
```

---

## Output Structure

```
analysis/phase2_SRM_across_between/
├── README.md                           # This file
├── EXECUTION_GUIDE.md                  # Detailed execution steps
├── QUICK_START.md                      # Fast deployment guide
├── IMPLEMENTATION_SUMMARY.md           # Technical details
│
├── evaluate_srm_vs_procrustes.py       # Within-subject SRM vs Procrustes
├── evaluate_srm_between_subject.py     # Between-subject HC vs CVD
├── evaluate_srm_c010_between_subject.py # C010 dataset variant
├── aggregate_srm_results.py            # Results aggregation
├── visualize_srm_comparison.py         # Performance plots
├── visualize_srm_c010_between_subject.py # C010 visualizations
├── visualize_c010_color_space.py       # Color space MDS (C010)
├── visualize_color_space_per_subject.py # Individual color spaces
├── summarize_individual_disparities.py  # Subject-level summaries
├── visualize_individual_disparities.py  # Disparity visualizations
│
├── utils/
│   └── srm_alignment.py                # Beta-based SRM implementation
│
├── sbatch/
│   ├── run_srm_evaluation.sbatch       # Within-subject array job
│   └── run_c010_between_subject.sbatch # C010 between-subject job
│
└── results/
    ├── srm_evaluation/
    │   └── {TIMESTAMP}/
    │       ├── sub-{ID}_{ROI}_srm_results.json     # Individual results (40 files)
    │       ├── sub-{ID}_{ROI}_srm_k_tuning.png     # K tuning curves
    │       ├── summary_by_roi.json                 # ROI-level aggregation
    │       ├── optimal_k_recommendations.json      # Best k per ROI
    │       ├── summary_all_subjects.json           # Overall summary
    │       └── visualizations/
    │           ├── srm_vs_procrustes_performance_by_roi.png
    │           ├── feature_tuning_curves_all_rois.png
    │           ├── improvement_distribution_by_roi.png
    │           ├── optimal_k_recommendations.png
    │           └── srm_winner_summary.png
    │
    ├── srm_between_subject/
    │   └── {TIMESTAMP}/
    │       ├── {ROI}_srm_between_subject_results.json
    │       ├── {ROI}_aligned_amplitudes.npy
    │       ├── {ROI}_hc_cvd_disparity_comparison.png
    │       ├── {ROI}_rdm_similarity_matrix.png
    │       ├── {ROI}_color_space_all_subjects.png
    │       ├── {ROI}_hc_vs_cvd_color_space_comparison.png
    │       └── {ROI}_log.txt
    │
    ├── SRM_SUMMARY.md                  # Quick results summary
    └── BETWEEN_SUBJECT_RESULTS.md      # Full between-subject analysis
```

---

## Limitations and Future Directions

### Current Limitations

#### 1. Low RDM Similarity (Between-Subject)
**Problem**: HC-HC RDM correlations range 0.03-0.45

**Possible Causes**:
- k=3-4 features insufficient (constrained by 8 stimuli)
- High noise in beta estimates despite run averaging
- True individual variability in color coding

**Impact**: Undermines confidence in shared response model

---

#### 2. Constraint on k (k ≤ 8)
**Problem**: Only 8 color stimuli → maximum k=8

**Comparison**:
- Brouwer & Heeger (2013): 180 hues → k up to 100+
- Our study: 8 discrete colors → k ≤ 8

**Implication**: Cannot capture high-dimensional color space

---

#### 3. CVD Heterogeneity
**Problem**: CVD-CVD RDM correlations negative in V2/V3

**Interpretation**:
- Each CVD subject has unique neural representation
- Not a homogeneous group
- Personalized approaches required

---

#### 4. Small Sample Size
**Problem**: Only 3 CVD subjects

**Impact**:
- Limited statistical power for CVD-CVD comparisons
- Cannot assess subtype differences (protanopia vs deuteranopia)
- Risk of false negatives

---

### Future Directions

#### 1. Procrustes-Based Validation ✅ RECOMMENDED
**Approach**: Complement SRM with pairwise Procrustes alignment

**Advantages**:
- No k constraint (full voxel space: 200-300 voxels)
- Robust to CVD heterogeneity
- Established baseline from Phase 1

**Status**: Pending implementation

---

#### 2. Alternative Dimensionality Reduction
**Options**:
- PCA on voxel patterns (no shared response assumption)
- Searchlight SRM (local voxel neighborhoods)
- ICA for independent components

---

#### 3. Continuous Hue Space
**Proposal**: Use 360° hue circle instead of 8 discrete colors

**Benefits**:
- Higher k possible (k ≤ 360)
- Better dimensionality for SRM
- Continuous color space analysis

**Challenges**: Longer scan time, more complex design

---

#### 4. GLMsingle for Better Betas
**Proposal**: Use GLMsingle for improved trial-wise beta estimates

**Benefits**:
- Higher SNR betas
- Better SRM performance
- Reduced noise in shared response

---

## SRM vs Procrustes: When to Use Each

### Use SRM When:
- Low SNR data requiring denoising
- High dimensionality (many voxels, few samples)
- Seeking shared structure across subjects
- Within-subject analysis (treat runs as "subjects")

### Use Procrustes When:
- High SNR data
- Need to preserve all variance (no dimensionality reduction)
- Pairwise alignment sufficient
- Heterogeneous groups (no shared structure assumption)

### Combined Approach:
1. **SRM for within-subject**: Denoise and optimize k
2. **Procrustes for between-subject**: Pairwise HC-CVD alignment
3. **Validate**: Cross-check findings across methods

---

## Implications

### For RQ2 (CVD Heterogeneity)

**SRM Findings Support**:
- V2/V3 show significant CVD effects (even in shared space)
- Negative CVD-CVD correlations → high heterogeneity
- Personalized interventions necessary

**Consistency with Procrustes Phase**:
- Both methods identify V2/V3 as critical loci
- Both show individual CVD differences
- Complementary evidence for heterogeneity

---

### For SRQ1 (Common Decoder)

**Within-Subject Success**:
- SRM improves RDM by >5% in V1 → adopt SRM
- Better denoising than Procrustes for low-SNR data

**Between-Subject Challenges**:
- Low RDM similarity limits decoder transfer
- May need subject-specific decoders even after SRM

---

### For Future Phases

**Phase 3 (Filter Optimization)**:
- Use SRM-aligned features for filter input
- Personalized loss functions per CVD subject
- Combine SRM denoising + Procrustes alignment

**Phase 1 (HC Common Space)**:
- SRM as alternative to GPA for hyperalignment
- Test: SRM-based common space vs Procrustes-based

---

## Related Documentation

### Detailed Guides
- [`EXECUTION_GUIDE.md`](EXECUTION_GUIDE.md) - Step-by-step execution instructions
- [`QUICK_START.md`](QUICK_START.md) - Fast deployment guide
- [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) - Technical implementation details

### Results Summaries
- [`results/SRM_SUMMARY.md`](results/SRM_SUMMARY.md) - Quick overview of findings
- [`results/BETWEEN_SUBJECT_RESULTS.md`](results/BETWEEN_SUBJECT_RESULTS.md) - Full between-subject analysis report

### Related Phases
- [`../phase1_preprocess_decoding/README.md`](../phase1_preprocess_decoding/README.md) - Baseline preprocessing
- [`../phase2_procrustes_cvd_hc/README.md`](../phase2_procrustes_cvd_hc/README.md) - Procrustes alignment approach

---

## References

### SRM Method
- **Chen, P. H., et al. (2015).** A Reduced-Dimension fMRI Shared Response Model. *NIPS*.
- **Nastase, S. A., et al. (2019).** Keep it real: rethinking the primacy of experimental control in cognitive neuroscience. *NeuroImage*, 200, 552-565.
- **BrainIAK SRM**: https://brainiak.org/docs/brainiak.funcalign.html

### Color Vision Neuroscience
- **Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and Reconstructing Color from Responses in Human Visual Cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- **Brouwer, G. J., & Heeger, D. J. (2013).** Categorical Clustering of the Neural Representation of Color. *Journal of Neuroscience*, 33(39), 15454-15465.

### Alignment Methods
- **Gower, J. C., & Dijksterhuis, G. B. (2004).** *Procrustes Problems*. Oxford University Press.
- **Haxby, J. V., et al. (2011).** A common, high-dimensional model of the representational space in human ventral temporal cortex. *Neuron*, 72(2), 404-416.

### Color Vision Deficiency
- **Neitz, J., & Neitz, M. (2011).** The genetics of normal and defective color vision. *Vision Research*, 51(7), 633-651.

---

## Appendix: Metric Definitions

### Procrustes Disparity
```python
# After optimal rotation R, scaling s, translation c:
# CVD_aligned = s * CVD @ R + c

disparity = ||CVD_aligned - HC||_F / sqrt(n_colors × n_features)
```
- Lower = better alignment
- Normalized by matrix dimensions
- Range: 0 (perfect) to ~2 (orthogonal)

---

### RDM Similarity
```python
# Representational Dissimilarity Matrix
RDM_ij = 1 - pearson_r(pattern_i, pattern_j)  # for all color pairs

# Similarity between subjects
similarity = spearman_r(RDM_subject1, RDM_subject2)
```
- Range: -1 to +1
- Measures structural similarity of color representation

---

### Cohen's d (Effect Size)
```python
d = (mean_CVD - mean_HC) / pooled_std
```
- |d| < 0.5: Small effect
- |d| = 0.5-0.8: Medium effect
- |d| > 0.8: Large effect

---

**Status**: ✅ Analysis completed + robustness validated
**Last Updated**: 2026-02-18
**Contact**: For methodology questions, see analysis scripts or CLAUDE.md
