"""
Test 1A: Verify HC-only Training Implementation

Purpose: Verify that existing evaluate_srm_between_subject.py correctly implements
         HC-only training by recomputing results and comparing to reported values.

Expected: Difference < 0.01 (numerical tolerance) for all ROIs
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent.parent))
sys.path.append(str(script_dir.parent.parent.parent.parent))

from utils.srm_alignment import apply_srm_alignment


# Subject definitions (from CLAUDE.md)
HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']

# k values used in original analysis
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 4}


def load_baseline_amplitudes(baseline_dir: Path, subject: str, roi: str) -> np.ndarray:
    """
    Load baseline amplitude data for a subject-ROI.

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline32 results
    subject : str
        Subject ID (e.g., 'sub-01')
    roi : str
        ROI name

    Returns
    -------
    amplitudes : np.ndarray
        Shape (n_runs=6, n_colors=8, n_voxels)
    """
    amp_file = baseline_dir / subject / roi / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"Amplitude file not found: {amp_file}")

    amplitudes = np.load(amp_file)

    # Expected shape: (6, 8, n_voxels)
    if amplitudes.shape[0] != 6 or amplitudes.shape[1] != 8:
        raise ValueError(f"Unexpected amplitude shape: {amplitudes.shape}")

    return amplitudes


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Compute Procrustes disparity between two point clouds.

    Parameters
    ----------
    X, Y : np.ndarray
        Shape (n_points, n_features)

    Returns
    -------
    disparity : float
        Procrustes disparity (normalized alignment error)
    """
    from scipy.linalg import orthogonal_procrustes

    # Center data
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)

    # Normalize
    X_norm = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_norm = Y_centered / np.linalg.norm(Y_centered, 'fro')

    # Find optimal rotation
    R, _ = orthogonal_procrustes(X_norm, Y_norm)

    # Compute disparity
    disparity = np.linalg.norm(X_norm @ R - Y_norm, 'fro')

    return disparity


def compute_rdm_correlation(patterns1: np.ndarray, patterns2: np.ndarray) -> float:
    """
    Compute Spearman correlation between RDMs.

    Parameters
    ----------
    patterns1, patterns2 : np.ndarray
        Shape (n_colors=8, n_voxels)

    Returns
    -------
    r : float
        Spearman correlation between RDM upper triangles
    """
    # Compute RDMs
    rdm1 = squareform(pdist(patterns1, metric='correlation'))
    rdm2 = squareform(pdist(patterns2, metric='correlation'))

    # Extract upper triangle
    idx = np.triu_indices(8, k=1)
    rdm1_vec = rdm1[idx]
    rdm2_vec = rdm2[idx]

    # Spearman correlation
    r, _ = spearmanr(rdm1_vec, rdm2_vec)

    return r


