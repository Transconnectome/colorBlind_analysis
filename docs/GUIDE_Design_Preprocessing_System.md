# Implementation Guide: Systematic Preprocessing Review

## Status: READY FOR IMPLEMENTATION

### Completed ✓
1. Plan document: `/Users/jinilkim/.claude/plans/memoized-honking-karp.md`
2. SBatch file: `run_systematic_review.sbatch`
3. Submission script: `submit_all_systematic_reviews.sh`
4. Started: `fir_reconstruction_BH2009_system.py` (partial)

### Remaining Work

## Core File: fir_reconstruction_BH2009_system.py

**Approach**: Modify `fir_reconstruction_BH2009.py` to support all preprocessing configurations

### Required Modifications

#### 1. Add at top (after imports, before line 70):
```python
import json
from datetime import datetime
import time

def generate_all_configs():
    """Generate all 144 configurations"""
    configs = []
    config_idx = 0
    for smooth in [0, 6, 8]:
        for hpass in [None, 0.01]:
            for motion in ['none', 'cosine', 'extended']:
                for compcor in [None, 5]:
                    for drift in [None, 'per_run']:
                        for standardize in [False, True]:
                            configs.append({
                                'config_idx': config_idx,
                                'smoothing_fwhm': smooth,
                                'high_pass_hz': hpass,
                                'motion_confounds': motion,
                                'compcor_components': compcor,
                                'drift_model': drift,
                                'standardize_voxels': standardize
                            })
                            config_idx += 1
    return configs

def config_to_name(config):
    """Convert config to name"""
    sm = f"sm{config['smoothing_fwhm']}"
    hp = "hpYe" if config['high_pass_hz'] else "hpNo"
    mo = {'none': 'moNo', 'cosine': 'moCo', 'extended': 'moEx'}[config['motion_confounds']]
    cc = "ccYe" if config['compcor_components'] else "ccNo"
    dr = "drPr" if config['drift_model'] == 'per_run' else "drNo"
    st = "stTr" if config['standardize_voxels'] else "stFa"
    return f"{sm}_{hp}_{mo}_{cc}_{dr}_{st}"
```

#### 2. Add confounds functions (from scenario5_voxelHRF.py lines 137-244):
```python
def load_motion_confounds(confounds_path, motion_type='none', compcor_n=None):
    # Copy implementation from fir_reconstruction_scenario5_voxelHRF.py:137-214
    ...

def regress_confounds(data, confounds):
    # Copy implementation from fir_reconstruction_scenario5_voxelHRF.py:216-244
    ...
```

#### 3. Modify `build_fir_design_matrix()` (line 222):
Add `drift_model` parameter:
```python
def build_fir_design_matrix(onsets, n_scans, tr, fir_delays, drift_model=None, run_idx=None, n_runs=None):
    # ... existing FIR code ...

    # At end, add:
    if drift_model == 'per_run' and run_idx is not None and n_runs is not None:
        drift_cols = np.zeros((n_scans, 2 * n_runs))
        drift_cols[:, run_idx * 2] = np.linspace(-1, 1, n_scans)
        drift_cols[:, run_idx * 2 + 1] = 1.0
        X = np.hstack([X_fir, drift_cols])
    else:
        X = X_fir
    return X
```

#### 4. Modify argument parsing (line 362):
```python
def parse_args():
    parser = argparse.ArgumentParser(description='Systematic preprocessing review')
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--run-all-configs', action='store_true',
                        help='Run all 144 configs')
    parser.add_argument('--single-config', type=int, default=None,
                        help='Run single config index (0-143)')
    return parser.parse_args()
```

#### 5. Wrap main analysis in function (lines 378-1898):
Convert the script body into:
```python
def run_analysis_with_config(subject_id, roi_name, config):
    """Run full analysis with given preprocessing config"""

    # Set globals from config
    global SMOOTHING_FWHM, HIGH_PASS_HZ, MOTION_TYPE, COMPCOR_N, DRIFT_MODEL, STANDARDIZE_VOXELS
    SMOOTHING_FWHM = config['smoothing_fwhm']
    HIGH_PASS_HZ = config['high_pass_hz']
    MOTION_TYPE = config['motion_confounds']
    COMPCOR_N = config['compcor_components']
    DRIFT_MODEL = config['drift_model']
    STANDARDIZE_VOXELS = config['standardize_voxels']

    # Existing analysis code (lines 378-1898) goes here
    # ... (with modifications for preprocessing)

    # Return metrics dict
    return {
        'snr_median': float(np.median(voxel_snr)),
        'snr_mean': float(np.mean(voxel_snr)),
        'run_correlation_mean': float(np.mean(run_correlations)),
        'run_correlation_min': float(np.min(run_correlations)),
        'run_correlation_max': float(np.max(run_correlations)),
        'hrf_consistency_mean': float(np.mean(hrf_correlations)),
        'hrf_consistency_median': float(np.median(hrf_correlations)),
        'r2_median': float(r2_median),
        'r2_mean': float(r2_mean),
        'classification_accuracy': float(mean_classification_acc),
        'reconstruction_error_mean': float(mean_reconstruction_error),
        'reconstruction_error_median': float(np.median([r['mean_error'] for r in reconstruction_results])),
        'n_voxels_total': int(n_voxels_total),
        'n_voxels_selected': int(n_voxels_selected)
    }
```

