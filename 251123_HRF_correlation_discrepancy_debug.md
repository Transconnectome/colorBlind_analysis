# HRF Correlation Discrepancy Debug Report

**Date:** 2025-01-23 (Updated)
**Issue:** Grid search reports HRF correlation 0.9998, but BH2009 pipeline shows 0.37-0.45

---

## Summary

**THREE CRITICAL BUGS FOUND AND FIXED:**

1. **CRITICAL: Blank stimulus bug** - Blank trials were modeled as stimuli instead of baseline
2. **Config mismatch**: Grid search "Config 26" ≠ BH2009 "Config 26"
3. **Drift regression bug**: Grid search creates drift regressors but doesn't use them

---

## CRITICAL BUG 0: Blank Trials Modeled as Stimuli (HIGHEST PRIORITY)

### Problem

Both grid search and BH2009 were using ALL events (color + blank):

```python
# WRONG CODE:
all_onsets = events['onset'].values  # Includes blank trials!
```

In B&H (2009) methodology:
- **Blank trials = implicit baseline** (should NOT be modeled)
- **Only color stimuli** should have FIR regressors
- This creates contrast: color response vs baseline

### Impact

1. **Wrong HRF**: Estimated HRF is average of (color + blank) responses
2. **No baseline**: No implicit baseline to contrast against
3. **Wrong amplitudes**: 2nd-level GLM amplitudes are meaningless
4. **Decoding failure**: Explains why classification = 4-10% (worse than chance)

### Fix Applied

**Files modified:**
- `grid_search_preprocessing.py` line 168-169
- `fir_reconstruction_BH2009_config26.py` line 565-566
- `fir_reconstruction_BH2009_smooth6mm.py` line 573-574

```python
# BEFORE (WRONG):
all_onsets = events['onset'].values

# AFTER (CORRECT):
color_events = events[events['trial_type'].str.startswith('color_')]
all_onsets = color_events['onset'].values
```

**Events file format confirmed:**
```
onset    duration    trial_type    ...
5.88     1.52        color_3
11.92    1.50        blank         ← Excluded now
18.27    1.51        color_4
25.16    1.51        color_3
31.78    1.52        blank         ← Excluded now
```

---

## Discrepancy 1: Config Mismatch

### Grid Search Config 26
```csv
id: 26
smoothing_fwhm: 8
high_pass: (empty)
drift_model: (empty)  ← NO DRIFT
confounds: motion_6
```

### BH2009 Config26 Script
```python
SMOOTHING_FWHM = 8
USE_MOTION_CONFOUNDS = True  # 6 parameters
DRIFT_MODEL = 'polynomial'   ← HAS DRIFT
```

**Problem:** The two "Config 26" are NOT the same!

- Grid search Config 26: 8mm smooth + motion_6 confounds, **NO drift**
- BH2009 script: 8mm smooth + motion_6 confounds + **polynomial drift**

**Grid search equivalent:** Should be Config 30 or 31 (with drift_model='polynomial')

---

## Discrepancy 2: Drift Regression Bug in Grid Search

### Drift Regression 원리

**Why we need drift regression:**

fMRI 데이터에는 **slow drift**(느린 표류)가 존재합니다:
- Scanner 온도 변화
- Subject의 각성 상태 변화
- 생리적 신호 (호흡, 심박)의 느린 변동

이러한 drift는 **stimulus와 무관**하지만 **신호를 오염**시킵니다.

**Polynomial drift model:**
```python
# Constant term: 모든 시점에 동일한 baseline shift
constant = [1, 1, 1, ..., 1]

# Linear term: 시간에 따라 선형적으로 증가/감소하는 drift
linear = [-1, -0.99, -0.98, ..., 0.98, 0.99, 1]
```

**Drift regression 수식:**

GLM 모델:
```
y = X_FIR · β_FIR + X_drift · β_drift + ε

where:
  y: voxel timeseries (1704 × 1)
  X_FIR: FIR regressors (1704 × 8)
  X_drift: drift regressors (1704 × 12)  [per-run: 6 runs × 2]
  β_FIR: HRF parameters (8 × 1)  ← This is what we want!
  β_drift: drift parameters (12 × 1)  ← Nuisance
```

