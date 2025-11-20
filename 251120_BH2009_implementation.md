# 251120 - B&H 2009 Faithful Implementation

## User Request (Korean)
251120_perRun_editDirection.md에 fir_reconstruction_perRun.py를 수정하기 위한 방향과 pseudo-code를 제공하였습니다. 새로운 파일을 제작하여서 해당 수정 사항을 정확하게 반영해주시길 바랍니다.

## Analysis

Based on `251120_perRun_editDirection.md`, the current per-run code has 5 major differences from Brouwer & Heeger (2009):

### 1. Use 8 FIR delays (not 10)
- **Paper**: 12s window, 8 time points at 1.5s TR
- **Previous code**: 10 delays (0-9 TR)
- **Fix**: `FIR_DELAYS = np.arange(8)  # 0,1,2,3,4,5,6,7`

### 2. Voxel-wise HRF estimation via pseudo-inverse (not optimal delay)
- **Paper**:
  - Step 1: For each voxel, build FIR design (8 delays) → estimate full voxel-wise HRF via `h_v = pinv(X) @ y`
  - Average voxel HRFs (from high R² voxels) → ROI HRF
  - Use entire ROI HRF shape as basis function
- **Previous code**:
  - FIR GLM extracts delay-specific betas
  - Compute universal_hrf → select single peak delay
  - Use beta at that single delay as "amplitude"
- **Fix**: Implement voxel-wise FIR deconvolution with pseudo-inverse

### 3. R² threshold: top 50% voxels only
- **Paper**: Select top 50% voxels by R² (model fit) to compute ROI HRF
- **Previous code**: Use all voxels in ROI mask (no R² filtering)
- **Fix**: Calculate R² per voxel → select top 50% → average to get ROI HRF

