#!/usr/bin/env python3
"""
Evaluate all 36 factorial conditions with standardized metrics.

Fixed implementation:
1. Proper crossnobis computation (per-run RDMs)
2. Correct condition name parsing
3. Actual Procrustes alignment
"""

import numpy as np
from pathlib import Path
import json
import sys
from scipy.stats import spearmanr

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))
from crossnobis_ldw import compute_rdm_crossnobis
from procrustes_normalized import procrustes_normalized


def compute_rdm_correlation_per_run(amplitudes):
    """
    Compute correlation-based RDM for each run separately.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)

    Returns
    -------
    rdms : np.ndarray, shape (n_runs, n_colors, n_colors)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    rdms = np.zeros((n_runs, n_colors, n_colors))

    for r in range(n_runs):
        # Correlation distance: 1 - Pearson correlation
        rdms[r] = 1 - np.corrcoef(amplitudes[r])

    return rdms


def rdm_reliability_spearman(rdms):
    """
    Compute RDM reliability using pairwise Spearman correlations.

    Parameters
    ----------
    rdms : np.ndarray, shape (n_runs, n_colors, n_colors)

    Returns
    -------
    mean_corr : float
        Mean Spearman correlation between all run pairs
    """
    n_runs, n_colors, _ = rdms.shape

    # Upper triangle indices
    triu_idx = np.triu_indices(n_colors, k=1)

    # Pairwise correlations
    correlations = []
    for i in range(n_runs):
        for j in range(i + 1, n_runs):
            rdm_i = rdms[i][triu_idx]
            rdm_j = rdms[j][triu_idx]
            corr, _ = spearmanr(rdm_i, rdm_j)
            if not np.isnan(corr):
                correlations.append(corr)

    if len(correlations) == 0:
        return np.nan

    return np.mean(correlations)


def compute_crossnobis_rdms_per_run(amplitudes):
    """
    Compute crossnobis RDM for each run using leave-one-run-out.

    For each test run:
      - Estimate covariance from other runs
      - Compute Mahalanobis distance in test run

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)

    Returns
    -------
    rdms : np.ndarray, shape (n_runs, n_colors, n_colors)
    shrinkages : np.ndarray, shape (n_runs,)
    """
    from sklearn.covariance import LedoitWolf

    n_runs, n_colors, n_voxels = amplitudes.shape
    rdms = np.zeros((n_runs, n_colors, n_colors))
    shrinkages = np.zeros(n_runs)

    for test_run in range(n_runs):
        # Leave-one-run-out
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_data = amplitudes[train_runs]  # (n_train, n_colors, n_voxels)

        # Reshape for covariance
        X_train = train_data.reshape(-1, n_voxels)  # (n_train * n_colors, n_voxels)

        # Ledoit-Wolf shrinkage
        lw = LedoitWolf()
        lw.fit(X_train)
        cov = lw.covariance_
        shrinkages[test_run] = lw.shrinkage_

        # Precision matrix
        try:
            cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            cov_inv = np.linalg.pinv(cov)

        # Test patterns
        test_patterns = amplitudes[test_run]  # (n_colors, n_voxels)

        # Mahalanobis distances
        for i in range(n_colors):
            for j in range(n_colors):
                diff = test_patterns[i] - test_patterns[j]
                dist_sq = diff @ cov_inv @ diff.T
                dist_sq = max(0, dist_sq)  # Numerical safety
                rdms[test_run, i, j] = np.sqrt(dist_sq)

    return rdms, shrinkages


def evaluate_single_condition(condition_dir, verbose=True):
    """
    Evaluate one condition with metrics before and after Procrustes alignment.

    Returns
    -------
    results : dict
        BEFORE Procrustes:
        - rdm_correlation_before: RDM reliability (Pearson-based)
        - rdm_crossnobis_before: RDM reliability (Mahalanobis-based)
        - decoding_accuracy_before: Leave-one-run-out classification

        Procrustes:
        - procrustes_disparity: Mean normalized Procrustes disparity

        AFTER Procrustes:
        - rdm_correlation_after: RDM reliability after alignment
        - rdm_crossnobis_after: RDM reliability after alignment
        - decoding_accuracy_after: Classification after alignment

        Improvements:
        - rdm_correlation_improvement: after - before
        - rdm_crossnobis_improvement: after - before
        - decoding_improvement: after - before

        Other:
        - shrinkage: Mean Ledoit-Wolf shrinkage
        - n_voxels: Number of voxels
    """
    if verbose:
        print(f"  Loading data...")

    # Load amplitudes
    amplitudes_path = condition_dir / "amplitudes_raw.npy"
    if not amplitudes_path.exists():
        raise FileNotFoundError(f"amplitudes_raw.npy not found in {condition_dir}")

    amplitudes_raw = np.load(amplitudes_path)  # (n_runs, n_colors, n_voxels)
    n_runs, n_colors, n_voxels = amplitudes_raw.shape

    if verbose:
        print(f"    Shape: {amplitudes_raw.shape}")

    # ========================================================================
    # BEFORE PROCRUSTES
    # ========================================================================
    if verbose:
        print("    Computing metrics BEFORE Procrustes...")

    # === Metric 1: RDM Correlation (Before) ===
    rdms_corr_before = compute_rdm_correlation_per_run(amplitudes_raw)
    rdm_corr_reliability_before = rdm_reliability_spearman(rdms_corr_before)

    # === Metric 2: RDM Crossnobis (Before) ===
    rdms_crossnobis_before, shrinkages = compute_crossnobis_rdms_per_run(amplitudes_raw)
    rdm_crossnobis_reliability_before = rdm_reliability_spearman(rdms_crossnobis_before)
    mean_shrinkage = np.mean(shrinkages)

    # === Metric 3: Decoding Accuracy (Before) ===
    correct_before = 0
    total = 0

    for test_run in range(n_runs):
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_amps = amplitudes_raw[train_runs].mean(axis=0)  # (n_colors, n_voxels)
        test_amps = amplitudes_raw[test_run]  # (n_colors, n_voxels)

        for true_color in range(n_colors):
            test_pattern = test_amps[true_color]
            distances = np.linalg.norm(train_amps - test_pattern, axis=1)
            predicted_color = np.argmin(distances)

            if predicted_color == true_color:
                correct_before += 1
            total += 1

    decoding_accuracy_before = correct_before / total

    # ========================================================================
    # PROCRUSTES ALIGNMENT
    # ========================================================================
    if verbose:
        print("    Applying Procrustes alignment...")

    amplitudes_aligned, disparities = procrustes_normalized(amplitudes_raw, reference='mean')
    mean_disparity = np.mean(disparities)

    # ========================================================================
    # AFTER PROCRUSTES
    # ========================================================================
    if verbose:
        print("    Computing metrics AFTER Procrustes...")

    # === Metric 1: RDM Correlation (After) ===
    rdms_corr_after = compute_rdm_correlation_per_run(amplitudes_aligned)
    rdm_corr_reliability_after = rdm_reliability_spearman(rdms_corr_after)

    # === Metric 2: RDM Crossnobis (After) ===
    rdms_crossnobis_after, _ = compute_crossnobis_rdms_per_run(amplitudes_aligned)
    rdm_crossnobis_reliability_after = rdm_reliability_spearman(rdms_crossnobis_after)

    # === Metric 3: Decoding Accuracy (After) ===
    correct_after = 0

    for test_run in range(n_runs):
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_amps = amplitudes_aligned[train_runs].mean(axis=0)  # (n_colors, n_voxels)
        test_amps = amplitudes_aligned[test_run]  # (n_colors, n_voxels)

        for true_color in range(n_colors):
            test_pattern = test_amps[true_color]
            distances = np.linalg.norm(train_amps - test_pattern, axis=1)
            predicted_color = np.argmin(distances)

            if predicted_color == true_color:
                correct_after += 1

    decoding_accuracy_after = correct_after / total

    # ========================================================================
    # COMPUTE IMPROVEMENTS
    # ========================================================================
    rdm_corr_improvement = rdm_corr_reliability_after - rdm_corr_reliability_before
    rdm_crossnobis_improvement = rdm_crossnobis_reliability_after - rdm_crossnobis_reliability_before
    decoding_improvement = decoding_accuracy_after - decoding_accuracy_before

    # === Voxel Correspondence ===
    voxel_aligned = None
    if (condition_dir / "voxel_coords.npy").exists():
        voxel_aligned = True

    results = {
        # Before Procrustes
        'rdm_correlation_before': float(rdm_corr_reliability_before),
        'rdm_crossnobis_before': float(rdm_crossnobis_reliability_before),
        'decoding_accuracy_before': float(decoding_accuracy_before),

        # Procrustes
        'procrustes_disparity': float(mean_disparity),

        # After Procrustes
        'rdm_correlation_after': float(rdm_corr_reliability_after),
        'rdm_crossnobis_after': float(rdm_crossnobis_reliability_after),
        'decoding_accuracy_after': float(decoding_accuracy_after),

        # Improvements (delta)
        'rdm_correlation_improvement': float(rdm_corr_improvement),
        'rdm_crossnobis_improvement': float(rdm_crossnobis_improvement),
        'decoding_improvement': float(decoding_improvement),

        # Other
        'shrinkage': float(mean_shrinkage),
        'n_voxels': int(n_voxels),
        'voxel_correspondence': voxel_aligned
    }

    return results


def parse_condition_name(name):
    """
    Parse condition name to extract factors.

    Format: c01_no_hp0_none_none
            c12_yes_hp001_cosine_per_run
            c36_yes_hp001_cosine_per_run_2nd

    Returns
    -------
    factors : dict
    """
    parts = name.split('_')

    # c01, no, hp0, motion, drift(+2nd)
    if len(parts) < 5:
        return None

    factors = {
        'condition_id': parts[0],
        'grid_resample': parts[1],  # no or yes
        'highpass': parts[2],  # hp0 or hp001
    }

    # Motion is parts[3]
    factors['motion'] = parts[3]  # none, standard, or cosine

    # Drift is parts[4] onwards
    # Can be: none, per_run, per_run_2nd
    drift_parts = parts[4:]
    drift = '_'.join(drift_parts)
    factors['drift'] = drift

    return factors


def main():
    """Evaluate all 36 conditions and save summary."""
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate all factorial conditions')
    parser.add_argument('--results-dir', type=str,
                        default='analysis/phase1_preprocess_decoding/results/grid_factorial',
                        help='Root directory containing all conditions')
    parser.add_argument('--subject', type=str, default='01',
                        help='Subject ID')
    parser.add_argument('--roi', type=str, default='V1',
                        help='ROI name')
    parser.add_argument('--output', type=str, default=None,
                        help='Output JSON file')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    print("=" * 80)
    print("Grid Resampling Factorial Evaluation")
    print("=" * 80)
    print(f"Results directory: {results_dir}")
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print()

    # Find all condition directories
    condition_dirs = sorted(results_dir.glob("c*"))

    if len(condition_dirs) == 0:
        print(f"ERROR: No condition directories found in {results_dir}")
        sys.exit(1)

    print(f"Found {len(condition_dirs)} conditions")
    print()

    all_results = {}
    failed_conditions = []

    for condition_dir in condition_dirs:
        condition_name = condition_dir.name
        print(f"Evaluating: {condition_name}")

        # Navigate to subject/ROI subdirectory
        data_dir = condition_dir / f"sub-{args.subject}" / args.roi

        if not data_dir.exists():
            print(f"  ⚠ Data directory not found: {data_dir}")
            failed_conditions.append(condition_name)
            print()
            continue

        try:
            results = evaluate_single_condition(data_dir, verbose=True)

            # Parse condition name to extract factors
            factors = parse_condition_name(condition_name)
            if factors:
                results.update(factors)

            all_results[condition_name] = results

            print(f"  Results:")
            print(f"    BEFORE Procrustes:")
            print(f"      RDM correlation:  {results['rdm_correlation_before']:.4f}")
            print(f"      RDM crossnobis:   {results['rdm_crossnobis_before']:.4f}")
            print(f"      Decoding:         {results['decoding_accuracy_before']:.4f}")
            print(f"    Procrustes disparity: {results['procrustes_disparity']:.4f}")
            print(f"    AFTER Procrustes:")
            print(f"      RDM correlation:  {results['rdm_correlation_after']:.4f} ({results['rdm_correlation_improvement']:+.4f})")
            print(f"      RDM crossnobis:   {results['rdm_crossnobis_after']:.4f} ({results['rdm_crossnobis_improvement']:+.4f})")
            print(f"      Decoding:         {results['decoding_accuracy_after']:.4f} ({results['decoding_improvement']:+.4f})")
            print()

        except Exception as e:
            import traceback
            print(f"  ❌ Failed: {e}")
            print(f"  Traceback:")
            traceback.print_exc()
            failed_conditions.append(condition_name)
            print()

    # Save results
    if args.output is None:
        output_file = results_dir / "evaluation_summary.json"
    else:
        output_file = Path(args.output)

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print("=" * 80)
    print(f"✅ Evaluation complete")
    print(f"   Successful: {len(all_results)} / {len(condition_dirs)}")
    print(f"   Failed: {len(failed_conditions)}")
    print()
    print(f"Saved to: {output_file}")

    if failed_conditions:
        print()
        print("Failed conditions:")
        for cond in failed_conditions:
            print(f"  - {cond}")

    print("=" * 80)

    # Summary statistics
    if len(all_results) > 0:
        print()
        print("Summary Statistics:")
        print()

        # Before Procrustes
        print("BEFORE Procrustes:")
        for metric in ['rdm_correlation_before', 'rdm_crossnobis_before', 'decoding_accuracy_before']:
            values = [r[metric] for r in all_results.values() if not np.isnan(r[metric])]
            if len(values) > 0:
                print(f"  {metric}:")
                print(f"    Mean:   {np.mean(values):.4f}")
                print(f"    Median: {np.median(values):.4f}")
                print(f"    Min:    {np.min(values):.4f}")
                print(f"    Max:    {np.max(values):.4f}")
        print()

        # After Procrustes
        print("AFTER Procrustes:")
        for metric in ['rdm_correlation_after', 'rdm_crossnobis_after', 'decoding_accuracy_after']:
            values = [r[metric] for r in all_results.values() if not np.isnan(r[metric])]
            if len(values) > 0:
                print(f"  {metric}:")
                print(f"    Mean:   {np.mean(values):.4f}")
                print(f"    Median: {np.median(values):.4f}")
                print(f"    Min:    {np.min(values):.4f}")
                print(f"    Max:    {np.max(values):.4f}")
        print()

        # Improvements
        print("Procrustes IMPROVEMENTS:")
        for metric in ['rdm_correlation_improvement', 'rdm_crossnobis_improvement', 'decoding_improvement']:
            values = [r[metric] for r in all_results.values() if not np.isnan(r[metric])]
            if len(values) > 0:
                print(f"  {metric}:")
                print(f"    Mean:   {np.mean(values):+.4f}")
                print(f"    Median: {np.median(values):+.4f}")
                print(f"    Positive: {sum(v > 0 for v in values)}/{len(values)}")
        print()

        # Other metrics
        print("Other Metrics:")
        for metric in ['procrustes_disparity', 'shrinkage']:
            values = [r[metric] for r in all_results.values() if not np.isnan(r[metric])]
            if len(values) > 0:
                print(f"  {metric}:")
                print(f"    Mean:   {np.mean(values):.4f}")
                print(f"    Median: {np.median(values):.4f}")
        print()

        # Best conditions (using AFTER metrics)
        print("Best Conditions (AFTER Procrustes):")
        for metric in ['rdm_correlation_after', 'rdm_crossnobis_after', 'decoding_accuracy_after']:
            values = [(name, r[metric]) for name, r in all_results.items()
                      if not np.isnan(r[metric])]
            if len(values) > 0:
                best_name, best_val = max(values, key=lambda x: x[1])
                print(f"  {metric}: {best_name} ({best_val:.4f})")

        # Lowest disparity
        values = [(name, r['procrustes_disparity']) for name, r in all_results.items()
                  if not np.isnan(r['procrustes_disparity'])]
        if len(values) > 0:
            best_name, best_val = min(values, key=lambda x: x[1])
            print(f"  procrustes_disparity (lowest): {best_name} ({best_val:.4f})")

        # Best improvement
        print()
        print("Best Improvements:")
        for metric in ['rdm_correlation_improvement', 'rdm_crossnobis_improvement', 'decoding_improvement']:
            values = [(name, r[metric]) for name, r in all_results.items()
                      if not np.isnan(r[metric])]
            if len(values) > 0:
                best_name, best_val = max(values, key=lambda x: x[1])
                print(f"  {metric}: {best_name} ({best_val:+.4f})")

        print()


if __name__ == '__main__':
    main()