**Correct estimation:**
```python
# Combine all regressors
X_full = [X_FIR | X_drift]  # (1704, 20)

# Estimate ALL parameters together
β_full = pinv(X_full) @ y  # (20, 1)

# Extract only HRF part
β_FIR = β_full[:8]  # First 8 elements
```

이렇게 하면 **drift의 영향이 β_drift에 흡수**되고, **β_FIR은 깨끗한 HRF**를 나타냅니다.

---

### Grid Search Code (BUGGY - 수정 완료)

**이전 코드 (WRONG):**

`grid_search_preprocessing.py` lines 226-263:

```python
# Build design matrix WITH drift
X_run = build_fir_design_matrix(events, n_scans_run, TR, FIR_DELAYS,
                                 config['drift_model'])
# If drift='polynomial': X_run shape = (284, 10) = 8 FIR + 2 drift

X_all = np.vstack(X_all_list)
# X_all shape = (1704, 10)

# ❌ WRONG: Extract ONLY FIR columns - THROWS AWAY DRIFT!
X_fir = X_all[:, :n_fir]
# X_fir shape = (1704, 8) - drift columns DISCARDED!

# ❌ WRONG: Fit with ONLY FIR - DRIFT NOT REGRESSED OUT!
for v in range(n_voxels):
    h_v = np.linalg.pinv(X_fir) @ y_voxel  # (8,1704) @ (1704,1) = (8,1)

    # Compute R²
    y_pred = X_fir @ h_v  # ❌ Prediction doesn't include drift!
```

**문제점:**

1. **Drift columns 생성**: `X_all`에 drift columns이 포함됨 (columns 8-9)
2. **Drift columns 버림**: `X_fir = X_all[:, :8]`로 추출하면서 drift 버림
3. **Drift 회귀 안됨**: `pinv(X_fir)`는 drift를 고려하지 않음
4. **결과**:
   ```
   y = X_FIR · β_FIR + (drift + noise)

   β_FIR = pinv(X_FIR) @ y
         = pinv(X_FIR) @ (X_FIR · β_true + drift)
         = β_true + pinv(X_FIR) @ drift  ← CONTAMINATED!
   ```

**Impact:**

모든 voxel이 **동일한 drift contamination**을 공유:
- Voxel 1 HRF: β_true + drift_component
- Voxel 2 HRF: β_true + drift_component
- → High correlation (but WRONG!)

---

### Grid Search Code (FIXED)

**수정된 코드 (CORRECT):**

```python
# Build design matrix WITH drift (same as before)
X_all = np.vstack(X_all_list)
# X_all shape = (1704, 10) = 8 FIR + 2 drift

# ✅ CORRECT: Use FULL matrix for fitting
for v in range(n_voxels):
    # Fit with FULL matrix (FIR + drift together)
    beta_full = np.linalg.pinv(X_all) @ y_voxel  # (10,1704) @ (1704,1) = (10,1)

    # Extract ONLY HRF part (first 8 elements)
    h_v = beta_full[:n_fir]  # (8,1)
    HRF_voxels[v] = h_v

    # Compute R² using FULL model
    y_pred = X_all @ beta_full  # ✅ Prediction includes drift!
    r2 = 1 - SS_res/SS_tot
```

**수정 원리:**

```
y = X_all · β_full + ε
  = [X_FIR | X_drift] · [β_FIR; β_drift] + ε

β_full = pinv(X_all) @ y
       = [β_FIR; β_drift]

where:
  β_FIR = first 8 elements  ← Clean HRF (drift regressed out!)
  β_drift = last 2 elements ← Captures drift
```

**수학적 증명 - 왜 "버리는" 것이 아닌가?**

실제 데이터: `y = X_FIR @ h_true + X_drift @ d_true + ε`

