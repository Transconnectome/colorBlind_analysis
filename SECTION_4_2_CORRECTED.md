### 4.2 Workflow: fir_reconstruction_zScore.py (BASELINE) ⭐ ACTUAL CODE

**File:** `fir_reconstruction_zScore.py` (1,814 lines)

**Key Difference:** This file uses **FOR-LOOPS throughout**, NOT separate functions!

---

#### Stage 1: Configuration (Lines 67-115)

```python
# Lines 107-114: Experiment parameters (ACTUAL CODE)
TR = 1.5
N_RUNS = 6
N_COLORS = 8

# FIR parameters
FIR_DELAYS = range(10)  # 0-15 seconds (10 TRs × 1.5s)
PEAK_DELAY = 3  # ~4.5s post-onset (typical HRF peak)
```

**Color Mappings (Lines 70-104):**
```python
# Test data: Regular 45° spacing (Lines 83-92)
LABEL2HUE_DEG_TEST = {
    'color_1': 0.0,
    'color_2': 45.0,
    'color_3': 90.0,
    'color_4': 135.0,
    'color_5': 180.0,
    'color_6': 225.0,
    'color_7': 270.0,
    'color_8': 315.0,
}

# Actual stimulus colors in CIELab (Lines 95-104)
COLOR_LAB = {
    'color_1': [75, 40.0, 0.0],        # 0°: Red
    'color_2': [75, 28.28, 28.28],     # 45°: Orange
    'color_3': [75, 0.0, 40.0],        # 90°: Yellow
    'color_4': [75, -28.28, 28.28],    # 135°: Green
    'color_5': [75, -40.0, 0.0],       # 180°: Cyan
    'color_6': [75, -28.28, -28.28],   # 225°: Blue
    'color_7': [75, 0.0, -40.0],       # 270°: Violet
    'color_8': [75, 28.28, -28.28],    # 315°: Pinkish
    'blank': [75, 0.0, 0.0]            # Neutral Gray
}
```

---

#### Stage 2: Load ROI Mask (Lines 376-399)

```python
# Lines 378-381: Load ROI mask path (ACTUAL CODE)
if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

# Lines 392-397: Load mask and create masker
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_path, standardize=False)
masker.fit()

n_voxels = np.sum(roi_img.get_fdata() > 0)
print(f"  Number of voxels: {n_voxels}")
```

---

#### Stage 3: Load Functional Data with FOR-LOOP (Lines 405-459)

**⭐ NO SEPARATE FUNCTION - Uses FOR-LOOP directly:**

```python
# Lines 405-459: Load all runs with FOR-LOOP (ACTUAL CODE)
print(f"[2/8] Loading {N_RUNS} runs of functional data and events")

func_imgs = []
events_list = []
confounds_list = []

VOLS_TO_DROP = 4  # ⭐ CRITICAL: Drop first 4 volumes!

for run in range(1, N_RUNS + 1):
    # Line 415: Construct functional image path
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    # Line 420: Load functional image
    func_img = nib.load(func_path)

    # Lines 422-424: ⭐ DROP FIRST 4 VOLUMES for T1 stabilization
    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    func_imgs.append(func_img)

    # Lines 428-436: Load events
    events_path = f"{EVENT_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"
    events = pd.read_csv(events_path, sep='\t')
    events_list.append(events)

    # Lines 438-453: Load confounds and drop first 4
    confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
    confounds = pd.read_csv(confounds_path, sep='\t')
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    confounds_subset = confounds[motion_cols]

    # Lines 449-451: ⭐ DROP confounds to match dropped volumes
    if VOLS_TO_DROP > 0:
        confounds_subset = confounds_subset.iloc[VOLS_TO_DROP:]

    confounds_list.append(confounds_subset)

    print(f"  Run {run}: {func_img.shape}, {len(events)} events")

print(f"  Total: {len(func_imgs)} runs loaded")
```

---

#### Stage 4: Fit FIR Model (Lines 465-485)

**Using nilearn's FirstLevelModel directly (NOT a separate function):**

