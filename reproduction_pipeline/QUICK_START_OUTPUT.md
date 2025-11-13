# Quick Start: Using Output Directory

This guide helps you run the reproduction pipeline using data from `/scratch/connectome/haba6030/colorBlind/output`.

## 🎯 What's Different?

| Main Version | Output Version |
|--------------|----------------|
| Uses reorganized data structure | Uses old `/output` directory |
| `config_reproduction.py` | `config_reproduction_output.py` |
| `build_rois_reproduction.py` | `build_rois_reproduction_output.py` |
| Results → `derivatives/` | Results → `output/derivatives_reproduction/` |

## 📋 Step-by-Step Instructions

### 1. Upload Files to Server

From your **local machine**:

```bash
# Upload reproduction pipeline directory
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
scp -r reproduction_pipeline/ haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. Discover Data Paths (IMPORTANT!)

SSH to server and find where your data actually is:

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/reproduction_pipeline

# Run path discovery
python3 << 'EOF'
from pathlib import Path
import os

base = Path("/scratch/connectome/haba6030/colorBlind/output")
print(f"\nSearching in: {base}\n")
print("="*70)

if not base.exists():
    print(f"ERROR: {base} does not exist!")
    print("\nTry these alternatives:")
    print("  - /scratch/connectome/haba6030/colorBlind/")
    print("  - /storage/connectome/haba6030/fmriprep_out/")
else:
    # Find subject directories
    print("\nSubject directories found:")
    for item in sorted(base.iterdir()):
        if item.is_dir() and item.name.startswith('sub-'):
            print(f"\n  📁 {item}")

            func_dir = item / "func"
            if func_dir.exists():
                bold = list(func_dir.glob("*bold.nii.gz"))
                events = list(func_dir.glob("*events.tsv"))
                confounds = list(func_dir.glob("*confounds*.tsv"))

                print(f"     BOLD files: {len(bold)}")
                print(f"     Event files: {len(events)}")
                print(f"     Confound files: {len(confounds)}")

                if bold:
                    print(f"     Example BOLD: {bold[0].name}")
                if events:
                    print(f"     Example event: {events[0].name}")

print("\n" + "="*70)
EOF
```

### 3. Update Config Based on Discovery

Edit `config_reproduction_output.py` based on what you found:

```bash
# Edit config
nano config_reproduction_output.py

# Update these lines (around line 85-95):
# If data is in /output/sub-01/func/
FMRIPREP_BASE = Path("/scratch/connectome/haba6030/colorBlind/output")

# OR if fMRIPrep data is still in storage
# FMRIPREP_BASE = Path("/storage/connectome/haba6030/fmriprep_out")
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

### 4. Verify Setup

```bash
python verify_setup_output.py
```

**Expected output:**
```
✓✓✓ ALL CHECKS PASSED
```

**If you see errors**, update the paths in `config_reproduction_output.py` accordingly.

### 5. Run Reproduction

**Option A: Interactive (Recommended for first time)**

```bash
# Step 1: Build ROI masks
python build_rois_reproduction_output.py

# Expected output:
#   V1: 344 voxels
#   V2: 310 voxels
#   hV4: 55 voxels

# Step 2: Run analysis for V2 (best ROI)
python run_reconstruction_reproduction_output.py --roi V2

# Expected output:
#   Novel error: 52.4° ✓
```

**Option B: SLURM Batch (Run all ROIs automatically)**

```bash
# Submit job
sbatch run_reproduction_output.sbatch

# Check job status
squeue -u $USER

# Monitor progress
tail -f logs/reproduce_output_JOBID.out

# Check for errors
tail -f logs/reproduce_output_JOBID.err
```

### 6. Download Results

From your **local machine**:

```bash
# Download all results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/output/derivatives_reproduction/ ./

# Or download just summaries
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/output/derivatives_reproduction/sub-01/fir_reconstruction_reproduction/*/summary.csv ./
```

## 🔍 Expected Results

If everything works correctly, you should see:

```
======================================================================
REPRODUCTION RESULTS
======================================================================
ROI: V2
Voxels: 310
Optimal delay: 5 TRs (7.5s)
Classification: 100.0%
Training error: 4.1°
Novel error: 52.4°

COMPARISON WITH DOCUMENTED RESULTS:
  Voxels: 310 vs 310 (expected) ✓
  Delay: 5 vs 5 TRs (expected) ✓
  Classification: 100.0% vs 100.0% (expected) ✓
  Training: 4.1° vs 4.1° (expected) ✓
  Novel: 52.4° vs 52.4° (expected) ✓

✓✓✓ EXCELLENT MATCH - Results successfully reproduced!
```

## ❌ Troubleshooting

### "fMRIPrep directory not found"

**Check where your functional data actually is:**
```bash
find /scratch/connectome/haba6030 -name "*task-rsvp*bold.nii.gz" -type f 2>/dev/null | head -5
```

Update `FMRIPREP_BASE` in `config_reproduction_output.py` to match.

### "Event file not found"

**Check where your event files are:**
```bash
find /scratch/connectome/haba6030 -name "*task-rsvp*events.tsv" -type f 2>/dev/null | head -5
```

The config tries multiple locations automatically. If none work, manually set the path in `get_event_file_path()`.

### "Atlas directory not found"

**Check atlas location:**
```bash
ls /scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/subj_vol_all/
```

Update `ATLAS_DIR` in config if needed.

### Results don't match expected values

**Possible causes:**
1. Wrong data - check you're using sub-01 (pilot) data
2. Wrong voxel counts - ROI masks may be different
3. Different preprocessing - check fMRIPrep version/settings

**Debug:**
```bash
# Check voxel counts
python -c "
import nibabel as nib
import numpy as np
roi = nib.load('/scratch/connectome/haba6030/colorBlind/output/derivatives_reproduction/sub-01/roi/sub-01_V2_mask.nii.gz')
print(f'V2 voxels: {int(np.sum(roi.get_fdata() > 0))}')
"
```

## 📊 Output Structure

```
/scratch/connectome/haba6030/colorBlind/output/
└── derivatives_reproduction/
    └── sub-01/
        ├── roi/
        │   ├── sub-01_V1_mask.nii.gz
        │   ├── sub-01_V2_mask.nii.gz
        │   ├── sub-01_hV4_mask.nii.gz
        │   └── sub-01_epi_mask.nii.gz
        └── fir_reconstruction_reproduction/
            ├── V1_universal_hrf/
            │   ├── log.txt
            │   ├── summary.csv
            │   └── figures/
            ├── V2_universal_hrf/
            │   ├── log.txt
            │   ├── summary.csv  ← Main result!
            │   └── figures/
            └── hV4_universal_hrf/
                ├── log.txt
                ├── summary.csv
                └── figures/
```

## 🎉 Success Criteria

You've successfully reproduced the results if:

- ✅ V2 novel error: **52.4° ± 2°**
- ✅ V1 novel error: **64.1° ± 2°**
- ✅ hV4 novel error: **75.0° ± 2°**
- ✅ All classification accuracies: **100%**
- ✅ Voxel counts match expected (±5%)

## 📞 Need Help?

1. Check `USE_OUTPUT_DIRECTORY.md` for detailed troubleshooting
2. Review `config_reproduction_output.py` comments
3. Verify paths using the discovery script (Step 2)
4. Compare with original `config_reproduction.py` to see differences

---

**Created:** 2025-11-09
**Purpose:** Reproduce results using old `/output` directory structure
**Status:** Ready to use
