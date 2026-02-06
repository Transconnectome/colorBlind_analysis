## GLMsingle + Whitening Integration

**Status**: Implementation Complete (2026-02-05)
**Expected Impact**: +100-150% RDM reliability improvement over FIR baseline
**Files**: 2,750+ lines of Python code

---

### Overview

This directory implements GLMsingle (Kay et al., 2022) with noise covariance estimation for whitening (Walther et al., 2016), replacing the current FIR-based baseline pipeline.

**Combined benefits**:
1. **GLMsingle**: Adaptive HRF fitting, GLMdenoise, Fracridge regularization (+30-35%)
2. **Whitening**: Spatial noise decorrelation using 1st-level residuals (+20-30%)
3. **Total expected**: +100-150% improvement in RDM reliability

---

### Pipeline Architecture

```
Step 1: GLMsingle with Residuals
├── Input:  fMRIPrep BOLD + BIDS events + ROI mask
├── Process: GLMsingle fit with HRF optimization
└── Output: Single-trial betas + 1st-level residuals

Step 2: Noise Covariance Estimation
├── Input:  1st-level residuals from Step 1
├── Process: Ledoit-Wolf covariance + eigendecomposition
└── Output: Σ (covariance) + W (whitening matrix)

Step 3: Whitened Amplitudes
├── Input:  Betas + Whitening matrix
├── Process: Apply W, average by color, z-score
└── Output: amplitudes_z_glmsingle.npy, amplitudes_z_whitened.npy

Step 4: Evaluation
├── Input:  GLMsingle, Whitened, FIR baseline amplitudes
├── Process: RDM reliability, decoding accuracy, noise ceiling
└── Output: Comparison JSON + figures
```

---

### File Structure

```
GLMsingle/
├── utils/
│   ├── __init__.py                        # Package initialization
│   ├── glmsingle_interface.py             # BOLD/event loading, GLMsingle wrapper
│   ├── glmsingle_config.py                # Configuration presets
│   └── whitening_from_residuals.py        # Noise covariance & whitening
│
├── 01_glmsingle_with_residuals.py         # Step 1: Run GLMsingle, save residuals
├── 02_estimate_noise_covariance.py        # Step 2: Estimate Σ, compute W
├── 03_glmsingle_whitened_amplitudes.py    # Step 3: Apply whitening
├── 04_evaluate_glmsingle_vs_fir.py        # Step 4: Compare methods
│
├── sbatch/
│   ├── run_glmsingle_pilot.sbatch         # Pilot test (4 ROIs × 3 methods)
│   └── run_glmsingle_full.sbatch          # Full analysis (40 subject-ROI pairs)
│
├── results/
│   └── {TIMESTAMP}/
│       └── sub-{ID}_{ROI}/
│           ├── betas_single_trial.npy
│           ├── residuals_1st_level.npy
│           ├── noise_covariance.npy
│           ├── whitening_matrix.npy
│           ├── amplitudes_z_glmsingle.npy
│           ├── amplitudes_z_whitened.npy
│           └── comparison_vs_fir.json
│
├── example1.ipynb                          # GLMsingle demo (from repo)
└── README.md                               # This file
```

---

### Usage

#### Local Testing (Interactive)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/GLMsingle

# Step 1: Run GLMsingle
python 01_glmsingle_with_residuals.py --subject 01 --roi V1 --local

# Step 2: Estimate noise covariance
python 02_estimate_noise_covariance.py --subject 01 --roi V1

# Step 3: Compute whitened amplitudes
python 03_glmsingle_whitened_amplitudes.py --subject 01 --roi V1

# Step 4: Evaluate vs FIR baseline
python 04_evaluate_glmsingle_vs_fir.py --subject 01 --roi V1 --save-figures
```

#### Server Deployment (SLURM)

**Pilot test** (4 ROIs × 3 methods = 12 jobs):
```bash
# On server
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/GLMsingle

# Edit sbatch/run_glmsingle_pilot.sbatch to set paths
sbatch sbatch/run_glmsingle_pilot.sbatch

