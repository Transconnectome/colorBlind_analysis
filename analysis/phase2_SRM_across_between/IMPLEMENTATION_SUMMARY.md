# SRM Scripts Adaptation to Baseline Results - Summary

**Date**: 2026-02-06
**Status**: ✅ Implementation Complete
**Purpose**: Adapt SRM evaluation scripts to use Phase 1 baseline results instead of waiting for Phase 2 whitening results

---

## Changes Made

### 1. Core Script Modifications

#### `evaluate_srm_vs_procrustes.py` (Within-Subject SRM)

**Key changes:**
- ✅ Added `socket` import for hostname detection
- ✅ Replaced `WHITENING_RESULTS_DIR` with `BASELINE_RESULTS_DIR`
- ✅ Added automatic path detection (server vs local)
- ✅ Created `load_baseline_amplitudes()` function
- ✅ Modified data loading to use:
  - `amplitudes_z.npy` (pre-Procrustes, for SRM input)
  - `amplitudes_procrustes.npy` (Procrustes baseline, for comparison)
- ✅ Updated all references from "whitened" to "baseline"
- ✅ Updated docstrings to reflect baseline data source

**Paths configured:**
```python
# Auto-detected based on hostname
if socket.gethostname().startswith('node'):
    # Server
    BASELINE_RESULTS_DIR = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline")
else:
    # Local
    BASELINE_RESULTS_DIR = Path("/Users/jinilkim/.../results/baseline")
```

#### `evaluate_srm_between_subject.py` (Between-Subject HC-CVD)

**Key changes:**
- ✅ Added `socket` import for hostname detection
- ✅ Replaced `WHITENING_RESULTS_DIR` with `BASELINE_RESULTS_DIR`
- ✅ Added automatic path detection
- ✅ Modified `load_subject_amplitudes()` to load `amplitudes_z.npy`
- ✅ Updated all references from "whitened" to "baseline"
- ✅ Updated docstrings

#### `sbatch/run_srm_evaluation.sbatch` (SLURM Array Job)

**Key changes:**
- ✅ Updated job description from "whitened data" to "baseline data"
- ✅ Replaced `WHITENING_RESULTS_DIR` with `BASELINE_RESULTS_DIR`
- ✅ Updated server path to baseline results
- ✅ Updated file checks:
  - `amplitudes_whitened.npy` → `amplitudes_z.npy`
  - `amplitudes_procrustes_whitened.npy` → `amplitudes_procrustes.npy`
- ✅ Removed references to `noise_ceiling_split_half.npy` (not in baseline)

### 2. Documentation Updates

#### `EXECUTION_GUIDE_PHASE3_SRM.md`

**Key changes:**
- ✅ Updated prerequisites: Phase 2 → Phase 1 ✅
- ✅ Removed placeholder path update instructions (now auto-configured)
- ✅ Updated expected input files (whitened → baseline)
- ✅ Simplified configuration section (paths auto-detected)
- ✅ Updated all references from "whitening" to "baseline"

### 3. New Helper Scripts

#### `deploy_srm_to_server.sh` (Local)

**Purpose**: Upload modified scripts to server
**Features:**
- Uploads all 4 Python scripts
- Uploads sbatch script
- Uploads execution guide
- Creates necessary directories on server
- Provides next-step instructions

#### `test_srm_server_interactive.sh` (Server)

**Purpose**: Interactive test on server before array job
**Features:**
- Checks baseline data exists
- Activates conda environment
- Verifies BrainIAK installation
- Runs single subject-ROI test (sub-01 V1)
- Monitors execution time
- Shows results preview
- Provides next-step instructions

#### `test_srm_baseline_local.sh` (Local, optional)

**Purpose**: Local testing (requires BrainIAK installation locally)
**Note**: BrainIAK not installed locally, so this is for reference only

---

## Data Flow Comparison

### Original Plan (Phase 2 Whitening)
```
Phase 2 Whitening
  ↓
amplitudes_whitened.npy ──┬──> SRM
                          └──> Procrustes on whitened data
  ↓
amplitudes_procrustes_whitened.npy ──> Baseline for comparison
```

