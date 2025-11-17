# Quick Start Guide - sbatch Reconstruction & CVD Analysis

## 🎯 Complete Workflow (One-Page Summary)

### Step 1: Upload to Server (LOCAL)
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp run_all_subjects.sh run_subject_all_rois.sh \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

scp visualize_Edits/fir_reconstruction_universal_hrf.py \
    visualize_Edits/fir_reconstruction_zScore.py \
    visualize_Edits/fir_reconstruction_zScore_voxelSelect.py \
    visualize_Edits/extract_colorblind_metrics.py \
    visualize_Edits/compare_subjects_cvd.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/visualize_Edits/
```

### Step 2: Server Setup (SERVER - only once)
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
chmod +x run_all_subjects.sh run_subject_all_rois.sh
mkdir -p logs/{pilot,sub-01,sub-02,sub-03,sub-04}
```

### Step 3: Run Reconstruction (SERVER)
```bash
# Choose one method:
bash run_all_subjects.sh universal_hrf --use-pca --n-components 6
bash run_all_subjects.sh zScore --use-pca --n-components 6
bash run_all_subjects.sh voxelSelect --use-pca --n-components 6

# This submits 5 jobs (one per subject, each processing 4 ROIs)

# Monitor:
squeue -u $USER  # Should show 5 jobs
tail -f logs/sub-01/reconstruction_*.out  # Watch specific subject
tail -f logs/*/reconstruction_*.out  # Watch all subjects
```

### Step 4: Extract CVD Metrics (SERVER - after jobs complete)
```bash
# Find your timestamp
ls -lt derivatives/ | head

# Set timestamp
TIMESTAMP=20250117_143022  # Replace with actual

# Extract metrics
for sub in P01 01 02 03 04; do
    python visualize_Edits/extract_colorblind_metrics.py \
        --subject $sub --timestamp $TIMESTAMP \
        --output-dir cvd_metrics_${TIMESTAMP}
done
```

### Step 5: Compare Groups (SERVER)
```bash
python visualize_Edits/compare_subjects_cvd.py \
    --cvd-subjects P01 \
    --non-cvd-subjects 01 02 03 04 \
    --metrics-dir cvd_metrics_${TIMESTAMP} \
    --output-dir cvd_comparison_${TIMESTAMP}
```

### Step 6: Download Results (LOCAL)
```bash
export TS=20250117_143022  # Replace with actual

# Download comparisons (recommended)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/cvd_comparison_${TS} ./
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/cvd_metrics_${TS} ./

# Or download full derivatives (large!)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/${TS} ./derivatives/
```

---

## 🔍 Key Verification Commands

```bash
# On SERVER:

# Count running jobs (should be 5 + 1 header = 6)
squeue -u $USER | wc -l

# Check which ROI each subject is processing
grep "Processing ROI" logs/*/reconstruction_*.out

# Count completed results (should be 20: 5 subjects × 4 ROIs)
find derivatives/$TIMESTAMP -name "results.pkl" | wc -l

# Check if all subjects processed
ls derivatives/$TIMESTAMP/
# Should show: pilot/ sub-01/ sub-02/ sub-03/ sub-04/

# Check for success/failures
grep -E "✓|✗" logs/*/reconstruction_*.out

# View final summaries
grep -A 10 "FINAL SUMMARY" logs/*/reconstruction_*.out
```

---

## 📊 Expected Outputs

### Reconstruction Results
```
derivatives/20250117_143022/
├── pilot/sub-01/fir_reconstruction_uni_hrf/
│   ├── V1_universal_hrf/results.pkl
│   ├── V2_universal_hrf/results.pkl
│   ├── V3_universal_hrf/results.pkl
│   └── hV4_universal_hrf/results.pkl
├── sub-01/ ... sub-04/ (same structure)
```

### CVD Metrics
```
cvd_metrics_20250117_143022/
├── P01_cvd_metrics.txt  # CVD subject
├── 01_cvd_metrics.txt   # Non-CVD
├── 02_cvd_metrics.txt
├── 03_cvd_metrics.txt
└── 04_cvd_metrics.txt
```

### Group Comparison
```
cvd_comparison_20250117_143022/
├── red_green_compression_comparison.png  # MOST IMPORTANT
├── novel_color_bias_comparison.png
├── color_space_structure_comparison.png
├── confusion_matrix_comparison.png
└── statistical_summary.txt
```

---

## 🎯 Key Findings to Look For

1. **Red-Green Compression Ratio** (primary CVD metric)
   - CVD (P01): Expected < 0.8 (compressed)
   - Non-CVD (01-04): Expected > 0.9 (preserved)
   - Statistical test: p < 0.05

2. **Novel Color Reconstruction Bias**
   - CVD: Systematic errors toward yellow/blue axis
   - Non-CVD: Random errors, no systematic bias

3. **Color Space Structure (MDS)**
   - CVD: Red-green dimension collapsed
   - Non-CVD: All dimensions preserved

---

## ⚠️ Troubleshooting

### Problem: Jobs not submitting
```bash
# Check SLURM status
sinfo
sinfo -n node2

# Try without nodelist specification
# Edit run_reconstruction.sh line 26: comment out #SBATCH --nodelist=node2
```

### Problem: All jobs fail
```bash
# Check first error
cat logs/slurm_P01_V1_*_*.err | head -50

# Verify conda environment
source /opt/ohba/anaconda/etc/profile.d/conda.sh
conda activate nilearn
python -c "import nilearn; print(nilearn.__version__)"
```

### Problem: ValueError in voxel selection
```bash
# This should be fixed with MAX criterion
# If still occurs, check:
grep "Functional voxel selection" logs/slurm_*_hV4_*.out
# Should show: "Selected X voxels out of Y (Z%)"
```

### Problem: Different timestamps
```bash
# Make sure you used run_all_subjects_rois.sh wrapper
# NOT individual sbatch commands

# If you have multiple timestamps, choose the latest:
ls -lt derivatives/ | head -5
```

---

## 📚 Detailed Documentation

- `SBATCH_GUIDE.md` - Complete sbatch usage guide
- `CVD_ANALYSIS_GUIDE.md` - CVD metrics theory and interpretation
- `VOXEL_SELECTION_METHODS.md` - Voxel selection approaches
- `CLAUDE.md` - Project overview and conventions

---

**Last Updated**: 2025-01-17
**Author**: Claude Code
**Purpose**: Quick reference for running complete reconstruction + CVD analysis pipeline
