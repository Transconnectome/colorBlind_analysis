# RDM Metric and Normalization Sensitivity Test - Server Execution Guide

**Purpose**: Test whether RDM distance metric (correlation vs crossnobis) and normalization method (none vs within vs pooled) affect FDR results.

**Date**: 2026-02-22

---

## Files Created

```
test_rdm_metric_and_normalization_server.py  # Main analysis script (supports test mode)
run_metric_norm_test.sbatch                   # SLURM batch file (full analysis)
test_metric_norm_interactive.sh               # Interactive test script (validation)
METRIC_NORM_TEST_GUIDE.md                     # This guide
```

**Output structure** (in same directory as scripts):
```
pre_validation/
├── logs/                    # SLURM logs, interactive test logs
│   ├── slurm_JOBID.out
│   └── interactive_test_*.log
├── results/                 # Analysis results (JSON)
│   └── metric_norm_test_*.json
└── test_rdm_metric_and_normalization_server.py
```

---

## Step 1: Upload to Server

**Single SCP command** (combines all files):

```bash
scp test_rdm_metric_and_normalization_server.py run_metric_norm_test.sbatch test_metric_norm_interactive.sh haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_filter_optimization/pre_validation/
```

---

## Step 2: Run Interactive Test (RECOMMENDED)

**Test pipeline before full submission** (~3-5 min):

```bash
# SSH to server
ssh haba6030@node3

# Navigate to directory
cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase3_filter_optimization/pre_validation

# Make script executable
chmod +x test_metric_norm_interactive.sh

# Run interactive test
bash test_metric_norm_interactive.sh
```

**What it tests**:
- 1 CVD subject (sub-08)
- 2 ROIs (V1, V2)
- 2 conditions (correlation + crossnobis, no normalization)
- Total: 2 subject-ROI × 2 conditions = 4 analyses

**Expected output**:
```
✅ SUCCESS! Pipeline validated.

Next steps:
1. Check results/metric_norm_test_*.json for output format
2. Verify convergence calculations are working
3. Submit full job: sbatch run_metric_norm_test.sbatch
```

---

## Step 3: Submit Full SLURM Job

**After interactive test passes**:

```bash
# Submit job
sbatch run_metric_norm_test.sbatch

# Check job status
squeue -u haba6030

# Monitor output
tail -f logs/slurm_JOBID.out
```

---

## Step 4: Download Results

Once job completes:

```bash
# Download results JSON
scp haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_filter_optimization/pre_validation/results/metric_norm_test_*.json analysis/future_phase3_filter_optimization/pre_validation/results/

# Download log files
scp haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_filter_optimization/pre_validation/logs/slurm_*.out analysis/future_phase3_filter_optimization/pre_validation/logs/
```

---

## Expected Runtime

- **Correlation metric**: ~5 min per condition (3 conditions = 15 min)
- **Crossnobis metric**: ~20 min per condition (3 conditions = 60 min)
- **Total**: ~75 minutes (6 conditions total)

---

## Resource Usage

- **Memory**: ~16 GB peak (allocated 32 GB for safety)
- **CPUs**: 4 cores (sklearn LedoitWolf parallelization)
- **Node**: node2 (CPU-only, no GPU needed)

---

## What the Script Does

### 6 Test Conditions

| # | Metric | Normalization | Description |
|---|--------|---------------|-------------|
| 1 | Correlation | None | **Baseline** (current method) |
| 2 | Correlation | Within-subject | Z-norm RDM values within each subject |
| 3 | Correlation | Pooled | Z-norm using HC pooled mean/std |
| 4 | Crossnobis | None | Cross-validated Mahalanobis distance |
| 5 | Crossnobis | Within-subject | Crossnobis + within z-norm |
| 6 | Crossnobis | Pooled | Crossnobis + pooled z-norm |

### For Each Condition

1. Computes RDM for each CVD subject (sub-08, sub-09, sub-10) × 4 ROIs
2. Computes RDM for each HC subject (sub-01 to sub-07) × 4 ROIs
3. Applies normalization (if specified)
4. Runs Crawford & Howell test for each of 28 color pairs
5. Applies within-ROI FDR correction (q<0.05)
6. Records:
   - Z-scores
   - P-values
   - FDR-significant pairs
   - RDM raw values
   - RDM normalized values
   - Shrinkage parameter (for crossnobis)

### Output

Single JSON file with all results:
```json
{
  "timestamp": "20260222_HHMMSS",
  "hostname": "node2",
  "tests": [
    {
      "metric": "correlation",
      "normalization": "none",
      "results": [
        {
          "subject": "sub-08",
          "roi": "V1",
          "n_fdr_sig": 3,
          "pairs": [/* 28 pairs with z-scores, p-values, etc. */]
        },
        // ... more subject-ROI combinations
      ]
    },
    // ... more conditions
  ]
}
```

---

## Key Analyses

After downloading results, analyze locally:

### 1. FDR Survivor Count Comparison

**Question**: Does metric/normalization change number of significant pairs?

```python
import json

with open('metric_norm_test_*.json') as f:
    results = json.load(f)

for test in results['tests']:
    metric = test['metric']
    norm = test['normalization']
    total_sig = sum(r['n_fdr_sig'] for r in test['results'])
    print(f"{metric} + {norm}: {total_sig} FDR-sig pairs")
```

**Expected**:
- If all conditions give similar counts (±10%): Method-independent (robust)
- If crossnobis differs >20%: Metric matters
- If z-norm differs >20%: Normalization matters

