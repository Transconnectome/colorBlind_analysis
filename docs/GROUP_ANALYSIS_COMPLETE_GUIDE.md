# Group-Level Analysis: Complete Execution Guide

## Overview

This guide provides step-by-step instructions for running and analyzing group-level fMRI analyses, excluding sub-01 due to insufficient voxel counts.

**Analysis subjects:** sub-02, sub-03, sub-05, sub-06, sub-07 (5 HC subjects)
**Excluded:** sub-01 (outlier), sub-04 (no V1 signal)
**CVD subjects:** sub-08, sub-09, sub-10

---

## Phase 1: Diagnostic Analysis (MUST RUN FIRST)

### Option 1: Within-Subject Reliability

**Purpose:** Verify that individual subjects have stable color representations before group analysis.

**What it does:**
- Split-half reliability analysis
- Checks if each subject's RDMs are consistent across runs
- **If reliability is low, group analysis will fail**

**Expected outcome:**
- Reliability > 0.5: Good (proceed to Phase 2)
- Reliability 0.3-0.5: Moderate (proceed with caution)
- Reliability < 0.3: Poor (don't proceed)

### 1.1 Upload Files

```bash
# Upload Python script
scp analysis/group_level/option1_within_subject_reliability.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# Upload SLURM batch file
scp analysis/group_level/run_option1_reliability.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/
```

### 1.2 Run Analysis

```bash
# SSH to server
ssh haba6030@node2

# Navigate to directory
cd /scratch/connectome/haba6030/colorBlind

# Submit job
sbatch analysis/group_level/run_option1_reliability.sbatch

# Check job status
squeue -u haba6030
```

### 1.3 Monitor Progress

```bash
# Watch real-time output
tail -f logs/group_level/option1_reliability_*.out

# Check for errors
tail -f logs/group_level/option1_reliability_*.err
```

### 1.4 Download Results

```bash
# On your local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/option1_within_subject_reliability/ \
    results/group_level/

# Download logs
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/group_level/option1_reliability_*.out \
    logs/group_level/

scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/group_level/option1_reliability_*.err \
    logs/group_level/
```

### 1.5 Analyze Results

**Check these files:**
```
results/group_level/option1_within_subject_reliability/
├── summary_results.csv          # Main results table
├── reliability_by_roi_subject.png  # Heatmap visualization
└── reliability_distribution.png    # Distribution by ROI
```

**Key metrics to check:**

```bash
# Quick summary
cat results/group_level/option1_within_subject_reliability/summary_results.csv
```

Expected output:
```
subject,roi,reliability,p_value,interpretation
02,V1,0.XX,0.XXX,Good/Moderate/Poor
02,V2,0.XX,0.XXX,Good/Moderate/Poor
...
```

**Decision point:**
- ✅ If most subjects show reliability > 0.5 → **Proceed to Phase 2**
- ⚠️ If many subjects < 0.3 → **Re-evaluate baseline preprocessing**

---

## Phase 2: Group-Level Methods (Run after Option 1)

### Option 2: Shared Response Model (SRM) - RECOMMENDED

**Purpose:** Find shared neural color representations across subjects using BrainIAK SRM.

**Advantages:**
- Validated for color fMRI (Bannert & Bartels 2025)
- Accounts for individual anatomical differences
- Finds latent shared space

**Computational cost:**
- Time: ~2-3 days
- Memory: ~64GB

### 2.1 Upload Files

```bash
# Upload Python script (with outlier detection)
scp analysis/group_level/option2_srm_analysis.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# Upload SLURM batch file (sub-01 excluded)
scp analysis/group_level/run_option2_srm.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# Optional: with CVD subjects
scp analysis/group_level/run_option2_srm_with_cvd.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/
```

### 2.2 Run Analysis

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# HC only (recommended for first run)
sbatch analysis/group_level/run_option2_srm.sbatch

# Optional: HC + CVD
# sbatch analysis/group_level/run_option2_srm_with_cvd.sbatch

# Check status
squeue -u haba6030
```

### 2.3 Monitor Progress

```bash
# Watch output
tail -f logs/group_level/option2_srm_*.out

# Check for warnings (important!)
grep "WARNING" logs/group_level/option2_srm_*.out

# Check SRM convergence
grep "SRM" logs/group_level/option2_srm_*.out
```

**Expected output:**
```
Loading V1 data for 5 subjects...
  sub-02: (6, 8, 429)
  sub-03: (6, 8, 429)
  sub-05: (6, 8, 429)
  sub-06: (6, 8, 429)
  sub-07: (6, 8, 429)
  Minimum voxels: 429
  Maximum voxels: 429
  Median voxels: 429
  No outliers detected ✓
```

### 2.4 Download Results

```bash
# On local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/option2_srm/ \
    results/group_level/

scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/group_level/option2_srm_*.out \
    logs/group_level/
```

### 2.5 Analyze Results

**Result structure:**
```
results/group_level/option2_srm/
├── V1/
│   ├── srm_results.npz              # SRM model outputs
│   ├── shared_space_rdms.npy        # RDMs in shared space
│   ├── rdm_similarity_matrix.png    # Inter-subject similarity
│   └── shared_space_consistency.png # Group consistency
├── V2/
├── V3/
└── hV4/
```

**Key metrics:**

```python
# Load results in Python
import numpy as np

# V1 example
results = np.load('results/group_level/option2_srm/V1/srm_results.npz')
mean_similarity = results['mean_rdm_similarity']
print(f"V1 mean RDM similarity in shared space: {mean_similarity:.3f}")

# Interpretation:
# > 0.5: Good shared representation
# 0.3-0.5: Moderate
# < 0.3: Poor (SRM may not be appropriate)
```

---

### Option 3: Supersubject Method - BASELINE

**Purpose:** Classical Brouwer & Heeger approach (concatenate all subjects).

**Advantages:**
- Simple, interpretable
- Fast (~1 day)
- Good baseline for comparison

**Disadvantages:**
- Ignores individual differences
- Assumes perfect anatomical alignment

### 3.1 Upload Files

```bash
# Upload Python script
scp analysis/group_level/option3_supersubject.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# Upload SLURM batch file (sub-01 excluded)
scp analysis/group_level/run_option3_supersubject.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# Optional: with CVD
scp analysis/group_level/run_option3_supersubject_with_cvd.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/
```

### 3.2 Run Analysis

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# HC only
sbatch analysis/group_level/run_option3_supersubject.sbatch

# Check status
squeue -u haba6030
```

### 3.3 Monitor and Download

```bash
# Monitor
tail -f logs/group_level/option3_supersubject_*.out

# Download results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/option3_supersubject/ \
    results/group_level/
```

### 3.4 Analyze Results

```
results/group_level/option3_supersubject/
├── V1/
│   ├── group_rdm.npy                # Group-averaged RDM
│   ├── group_rdm.png                # Visualization
│   └── reconstruction_accuracy.txt  # Decoding performance
├── V2/
├── V3/
└── hV4/
```

---

## Phase 3: Compare Methods

### 3.1 Compare Option 2 vs Option 3

**Key questions:**
1. Does SRM improve inter-subject consistency vs. concatenation?
2. Which ROIs benefit most from SRM?
3. Are individual differences large?

**Comparison metrics:**

| Metric | Option 2 (SRM) | Option 3 (Supersubject) |
|--------|----------------|-------------------------|
| Mean RDM similarity | ? | ? |
| Reconstruction accuracy | ? | ? |
| Between-subject variance | Lower (aligned) | Higher |

### 3.2 Generate Comparison Report

Create a summary comparing all results:

```bash
# On local machine
cat > analysis_summary.txt <<'EOF'
=== Group-Level Analysis Summary ===

Subjects included: sub-02, sub-03, sub-05, sub-06, sub-07 (n=5)
Excluded: sub-01 (outlier), sub-04 (no V1 signal)

--- Option 1: Within-Subject Reliability ---
V1: [mean reliability]
V2: [mean reliability]
V3: [mean reliability]
hV4: [mean reliability]

Decision: [Proceed/Reconsider based on reliability]

--- Option 2: SRM (HC only) ---
V1: Mean similarity = [X.XX]
V2: Mean similarity = [X.XX]
V3: Mean similarity = [X.XX]
hV4: Mean similarity = [X.XX]

--- Option 3: Supersubject (HC only) ---
V1: Group RDM quality = [X.XX]
V2: Group RDM quality = [X.XX]
V3: Group RDM quality = [X.XX]
hV4: Group RDM quality = [X.XX]

--- Conclusions ---
Best method: [SRM/Supersubject]
Best ROI: [V1/V2/V3/hV4]
Proceed to CVD analysis: [Yes/No]
EOF
```

---

## Phase 4: CVD Analysis (Optional)

**Only run if Phase 2/3 show good HC group consistency**

### 4.1 Run HC + CVD Analyses

```bash
# SRM with CVD
sbatch analysis/group_level/run_option2_srm_with_cvd.sbatch

# Supersubject with CVD
sbatch analysis/group_level/run_option3_supersubject_with_cvd.sbatch
```

### 4.2 CVD-Specific Outputs

```
results/group_level/option2_srm_with_cvd/
├── V1/
│   ├── cvd_analysis_results.npz     # CVD vs HC comparison
│   ├── cvd_rdm_comparison.png       # Individual CVD RDMs
│   └── reconstruction_errors.csv    # CVD reconstruction quality
```

---

## Troubleshooting

### Issue 1: Job Fails Immediately

```bash
# Check error log
cat logs/group_level/option*_*.err

# Common causes:
# - Missing conda environment
# - Missing BrainIAK (Option 2 only)
# - File not found errors
```

### Issue 2: Dimension Mismatch Errors

```bash
# Check if outlier warnings appear
grep "WARNING" logs/group_level/option2_srm_*.out

# If sub-01 is still included, verify sbatch files
grep "hc-subjects" analysis/group_level/run_option*.sbatch
# Should show: 02 03 05 06 07 (no 01)
```

### Issue 3: Low Reliability (Option 1)

**If Option 1 shows low reliability (<0.3):**

1. Check individual-level baseline results
2. Consider different preprocessing (smoothing, confounds)
3. May need to exclude specific subjects
4. Group analysis not recommended

### Issue 4: SRM Fails to Converge

```bash
# Check SRM iteration logs
grep "iteration" logs/group_level/option2_srm_*.out

# If not converging:
# - Increase --n-iter (currently 10)
# - Decrease --k-features (currently 20)
# - Check for NaN/Inf values
```

---

## Quick Reference: All Commands

### Upload All Files (One-Time Setup)

```bash
# Python scripts
scp analysis/group_level/option1_within_subject_reliability.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

scp analysis/group_level/option2_srm_analysis.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

scp analysis/group_level/option3_supersubject.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# SLURM batch files
scp analysis/group_level/run_option*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/
```

### Run All Analyses (Sequential)

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Step 1: Diagnostic (MUST RUN FIRST)
sbatch analysis/group_level/run_option1_reliability.sbatch

# Wait for completion, check results, then:

# Step 2: SRM (recommended)
sbatch analysis/group_level/run_option2_srm.sbatch

# Step 3: Supersubject (baseline)
sbatch analysis/group_level/run_option3_supersubject.sbatch
```

### Download All Results

```bash
# On local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/ \
    results/

scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/group_level/option*.out \
    logs/group_level/
```

---

## Expected Timeline

| Analysis | Time | Memory | Priority |
|----------|------|--------|----------|
| Option 1 (Reliability) | ~2-4 hours | 16GB | **MUST RUN FIRST** |
| Option 2 (SRM) | ~2-3 days | 64GB | High |
| Option 3 (Supersubject) | ~1 day | 32GB | Medium |
| Option 2 + CVD | ~2-3 days | 64GB | After HC validation |
| Option 3 + CVD | ~1 day | 32GB | After HC validation |

**Total estimated time:** ~1 week for complete analysis

---

## Success Criteria

### ✅ Phase 1 Success
- Within-subject reliability > 0.5 for most subjects/ROIs
- No missing data errors
- Interpretable visualizations

### ✅ Phase 2/3 Success
- No outlier warnings (sub-01 excluded)
- SRM converges within 10 iterations
- Mean RDM similarity > 0.3 in shared space
- Consistent results between Option 2 and 3

### ✅ Phase 4 Success
- CVD subjects successfully projected to HC space
- Interpretable HC vs CVD differences
- Reconstruction errors quantified

---

## Final Outputs

After completing all analyses, you should have:

1. **Reliability report** (Option 1)
   - Per-subject, per-ROI reliability estimates
   - Decision: proceed or re-evaluate

2. **Group consistency metrics** (Option 2)
   - Shared space RDM similarities
   - Latent feature representations

3. **Baseline group analysis** (Option 3)
   - Classical supersubject results
   - Comparison benchmark

4. **CVD analysis** (Optional)
   - HC vs CVD differences
   - Individual CVD profiles

5. **Comprehensive comparison**
   - Which method works best
   - Which ROIs show strongest effects
   - Recommendation for final analysis

---

**Next Steps:** Start with Phase 1 (Option 1 reliability analysis)