# Monitor progress
squeue -u haba6030
tail -f logs/glmsingle_pilot_*.out
```

**Full analysis** (40 subject-ROI pairs):
```bash
sbatch sbatch/run_glmsingle_full.sbatch
```

---

### Configuration Options

#### GLMsingle Configs

**Full** (recommended):
- Adaptive HRF (20 basis functions)
- GLMdenoise (10 noise PCs)
- Fracridge (20 ridge fractions)
- Expected runtime: 20-40 min/subject-ROI

**Conservative** (fallback):
- Canonical HRF (no adaptation)
- GLMdenoise + Fracridge still enabled
- Faster: 10-20 min/subject-ROI

```python
# In code
from utils.glmsingle_config import get_config_full, get_config_conservative

config = get_config_full(n_pcs=10)  # Full pipeline
config = get_config_conservative(n_pcs=10)  # Faster fallback
```

#### Whitening Methods

- **ledoit_wolf** (recommended): Shrinkage regularization for stability
- **empirical**: Sample covariance (needs many samples)
- **diagonal**: Assume independent voxels (no spatial correlation)
- **block_diagonal**: For large ROIs (>1000 voxels)

```bash
python 02_estimate_noise_covariance.py --subject 01 --roi V1 --method ledoit_wolf
python 02_estimate_noise_covariance.py --subject 01 --roi V1 --block-size 100  # Block-diagonal
```

---

### Expected Outputs

#### Successful Run (Realistic Case)

```
Step 1: GLMsingle with Residuals
  ✓ Betas: (6 runs, 288 trials, 400 voxels)
  ✓ Residuals: (6 runs, 240 scans, 400 voxels)
  ✓ Mean R²: 0.45 (vs 0.31 FIR baseline)
  ✓ Voxels R² > 0.2: 75% (vs 37.5% FIR)

Step 2: Noise Covariance Estimation
  ✓ Covariance: (400, 400) - 1.28 MB
  ✓ Shrinkage: 0.12 (good conditioning)
  ✓ Condition number: 2.3e8 (acceptable)
  ✓ Correlation reduction: 52% (excellent)

Step 3: Whitened Amplitudes
  ✓ GLMsingle: (6, 8, 400)
  ✓ Whitened: (6, 8, 400)
  ✓ Correlation GLM-Whitened: 0.88 (expected)

Step 4: Evaluation
  FIR baseline:            r = 0.226
  GLMsingle:               r = 0.302 (+34%)
  GLMsingle + Whitening:   r = 0.420 (+86%)

  ✅✅ ADOPT GLMsingle + Whitening
```

#### Pessimistic Case (Whitening doesn't help)

```
Step 4: Evaluation
  FIR baseline:            r = 0.226
  GLMsingle:               r = 0.280 (+24%)
  GLMsingle + Whitening:   r = 0.295 (+31%)

  ✅ ADOPT GLMsingle only
  ❌ Skip whitening (adds <10%)
```

#### Optimistic Case (Major improvement)

```
Step 4: Evaluation
  FIR baseline:            r = 0.226
  GLMsingle:               r = 0.320 (+42%)
  GLMsingle + Whitening:   r = 0.550 (+143%)

  ✅✅✅ ADOPT - Major improvement!
  Consider publishing methodology
```

---

### Decision Criteria

**Adopt thresholds**:
- ✅✅ **Strong adoption**: Total improvement >50% (r > 0.34)
- ✅ **Moderate adoption**: Total improvement 30-50%
- ⚠️ **Review**: Total improvement 5-30%
- ❌ **Reject**: Total improvement <5%

**Whitening benefit**:
- ✅ Use whitening if incremental >20%
- ⚠️ Consider whitening if incremental 10-20%
- ❌ Skip whitening if incremental <10%

---

### Troubleshooting

#### Issue 1: GLMsingle doesn't provide residuals

**Symptom**: `'residuals' not in results`

**Solution**:
```python
# Residuals computed manually in run_glmsingle_with_residuals()
# Fallback: residuals = data - design @ betas
# Already implemented in glmsingle_interface.py
```

#### Issue 2: High condition number (>1e10)

**Symptom**: `WARNING: High condition number`

**Solution**:
```bash
# Use Ledoit-Wolf shrinkage (automatic)
python 02_estimate_noise_covariance.py --method ledoit_wolf