```python
# Lines 465-481: Fit FIR model (ACTUAL CODE)
print(f"[3/8] Fitting FIR model (may take 5-10 minutes)")
print(f"  Using hrf_model='fir' with {len(FIR_DELAYS)} time bins")

fir_model = FirstLevelModel(
    t_r=TR,
    hrf_model='fir',
    fir_delays=FIR_DELAYS,  # range(10) = [0,1,2,...,9]
    drift_model='cosine',
    high_pass=1/128.0,
    mask_img=roi_path,
    standardize=False,
    minimize_memory=False
)

fir_model.fit(func_imgs, events_list, confounds_list)

print("  FIR model fitted successfully!")
```

**Key Points:**
- `hrf_model='fir'` → FIR basis functions
- `fir_delays=range(10)` → 10 time bins (0-15s with TR=1.5s)
- `drift_model='cosine'` → Cosine drift model
- Model is fitted to ALL 6 runs simultaneously

---

#### Stage 5: Extract Mean HRF with FOR-LOOP (Lines 491-540)

**⭐ NO SEPARATE FUNCTION - Uses FOR-LOOP:**

```python
# Lines 491-511: Extract FIR response for each color with FOR-LOOP (ACTUAL CODE)
print(f"[4/8] Visualizing mean HRF estimated from FIR")

# Extract FIR response for each color at all delays
mean_responses = []  # (n_colors, n_delays)

for color_idx in range(1, N_COLORS + 1):
    color_responses = []

    for delay in FIR_DELAYS:
        contrast_name = f'color_{color_idx}_delay_{delay}'
        try:
            # ⭐ Get effect_size (not z_score) for HRF visualization
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='effect_size')
            mean_response = masker.transform(contrast_map).mean()  # Mean across voxels
            color_responses.append(mean_response)
        except:
            color_responses.append(0)

    mean_responses.append(color_responses)

mean_responses = np.array(mean_responses)  # Shape: (8, 10)

# Lines 517-523: Compute universal HRF and find optimal delay (ACTUAL CODE)
# Compute universal HRF (average across all colors)
universal_hrf = mean_responses.mean(axis=0)  # Average across colors → (10,)

# CORRECTED: Find peak using absolute value (handles negative baseline)
optimal_delay = np.argmax(np.abs(universal_hrf))
optimal_time = optimal_delay * TR

print(f"  Optimal delay: {optimal_delay} TRs ({optimal_time:.1f}s)")
print(f"  Peak amplitude: {universal_hrf[optimal_delay]:.4f}")

# Lines 535-536: Update PEAK_DELAY to use optimal delay
PEAK_DELAY = optimal_delay
print(f"  >>> Using optimal delay {PEAK_DELAY} TRs ({PEAK_DELAY * TR}s) for all voxels")
```

**Visualization (Lines 542-569):**
```python
# Lines 542-566: Plot HRF with optimal delay marked (ACTUAL CODE)
fig, ax = plt.subplots(figsize=(10, 6))
time_points = np.array(list(FIR_DELAYS)) * TR

# Plot individual color HRFs
for color_idx in range(N_COLORS):
    ax.plot(time_points, mean_responses[color_idx],
            label=f'color_{color_idx+1}', alpha=0.5, linewidth=1)

# Plot universal HRF (bold)
ax.plot(time_points, universal_hrf, 'k-', linewidth=3,
        label='Universal HRF (average)', zorder=10)

ax.axvline(x=optimal_time, color='r', linestyle='--', linewidth=2, alpha=0.8,
           label=f'Optimal delay ({optimal_time:.1f}s)')
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Mean response amplitude (% signal change)')
ax.set_title(f'Universal HRF from FIR estimation - {ROI_NAME}')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

plt.savefig(fig_dir / f"{ROI_NAME}_universal_hrf.png", dpi=150, bbox_inches='tight')
```

**Insert Figure:** `logs_1117/comprehensive_analysis/comprehensive_hrf_zScore.png`

---

#### Stage 6: Extract Z-Scores with FOR-LOOP (Lines 576-614)

**⭐ NO SEPARATE FUNCTION - Uses nested FOR-LOOPS:**