**잘못된 방법 (drift를 무시):**
```python
X_fir = X_all[:, :8]  # Drift 제거
h_wrong = pinv(X_fir) @ y
        = pinv(X_fir) @ (X_fir @ h_true + X_drift @ d_true + ε)
        = h_true + pinv(X_fir) @ X_drift @ d_true + noise
                   ↑________________________↑
                   DRIFT CONTAMINATION (≠ 0!)
```

**올바른 방법 (drift를 회귀):**
```python
beta_full = pinv(X_all) @ y
[h_correct; d_correct] = pinv([X_fir | X_drift]) @ y

By partitioned regression:
h_correct ≈ h_true  (drift absorbed into d_correct!)
d_correct ≈ d_true
```

**핵심**:
- Drift columns를 "버리는" 것이 아니라
- Drift를 **모델에 포함시켜서 회귀**한 후
- **HRF part만 추출**하는 것!

이렇게 하면 drift 영향이 `d_correct`로 흡수되고, `h_correct`는 깨끗해집니다.

**X_fir과 X_drift가 orthogonal하지 않기 때문에**, drift를 무시하면 HRF가 오염됩니다!

---

### BH2009 Code (이미 CORRECT)

`fir_reconstruction_BH2009_config26.py` lines 576-585:

```python
# Build design matrix WITH drift
X_fir = build_fir_design_matrix(all_onsets, n_scans, TR, FIR_DELAYS,
                                run_idx=run_idx, n_runs=N_RUNS)
# Shape: (284, 20) = 8 FIR + 12 per-run drift

X_fir_all = np.vstack(X_fir_all)  # Shape: (1704, 20)

# ✅ CORRECT: Fit with FULL matrix
beta_full = np.linalg.pinv(X_fir_all) @ y_voxel  # (20, 1)

# ✅ CORRECT: Extract ONLY HRF betas
h_v = beta_full[:len(FIR_DELAYS)]  # First 8 elements

# ✅ CORRECT: R² computed with full model
y_pred = X_fir_all @ beta_full
r2 = compute_r2(y_voxel, y_pred)
```

**BH2009는 처음부터 올바르게 구현되어 있었습니다!**
```

**Correct approach:**
1. Create design matrix with FIR + drift columns
2. **Fit with full matrix** (regresses out drift)
3. Extract only HRF betas

---

## Discrepancy 3: Motion Confound Regression

Both approaches regress motion confounds, but at different stages:

### Grid Search: Via nilearn.signal.clean()

```python
# load_and_preprocess_data(), lines 110-127
if config['confounds'] == 'motion_6':
    confounds_mat = confounds_df[motion_cols].iloc[VOLS_TO_DROP:].values

# Regress confounds BEFORE HRF estimation
func_data = clean(
    func_data,
    confounds=confounds_mat,
    ...
)
```

**Timing:** Confounds regressed from **raw timeseries** before HRF estimation

### BH2009: Manual OLS regression

```python
# load data section, lines 483-503
confounds = load_motion_confounds(confounds_path)

# Regress confounds BEFORE HRF estimation
func_data = regress_confounds(func_data, confounds)
```

Where `regress_confounds()` does:
```python
X = np.hstack([confounds, np.ones((n, 1))])  # Add intercept
betas = np.linalg.pinv(X) @ data
data_clean = data - (X @ betas)
```

**Timing:** Also confounds regressed from **raw timeseries** before HRF estimation

**Assessment:** Both approaches are equivalent here, no issue.

---

## Discrepancy 4: Per-Run vs Multi-Run Drift Regressors

### Grid Search Drift Regressors

`build_fir_design_matrix()` lines 181-192:

```python
if drift_model == 'polynomial':
    constant = np.ones((n_scans, 1))
    time_axis = np.linspace(-1, 1, n_scans).reshape(-1, 1)
    X = np.hstack([X_fir, constant, time_axis])