### 4. 2nd-level GLM with HRF + derivative regressors
- **Paper**:
  1. Use ROI average HRF h(t) and derivative h'(t)
  2. For 8 colors: create design matrix [color_i ⊗ h, color_i ⊗ h'] → 16 columns
  3. Per voxel, per run: β = pinv(X) @ y
  4. First 8 betas = color amplitudes, last 8 (derivative) discarded
  5. Z-score per voxel per run across 8 colors
- **Previous code**:
  - Uses single peak delay beta as amplitude (not 2nd-level GLM)
  - No derivative regressors
- **Fix**: Implement 2nd-level GLM with 16-column design matrix

### 5. ROI average HRF computation
- **Paper**:
  - Color-ignored FIR
  - Voxel-wise HRF
  - R² selection
  - Average HRFs
- **Previous code**:
  - Computes universal_hrf by averaging FIR betas across colors and voxels
  - Mathematically different from paper's approach
- **Fix**: Follow exact sequence: color-ignored FIR → voxel HRF → R² selection → average

## Implementation

Created **`fir_reconstruction_BH2009.py`** with the following key features:

### Pipeline Overview
```python
# Step 1: Voxel-wise FIR HRF estimation (8 delays)
FIR_DELAYS = np.arange(8)  # 0-7 delays

for voxel in ROI_voxels:
    y = concatenate_all_runs(fmri_data[:, voxel])
    X_fir = build_fir_design_matrix(all_onsets, FIR_DELAYS)  # color-ignored
    h_v = np.linalg.pinv(X_fir) @ y  # (8,)
    HRF_voxel[voxel] = h_v

    # Compute R²
    y_pred = X_fir @ h_v
    r2[voxel] = compute_r2(y, y_pred)

# Step 2: Voxel selection (top 50% by R²)
r2_threshold = np.median(r2_voxel)
selected_voxels = r2_voxel >= r2_threshold

# Step 3: ROI average HRF
ROI_HRF = np.mean(HRF_voxel[selected_voxels], axis=0)
ROI_HRF_deriv = np.gradient(ROI_HRF)

# Step 4: 2nd-level GLM (per run, 16-column design)
for run in runs:
    y_run = fmri_data[run][:, selected_voxels]  # (n_scans, n_voxels)

    # Build design: [color_1⊗h, ..., color_8⊗h, color_1⊗h', ..., color_8⊗h']
    X_2nd = []
    for color in range(1, 9):
        stick = create_stick_function(events[events.color == color])
        X_2nd.append(np.convolve(stick, ROI_HRF)[:n_scans])
    for color in range(1, 9):
        stick = create_stick_function(events[events.color == color])
        X_2nd.append(np.convolve(stick, ROI_HRF_deriv)[:n_scans])
    X_2nd = np.column_stack(X_2nd)  # (n_scans, 16)

    # Amplitude estimation per voxel
    for voxel in selected_voxels:
        beta = np.linalg.pinv(X_2nd) @ y_run[:, voxel]  # (16,)
        amplitudes[run, :, voxel] = beta[:8]  # Keep only HRF betas

# Step 5: Z-score normalization
amplitudes_z = zscore(amplitudes, axis=1)  # Per voxel, per run, across colors

# Step 6: Classification and Reconstruction (unchanged)
# ... leave-one-run-out CV with 6-channel forward model
```

### Key Differences from Previous Code

| Aspect | Previous Code | New Code (BH2009) |
|--------|--------------|-------------------|
| FIR delays | 10 delays (0-14) | 8 delays (0-7) |
| HRF estimation | Optimal delay selection | Voxel-wise pseudo-inverse |
| Voxel selection | All voxels in mask | Top 50% by R² |
| Amplitude estimation | Single delay beta | 2nd-level GLM (16 columns) |
| Derivative | Not used | Included (but discarded) |

### File Structure

**`fir_reconstruction_BH2009.py`**
- Lines 1-120: Configuration and helper functions
- Lines 121-197: Argument parsing and setup
- Lines 198-244: Load ROI mask
- Lines 245-298: Load functional data
- Lines 299-351: **Step 1: Voxel-wise FIR HRF estimation**
- Lines 352-362: **Step 2: Voxel selection (top 50% by R²)**
- Lines 363-414: **Step 3: ROI average HRF and derivative**
- Lines 415-458: **Step 4: 2nd-level GLM amplitude estimation**
- Lines 459-469: **Step 5: Z-score normalization**
- Lines 470-518: **Step 6: Classification**
- Lines 519-650: **Step 7: Reconstruction**
- Lines 651-end: Save results

### SBATCH Script

Created **`run_BH2009.sbatch`** for server execution:

```bash
#!/bin/bash
#SBATCH --job-name=BH2009_reconstruction
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/BH2009_%A_%a.out
#SBATCH --error=logs/BH2009_%A_%a.err
#SBATCH --array=0-23  # 4 subjects × 6 ROIs

source ~/.bashrc
conda activate nilearn

SUBJECTS=(P01 01 02 03)
ROIS=(V1 V2 V3 hV4 BrainMask)

SUBJECT_IDX=$((SLURM_ARRAY_TASK_ID / 6))
ROI_IDX=$((SLURM_ARRAY_TASK_ID % 6))

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}

python fir_reconstruction_BH2009.py \
    --subject $SUBJECT \
    --roi $ROI \
    --use-pca \
    --n-components 6
```

## Server Deployment Procedure

### (1) Upload Code to Server

```bash
# From local machine
scp fir_reconstruction_BH2009.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

scp run_BH2009.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### (2) Run on Server

```bash
# SSH to server
ssh haba6030@node2

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory
mkdir -p logs

# Submit job array
sbatch run_BH2009.sbatch

# Check job status
squeue -u haba6030

# Monitor specific job
tail -f logs/BH2009_<JOB_ID>_<ARRAY_ID>.out
```

### (3) Download Results

```bash
# From local machine
# Download all results for a specific subject and ROI
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009/<timestamp>_sub-01_V1/ \
    ./derivatives/BH2009/

# Or download specific files
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009/*/analysis_summary.json \
    ./results/
```

## Expected Outputs

For each subject-ROI combination, the code saves:

### Numerical Results
- `analysis_summary.json`: Key metrics (classification accuracy, reconstruction error, R² threshold, etc.)
- `roi_hrf.npy`: ROI average HRF (8 time points)
- `roi_hrf_deriv.npy`: HRF derivative
- `selected_voxels_mask.npy`: Boolean mask of selected voxels
- `r2_voxel.npy`: R² values for all voxels
- `amplitudes_raw.npy`: Raw amplitudes (runs × colors × voxels)
- `amplitudes_z.npy`: Z-scored amplitudes

### CSV Results
- `classification_results.csv`: Per-run classification accuracy
- `reconstruction_results.csv`: Per-run reconstruction errors with hit rates

### Figures
- `roi_hrf.png`: ROI HRF and derivative visualization

## Verification Tests

To verify the implementation matches B&H 2009:

1. **FIR delays**: Check that `FIR_DELAYS` has exactly 8 elements
2. **Voxel selection**: Verify `n_voxels_selected ≈ 0.5 × n_voxels_total`
3. **R² distribution**: Check that median(r²) is used as threshold
4. **2nd-level design**: Verify design matrix has 16 columns per run
5. **Amplitude shape**: Check `amplitudes_raw.shape == (6, 8, n_voxels_selected)`

## Key Improvements

1. ✅ **Faithful to paper**: Implements exact B&H 2009 pipeline
2. ✅ **Proper voxel-wise HRF**: Uses pseudo-inverse instead of optimal delay
3. ✅ **SNR-based selection**: Top 50% voxels by R²
4. ✅ **2nd-level GLM**: HRF + derivative regressors (16 columns)
5. ✅ **Modular design**: Clear separation of pipeline steps
6. ✅ **Comprehensive outputs**: Saves all intermediate results for validation

## Comparison with Previous Code

Running both versions on the same data should reveal:
- **HRF shape**: BH2009 uses full 8-point HRF vs single delay
- **Voxel count**: BH2009 uses ~50% fewer voxels (R² selection)
- **Amplitude estimation**: BH2009 accounts for temporal latency via derivative
- **Performance**: May differ due to more faithful implementation of paper methods

## Next Steps

1. Run analysis on pilot data (P01) first
2. Compare results with previous implementations
3. If successful, run on all test subjects (01-04)
4. Analyze differences in classification/reconstruction performance
5. Document findings in results summary