```python
# Lines 576-614: Extract Z-scores with FOR-LOOPS (ACTUAL CODE)
print(f"[5/8] Extracting Z-SCORE estimates for {N_COLORS} colors")
print(f"  NOTE: Using Z-scores instead of Beta values!")
print(f"  Z-scores automatically weight voxels by statistical significance")

all_betas = []  # Variable name misleading - actually contains Z-SCORES!
z_maps = []     # Z-score maps for visualization

# FOR-LOOP over runs
for run_idx in range(N_RUNS):
    run_betas = []

    # FOR-LOOP over colors
    for color_idx in range(1, N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{PEAK_DELAY}'

        try:
            # ⭐ KEY: Extract Z-scores (not betas!)
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
            betas = masker.transform(contrast_map).ravel()  # Variable name 'betas' but contains Z-SCORES!
            run_betas.append(betas)

            # Z-map (only from first run for visualization)
            if run_idx == 0:
                z_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
                z_maps.append(z_map)

        except Exception as e:
            print(f"  Warning: Could not extract {contrast_name}: {e}")
            run_betas.append(np.zeros(n_voxels))
            if run_idx == 0:
                z_maps.append(None)

    all_betas.append(np.array(run_betas))
    print(f"  Run {run_idx+1}: Extracted {len(run_betas)} color z-scores")

all_betas = np.array(all_betas)  # Shape: (6, 8, n_voxels) - CONTAINS Z-SCORES!
print(f"  Total shape: {all_betas.shape}")
print(f"  Data type: Z-SCORES (not betas!)")
```

**Key Point:** Variable is named `all_betas` but actually contains **Z-SCORES**! This is for backward compatibility with the original beta-based version.

---

#### Stage 7: Classification with FOR-LOOP (Lines 1196-1277)

**⭐ NO SEPARATE FUNCTION - Uses FOR-LOOP:**

```python
# Lines 1196-1239: Classification with leave-one-run-out (ACTUAL CODE)
print(f"[6/8] Classification with diagonal LDA (leave-one-run-out)")
print(f"  Using Z-SCORES as features (not betas!)")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")

classification_results = []

# FOR-LOOP over test runs
for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # Prepare train/test data
    X_train = all_betas[train_runs].reshape(-1, n_voxels)  # (40, n_voxels) = 5 runs × 8 colors
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))  # [0,1,2,...,7, 0,1,2,...,7, ...]

    X_test = all_betas[test_run]  # (8, n_voxels)
    y_test = np.arange(N_COLORS)  # [0,1,2,3,4,5,6,7]

    # Standardize (Z-scores already normalized, but standardize again for PCA)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA
    if USE_PCA:
        pca = PCA(n_components=N_PCA_COMPONENTS)
        X_train_final = pca.fit_transform(X_train_scaled)  # (40, 6)
        X_test_final = pca.transform(X_test_scaled)        # (8, 6)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    # Classify using diagonal LDA (helper function defined at line 120)
    y_pred = diag_linear_predict(X_train_final, y_train, X_test_final)
    acc = (y_pred == y_test).mean()

    classification_results.append({
        'test_run': test_run + 1,
        'accuracy': acc,
        'y_true': y_test,
        'y_pred': y_pred
    })

    print(f"  Test run {test_run+1}: {acc:.3f} ({acc*100:.1f}%)")

mean_classification_acc = np.mean([r['accuracy'] for r in classification_results])
print(f"Mean classification accuracy: {mean_classification_acc:.3f} ({mean_classification_acc*100:.1f}%)")
```

**Helper Function Used (Lines 120-135):**
```python
def diag_linear_predict(train_X, train_y, test_X):
    """Diagonal Linear Discriminant Analysis (B&H 2009 method)"""
    classes = np.unique(train_y)
    means = np.stack([train_X[train_y==c].mean(axis=0) for c in classes])
    vars_  = np.stack([train_X[train_y==c].var(axis=0) + 1e-8 for c in classes])

    ll = []
    for k in range(len(classes)):
        ll_k = -0.5 * (
            np.log(2*np.pi*vars_[k]).sum() +
            ((test_X - means[k])**2 / vars_[k]).sum(axis=1)
        )
        ll.append(ll_k)
    ll = np.stack(ll, axis=1)
    preds = classes[ll.argmax(axis=1)]
    return preds
```