### 2. Convergence Analysis

**Question**: Do z-scores correlate between conditions?

```python
import numpy as np
from scipy.stats import spearmanr

baseline = results['tests'][0]  # correlation + none
test_cond = results['tests'][3]  # crossnobis + none

# Extract z-scores for matching subject-ROI pairs
baseline_z = []
test_z = []

for b_res in baseline['results']:
    key = (b_res['subject'], b_res['roi'])
    t_res = next((r for r in test_cond['results']
                  if r['subject'] == b_res['subject'] and r['roi'] == b_res['roi']), None)
    if t_res:
        baseline_z.extend(b_res['z_scores'])
        test_z.extend(t_res['z_scores'])

r, p = spearmanr(baseline_z, test_z)
print(f"Correlation r={r:.3f}, p={p:.3e}")
```

**Expected**:
- r > 0.9: Very high convergence (metric doesn't matter)
- r = 0.7-0.9: Moderate convergence (report both metrics)
- r < 0.7: Low convergence (metric choice critical)

### 3. Pair Agreement Rate

**Question**: Do same pairs remain significant?

```python
baseline_pairs = set()
test_pairs = set()

for res in baseline['results']:
    for pair in res['pairs']:
        if pair['fdr_sig']:
            baseline_pairs.add((res['subject'], res['roi'], pair['pair']))

for res in test_cond['results']:
    for pair in res['pairs']:
        if pair['fdr_sig']:
            test_pairs.add((res['subject'], res['roi'], pair['pair']))

agreement = len(baseline_pairs & test_pairs)
disagreement = len(baseline_pairs ^ test_pairs)
rate = agreement / (agreement + disagreement) if (agreement + disagreement) > 0 else 0

print(f"Agreement: {agreement}, Disagreement: {disagreement}, Rate: {rate:.1%}")
```

**Expected**:
- Rate > 95%: Excellent agreement
- Rate 80-95%: Moderate agreement
- Rate < 80%: Poor agreement (results change)

---

## Interpretation Guidelines

### Q1: Does crossnobis method affect results?

**If convergence r > 0.9 AND agreement > 95%:**
- Metric choice does NOT matter
- Use correlation distance (simpler, current method validated)

**If convergence r = 0.7-0.9 OR agreement 80-95%:**
- Moderate sensitivity
- Report both metrics or note limitation

**If convergence r < 0.7 OR agreement < 80%:**
- Metric choice CRITICAL
- Prefer crossnobis (more principled for fMRI noise structure)

### Q2: Does z-normalization affect results?

**If z-norm total FDR pairs within ±10% of baseline:**
- Normalization does NOT matter
- Keep current method (no norm, simpler interpretation)

**If z-norm differs >20%:**
- Variance baseline matters
- Use within-subject z-norm (accounts for individual variance)

---

## Troubleshooting

### Job fails with OOM (Out of Memory)

Increase memory allocation:
```bash
#SBATCH --mem=64G
```

### Crossnobis very slow

Expected behavior - Ledoit-Wolf covariance estimation is O(n_voxels^3). Reduce parallelization overhead:
```bash
#SBATCH --cpus-per-task=2
```

### Import errors

Check conda environment:
```bash
conda activate nilearn
python -c "import sklearn, scipy, numpy; print('OK')"
```

---

## Advanced: Custom Test Mode

For fine-grained testing, use Python script directly:

```bash
# Custom subjects and ROIs
python test_rdm_metric_and_normalization_server.py --test_mode \
    --test_subjects sub-08 sub-09 \
    --test_rois V1 V2 V3 \
    --test_conditions correlation_none crossnobis_none correlation_within

# All CVD subjects, one ROI, two conditions
python test_rdm_metric_and_normalization_server.py --test_mode \
    --test_subjects sub-08 sub-09 sub-10 \
    --test_rois V2 \
    --test_conditions correlation_none crossnobis_none
```

**Available conditions**:
- `correlation_none` (baseline)
- `correlation_within`
- `correlation_pooled`
- `crossnobis_none`
- `crossnobis_within`
- `crossnobis_pooled`

---

## Output File Structure

**Results JSON** (`results/metric_norm_test_TIMESTAMP.json`):
```json
{
  "timestamp": "20260222_153045",
  "hostname": "node2",
  "test_mode": false,
  "n_hc": 7,
  "n_cvd": 3,
  "cvd_subjects": ["sub-08", "sub-09", "sub-10"],
  "rois": ["V1", "V2", "V3", "hV4"],
  "conditions": ["correlation_none", "correlation_within", ...],
  "tests": [/* detailed results per condition */]
}
```

**Logs** (`logs/slurm_JOBID.out` or `logs/interactive_test_TIMESTAMP.log`):
- Resource monitoring (memory usage every 60s)
- Progress per condition/ROI/subject
- Final summary with download instructions

---

## Next Steps

1. **Run interactive test** (~5 min) - validate pipeline
2. **Submit full job** (~75 min) - complete analysis
3. **Download results** to local
4. **Generate comparison report** (convergence, agreement, recommendations)
5. **Update figure documentation** if metric/norm affects conclusions
6. **Commit analysis** to git with findings

---

**Created**: 2026-02-22
**Updated**: 2026-02-22 (added test mode, output reorganization)
**Script**: test_rdm_metric_and_normalization_server.py
**Job**: run_metric_norm_test.sbatch
**Interactive test**: test_metric_norm_interactive.sh
