# Analysis Recommendations for Improving Decoding Performance

## Identified Problems in bh_anal.py

### 1. **Deconvolution Approach Issues**
**Problem**: Lines 240-246 in bh_anal.py average the voxel-specific HIRF across all voxels to create a "canonical" HIRF, which is then used for all voxels.

```python
# Current approach (problematic)
mean_hirf = np.mean(np.array(hirfs), axis=0)  # (hirf_len, voxels)
canonical_hirf = np.mean(mean_hirf, axis=1)   # Average across voxels
```

**Why this is bad**:
- HRF varies substantially across brain regions and voxels
- V1 typically has faster HRF than higher visual areas
- Averaging destroys voxel-specific timing information
- This is NOT what Brouwer & Heeger (2009) did

**Solution**: Either use voxel-specific HRFs or use standard parametric HRF models (Glover, SPM)

### 2. **No Voxel Selection**
**Problem**: bh_anal.py uses all voxels in ROI without selection

**Why this is bad**:
- Many voxels have poor SNR and add noise
- Not all voxels in anatomical ROI are functionally responsive
- Including uninformative voxels degrades classification

**Solution**: Select voxels by:
- Response magnitude (top-k by |beta| or variance)
- Signal-to-noise ratio
- Split-half reliability
- F-statistics from GLM

### 3. **Missing Normalization**
**Problem**: bh_anal.py doesn't explicitly normalize voxel responses before decoding

**Why this is bad**:
- Voxels with higher baseline activity dominate the classifier
- Prevents the model from learning distributed patterns
- Different runs may have different overall signal levels

**Solution**: Apply voxel-wise z-scoring per run before classification/reconstruction

### 4. **Confound Regression**
**Problem**: bh_anal.py only regresses 6 motion parameters (lines 210-221)

**Why this is bad**:
- Motion is not the only source of noise
- Physiological noise (cardiac, respiratory) can be substantial
- CompCor has been shown to improve decoding in many studies

**Solution**: Use comprehensive confound strategy (CompCor, ICA-AROMA)

---

## Recommended Analysis Pipeline

Based on successful fMRI decoding studies (particularly visual decoding), here's the recommended pipeline:

### Stage 1: GLM with Standard HRF
```python
# Use established HRF model
glm = FirstLevelModel(
    t_r=1.5,
    hrf_model='glover + derivative',  # or 'spm + derivative'
    drift_model='cosine',
    high_pass=1/128.0,
    noise_model='ar1'
)

# Use comprehensive confounds
confounds, _ = load_confounds_strategy(
    func_path,
    strategy=['high_pass', 'motion', 'compcor']
)

glm.fit(func_img, events=events, confounds=confounds)
```

**Rationale**:
- Glover + derivative provides flexibility for HRF shape variations
- Cosine drift + high-pass filtering removes slow trends
- AR(1) noise model accounts for temporal autocorrelation
- CompCor removes physiological noise

### Stage 2: Voxel Selection
```python
# Compute voxel quality metrics
betas_all_runs = []  # (n_runs, n_colors, n_voxels)

# Method 1: Response magnitude
voxel_scores = np.abs(betas_all_runs).mean(axis=(0, 1))
top_k = np.argsort(voxel_scores)[::-1][:5000]

# Method 2: F-statistics (better)
# Compute F-stat for color effect per voxel
# Select top-k by F-value

# Method 3: Split-half reliability (best but computationally expensive)
# Correlate odd vs even runs
# Select voxels with highest reliability
```

**Rationale**:
- Typical successful studies use 1000-10000 voxels
- More voxels ≠ better performance (curse of dimensionality)
- Voxel selection is feature selection

### Stage 3: Normalization
```python
# Z-score per voxel per run
for run in range(n_runs):
    for voxel in range(n_voxels):
        vals = betas[run, :, voxel]  # across colors
        betas[run, :, voxel] = (vals - vals.mean()) / (vals.std() + 1e-8)
```

**Rationale**:
- Removes voxel-specific baseline differences
- Equalizes contribution across voxels
- Standard practice in MVPA

### Stage 4: Classification/Reconstruction
```python
# Use leave-one-run-out cross-validation
# Standard classifiers:
# - Linear SVM (most common in MVPA)
# - Diagonal linear discriminant (Brouwer & Heeger used this)
# - Nearest centroid (simple, interpretable)

# For reconstruction:
# - Forward encoding model with ridge regularization
# - Test multiple lambda values: [1e-3, 1e-2, 1e-1, 1, 10]
```

---

## Literature-Based Best Practices

### From Brouwer & Heeger (2009) Original Paper
**What they actually did**:
1. Used standard HRF convolution (not deconvolution for final analysis)
2. Selected voxels by F-statistic from color vs. blank contrast
3. Used 300-1000 voxels per ROI
4. Applied normalization (z-scoring)
5. Used diagonal covariance discriminant analysis
6. Regularization (ridge) in forward model

### From Naselaris et al. (2011) "Encoding and Decoding in fMRI"
**Key recommendations**:
1. **Feature selection is critical**: "The performance of encoding models depends strongly on selecting voxels that have reliable responses"
2. **Regularization**: Always use regularization (ridge, lasso, elastic net)
3. **Cross-validation**: Use nested CV if tuning hyperparameters
4. **Baseline**: Compare against chance-level permutation tests