---

#### Stage 8: Reconstruction with FOR-LOOP (Lines 1283-1454)

**⭐ NO SEPARATE FUNCTION - Uses FOR-LOOP for leave-one-run-out:**

```python
# Lines 1283-1424: Reconstruction with forward model (ACTUAL CODE)
print(f"[7/8] Reconstruction with B&H forward model")
print(f"  Using Z-SCORES as features (not betas!)")

# Create 6-channel basis functions (Lines 1288-1307)
def create_basis_functions(n_channels=6):
    """Create 6 idealized color channels"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist

            # Half-wave rectified cosine, squared
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis

basis_functions = create_basis_functions(n_channels=6)

def hue_to_channels(hue_deg):
    """Convert hue (0-360) to 6 channel outputs"""
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

# Leave-one-run-out reconstruction (Lines 1318-1419)
reconstruction_results = []

# FOR-LOOP over test runs
for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # Prepare data
    X_train = all_betas[train_runs].reshape(-1, n_voxels)  # (40, n_voxels)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))
    X_test = all_betas[test_run]  # (8, n_voxels)
    y_test = np.arange(N_COLORS)

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA
    if USE_PCA:
        pca = PCA(n_components=N_PCA_COMPONENTS)
        X_train_final = pca.fit_transform(X_train_scaled)  # (40, 6)
        X_test_final = pca.transform(X_test_scaled)        # (8, 6)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    # Train forward model: B = W × C (Lines 1343-1354)
    # Get channel outputs for training colors
    C_train = []
    for color_idx in y_train:
        color_name = f'color_{color_idx+1}'
        hue_deg = LABEL2HUE_DEG[color_name]
        channels = hue_to_channels(hue_deg)
        C_train.append(channels)
    C_train = np.array(C_train).T  # (6, 40)

    # Estimate weights: W = B × C^T × (C × C^T)^-1
    W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

    # Test: estimate channels from test data (Line 1358)
    C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T  # (6, 8)

    # Reconstruct hues (Lines 1361-1403)
    reconstructed_hues = []
    true_hues = []

    # FOR-LOOP over test colors
    for test_idx, color_idx in enumerate(y_test):
        # Estimated channels
        estimated_channels = C_test_est[:, test_idx]

        # Find best matching hue (0-360) by correlation
        correlations = []
        for h in range(360):
            template_channels = basis_functions[h]
            corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
            correlations.append(corr)

        correlations = np.array(correlations)
        reconstructed_hue = np.argmax(correlations)

        # True hue
        color_name = f'color_{color_idx+1}'
        true_hue = LABEL2HUE_DEG[color_name]

        reconstructed_hues.append(reconstructed_hue)
        true_hues.append(true_hue)

    # Calculate reconstruction error
    errors = circular_diff_deg(np.array(reconstructed_hues), np.array(true_hues))
    mean_error = errors.mean()

    reconstruction_results.append({
        'test_run': test_run + 1,
        'mean_error': mean_error,
        'reconstructed_hues': reconstructed_hues,
        'true_hues': true_hues,
        'errors': errors
    })

    print(f"  Test run {test_run+1}: Mean error = {mean_error:.1f}°")

mean_reconstruction_error = np.mean([r['mean_error'] for r in reconstruction_results])
print(f"Mean reconstruction error: {mean_reconstruction_error:.1f}°")
```

**Helper Function Used (Lines 137-140):**
```python
def circular_diff_deg(a, b):
    """Circular difference in degrees (0-360)"""
    diff = np.abs(a - b)
    return np.minimum(diff, 360 - diff)
```

---

#### Stage 9: Novel Color Reconstruction with FOR-LOOP (Lines 1460-1554)

**⭐ Leave-one-color-out with NESTED FOR-LOOPS:**

