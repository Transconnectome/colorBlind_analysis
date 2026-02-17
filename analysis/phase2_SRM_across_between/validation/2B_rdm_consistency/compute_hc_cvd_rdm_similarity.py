"""
Test 2B (CORRECTED): HC-CVD RDM Similarity

Purpose: Test if CVD subjects preserve the SAME relational color structure as HC
         CRITICAL TEST for validating "parallel" pattern

Method:
1. For each subject, compute RDM from averaged runs
2. Compute RDM similarity (Spearman correlation) between:
   - HC-HC pairs (within-HC similarity)
   - CVD-CVD pairs (within-CVD similarity)
   - HC-CVD pairs (between-group similarity)
3. Test hypothesis: HC-CVD similarity should be HIGH (comparable to HC-HC)

Expected: If CVD preserves color structure ("parallel"), then:
          - HC-CVD RDM correlation should be high (>0.4-0.5)
          - HC-CVD correlation should be comparable to HC-HC correlation
          - This shows CVD uses SAME relational structure as HC

Interpretation: "Parallel" = CVD의 RDM이 HC의 RDM과 유사하다
                (NOT: CVD의 split-half reliability가 HC보다 높다)
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr, ttest_ind
from scipy.spatial.distance import squareform, pdist
from itertools import combinations

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'hV4']


def load_baseline_amplitudes(baseline_dir: Path, subject: str, roi: str) -> np.ndarray:
    """Load baseline amplitude data."""
    roi_mapped = 'V4' if roi == 'hV4' else roi

    amp_file_options = [
        baseline_dir / subject / roi_mapped / 'amplitudes_procrustes.npy',
        baseline_dir / subject / roi_mapped / 'amplitudes_raw.npy'
    ]

    for amp_file in amp_file_options:
        if amp_file.exists():
            amplitudes = np.load(amp_file)
            if amplitudes.shape[0] != 6 or amplitudes.shape[1] != 8:
                raise ValueError(f"Unexpected amplitude shape: {amplitudes.shape}")
            return amplitudes

    raise FileNotFoundError(f"Amplitude file not found for {subject}/{roi_mapped}")


def compute_rdm(patterns: np.ndarray) -> np.ndarray:
    """
    Compute RDM from pattern matrix.

    Parameters
    ----------
    patterns : np.ndarray
        Shape (n_colors=8, n_voxels)

    Returns
    -------
    rdm : np.ndarray
        Shape (8, 8) dissimilarity matrix using correlation distance
    """
    rdm = squareform(pdist(patterns, metric='correlation'))
    return rdm


def main(baseline_dir: Path, output_dir: Path):
    """
    Main function for HC-CVD RDM similarity analysis.

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline amplitudes
    output_dir : Path
        Output directory
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Settings
    settings = {
        'timestamp': timestamp,
        'baseline_dir': str(baseline_dir),
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'rois': ROIS,
        'metric': 'rdm_spearman_correlation',
        'hypothesis': 'HC-CVD RDM similarity should be high (parallel pattern)'
    }

    with open(results_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    # Results storage
    rdm_results = {}
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("Test 2B (CORRECTED): HC-CVD RDM Similarity")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append("")
    report_lines.append("CRITICAL TEST: HC-CVD RDM correlation should be HIGH")
    report_lines.append("               (validates 'parallel' = same relational structure)")
    report_lines.append("")

    print(f"\n=== Computing HC-CVD RDM Similarity ===\n")

    for roi in ROIS:
        print(f"=== {roi} ===")
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"ROI: {roi}")
        report_lines.append(f"{'='*80}")

        # Load all subjects and compute RDMs
        subject_rdms = {}

        for subject in ALL_SUBJECTS:
            try:
                # Load and average across runs
                amplitudes = load_baseline_amplitudes(baseline_dir, subject, roi)  # (6, 8, n_voxels)
                pattern = amplitudes.mean(axis=0)  # (8, n_voxels)

                # Compute RDM
                rdm = compute_rdm(pattern)  # (8, 8)

                subject_rdms[subject] = rdm

                print(f"  Loaded {subject}: pattern shape {pattern.shape}")

            except Exception as e:
                print(f"  WARNING: Could not load {subject}: {e}")
                continue

        if len(subject_rdms) < 8:
            print(f"  ERROR: Insufficient subjects ({len(subject_rdms)}/10)")
            report_lines.append(f"  ❌ Insufficient data")
            continue

        print(f"  Total subjects loaded: {len(subject_rdms)}")

        # Compute pairwise RDM similarities
        hc_hc_correlations = []
        cvd_cvd_correlations = []
        hc_cvd_correlations = []

        all_subjects_list = list(subject_rdms.keys())

        for subj_i, subj_j in combinations(all_subjects_list, 2):
            # Extract upper triangle vectors
            mask = np.triu(np.ones_like(subject_rdms[subj_i], dtype=bool), k=1)
            vec_i = subject_rdms[subj_i][mask]
            vec_j = subject_rdms[subj_j][mask]

            # Spearman correlation
            r, _ = spearmanr(vec_i, vec_j)

            # Categorize by group
            if subj_i in HC_SUBJECTS and subj_j in HC_SUBJECTS:
                hc_hc_correlations.append(r)
            elif subj_i in CVD_SUBJECTS and subj_j in CVD_SUBJECTS:
                cvd_cvd_correlations.append(r)
            else:  # One HC, one CVD
                hc_cvd_correlations.append(r)

        # Compute statistics
        hc_hc_mean = np.mean(hc_hc_correlations) if hc_hc_correlations else 0.0
        hc_hc_std = np.std(hc_hc_correlations) if hc_hc_correlations else 0.0

        cvd_cvd_mean = np.mean(cvd_cvd_correlations) if cvd_cvd_correlations else 0.0
        cvd_cvd_std = np.std(cvd_cvd_correlations) if cvd_cvd_correlations else 0.0

        hc_cvd_mean = np.mean(hc_cvd_correlations) if hc_cvd_correlations else 0.0
        hc_cvd_std = np.std(hc_cvd_correlations) if hc_cvd_correlations else 0.0

        # Critical test: Is HC-CVD correlation high?
        # Compare HC-CVD to HC-HC
        if hc_hc_correlations and hc_cvd_correlations:
            t_stat, p_value = ttest_ind(hc_cvd_correlations, hc_hc_correlations)
        else:
            t_stat, p_value = np.nan, np.nan

        # Report
        report_lines.append(f"\nRDM Similarity Statistics:")
        report_lines.append(f"  HC-HC (n={len(hc_hc_correlations)}): {hc_hc_mean:.3f} ± {hc_hc_std:.3f}")
        report_lines.append(f"  CVD-CVD (n={len(cvd_cvd_correlations)}): {cvd_cvd_mean:.3f} ± {cvd_cvd_std:.3f}")
        report_lines.append(f"  HC-CVD (n={len(hc_cvd_correlations)}): {hc_cvd_mean:.3f} ± {hc_cvd_std:.3f}")

        report_lines.append(f"\nCritical Comparison (HC-CVD vs HC-HC):")
        report_lines.append(f"  Difference: {hc_cvd_mean - hc_hc_mean:+.3f}")
        report_lines.append(f"  t-test: t={t_stat:.3f}, p={p_value:.4f}")

        # Critical validation for V1/V2
        if roi in ['V1', 'V2']:
            # Criterion: HC-CVD correlation should be >0.4 (moderate-high)
            # AND not significantly lower than HC-HC
            is_high = hc_cvd_mean > 0.4
            not_lower = (p_value > 0.05) or (hc_cvd_mean >= hc_hc_mean)

            if is_high and not_lower:
                report_lines.append(f"  ✅ CRITICAL: HC-CVD similarity HIGH ({hc_cvd_mean:.3f} > 0.4)")
                report_lines.append(f"              HC-CVD comparable to HC-HC (validates 'parallel')")
                print(f"  ✅ CRITICAL VALIDATION PASSED")
                print(f"     HC-CVD: {hc_cvd_mean:.3f}, HC-HC: {hc_hc_mean:.3f}")
            else:
                if not is_high:
                    report_lines.append(f"  ❌ WARNING: HC-CVD similarity LOW ({hc_cvd_mean:.3f} < 0.4)")
                if not not_lower:
                    report_lines.append(f"  ❌ WARNING: HC-CVD significantly < HC-HC (p={p_value:.4f})")
                report_lines.append(f"              'Parallel' pattern NOT validated")
                print(f"  ❌ VALIDATION FAILED")
        else:
            report_lines.append(f"  ℹ️  Note: {roi} not critical for validation")

        # Store results
        rdm_results[roi] = {
            'hc_hc': {
                'mean': float(hc_hc_mean),
                'std': float(hc_hc_std),
                'values': [float(r) for r in hc_hc_correlations],
                'n_pairs': len(hc_hc_correlations)
            },
            'cvd_cvd': {
                'mean': float(cvd_cvd_mean),
                'std': float(cvd_cvd_std),
                'values': [float(r) for r in cvd_cvd_correlations],
                'n_pairs': len(cvd_cvd_correlations)
            },
            'hc_cvd': {
                'mean': float(hc_cvd_mean),
                'std': float(hc_cvd_std),
                'values': [float(r) for r in hc_cvd_correlations],
                'n_pairs': len(hc_cvd_correlations)
            },
            'hc_cvd_vs_hc_hc': {
                't_statistic': float(t_stat) if np.isfinite(t_stat) else None,
                'p_value': float(p_value) if np.isfinite(p_value) else None,
                'difference': float(hc_cvd_mean - hc_hc_mean)
            },
            'validation': {
                'hc_cvd_high': bool(hc_cvd_mean > 0.4),
                'hc_cvd_comparable_to_hc_hc': bool((p_value > 0.05) or (hc_cvd_mean >= hc_hc_mean)) if np.isfinite(p_value) else False
            }
        }

        print()

    # Overall summary
    report_lines.append(f"\n{'='*80}")
    report_lines.append("OVERALL SUMMARY")
    report_lines.append(f"{'='*80}")

    critical_rois_pass = []
    for roi in ['V1', 'V2']:
        if roi in rdm_results:
            validation = rdm_results[roi]['validation']
            if validation['hc_cvd_high'] and validation['hc_cvd_comparable_to_hc_hc']:
                critical_rois_pass.append(roi)

    report_lines.append(f"\nCritical ROIs (V1/V2) with HC-CVD similarity validated: {len(critical_rois_pass)}/2")

    for roi in ['V1', 'V2']:
        if roi in rdm_results:
            hc_cvd_mean = rdm_results[roi]['hc_cvd']['mean']
            hc_hc_mean = rdm_results[roi]['hc_hc']['mean']
            if roi in critical_rois_pass:
                report_lines.append(f"  ✅ {roi}: HC-CVD={hc_cvd_mean:.3f} (high & comparable to HC-HC={hc_hc_mean:.3f})")
            else:
                report_lines.append(f"  ❌ {roi}: HC-CVD={hc_cvd_mean:.3f} (low or < HC-HC={hc_hc_mean:.3f})")

    report_lines.append(f"\nInterpretation:")
    report_lines.append(f"  - High HC-CVD correlation: CVD preserves HC's relational color structure")
    report_lines.append(f"  - Low HC-CVD correlation: CVD uses different color structure")

    if len(critical_rois_pass) == 2:
        report_lines.append(f"\n✅ VALIDATION SUCCESSFUL: 'Parallel' pattern confirmed in V1/V2")
        report_lines.append(f"   CVD subjects use SAME relational color structure as HC")
    elif len(critical_rois_pass) == 1:
        report_lines.append(f"\n⚠️  PARTIAL VALIDATION: 'Parallel' pattern confirmed in {critical_rois_pass[0]} only")
    else:
        report_lines.append(f"\n❌ VALIDATION FAILED: 'Parallel' pattern NOT confirmed")
        report_lines.append(f"   CVD may use different color structure than HC")

    # Save results
    with open(results_dir / 'hc_cvd_rdm_similarity_results.json', 'w') as f:
        json.dump(rdm_results, f, indent=2)

    with open(results_dir / 'hc_cvd_rdm_similarity_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"{'='*80}")
    print(f"Results saved to: {results_dir}")
    print(f"{'='*80}")

    # Print report
    print('\n'.join(report_lines))

    return rdm_results


if __name__ == '__main__':
    # Paths
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')

    # Baseline results
    baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

    if not baseline_dir.exists():
        raise FileNotFoundError(f"Baseline results not found: {baseline_dir}")

    print(f"Using baseline results: {baseline_dir}")

    # Output directory
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '2B_rdm_consistency' / 'results'

    # Run HC-CVD RDM similarity analysis
    results = main(baseline_dir, output_dir)

    print("\n✅ HC-CVD RDM similarity analysis completed!")