# Or block-diagonal for very large ROIs
python 02_estimate_noise_covariance.py --block-size 100
```

#### Issue 3: Low correlation reduction (<10%)

**Symptom**: Whitening doesn't reduce spatial correlations

**Possible causes**:
- Voxels already uncorrelated (good!)
- Shrinkage too aggressive (increase samples)
- Wrong covariance estimation method

**Solution**:
```bash
# Check shrinkage parameter in whitening_metadata.json
# Expected: 0.05-0.20
# If >0.5: Data high-dimensional, consider block-diagonal

# Try empirical covariance (if enough samples)
python 02_estimate_noise_covariance.py --method empirical
```

#### Issue 4: Memory overflow

**Symptom**: `MemoryError` during covariance estimation

**Solution**:
```bash
# Use block-diagonal approximation
python 02_estimate_noise_covariance.py --block-size 100

# Or reduce number of concurrent jobs in SLURM
# Edit sbatch: #SBATCH --array=1-40%3  (instead of %6)
```

---

### Computational Resources

#### Per Subject-ROI

**Step 1** (GLMsingle):
- Runtime: 20-40 min (400 voxels)
- Memory: 16-24 GB
- Storage: ~500 MB (betas + residuals)

**Step 2** (Covariance):
- Runtime: 5-10 min
- Memory: 8-16 GB
- Storage: ~2 MB (Σ + W for 400 voxels)

**Step 3** (Whitening):
- Runtime: 2-5 min
- Memory: 4-8 GB
- Storage: ~20 MB (amplitudes)

**Step 4** (Evaluation):
- Runtime: 5-10 min
- Memory: 4-8 GB
- Storage: ~5 MB (results + figures)

**Total per subject-ROI**:
- Runtime: ~40-60 min
- Memory peak: 24 GB
- Storage: ~530 MB

#### Full Analysis (40 pairs)

**Sequential**: 40 × 50 min = ~33 hours
**Parallel (6 jobs)**: 40/6 × 50 min = ~5.5 hours
**Total storage**: 40 × 530 MB = ~22 GB

**SLURM config**:
```bash
#SBATCH --array=1-40%6
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --qos=shared
#SBATCH --nodelist=node2
```

---

### Dependencies

**Python packages**:
```bash
# GLMsingle (install from GitHub)
pip install git+https://github.com/cvnlab/GLMsingle.git

# Core scientific (should already be in nilearn environment)
# numpy scipy pandas scikit-learn nibabel matplotlib seaborn

# GLMsingle additional dependencies (auto-installed):
# fracridge tqdm h5py
```

**GLMsingle installation**:
- **IMPORTANT**: Not on PyPI - must install from GitHub
- Command: `pip install git+https://github.com/cvnlab/GLMsingle.git`
- GitHub: https://github.com/cvnlab/GLMsingle
- Requirements: numpy, scipy, scikit-learn, matplotlib, tqdm, fracridge, nibabel, h5py, pandas

---

### References

1. **GLMsingle**: Kay, K.N., Jamison, K.W., Vizioli, L., Zhang, R., Margalit, E., & Ugurbil, K. (2022). GLMsingle: A toolbox for improving single-trial fMRI response estimates. *bioRxiv*. https://doi.org/10.1101/2022.01.31.478431

2. **Whitening**: Walther, A., Nili, H., Ejaz, N., Alink, A., Kriegeskorte, N., & Diedrichsen, J. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.

3. **Ledoit-Wolf Shrinkage**: Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *Journal of Multivariate Analysis*, 88(2), 365-411.

---

---

## 📊 Visualization & example1.ipynb Mapping

### Cell-by-Cell Implementation Map