def verify_hc_only_training(baseline_dir: Path, existing_results_dir: Path,
                            output_dir: Path):
    """
    Main verification function.

    Steps:
    1. Load baseline amplitudes for all subjects
    2. Average across runs: (n_subjects, n_colors=8, n_voxels)
    3. Train SRM on HC subjects only (sub-01 to sub-07)
    4. Project CVD subjects to shared space
    5. Compute Procrustes disparities
    6. Compare to existing results

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline32 results
    existing_results_dir : Path
        Directory containing original SRM results
    output_dir : Path
        Output directory for verification results
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Settings
    settings = {
        'timestamp': timestamp,
        'baseline_dir': str(baseline_dir),
        'existing_results_dir': str(existing_results_dir),
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'rois': ROIS,
        'k_values': K_VALUES,
        'n_runs': 6,
        'n_colors': 8
    }

    with open(results_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    # Results storage
    verification_results = {}
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("Test 1A: HC-only Training Verification")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append(f"HC subjects: {HC_SUBJECTS}")
    report_lines.append(f"CVD subjects: {CVD_SUBJECTS}")
    report_lines.append("")

    for roi in ROIS:
        print(f"\n=== Verifying {roi} ===")
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"ROI: {roi}")
        report_lines.append(f"{'='*80}")

        k = K_VALUES[roi]
        report_lines.append(f"SRM components (k): {k}")

        # Load existing results (try both naming conventions)
        # New format: V1_procrustes_srm_results.json
        # Old format: V1_srm_between_subject_results.json
        roi_mapped = 'V4' if roi == 'hV4' else roi
        existing_file = existing_results_dir / f"{roi_mapped}_procrustes_srm_results.json"

        if not existing_file.exists():
            existing_file = existing_results_dir / f"{roi}_srm_between_subject_results.json"

        if not existing_file.exists():
            print(f"  WARNING: Existing results not found for {roi}")
            report_lines.append(f"  ⚠️  Existing results not found")
            continue

        with open(existing_file, 'r') as f:
            existing_data = json.load(f)

        # Load amplitudes for all subjects
        hc_amplitudes = []
        cvd_amplitudes = []

        for subject in HC_SUBJECTS:
            try:
                amp = load_baseline_amplitudes(baseline_dir, subject, roi)
                # Average across runs: (8, n_voxels)
                hc_amplitudes.append(amp.mean(axis=0))
            except FileNotFoundError as e:
                print(f"  ERROR: {e}")
                report_lines.append(f"  ❌ {e}")
                continue

        for subject in CVD_SUBJECTS:
            try:
                amp = load_baseline_amplitudes(baseline_dir, subject, roi)
                cvd_amplitudes.append(amp.mean(axis=0))
            except FileNotFoundError as e:
                print(f"  ERROR: {e}")
                report_lines.append(f"  ❌ {e}")
                continue

        if len(hc_amplitudes) != 7 or len(cvd_amplitudes) != 3:
            print(f"  ERROR: Incomplete data (HC: {len(hc_amplitudes)}, CVD: {len(cvd_amplitudes)})")
            report_lines.append(f"  ❌ Incomplete data")
            continue

        hc_amplitudes = np.array(hc_amplitudes)  # (7, 8, n_voxels)
        cvd_amplitudes = np.array(cvd_amplitudes)  # (3, 8, n_voxels)

        print(f"  HC amplitudes: {hc_amplitudes.shape}")
        print(f"  CVD amplitudes: {cvd_amplitudes.shape}")

        # Train SRM on HC subjects only
        print(f"  Training SRM (k={k}) on HC subjects only...")
        hc_aligned, srm_model = apply_srm_alignment(hc_amplitudes, k=k)

        # Project CVD subjects to shared space
        print(f"  Projecting CVD subjects to shared space...")
        cvd_aligned = []
        for cvd_amp in cvd_amplitudes:
            # Transform: (8, n_voxels) @ W -> (8, k)
            cvd_transformed = cvd_amp @ srm_model.w_[0]  # Use first subject's W as reference
            cvd_aligned.append(cvd_transformed)
        cvd_aligned = np.array(cvd_aligned)  # (3, 8, k)

        print(f"  HC aligned: {hc_aligned.shape}")
        print(f"  CVD aligned: {cvd_aligned.shape}")

        # Compute HC reference (mean of aligned HC patterns)
        hc_reference = hc_aligned.mean(axis=0)  # (8, k)

        # Compute Procrustes disparities
        hc_disparities = []
        for hc_pattern in hc_aligned:
            disparity = compute_procrustes_disparity(hc_pattern, hc_reference)
            hc_disparities.append(disparity)

        cvd_disparities = []
        for cvd_pattern in cvd_aligned:
            disparity = compute_procrustes_disparity(cvd_pattern, hc_reference)
            cvd_disparities.append(disparity)

        # Recomputed metrics
        recomputed_hc_disparity_mean = np.mean(hc_disparities)
        recomputed_cvd_disparity_mean = np.mean(cvd_disparities)

        # Extract existing metrics (handle different possible structures)
        if 'results' in existing_data and 'disparities' in existing_data['results']:
            # New structure
            disparities = existing_data['results']['disparities']
            existing_hc_disparity = disparities.get('hc_to_hc_reference', {}).get('mean')
            existing_cvd_disparity = disparities.get('cvd_to_hc_reference', {}).get('mean')
        elif 'hc_hc_procrustes_disparity_mean' in existing_data:
            # Old structure
            existing_hc_disparity = existing_data['hc_hc_procrustes_disparity_mean']
            existing_cvd_disparity = existing_data.get('cvd_hc_procrustes_disparity_mean')
        else:
            existing_hc_disparity = None
            existing_cvd_disparity = None

        # Compute differences
        if existing_hc_disparity is not None:
            hc_diff = abs(recomputed_hc_disparity_mean - existing_hc_disparity)
        else:
            hc_diff = None

        if existing_cvd_disparity is not None:
            cvd_diff = abs(recomputed_cvd_disparity_mean - existing_cvd_disparity)
        else:
            cvd_diff = None

        # Check pass/fail (threshold: 0.01)
        threshold = 0.01
        hc_pass = hc_diff is not None and hc_diff < threshold
        cvd_pass = cvd_diff is not None and cvd_diff < threshold

        # Store results
        verification_results[roi] = {
            'k': k,
            'recomputed_hc_disparity_mean': float(recomputed_hc_disparity_mean),
            'recomputed_cvd_disparity_mean': float(recomputed_cvd_disparity_mean),
            'existing_hc_disparity_mean': existing_hc_disparity,
            'existing_cvd_disparity_mean': existing_cvd_disparity,
            'hc_disparity_difference': hc_diff,
            'cvd_disparity_difference': cvd_diff,
            'hc_pass': hc_pass,
            'cvd_pass': cvd_pass,
            'hc_disparities': [float(d) for d in hc_disparities],
            'cvd_disparities': [float(d) for d in cvd_disparities]
        }

        # Report
        report_lines.append(f"\nRecomputed Metrics:")
        report_lines.append(f"  HC-HC disparity: {recomputed_hc_disparity_mean:.4f}")
        report_lines.append(f"  CVD-HC disparity: {recomputed_cvd_disparity_mean:.4f}")
        report_lines.append(f"\nExisting Metrics:")
        report_lines.append(f"  HC-HC disparity: {existing_hc_disparity}")
        report_lines.append(f"  CVD-HC disparity: {existing_cvd_disparity}")
        report_lines.append(f"\nDifferences:")
        report_lines.append(f"  HC-HC difference: {hc_diff}")
        report_lines.append(f"  CVD-HC difference: {cvd_diff}")
        report_lines.append(f"\nVerification (threshold < {threshold}):")
        report_lines.append(f"  HC-HC: {'✅ PASS' if hc_pass else '❌ FAIL'}")
        report_lines.append(f"  CVD-HC: {'✅ PASS' if cvd_pass else '❌ FAIL'}")

        print(f"  Recomputed HC-HC: {recomputed_hc_disparity_mean:.4f} (diff: {hc_diff})")
        print(f"  Recomputed CVD-HC: {recomputed_cvd_disparity_mean:.4f} (diff: {cvd_diff})")
        print(f"  HC-HC verification: {'PASS' if hc_pass else 'FAIL'}")
        print(f"  CVD-HC verification: {'PASS' if cvd_pass else 'FAIL'}")

    # Overall summary
    report_lines.append(f"\n{'='*80}")
    report_lines.append("OVERALL SUMMARY")
    report_lines.append(f"{'='*80}")

    all_pass = all(verification_results[roi]['hc_pass'] and verification_results[roi]['cvd_pass']
                   for roi in verification_results)

    if all_pass:
        report_lines.append("✅ ALL TESTS PASSED")
        report_lines.append("   HC-only training implementation is CORRECT")
    else:
        report_lines.append("❌ SOME TESTS FAILED")
        report_lines.append("   Review differences above threshold")

    # Save results
    with open(results_dir / 'results.json', 'w') as f:
        json.dump(verification_results, f, indent=2)

    with open(results_dir / 'verification_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"\n{'='*80}")
    print(f"Results saved to: {results_dir}")
    print(f"{'='*80}")

    # Print report
    print('\n'.join(report_lines))


if __name__ == '__main__':
    # Paths
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')

    # Baseline results (C010 dataset)
    baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

    if not baseline_dir.exists():
        raise FileNotFoundError(f"Baseline results not found: {baseline_dir}")

    print(f"Using baseline results: {baseline_dir}")

    # SRM results (c010 combined)
    existing_results_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'results' / 'c010' / 'combined_20260209'

    if not existing_results_dir.exists():
        raise FileNotFoundError(f"SRM results not found: {existing_results_dir}")

    print(f"Using existing SRM results: {existing_results_dir}")

    # Output directory
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1A_verify_hc_only' / 'results'

    # Run verification
    verify_hc_only_training(baseline_dir, existing_results_dir, output_dir)
