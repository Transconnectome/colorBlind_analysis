# CRITICAL: Blank Stimulus Bug

**Date:** 2025-01-23
**Severity:** CRITICAL - Invalidates ALL results

---

## Bug Description

Both grid search and BH2009 pipeline are treating **blank trials as stimuli**.

### Current Code (WRONG)

**Grid search** (`grid_search_preprocessing.py` line 163):
```python
all_onsets = events['onset'].values  # Gets ALL onsets including blank!
```

**BH2009** (`fir_reconstruction_BH2009_config26.py` line 564):
```python
all_onsets = events['onset'].values  # Gets ALL onsets including blank!
```

Both then use `all_onsets` to build FIR design matrix, treating **blank as a stimulus**.

### What Should Happen

According to B&H (2009) methodology:
- **Blank trials = implicit baseline** (no modeling)
- **Only color stimuli** should have FIR regressors
- This creates contrast: color vs baseline

### Why This Is Critical

1. **No baseline**: If blank is modeled as stimulus, there's no baseline to compare against
2. **Confounds HRF**: Estimated "HRF" is actually the average response to all events (colors + blank)
3. **Wrong amplitudes**: 2nd-level GLM amplitudes will be meaningless
4. **Explains low performance**: Decoding fails because signal is contaminated

---

## Impact on Results

### Grid Search: HRF corr = 0.994-0.9998

**Why it's high:**
- All voxels respond to "everything" (colors + blank)
- High correlation because all voxels have same contaminated HRF
- **But the HRF is WRONG**

### BH2009: Classification = 4-10%, Reconstruction = 85-94°

**Why it fails:**
- HRF estimated from colors + blank (wrong)
- Amplitudes don't represent color-specific responses
- No meaningful signal to decode

---

## Correct Implementation

### Fix 1: Filter Events (Color-Only)

**Grid search** should change line 163:
```python
# BEFORE (WRONG):
all_onsets = events['onset'].values

# AFTER (CORRECT):
color_events = events[events['trial_type'].str.startswith('color_')]
all_onsets = color_events['onset'].values
```

**BH2009** should change line 564:
```python
# BEFORE (WRONG):
all_onsets = events['onset'].values

# AFTER (CORRECT):
color_events = events[events['trial_type'].str.startswith('color_')]
all_onsets = color_events['onset'].values
```

### Verify Events File Format

Need to check actual events file to confirm column names:
```bash
head -20 /storage/connectome/haba6030/colorBlind_dataOct/sub-01/func/sub-01_task-rsvp_run-1_events.tsv
```

Expected format:
```
onset    duration    trial_type
0.0      0.5         blank
2.0      0.5         color_1
4.0      0.5         blank
6.0      0.5         color_3
...
```

Or possibly:
```
onset    duration    trial_type    color_label
0.0      0.5         stimulus      0  (0 = blank)
2.0      0.5         stimulus      1  (1-8 = colors)
...
```

---

## Why This Bug Went Unnoticed

1. **Multi-run concatenation** still produces stable estimates (but wrong HRF)
2. **High HRF correlation** seems good (but measures wrong thing)
3. **No explicit validation** that blank trials are excluded

---

## Secondary Issue: Motion Confounds

User question: "Grid search Config 24/28 (no motion) shows HRF corr = 0.994, Config 26/30 (with motion) shows 0.9998. If no-motion works better, shouldn't we not use motion?"

### Analysis

**Grid search shows:**
- No motion: HRF corr = 0.994, tSNR = 71.7
- With motion: HRF corr = 0.9998, tSNR = 89.5

**Motion helps because:**
1. **tSNR increases** from 71.7 → 89.5 (25% improvement)
2. **HRF correlation increases** from 0.994 → 0.9998
3. Motion confounds remove subject-specific motion artifacts
4. Cleaner signal → more homogeneous HRF

**But both are based on BUGGY blank handling!**

After fixing blank bug:
- Need to re-run grid search
- Re-evaluate motion confound effect
- Current results are unreliable

---

## Action Items

### 1. Verify Events File Format (URGENT)

```bash
# On server
head -30 /storage/connectome/haba6030/colorBlind_dataOct/sub-01/func/sub-01_task-rsvp_run-1_events.tsv
```

Need to know:
- Column names
- How blank is coded (`blank`, `color_0`, `trial_type==0`, etc.)
- How colors are coded (`color_1` to `color_8`)

### 2. Fix Grid Search (HIGH PRIORITY)

**File:** `grid_search_preprocessing.py`

**Line 163** (in `build_fir_design_matrix`):
```python
def build_fir_design_matrix(events, n_scans, tr, fir_delays, drift_model=None):
    """Build FIR design matrix with optional drift regressors"""

    # FIX: Exclude blank trials
    color_events = events[events['trial_type'].str.startswith('color_')]
    all_onsets = color_events['onset'].values

    # ... rest of function
```

### 3. Fix BH2009 Pipeline (HIGH PRIORITY)

**Files:**
- `fir_reconstruction_BH2009_config26.py`
- `fir_reconstruction_BH2009_smooth6mm.py`

**Line ~564** (in 1st-level GLM):
```python
# Get color onsets only (exclude blank)
events = events_list[run_idx]
color_events = events[events['trial_type'].str.startswith('color_')]
all_onsets = color_events['onset'].values
```

### 4. Re-run Everything

After fixing blank bug:
1. Re-run grid search
2. Re-run BH2009 pipeline (all subjects)
3. Compare motion vs no-motion effects
4. Evaluate drift model effects

**Expected changes:**
- HRF correlation might decrease (but will be CORRECT)
- tSNR should stay similar
- Classification/reconstruction should IMPROVE dramatically
- R² should increase

---

## Root Cause Analysis

### Why Did We Make This Mistake?

Looking at B&H (2009) paper:
- They mention "8 colors + blank"
- But blank is **implicit baseline**, not modeled
- Our code took "all events" literally

### Design Matrix Should Be:

**1st-level (HRF estimation):**
```
Columns: FIR_delay0, FIR_delay1, ..., FIR_delay7, drift_regressors
Modeled: Color onsets only
Baseline: Blank trials (unmodeled)
```

**2nd-level (Amplitude estimation):**
```
Columns: color1_HRF, color1_deriv, color2_HRF, color2_deriv, ..., color8_HRF, color8_deriv
Modeled: Each color separately with ROI_HRF
Baseline: Blank trials (unmodeled)
```

---

## Expected Impact After Fix

### Grid Search

**Before (buggy):**
- Config 26: HRF corr = 0.9998, tSNR = 89.5

**After (fixed):**
- HRF corr might drop to 0.95-0.98 (but CORRECT)
- tSNR should stay ~90
- R² should improve (better model fit)

### BH2009 Pipeline

**Before (buggy):**
- HRF corr = 0.37-0.45
- Classification = 4-10% (worse than chance)
- Reconstruction = 85-94°

**After (fixed):**
- HRF corr should increase to 0.95-0.98
- Classification should be 40-60% (B&H 2009 reported ~50%)
- Reconstruction should be 30-45° (B&H 2009 reported ~35°)

---

## Conclusion

**CRITICAL BUG:** Both grid search and BH2009 are modeling blank trials as stimuli.

**Fix:** Filter events to exclude blank before creating FIR design matrix.

**Next step:**
1. Check events file format
2. Fix both scripts
3. Re-run everything
4. Re-evaluate motion confound and drift model effects

**This bug likely explains:**
- Why BH2009 decoding fails completely
- Why HRF correlations are inconsistent
- Why results don't match B&H (2009) paper
