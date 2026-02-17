# Drift Removal Validation Scripts

**Location**: `analysis/phase1_preprocess_decoding/validation/`
**Purpose**: Validate the C010 pipeline drift removal methodology
**Date**: 2026-02-16

---

## Quick Start

**Upload to server**:
```bash
scp validation/*.py validation/*.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/validation/
```

**Run on server**:
```bash
# SSH and navigate
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/validation

# Interactive mode (RECOMMENDED)
srun --nodelist=node2 --qos=shared --cpus-per-task=4 --mem=8G --time=1:00:00 --pty bash
source ~/.bashrc
conda activate nilearn

# Run validations (~35 min total)
python validate_drift_removal.py --subject 01 --roi V1
python validate_drift_removal.py --subject 01 --roi V2
python validate_onset_randomization.py --subject 01 --roi V1 --n-seeds 5
python validate_onset_randomization.py --subject 01 --roi V2 --n-seeds 5
```

**Download results**:
```bash
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/drift_validation ./
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/onset_validation ./
```

---

## Files

### Python Scripts

- **validate_drift_removal.py** (33 KB)
  - Compares 1st+2nd drift vs 2nd-only drift
  - Runtime: ~2.3 min per ROI
  - Memory: ~3.2 GB

- **validate_onset_randomization.py** (28 KB)
  - Verifies FIR robustness via onset shuffling
  - Runtime: ~14 min per ROI
  - Memory: ~3.2 GB

### SLURM Batch Files

- **validate_drift_removal.sbatch**
  - Settings: 8 GB, 30 min, 4 CPUs
  - Runs both V1 and V2

- **validate_onset_randomization.sbatch**
  - Settings: 8 GB, 1 hour, 4 CPUs
  - Runs both V1 and V2

### Documentation

- **README.md** (this file) - Quick reference
- **VALIDATION_QUICKSTART.md** - Step-by-step guide
- **DRIFT_VALIDATION_README.md** - Comprehensive documentation
- **VALIDATION_OPTIMIZATION_SUMMARY.md** - Resource optimization details

---

## Resource Requirements (Optimized)

Based on actual testing:
- **Memory**: 3.2 GB (allocated 8 GB for 2.5x headroom)
- **Time**: ~35 min total for all validations
- **CPU**: 97% utilization with 4 cores

---

## Output Structure

```
derivatives/
├── drift_validation/
│   └── sub-01/
│       ├── V1/
│       │   ├── drift_comparison.json
│       │   ├── drift_comparison.png
│       │   ├── 2nd_only/
│       │   │   ├── hrf_variability.png
│       │   │   ├── metrics.json
│       │   │   └── *.npy files
│       │   └── 1st_2nd/
│       │       └── (same structure)
│       └── V2/ (same structure)
│
└── onset_validation/
    └── sub-01/
        ├── V1/
        │   ├── onset_validation.json
        │   ├── onset_validation.png
        │   ├── original/
        │   │   ├── hrf_variability.png
        │   │   ├── fir_quality.json
        │   │   └── *.npy files
        │   ├── random_seed42/
        │   ├── random_seed43/
        │   ├── random_seed44/
        │   ├── random_seed45/
        │   └── random_seed46/
        └── V2/ (same structure)
```

---

## Interpretation

### Drift Comparison

**Good result** (current method sufficient):
- HRF correlation difference < 0.01
- RDM reliability similar

**Action needed**:
- HRF correlation difference > 0.05 → Consider 1st+2nd drift

### Onset Randomization

**KEY METRIC: HRF Correlation Drop**

**Good result** (FIR is robust):
- Original HRF correlation: ~0.90 (high)
- Randomized HRF correlation: ~0.0-0.2 (low)
- **Correlation drop > 0.5** → Temporal structure is REAL ✓

**Warning sign** (drift contamination):
- Original HRF correlation: ~0.90
- Randomized HRF correlation: ~0.85 (still high!)
- **Correlation drop < 0.1** → Drift contamination ⚠

**Secondary metrics**:
- FIR shape: Convex → Random/flat (good)
- FIR shape: Linear ramp persists (warning)

---

## For More Details

- Quick guide: `VALIDATION_QUICKSTART.md`
- Full documentation: `DRIFT_VALIDATION_README.md`
- Optimization analysis: `VALIDATION_OPTIMIZATION_SUMMARY.md`

---

**Last updated**: 2026-02-16