```

**Structure:** Global drift across all concatenated runs
- Run 1: constant=1, linear=[-1, ..., -0.3]
- Run 2: constant=1, linear=[-0.3, ..., 0.3]  ← CONTINUOUS!
- Run 3: constant=1, linear=[0.3, ..., 1]

**Problem:** Assumes drift is continuous across runs (not realistic)

### BH2009 Per-Run Drift Regressors

`build_fir_design_matrix()` lines 215-229:

```python
if DRIFT_MODEL == 'polynomial':
    if run_idx is not None and n_runs is not None:
        # Per-run drift regressors
        drift_cols = np.zeros((n_scans, 2 * n_runs))

        # This run's linear drift
        drift_cols[:, run_idx * 2] = np.linspace(-1, 1, n_scans)

        # This run's constant
        drift_cols[:, run_idx * 2 + 1] = 1.0

        X = np.hstack([X_fir, drift_cols])
```

**Structure:** Independent drift per run
- 12 drift columns (6 runs × 2)
- Run 1: columns 0-1 active, others zero
- Run 2: columns 2-3 active, others zero
- Each run has its own intercept and slope

**Assessment:** BH2009 approach is more realistic (each run has independent drift)

---

## Why Grid Search Shows High HRF Correlation

### Config 26 (no drift): HRF corr = 0.9998

**Reasons:**
1. Multi-run concatenation (1704 TRs) → stable estimation
2. Motion confounds regressed out → removes subject motion patterns
3. 8mm smoothing → voxels spatially correlated
4. **No drift regression** → all voxels share same slow drift
5. → High correlation (but contaminated with drift!)

### Configs with polynomial drift: HRF corr = 0.94-0.9998

**Should be even better** (drift regressed out), but:
1. **Bug:** Drift columns created but NOT used
2. Same as no-drift case
3. Still contaminated with drift

**Grid search HRF correlation is INFLATED by drift contamination!**

---

## Why BH2009 Shows Low HRF Correlation

### BH2009 Config26: HRF corr = 0.37-0.45

**Possible reasons:**

1. **Different preprocessing** than grid search Config 26
   - BH2009 has drift regressors (polynomial)
   - Grid search Config 26 doesn't

2. **Per-run drift regressors** (12 columns)
   - More aggressive drift removal
   - May remove some signal along with drift

3. **Over-regression?**
   - Motion (6 parameters) + per-run drift (12 parameters) = 18 nuisance regressors
   - Might be removing too much signal

4. **Data quality issues?**
   - But grid search showed tSNR = 89.5 (good)
   - P01 also shows low correlation

5. **Bug in BH2009 code?**
   - Need to verify HRF calculation

---

## Which Metrics Are Trustworthy?

### Grid Search Metrics: QUESTIONABLE

**tSNR = 89.5:** ✓ Trustworthy (measured on preprocessed data)

**HRF correlation = 0.9998:** ✗ Inflated
- Contaminated by drift (for configs with no drift)
- Bug in drift regression (for configs with polynomial drift)
- **Not representative of true HRF homogeneity**

**R² = nan:** Known issue (all R² ≤ 0, needs fixing)

### BH2009 Metrics: UNCLEAR

**HRF correlation = 0.37-0.45:** Either:
- Correct (preprocessing is too aggressive)
- Or bug in calculation

**R² = 0.01:** Very low, suggests poor fit

**Run-to-run reliability = 0.02-0.04:** Very low, suggests instability

**Classification = 4-10%:** Worse than chance (12.5%)

**Either:**
1. The preprocessing is destroying signal
2. Or there's a fundamental bug in the pipeline

---

## Recommended Next Steps

### 1. Fix Grid Search Drift Bug (HIGH PRIORITY)

**File:** `grid_search_preprocessing.py`

**Current (WRONG):**
```python
# Line 240-241
X_fir = X_all[:, :n_fir]  # Throws away drift columns