### From Kamitani & Tong (2005) "Decoding the visual and subjective contents"
**Methodological insights**:
1. Used linear SVM with RBF kernel
2. Selected ~400 voxels from V1+V2 based on activation strength
3. Achieved 75-100% accuracy on orientation decoding
4. **Key**: Careful voxel selection was critical

### From Kriegeskorte (2008) "Representational Similarity Analysis"
**Alternative approach if decoding fails**:
1. Compute representational dissimilarity matrices (RDMs)
2. Test if color RDM has expected structure
3. Can reveal if information is present even if decoding is poor

---

## Specific Fixes for Your Code

### Fix 1: Replace Deconvolution with Standard HRF
**In bh_anal.py, replace `run_deconv_glm()` with**:

```python
def run_standard_glm(self):
    """Standard GLM with established HRF model"""

    for run in range(1, self.config.N_RUNS + 1):
        # Load data
        func_img = nib.load(self.config.get_func_img_path(run))
        events = pd.read_csv(self.config.get_event_file_path(run), sep='\t')

        # Load confounds with CompCor
        confounds, _ = load_confounds_strategy(
            self.config.get_func_img_path(run),
            strategy=['high_pass', 'motion', 'compcor']
        )

        # Fit GLM
        glm = FirstLevelModel(
            t_r=self.config.TR,
            hrf_model='glover + derivative',
            drift_model='cosine',
            high_pass=1/128.0,
            noise_model='ar1'
        )
        glm.fit(func_img, events=events, confounds=confounds)

        # Extract betas
        betas = []
        for color_idx in range(1, self.config.N_COLORS + 1):
            beta_map = glm.compute_contrast(
                f'color_{color_idx}',
                output_type='effect_size'
            )
            betas.append(beta_map)

        # Save per-run betas
        # ... (save code)
```

### Fix 2: Add Voxel Selection to `run_extract_roi()`
**Add after line 670 in bh_anal.py**:

```python
def run_extract_roi(self, n_voxels=5000):
    """Extract ROI responses with voxel selection"""

    # ... (existing code to load betas)

    # Select voxels by response magnitude
    voxel_scores = np.abs(roi_betas).mean(axis=0)  # (n_voxels,)

    if n_voxels < voxel_scores.shape[0]:
        top_k_idx = np.argsort(voxel_scores)[::-1][:n_voxels]
        roi_betas = roi_betas[:, top_k_idx]
        self._status(f"[OK] Selected top {n_voxels} voxels from {len(voxel_scores)}")

    # Save with normalization
    # ... (save code)
```

### Fix 3: Add Normalization to `run_forward_model()`
**Add before line 887 in bh_anal.py**:

```python
# Normalize: z-score per voxel per run
arr_normalized = np.zeros_like(arr)
for run_idx in range(n_runs):
    for vox_idx in range(arr.shape[2]):
        vals = arr[run_idx, :, vox_idx]
        mu = vals.mean()
        sd = vals.std(ddof=1)
        if sd > 1e-8:
            arr_normalized[run_idx, :, vox_idx] = (vals - mu) / sd
        else:
            arr_normalized[run_idx, :, vox_idx] = vals - mu

arr = arr_normalized  # Use normalized data
```

---

## Quick Start: Testing Order

1. **First, run diagnostics**:
   ```bash
   conda activate nilearn
   python diagnostic_analysis.py
   ```

2. **Then, run systematic tests**:
   ```bash
   python systematic_testing.py
   ```

3. **Analyze results** to find best configuration

4. **Modify bh_anal.py** with winning settings

---

## Expected Performance Benchmarks

Based on similar studies:

| ROI | Classification Accuracy | Reconstruction Hit Rate |
|-----|------------------------|------------------------|
| V1  | 40-60% (chance=12.5%)  | 30-50% (within 22.5°)  |
| V2  | 35-55%                 | 25-45%                 |
| V3  | 30-50%                 | 20-40%                 |
| V4  | 35-55%                 | 25-45%                 |
| Combined | 50-70%           | 40-60%                 |

**If performance is below this**:
- Check preprocessing quality (motion, alignment)
- Verify stimulus timing accuracy
- Check if colors are sufficiently discriminable
- Consider aggregating across ROIs
- Try different classifier (e.g., SVM instead of diagonal linear)

---

## Advanced Techniques to Try

### 1. **Hyperalignment** (Haxby et al., 2011)
If you eventually want to compare CVD vs non-CVD individuals, hyperalignment can help align functional spaces.

### 2. **Encoding Model Comparison**
Test different channel bases:
- 6 channels (current)
- 8 channels (matches number of colors)
- 12 channels
- Gaussian channels

### 3. **Temporal Dynamics**
Instead of using single time-point betas, use FIR with multiple delays and test if temporal pattern helps.

### 4. **Multivariate Noise Normalization**
Use noise covariance from residuals to whiten data (Walther et al., 2016)

---

## Key References

1. Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.

2. Naselaris, T., Kay, K. N., Nishimoto, S., & Gallant, J. L. (2011). Encoding and decoding in fMRI. *NeuroImage*, 56(2), 400-410.

3. Kamitani, Y., & Tong, F. (2005). Decoding the visual and subjective contents of the human brain. *Nature Neuroscience*, 8(5), 679-685.

4. Haynes, J. D., & Rees, G. (2006). Decoding mental states from brain activity in humans. *Nature Reviews Neuroscience*, 7(7), 523-534.

5. Walther, A., et al. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.

6. Kriegeskorte, N., Mur, M., & Bandettini, P. (2008). Representational similarity analysis. *Frontiers in Systems Neuroscience*, 2, 4.