### Adapted Plan (Phase 1 Baseline)
```
Phase 1 Baseline
  ↓
amplitudes_z.npy ──┬──> SRM
                   └──> Procrustes (already computed)
  ↓
amplitudes_procrustes.npy ──> Baseline for comparison
```

**Advantages:**
1. ✅ Immediate testing (no waiting for Phase 2)
2. ✅ Fair comparison (both SRM and Procrustes start from z-scored data)
3. ✅ Simpler setup (no placeholder path updates needed)

---

## File Locations

### Modified Scripts
```
analysis/validation/scripts/
├── evaluate_srm_vs_procrustes.py          ✅ Modified
├── evaluate_srm_between_subject.py        ✅ Modified
├── aggregate_srm_results.py               (No changes needed)
├── visualize_srm_comparison.py            (No changes needed)
├── sbatch/run_srm_evaluation.sbatch       ✅ Modified
└── EXECUTION_GUIDE_PHASE3_SRM.md          ✅ Updated
```

### New Scripts
```
analysis/validation/scripts/
├── test_srm_server_interactive.sh         ✅ New
└── SRM_BASELINE_ADAPTATION_SUMMARY.md     ✅ New (this file)
```

---

## Deployment Instructions

### Step 1: Upload to Server

**From local machine:**
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Upload Python scripts and test script
scp evaluate_srm_vs_procrustes.py evaluate_srm_between_subject.py aggregate_srm_results.py visualize_srm_comparison.py test_srm_server_interactive.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/

# Upload sbatch script
scp sbatch/run_srm_evaluation.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/sbatch/

# Create directories on server
ssh haba6030@node2 "mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/{results/srm_evaluation,logs}"
```

### Step 2: Verify Baseline Data on Server

**SSH to server:**
```bash
ssh haba6030@node2

# Check baseline directory
ls /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/only_Zscore_1stGLM/sub-01/V1/

# Expected files:
# amplitudes_z.npy
# amplitudes_procrustes.npy
# analysis_summary.json
# (and other baseline files)
```

### Step 3: Install BrainIAK (if not already installed)

```bash
conda activate nilearn

# Check if already installed
python -c "import brainiak; print('BrainIAK version:', brainiak.__version__)" 2>&1

# If not installed:
conda install -c brainiak -c conda-forge brainiak

# Installation may take 10-15 minutes
```

### Step 4: Run Interactive Test

```bash
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Run test script
bash test_srm_server_interactive.sh
```

**Expected runtime:** 5-10 minutes (SRM is computationally intensive)

**Expected output:**
```
[1/4] Checking prerequisites...
  ✓ Baseline directory exists
  ✓ Test subject data exists
[2/4] Activating conda environment...
  ✓ Environment activated
[3/4] Checking BrainIAK...
  ✓ BrainIAK version: 0.11
[4/4] Running SRM evaluation...
  Subject: sub-01
  ROI: V1
...
✅ Test completed successfully in XXXs
```

### Step 5: Submit Array Job (after successful test)

```bash
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Submit array job for all 40 subject-ROI pairs
sbatch sbatch/run_srm_evaluation.sbatch

# Monitor job
squeue -u haba6030

# Check outputs
tail -f logs/srm_eval_JOBID_*.out
```

**Expected runtime:** 3-4 hours total (parallel execution)

---

## Expected Results

### Within-Subject (evaluate_srm_vs_procrustes.py)

**Output files per subject-ROI:**
```
results/srm_evaluation/{TIMESTAMP}/
├── sub-01_V1_srm_results.json        # Metrics + comparison
├── sub-01_V1_srm_k_tuning.png        # Feature tuning curve
└── sub-01_V1_memory.log              # Memory usage
```

**Metrics in JSON:**
- Procrustes baseline: RDM correlation, decoding accuracy
- SRM results by k: RDM correlation, accuracy, variance explained
- Best k selection
- Improvement over Procrustes (absolute + percentage)
- Winner determination (SRM vs Procrustes)

**Expected improvements (based on literature):**
- RDM correlation: +5-15% (if SRM beneficial)
- Decoding accuracy: +3-8%
- Optimal k: 30-100 (depending on ROI voxel count)

### Between-Subject (evaluate_srm_between_subject.py)

**Output files per ROI:**
```
results/srm_between_subject/{TIMESTAMP}/
├── V1_srm_between_subject_results.json
├── V1_hc_cvd_disparity_comparison.png
└── V1_rdm_similarity_matrix.png
```

**Metrics in JSON:**
- HC-to-HC disparities (mean ± std)
- CVD-to-HC disparities (mean ± std)
- Statistical test (t-test, p-value)
- Inter-subject RDM correlations (HC-HC, CVD-CVD, HC-CVD)
- Effect size (Cohen's d)

---

## Verification Checklist

After array job completes:

- [ ] All 40 result files created (10 subjects × 4 ROIs)
- [ ] No OOM (Out of Memory) errors in logs
- [ ] Procrustes baseline metrics match Phase 1 results
- [ ] SRM improvements are reasonable (not suspiciously high/low)
- [ ] Best k values are within expected ranges per ROI
- [ ] Memory usage logs show peak < 32GB (job limit)

**Aggregate results:**
```bash
python aggregate_srm_results.py \
    --results-dir results/srm_evaluation/{TIMESTAMP} \
    --output-dir results/srm_evaluation/aggregated