```python
# Lines 1460-1554: Novel color reconstruction (ACTUAL CODE)
print(f"[8/8] Leave-one-color-out reconstruction (novel colors)")

novel_color_results = []

# FOR-LOOP over held-out colors
for held_out_color in range(N_COLORS):
    all_errors_this_color = []
    all_reconstructed_hues = []

    # FOR-LOOP over test runs
    for test_run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != test_run]

        # Remove held-out color from training (Lines 1473-1481)
        X_train_list = []
        y_train_list = []

        for r in train_runs:
            for c in range(N_COLORS):
                if c != held_out_color:  # ⭐ Skip held-out color
                    X_train_list.append(all_betas[r, c])
                    y_train_list.append(c)

        X_train = np.array(X_train_list)  # (35, n_voxels) = 5 runs × 7 colors
        y_train = np.array(y_train_list)

        X_test = all_betas[test_run, held_out_color:held_out_color+1]  # (1, n_voxels)
        y_test = np.array([held_out_color])

        # Standardize + PCA (Lines 1489-1501)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        if USE_PCA:
            pca = PCA(n_components=min(N_PCA_COMPONENTS, len(X_train)))
            X_train_final = pca.fit_transform(X_train_scaled)
            X_test_final = pca.transform(X_test_scaled)
        else:
            X_train_final = X_train_scaled
            X_test_final = X_test_scaled

        # Train forward model (Lines 1503-1512)
        C_train = []
        for color_idx in y_train:
            color_name = f'color_{color_idx+1}'
            hue_deg = LABEL2HUE_DEG[color_name]
            channels = hue_to_channels(hue_deg)
            C_train.append(channels)
        C_train = np.array(C_train).T

        W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

        # Reconstruct held-out color (Lines 1514-1530)
        C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T
        estimated_channels = C_test_est[:, 0]

        correlations = []
        for h in range(360):
            template_channels = basis_functions[h]
            corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
            correlations.append(corr)

        reconstructed_hue = np.argmax(correlations)

        color_name = f'color_{held_out_color+1}'
        true_hue = LABEL2HUE_DEG[color_name]

        error = circular_diff_deg(reconstructed_hue, true_hue)
        all_errors_this_color.append(error)
        all_reconstructed_hues.append(reconstructed_hue)

    # Compute circular mean of reconstructed hues (Line 1538)
    mean_reconstructed_hue, R = circular_mean_deg(all_reconstructed_hues)

    novel_color_results.append({
        'color': color_name,
        'reconstructed_hue': mean_reconstructed_hue,
        'reconstructed_hues': all_reconstructed_hues,
        'mean_error': np.mean(all_errors_this_color),
        'errors': all_errors_this_color
    })

    print(f"  {color_name}: Mean error = {np.mean(all_errors_this_color):.1f}°")

mean_novel_error = np.mean([r['mean_error'] for r in novel_color_results])
print(f"Mean error (novel colors): {mean_novel_error:.1f}°")
```

---

## Summary: Actual Code Structure

**The file uses FOR-LOOPS throughout, NOT separate functions!**

| Stage | Lines | Implementation |
|-------|-------|----------------|
| Configuration | 67-115 | Global variables |
| Load ROI | 376-399 | Direct code |
| Load data | 405-459 | **FOR-LOOP** over 6 runs |
| Fit FIR | 470-481 | FirstLevelModel.fit() |
| Extract HRF | 494-540 | **Nested FOR-LOOPS** (colors × delays) |
| Extract Z-scores | 584-614 | **Nested FOR-LOOPS** (runs × colors) |
| Classification | 1204-1277 | **FOR-LOOP** over test runs |
| Reconstruction | 1320-1454 | **FOR-LOOP** over test runs |
| Novel colors | 1466-1554 | **Nested FOR-LOOPS** (colors × runs) |

**Helper Functions (Actually exist):**
- `diag_linear_predict()` (120-135)
- `circular_diff_deg()` (137-140)
- `circular_mean_deg()` (142-151)
- `lab2rgb_accurate()` (174-215)
- `get_stimulus_color_rgb()` (217-239)
- `create_basis_functions()` (1288-1307)
- `hue_to_channels()` (1312-1315)

**Key Variables:**
- `all_betas` - Shape: (6, 8, n_voxels) - Actually contains **Z-SCORES** (not betas!)
- `PEAK_DELAY` - Updated dynamically based on universal HRF
- `VOLS_TO_DROP = 4` - First 4 volumes dropped for T1 stabilization