#### 6. Add main loop (replace lines 378-1898):
```python
if __name__ == '__main__':
    args = parse_args()

    if args.run_all_configs:
        all_configs = generate_all_configs()
        output_base = f"derivatives/BH2009_systematic_review/sub-{args.subject}/{args.roi}"
        os.makedirs(output_base, exist_ok=True)

        results = []
        for config in all_configs:
            config_name = config_to_name(config)
            checkpoint_path = f"{output_base}/checkpoint_{config['config_idx']:03d}.json"

            if os.path.exists(checkpoint_path):
                print(f"[{config['config_idx']+1}/144] Skipping {config_name}")
                with open(checkpoint_path, 'r') as f:
                    results.append(json.load(f))
                continue

            print(f"\n{'='*80}")
            print(f"[{config['config_idx']+1}/144] Running: {config_name}")
            print(f"{'='*80}")

            try:
                start_time = time.time()
                metrics = run_analysis_with_config(args.subject, args.roi, config)
                elapsed = time.time() - start_time

                checkpoint = {
                    'config_idx': config['config_idx'],
                    'config': config,
                    'config_name': config_name,
                    'subject': args.subject,
                    'roi': args.roi,
                    'metrics': metrics,
                    'timing': {'total_seconds': elapsed},
                    'timestamp': datetime.now().isoformat()
                }

                with open(checkpoint_path, 'w') as f:
                    json.dump(checkpoint, f, indent=2)

                results.append(checkpoint)
                print(f"✓ Completed in {elapsed/60:.1f} min")

            except Exception as e:
                print(f"✗ FAILED: {str(e)}")
                traceback.print_exc()
                continue

        # Save summary
        with open(f"{output_base}/summary_all_configs.json", 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Completed {len(results)}/144 configurations")
        print(f"{'='*80}")
```

#### 7. Modify data loading section (around line 515):
```python
# BEFORE creating masker, add smoothing
if SMOOTHING_FWHM > 0:
    func_img = nimg.smooth_img(func_img, fwhm=SMOOTHING_FWHM)
    print(f"    Applied {SMOOTHING_FWHM}mm smoothing")

# Create masker with conditional standardization
masker = NiftiMasker(
    mask_img=roi_img,
    standardize=STANDARDIZE_VOXELS  # from config
)

# After masking, add high-pass filtering
if HIGH_PASS_HZ is not None:
    func_data = nsignal.clean(func_data, detrend=False, standardize=False,
                              high_pass=HIGH_PASS_HZ, t_r=TR)
    print(f"    Applied {HIGH_PASS_HZ} Hz high-pass filter")

# Add confounds regression
if MOTION_TYPE != 'none' or COMPCOR_N is not None:
    confounds_path = func_path.replace('_bold.nii.gz', '_desc-confounds_timeseries.tsv')
    confounds, n_conf = load_motion_confounds(confounds_path, MOTION_TYPE, COMPCOR_N)
    if confounds is not None:
        if VOLS_TO_DROP > 0:
            confounds = confounds[VOLS_TO_DROP:, :]
        func_data = regress_confounds(func_data, confounds)
        print(f"    Regressed {n_conf} confounds")
```

#### 8. Update FIR GLM calls (around line 661):
```python
X_fir = build_fir_design_matrix(all_onsets, n_scans, TR, FIR_DELAYS,
                                drift_model=DRIFT_MODEL,  # ADD THIS
                                run_idx=run_idx, n_runs=N_RUNS)
```

## Alternative: Simpler Wrapper Approach

If full integration is too complex, create a simple wrapper that:
1. Generates configs
2. Temporarily modifies BH2009.py parameters
3. Calls it 144 times

Would be faster to implement but less elegant.

## Next Steps

**Option A**: Complete implementation now (est. 2-3 hours)
**Option B**: Continue in next session with fresh context
**Option C**: Use simpler wrapper approach (30 min)

Which approach would you prefer?