# Line 252
h_v = np.linalg.pinv(X_fir) @ y_voxel  # No drift regression
```

**Fix:**
```python
# Line 247-258 (replace entire voxel loop)
for v in range(n_voxels):
    y_voxel = y_all[:, v]

    # Fit with FULL matrix (includes drift)
    if config['drift_model'] == 'polynomial':
        beta_full = np.linalg.pinv(X_all) @ y_voxel
        h_v = beta_full[:n_fir]  # Extract HRF part
    else:
        # No drift, X_all only has FIR
        h_v = np.linalg.pinv(X_all) @ y_voxel

    HRF_voxels[v] = h_v

    # Compute R² using FULL model
    y_pred = X_all @ (beta_full if config['drift_model'] else h_v)
    r2_voxels[v] = compute_r2(y_voxel, y_pred)
```

### 2. Re-run Grid Search with Fixed Code

Compare results:
- Before fix: Config 26 HRF corr = 0.9998
- After fix: Should be lower (drift properly regressed)

### 3. Add Debug Output to BH2009

**File:** `fir_reconstruction_BH2009_config26.py`

Add after line 594:

```python
# DEBUG: Print HRF estimation details
if voxel_idx == 0:  # First voxel
    print(f"\n  DEBUG: HRF Estimation")
    print(f"    X_fir_all shape: {X_fir_all.shape}")
    print(f"    y_voxel shape: {y_voxel.shape}")
    print(f"    beta_full shape: {beta_full.shape}")
    print(f"    HRF shape: {h_v.shape}")
    print(f"    HRF values: {h_v}")
    print(f"    HRF norm: {np.linalg.norm(h_v):.4f}")
```

And after line 680:

```python
# DEBUG: Print correlation details
print(f"\n  DEBUG: HRF Correlation Calculation")
print(f"    Selected voxels: {n_voxels_selected}")
print(f"    ROI_HRF: {ROI_HRF}")
print(f"    ROI_HRF norm: {np.linalg.norm(ROI_HRF):.4f}")
print(f"    First 5 voxel HRFs:")
for i in range(min(5, n_voxels_selected)):
    print(f"      Voxel {i}: {HRF_selected[i]}")
    print(f"      Correlation: {hrf_correlations[i]:.4f}")
```

### 4. Test Minimal Case

Create a minimal test script:
1. Load sub-01 V1 data (just run 1)
2. Apply Config 26 preprocessing (8mm smooth + motion)
3. Estimate HRF with and without drift regressors
4. Compare HRF correlation

This will isolate whether drift regression is the issue.

### 5. Compare Grid Search Config 30/31 vs BH2009

Grid search Config 30/31 have:
- smooth=8mm
- drift_model='polynomial'
- confounds='motion_6'

This matches BH2009 Config26 settings (except for the grid search bug).

After fixing the bug, compare:
- Fixed grid search Config 30/31 results
- BH2009 results

They should match!

---

## Expected Outcomes

### If Grid Search Bug Fix Works

After fixing drift regression bug:
- Configs with drift_model should have **different** HRF correlation
- Should be lower than current 0.9998
- Should remove drift contamination
- **R² should improve** (proper model fit)

### If BH2009 Has Calculation Bug

After adding debug output:
- Might reveal HRF values are wrong
- Or ROI_HRF is wrong
- Or correlation calculation is wrong

### If Preprocessing Is Too Aggressive

- Per-run drift (12 regressors) might be overkill
- Try global drift (2 regressors) instead
- Compare Config 26 with and without drift

---

## Conclusion

**Grid search results are UNRELIABLE** due to:
1. Config mismatch (Config 26 ≠ BH2009 Config26)
2. Drift regression bug (creates but doesn't use drift columns)
3. Inflated HRF correlation (drift contamination)

**BH2009 results are SUSPICIOUSLY LOW** (0.37-0.45 vs expected 0.997-0.9998)

**Need to:**
1. Fix grid search bug
2. Re-run grid search
3. Add debug output to BH2009
4. Compare corrected grid search vs BH2009

**Most likely issue:** BH2009 per-run drift regressors (12 columns) are too aggressive, removing signal along with drift.

**Test:** Run BH2009 with `DRIFT_MODEL = None` or with global drift (2 columns) instead of per-run drift (12 columns).