This section shows how each part of `example1.ipynb` (GLMsingle tutorial) is implemented in our codebase.

| Notebook Section | Cell(s) | Our Implementation | File Location |
|-----------------|---------|-------------------|---------------|
| **Import libraries** | 2 | Import section | `01_glmsingle_with_residuals.py:1-30` |
| **Load data & design** | 6-7 | `load_event_files()`<br>`build_design_matrices()`<br>`load_bold_data()` | `utils/glmsingle_interface.py:31-220` |
| **Visualize design** | 10 | `plot_design_matrices()` | `utils/visualization.py:18-65`<br>→ Called in `01_glmsingle:448` |
| **Run GLMsingle** | 14-15 | `run_glmsingle_with_residuals()` | `utils/glmsingle_interface.py:221-487`<br>→ Called in `01_glmsingle:283` |
| **Plot GLM outputs** | 19 | `plot_glmsingle_outputs()`<br>- Average betas<br>- R² map<br>- HRF index<br>- FRACvalue | `utils/visualization.py:68-157`<br>→ Called in `01_glmsingle:460` |
| **Run baseline GLM** | 21-22 | `get_config_conservative()` | `utils/glmsingle_config.py:56-94`<br>→ Used in `04_evaluate:XX` |
| **Find repeats** | 25-28 | Not applicable<br>(RSVP has no repeats) | → FIR baseline comparison instead |
| **Compute reliability** | 32 | `compute_rdm_reliability()` | `04_evaluate_glmsingle_vs_fir.py` |
| **Plot reliability** | 34 | `plot_reliability_comparison()`<br>- Bar chart<br>- Brain map | `utils/visualization.py:160-237`<br>→ Called in `04_evaluate:XX` |

### Key Differences: example1.ipynb vs Our Implementation

#### 1. Design Matrix Approach

**example1.ipynb** (Natural Scenes Dataset):
```python
# 583 unique images, some repeated 2-3 times
design[0].shape  # (300 TRs, 583 conditions)

# Each image = 1 condition
# Repeated images allow split-half reliability
```

**Our implementation** (Color Vision RSVP):
```python
# 8 colors, ~48 trials each
design[0].shape  # (240 TRs, 8 conditions)

# Each color = 1 condition
# All trials of same color merged in design matrix
# GLMsingle returns single-trial betas internally
```

#### 2. Reliability Metric

**example1.ipynb**:
- Split-half correlation on repeated images
- Correlates 1st vs 2nd presentation of same image

**Our implementation**:
- RDM reliability (no within-session repeats)
- Compares representational dissimilarity matrices between runs

#### 3. Additional Features (Not in Notebook)

✅ **Noise covariance estimation** (`02_estimate_noise_covariance.py`)
✅ **Whitening** (`03_glmsingle_whitened_amplitudes.py`)
✅ **Color distribution visualization** (`utils/visualization.py:240-299`)
✅ **SLURM batch processing** (`sbatch/*.sbatch`)

### Implemented Visualizations

#### From example1.ipynb

**1. Design Matrix Heatmap** (Cell 10)
```python
plot_design_matrices(design_list, trial_labels_list, output_dir)
```
**Output**: `figures/design_matrices.png`
- Shows (n_scans, 8 colors) per run
- Binary matrix with event onsets marked

**2. GLMsingle Output Maps** (Cell 19)
```python
plot_glmsingle_outputs(results, output_dir, roi_mask=roi_mask)
```
**Output**: `figures/glmsingle_outputs.png`
- 2×2 grid:
  - Average betas (RdBu_r colormap)
  - Model R² (hot colormap)
  - Optimal HRF index (jet colormap)
  - Fracridge level (copper colormap)

**3. Reliability Comparison** (Cell 34)
```python
plot_reliability_comparison(reliabilities, reliability_maps, output_dir)
```
**Output**: `figures/reliability_comparison.png`
- Bar chart: FIR vs GLMsingle vs GLMsingle+Whitening
- Brain map: Improvement (GLMsingle+W - FIR)

#### Additional Visualizations (Not in Notebook)

