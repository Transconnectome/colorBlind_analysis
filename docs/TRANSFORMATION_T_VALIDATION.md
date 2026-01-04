# Transformation T Validation

## 📌 Overview

This analysis validates whether the systematic difference **T = CVD_mean - HC_mean** discovered in Option 2D can effectively correct CVD voxel responses to match HC responses.

## 🎯 Goal

Test if applying the transformation T can "normalize" CVD brain responses:

```
CVD_corrected = CVD_original - T

Expected: CVD_corrected ≈ HC_mean
```

This is the **critical validation step** before designing the color filter.

---

## 📊 What We Found in Option 2D

### Option A Results (Reference-based Procrustes)

| ROI | HC Disparity | CVD Disparity | CVD RMS Diff | Consistency |
|-----|--------------|---------------|--------------|-------------|
| V1  | 0.089        | 0.111         | **0.507**    | **0.998**   |
| V2  | 0.129        | 0.162         | **0.653**    | **0.996**   |

**Key Findings**:
1. ✅ **Systematic CVD difference exists**: RMS 0.5-0.65
2. ✅ **Perfect consistency**: 0.998 across all 3 CVD subjects
3. ✅ **5-6x larger than HC variability**: 0.507 >> 0.089

**Color-specific pattern** (V1):
- Color 5: RMS = 0.617 (largest - likely red-green axis)
- Color 6: RMS = 0.411 (smallest - likely blue-yellow axis)
- Matches CVD characteristics (protanopia/deuteranopia)

---

## 🧪 Validation Strategy

### Step 1: Load Data
- HC_mean from Option 2D (aligned to sub-02 reference)
- T = cvd_common_diff_option_a.npy
- Individual CVD patterns (sub-08, sub-09, sub-10)

### Step 2: For Each CVD Subject
1. Load original pattern
2. Align to sub-02 reference (Procrustes)
3. Measure distance **before correction**:
   - RMS distance to HC_mean
   - Spearman correlation with HC_mean
4. Apply correction: `CVD_corrected = CVD_original - T`
5. Measure distance **after correction**:
   - RMS distance to HC_mean (should decrease dramatically)
   - Correlation with HC_mean (should increase)

### Step 3: Calculate Improvement
- **RMS reduction** = (RMS_before - RMS_after) / RMS_before × 100%
- **Correlation gain** = Corr_after - Corr_before

### Step 4: Color-specific Analysis
- Which colors show largest improvement?
- Does it match the colors with largest T?

---

## ✅ Success Criteria

| Metric | Excellent | Moderate | Insufficient |
|--------|-----------|----------|--------------|
| **RMS Reduction** | > 80% | 50-80% | < 50% |
| **Correlation Gain** | > 0.3 | 0.1-0.3 | < 0.1 |
| **Consistency** | All 3 CVD subjects show improvement | 2/3 show improvement | < 2/3 |

### Expected Outcome

If T is a valid transformation:
- **Before**: CVD is ~0.5 RMS away from HC_mean
- **After**: CVD should be ~0.1 RMS away (80% reduction)
- This would indicate T captures the systematic CVD difference

---

## 🔄 Connection to Filter Design

### Current Pipeline Status

```
[✅ Find systematic difference] → [🔄 Validate T] → [⏭️ Test reconstruction] → [⏭️ Design filter]
         Option 2D                 This step        Next step           Final goal
```

### If Validation Succeeds

**Next Step**: Test if corrected CVD patterns improve color reconstruction

1. Learn W matrix from HC data (color → voxel mapping)
2. Test reconstruction on:
   - Original CVD patterns (baseline error)
   - Corrected CVD patterns (should improve!)
3. Calculate reconstruction error reduction

**Filter Architecture**:
```
External stimulus → CVD eye → CVD brain response → [+T] → HC-like response → [W matrix] → Correct color
```

### If Validation Fails

**Possible reasons**:
1. T is correct but individuals differ (need per-subject T)
2. T only works for specific colors (need color-specific T)
3. Additional factors beyond T (e.g., nonlinear effects)

**Alternative approach**:
- Create subject-specific transformations
- Use machine learning for nonlinear correction
- Focus on specific color axes (red-green vs blue-yellow)

---

## 📁 Output Files

### Numerical Results
- `validation_results_V1.csv` - Per-subject metrics for V1
- `validation_results_V2.csv` - Per-subject metrics for V2
- `validation_results_all.csv` - Combined summary

**Columns**:
- subject: CVD subject ID
- roi: Brain region
- rms_before: Distance before correction
- rms_after: Distance after correction
- rms_reduction_%: Percentage reduction
- corr_before: Correlation before
- corr_after: Correlation after
- corr_improvement: Correlation gain

### Visualizations

`transformation_validation_V1.png` and `transformation_validation_V2.png`:

**Six panels**:
1. **RMS Distance Comparison**: Before vs After (bar chart)
2. **RMS Reduction %**: Effectiveness per subject (with 80%/50% thresholds)
3. **Correlation Improvement**: Before vs After
4. **Color-specific RMS (Before)**: Heatmap showing which colors differ most
5. **Color-specific RMS (After)**: Heatmap showing correction effectiveness
6. **Color-specific Reduction**: Which colors benefit most from T

---

## 🚀 Execution

### Upload Files to Server
```bash
# Upload Python script
scp analysis/group_level/validate_transformation_t.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# Upload SBATCH script
scp analysis/group_level/run_validate_transformation_t.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/
```

### Run on Server
```bash
# SSH to server
ssh haba6030@node2

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Submit job
sbatch analysis/group_level/run_validate_transformation_t.sbatch

# Monitor job
squeue -u haba6030
tail -f logs/group_level/validate_transformation_t_<JOB_ID>.out
```

### Download Results
```bash
# Download all validation results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/transformation_validation/ \
    results/group_level/
```

---

## 🔍 Interpretation Guide

### Scenario 1: High Success (RMS Reduction > 80%)
**Interpretation**: T is a robust, stable transformation
**Implication**: Can proceed to reconstruction testing and filter design
**Next step**: Test if W matrix is shared between HC and CVD

### Scenario 2: Moderate Success (RMS Reduction 50-80%)
**Interpretation**: T captures main effect but individual differences remain
**Implication**: May need subject-specific adjustments
**Next step**: Analyze residual differences, consider T + δT per subject

### Scenario 3: Color-specific Success
**Interpretation**: T works for some colors (e.g., red-green) but not others
**Implication**: Color-axis-specific transformations needed
**Next step**: Design separate T_red-green and T_blue-yellow

### Scenario 4: Low Success (RMS Reduction < 50%)
**Interpretation**: Group-level T insufficient, high individual variability
**Implication**: Need per-subject transformation learning
**Next step**: Pivot to individual-level analysis

---

## 💡 Key Assumptions Being Tested

1. **Linearity**: CVD = HC + T (linear additive model)
2. **Stability**: Same T works for all CVD subjects
3. **Completeness**: T captures all systematic differences
4. **Voxel-level**: Transformation works at voxel response level

If any assumption fails, we'll learn something important about CVD neural representation!

---

## 📚 Related Documents

- `ORIGINAL_HYPOTHESIS_AND_GOAL.md` - Initial assumptions and filter architecture
- `OPTION2D_RESULTS_DETAILED_EXPLANATION.md` - Option 2D results and methodology
- `GUIDE_GroupLevel.md` - Overall group-level analysis guide