```

**Visualize:**
```bash
python visualize_srm_comparison.py \
    --results-file results/srm_evaluation/aggregated/srm_summary.json \
    --output-dir results/srm_evaluation/figures
```

---

## Troubleshooting

### Issue: BrainIAK ImportError

**Solution:**
```bash
conda activate nilearn
conda install -c brainiak -c conda-forge brainiak
```

### Issue: Baseline files not found

**Check server path:**
```bash
ls /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline/
```

**Verify Phase 1 completed successfully**

### Issue: OOM (Out of Memory)

**For large ROIs (V1), reduce max concurrent tasks:**
```bash
# In sbatch script, line 8:
#SBATCH --array=1-40%5  # Run max 5 tasks at once (instead of default)
```

**Or increase memory:**
```bash
#SBATCH --mem=64G  # Double memory allocation
```

### Issue: SRM takes too long

**Expected runtimes:**
- V1 (354 voxels): ~10-15 min per subject
- V2 (279 voxels): ~8-12 min
- V3 (50 voxels): ~3-5 min
- hV4 (70 voxels): ~5-8 min

**If significantly longer:** Check if other users are running jobs on node2

---

## Success Criteria

✅ **Complete** when:
1. All 40 SRM evaluation tasks complete successfully
2. Results show meaningful SRM vs Procrustes comparison
3. Procrustes baseline matches Phase 1 results (validation)
4. SRM improvements are within expected ranges
5. Between-subject analysis shows HC-CVD disparities
6. Aggregate results and figures generated

---

## Next Steps (After Phase 3)

1. **Analyze SRM results:**
   - Determine if SRM > 5% improvement over Procrustes
   - Select optimal k per ROI
   - Decide on SRM adoption for future phases

2. **Phase 2 (Whitening):**
   - Can still be done later if needed
   - Will provide additional noise reduction
   - SRM scripts can be re-run on whitened data by simply updating paths

3. **Future Phases:**
   - Phase 1 (Hyperalignment): Use SRM or Procrustes based on Phase 3 results
   - Phase 2 (Forward Model): 360° hue encoder
   - Phase 3 (Filter): CVD transformation learning

---

## Files Summary

| File | Status | Purpose |
|------|--------|---------|
| `evaluate_srm_vs_procrustes.py` | ✅ Modified | Within-subject SRM evaluation |
| `evaluate_srm_between_subject.py` | ✅ Modified | Between-subject HC-CVD comparison |
| `run_srm_evaluation.sbatch` | ✅ Modified | SLURM array job script |
| `EXECUTION_GUIDE_PHASE3_SRM.md` | ✅ Updated | Step-by-step execution guide |
| `deploy_srm_to_server.sh` | ✅ New | Upload scripts to server |
| `test_srm_server_interactive.sh` | ✅ New | Interactive test on server |
| `test_srm_baseline_local.sh` | ✅ New | Local test (optional) |
| `aggregate_srm_results.py` | ⏸️ No changes | Aggregation (works as-is) |
| `visualize_srm_comparison.py` | ⏸️ No changes | Visualization (works as-is) |

---

**END OF SUMMARY**