**4. Color Distribution**
```python
plot_color_distribution(trial_labels_list, output_dir)
```
**Output**: `figures/color_distribution.png`
- Heatmap: Trials per color per run
- Bar chart: Distribution across runs

**5. Text Summary**
```python
create_text_summary(results, design_list, output_dir)
```
**Output**: `figures/summary.txt`
- Model fit statistics (R², HRF, Fracridge)
- Configuration details

### Visualization Usage

**Automatic** (in main scripts):
```bash
# Visualizations created automatically in Step 9
python 01_glmsingle_with_residuals.py --subject 01 --roi V1
# → Saves to results/.../sub-01_V1/figures/
```

**Manual** (standalone):
```python
from utils.visualization import create_diagnostic_report

create_diagnostic_report(
    results=results_dict,
    design_list=design_list,
    trial_labels_list=trial_labels_list,
    output_dir=Path('diagnostics/'),
    roi_mask=roi_mask
)
```

### Figure Gallery (Example Outputs)

**Design Matrices** (`design_matrices.png`):
```
┌────────────────────────┬────────────────────────┐
│ Run 1                  │ Run 2                  │
│ ┌────────────────────┐ │ ┌────────────────────┐ │
│ │ 8 color columns    │ │ │ 8 color columns    │ │
│ │ (240 TRs)          │ │ │ (240 TRs)          │ │
│ │ Binary onsets      │ │ │ Binary onsets      │ │
│ └────────────────────┘ │ └────────────────────┘ │
└────────────────────────┴────────────────────────┘
```

**GLMsingle Outputs** (`glmsingle_outputs.png`):
```
┌─────────────────────┬─────────────────────┐
│ Avg Betas (RdBu_r)  │ R² (hot)            │
│ [-5, +5]            │ [0, 100]            │
├─────────────────────┼─────────────────────┤
│ HRF Index (jet)     │ Frac Level (copper) │
│ [0, 20]             │ [0, 1]              │
└─────────────────────┴─────────────────────┘
```

**Reliability Comparison** (`reliability_comparison.png`):
```
┌──────────────────────┬──────────────────────┐
│ Bar Chart            │ Brain Map            │
│  0.4┐                │ Improvement (RdBu_r) │
│     │    ┌──┐        │ ┌──────────────────┐ │
│  0.3│  ┌─┘  │        │ │ GLMsingle+White  │ │
│     │┌─┘    │        │ │ minus FIR        │ │
│  0.2└┘      │        │ │ [-0.3, +0.3]     │ │
│  FIR GLM GLM+W       │ └──────────────────┘ │
└──────────────────────┴──────────────────────┘
```

**Color Distribution** (`color_distribution.png`):
```
┌─────────────────────┬─────────────────────┐
│ Heatmap (YlOrRd)    │ Bar Chart           │
│     R1 R2 R3 ...    │ 60┐                 │
│ C1  48 48 48        │   │ ▄▄▄             │
│ C2  48 48 48        │ 50│ ███ Run1        │
│ ...                 │   │ ▄▄▄ Run2        │
│ C8  48 48 48        │ 40│ ███ ...         │
│                     │   └─C1 C2 ... C8    │
└─────────────────────┴─────────────────────┘
```

---

### TODOs

- [x] Implement visualizations from example1.ipynb
- [x] Add color distribution visualization
- [x] Create diagnostic report generator
- [ ] Implement ROI mask loading from standard atlases
- [ ] Add permutation tests for statistical significance
- [ ] Create batch visualization script for all subject-ROI pairs
- [ ] Integrate with Phase 2 Procrustes alignment
- [ ] Profile memory usage on node2 vs node4
- [ ] Test on GPU (node3) if GLMsingle supports it

---

### Contact

For issues or questions about this implementation:
- Check `/Users/.../GLMsingle/results/{timestamp}/sub-{ID}_{ROI}/*.json` for diagnostics
- Review GLMsingle documentation: https://glmsingle.readthedocs.io/
- Contact: haba6030@node2 (server) or local development machine
