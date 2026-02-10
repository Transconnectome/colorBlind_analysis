#!/usr/bin/env python3
"""
Validation Tests for Decoder Models

Implements 4 critical validation tests:
1. Permutation Test (Section 6.2) - Label shuffle
2. Bootstrap CI (Section 6.4) - Confidence intervals
3. Test-Retest Reliability (Section 6.3) - Split-half correlation
4. Cross-Subject Generalization (Section 6.5) - HC→HC vs HC→CVD

Usage:
    python run_validation_tests.py \
        --baseline_dir /path/to/full_dataset_C010 \
        --performance_dir /path/to/results/{timestamp} \
        --output_dir /path/to/results/{timestamp}
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import warnings
from datetime import datetime
from scipy import stats

# Add project root
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root / "analysis"))

warnings.filterwarnings('ignore')

# ============================================================================
# Configuration
# ============================================================================

HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']

N_PERMUTATIONS = 1000
N_BOOTSTRAP = 1000
N_SPLIT_HALF = 1000

HUE_ANGLES = [i * 45 for i in range(8)]  # 0, 45, ..., 315


# ============================================================================
# Helper Functions
# ============================================================================

def load_amplitudes(baseline_dir, subject, roi, alignment='raw'):
    """Load amplitudes from full_dataset_C010"""
    subject_roi_dir = Path(baseline_dir) / f"sub-{subject}" / roi

    if alignment == 'raw':
        amp_path = subject_roi_dir / "amplitudes_raw.npy"
    elif alignment == 'procrustes':
        amp_path = subject_roi_dir / "amplitudes_procrustes.npy"
    else:
        raise ValueError(f"Unknown alignment: {alignment}")

    if not amp_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amp_path}")

    return np.load(amp_path)


def circular_diff_deg(hue1, hue2):
    """Compute circular difference in degrees"""
    diff = hue1 - hue2
    diff = np.mod(diff + 180, 360) - 180
    return diff


def labels_to_hue(labels):
    """Convert labels (0-7) to hue angles"""
    return np.array([HUE_ANGLES[int(l)] for l in labels])


def hue_to_labels(hue_angles):
    """Convert hue angles to nearest labels"""
    labels = []
    for hue in hue_angles:
        diffs = [abs(circular_diff_deg(hue, target_hue)) for target_hue in HUE_ANGLES]
        labels.append(np.argmin(diffs))
    return np.array(labels)


# ============================================================================
# 1. Permutation Test
# ============================================================================

def permutation_test_single(amplitudes, model_class, model_name, observed_acc,
                            n_permutations=1000):
    """
    Permutation test for a single subject-ROI-model

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        model_class: Decoder class
        model_name: Model name
        observed_acc: Observed accuracy (from LORO CV)
        n_permutations: Number of permutations

    Returns:
        results: Dict with null distribution, p-value, z-score
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    labels = np.arange(n_colors)

    null_distribution = []

    # Determine if model uses labels or hue
    uses_labels = model_name in ['LDA', 'SVM', 'MLP', 'ForwardEncoding']

    for iteration in range(n_permutations):
        # Shuffle labels WITHIN each run (preserve temporal structure)
        shuffled_amplitudes = np.zeros_like(amplitudes)

        for run in range(n_runs):
            shuffled_labels = np.random.permutation(labels)
            shuffled_amplitudes[run] = amplitudes[run][shuffled_labels]

        # LORO CV with shuffled data
        fold_accs = []

        for test_run in range(n_runs):
            train_runs = [r for r in range(n_runs) if r != test_run]
            X_train = shuffled_amplitudes[train_runs].reshape(-1, n_voxels)
            X_test = shuffled_amplitudes[test_run]

            if uses_labels:
                y_train = np.tile(labels, len(train_runs))
                y_test = labels
            else:
                hue_angles = labels_to_hue(labels)
                y_train = np.tile(hue_angles, len(train_runs))
                y_test = hue_angles

            # Train and predict
            model = model_class()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            # Compute accuracy
            if uses_labels:
                acc = np.mean(y_test == y_pred)
            else:
                y_pred_labels = hue_to_labels(y_pred)
                y_test_labels = hue_to_labels(y_test)
                acc = np.mean(y_test_labels == y_pred_labels)

            fold_accs.append(acc)

        null_acc = np.mean(fold_accs)
        null_distribution.append(null_acc)

    null_distribution = np.array(null_distribution)

    # Compute p-value
    p_value = (null_distribution >= observed_acc).sum() / n_permutations

    # Compute z-score
    null_mean = np.mean(null_distribution)
    null_std = np.std(null_distribution)
    z_score = (observed_acc - null_mean) / null_std if null_std > 0 else 0

    results = {
        'observed_acc': float(observed_acc),
        'null_mean': float(null_mean),
        'null_std': float(null_std),
        'null_distribution': null_distribution.tolist(),
        'p_value': float(p_value),
        'z_score': float(z_score),
        'n_permutations': n_permutations
    }

    return results


def run_permutation_test(baseline_dir, performance_dir, alignment='procrustes'):
    """
    Run permutation test for all subjects-ROIs-models

    Args:
        baseline_dir: Path to full_dataset_C010
        performance_dir: Path to performance results
        alignment: Which alignment to test

    Returns:
        all_results: Dict with permutation test results
    """
    print(f"\n{'='*80}")
    print(f"Permutation Test (Alignment: {alignment})")
    print(f"{'='*80}\n")

    # Load performance data to get observed accuracies
    performance_files = list(Path(performance_dir).glob("sub-*_performance_raw.json"))

    if len(performance_files) == 0:
        raise FileNotFoundError(f"No performance files found in {performance_dir}")

    all_results = {}

    for perf_file in performance_files:
        with open(perf_file, 'r') as f:
            perf_data = json.load(f)

        subject = perf_data['subject']
        models = perf_data['models']
        rois = perf_data['rois']

        print(f"Subject: sub-{subject}")

        all_results[subject] = {}

        for roi in rois:
            print(f"  ROI: {roi}")

            # Load amplitudes
            try:
                amplitudes = load_amplitudes(baseline_dir, subject, roi, alignment)
            except FileNotFoundError:
                print(f"    ERROR: Amplitudes not found")
                continue

            all_results[subject][roi] = {}

            for model_name in models:
                print(f"    Model: {model_name}...", end=' ', flush=True)

                # Get observed accuracy
                try:
                    fold_results = perf_data['results'][alignment][roi][model_name]
                    observed_acc = np.mean([f['acc_exact'] for f in fold_results])
                except KeyError:
                    print("SKIP (no performance data)")
                    continue

                # Import model class
                from run_model_comparison import (
                    LDADecoder, RidgeDecoder, KernelRidgeDecoder,
                    SVMDecoder, MLPDecoder, ForwardEncodingDecoder
                )

                model_map = {
                    'LDA': LDADecoder,
                    'Ridge': RidgeDecoder,
                    'KernelRidge': KernelRidgeDecoder,
                    'SVM': SVMDecoder,
                    'MLP': MLPDecoder,
                    'ForwardEncoding': ForwardEncodingDecoder
                }

                if model_name not in model_map:
                    print("SKIP (unknown model)")
                    continue

                model_class = model_map[model_name]

                # Run permutation test
                try:
                    results = permutation_test_single(
                        amplitudes,
                        model_class,
                        model_name,
                        observed_acc,
                        n_permutations=N_PERMUTATIONS
                    )

                    all_results[subject][roi][model_name] = results

                    print(f"p={results['p_value']:.4f}, z={results['z_score']:.2f}")

                except Exception as e:
                    print(f"ERROR: {e}")
                    continue

    return all_results


# ============================================================================
# 2. Bootstrap Confidence Intervals
# ============================================================================

def bootstrap_ci_group(performance_data, alignment='procrustes', n_bootstrap=1000):
    """
    Bootstrap CI for group means (subject-level resampling)

    Args:
        performance_data: List of performance dicts
        alignment: Which alignment
        n_bootstrap: Number of bootstrap iterations

    Returns:
        ci_results: Dict with mean, CI_lower, CI_upper per model
    """
    print(f"\n{'='*80}")
    print(f"Bootstrap CI - Group Level (Alignment: {alignment})")
    print(f"{'='*80}\n")

    # Collect data per model
    model_data = {}  # model -> list of (subject, roi, accuracies)

    for perf_dict in performance_data:
        subject = perf_dict['subject']

        for roi in perf_dict['rois']:
            for model in perf_dict['models']:
                try:
                    fold_results = perf_dict['results'][alignment][roi][model]
                    accs = [f['acc_exact'] for f in fold_results]

                    if model not in model_data:
                        model_data[model] = []

                    model_data[model].append({
                        'subject': subject,
                        'roi': roi,
                        'accuracies': accs,
                        'mean_acc': np.mean(accs)
                    })

                except KeyError:
                    continue

    # Bootstrap for each model
    ci_results = {}

    for model, data_list in model_data.items():
        print(f"Model: {model}")

        # Bootstrap: resample subject-ROI pairs
        bootstrap_means = []

        for iteration in range(n_bootstrap):
            # Resample with replacement
            sampled_indices = np.random.choice(len(data_list), size=len(data_list), replace=True)
            sampled_data = [data_list[i] for i in sampled_indices]

            # Compute mean
            mean_acc = np.mean([d['mean_acc'] for d in sampled_data])
            bootstrap_means.append(mean_acc)

        bootstrap_means = np.array(bootstrap_means)

        # Compute CI
        ci_lower = np.percentile(bootstrap_means, 2.5)
        ci_upper = np.percentile(bootstrap_means, 97.5)
        mean_acc = np.mean([d['mean_acc'] for d in data_list])

        ci_results[model] = {
            'mean': float(mean_acc),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'bootstrap_distribution': bootstrap_means.tolist()
        }

        print(f"  Mean: {mean_acc:.3f}, 95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

    return ci_results


# ============================================================================
# 3. Test-Retest Reliability
# ============================================================================

def split_half_reliability(performance_data, alignment='procrustes', n_iterations=1000):
    """
    Split-half reliability with Spearman-Brown correction

    Args:
        performance_data: List of performance dicts
        alignment: Which alignment
        n_iterations: Number of split-half iterations

    Returns:
        reliability_results: Dict with reliability per model
    """
    print(f"\n{'='*80}")
    print(f"Split-Half Reliability (Alignment: {alignment})")
    print(f"{'='*80}\n")

    # Collect fold-wise accuracies per model
    model_data = {}  # model -> list of (subject, roi, [6 fold accuracies])

    for perf_dict in performance_data:
        subject = perf_dict['subject']

        for roi in perf_dict['rois']:
            for model in perf_dict['models']:
                try:
                    fold_results = perf_dict['results'][alignment][roi][model]
                    fold_accs = [f['acc_exact'] for f in fold_results]

                    if len(fold_accs) != 6:
                        continue  # Skip if not 6 folds

                    if model not in model_data:
                        model_data[model] = []

                    model_data[model].append({
                        'subject': subject,
                        'roi': roi,
                        'fold_accuracies': fold_accs
                    })

                except KeyError:
                    continue

    # Compute split-half reliability for each model
    reliability_results = {}

    for model, data_list in model_data.items():
        print(f"Model: {model}")

        reliability_estimates = []

        for iteration in range(n_iterations):
            # For each subject-ROI, compute split-half
            scores_A = []
            scores_B = []

            for data in data_list:
                fold_accs = np.array(data['fold_accuracies'])

                # Random split into two halves
                indices = np.random.permutation(6)
                half_A = indices[:3]
                half_B = indices[3:]

                score_A = np.mean(fold_accs[half_A])
                score_B = np.mean(fold_accs[half_B])

                scores_A.append(score_A)
                scores_B.append(score_B)

            # Correlation across subjects
            if len(scores_A) > 1:
                r, _ = stats.spearmanr(scores_A, scores_B)

                # Spearman-Brown correction
                r_corrected = 2 * r / (1 + r) if (1 + r) > 0 else 0

                reliability_estimates.append(r_corrected)

        reliability_estimates = np.array(reliability_estimates)

        # Compute mean and CI
        mean_reliability = np.mean(reliability_estimates)
        ci_lower = np.percentile(reliability_estimates, 2.5)
        ci_upper = np.percentile(reliability_estimates, 97.5)

        reliability_results[model] = {
            'mean_reliability': float(mean_reliability),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'reliability_distribution': reliability_estimates.tolist()
        }

        print(f"  Reliability: {mean_reliability:.3f}, 95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

    return reliability_results


# ============================================================================
# 4. Cross-Subject Generalization
# ============================================================================

def cross_subject_generalization(baseline_dir, alignment='procrustes'):
    """
    Test cross-subject generalization: HC→HC vs HC→CVD

    Args:
        baseline_dir: Path to full_dataset_C010
        alignment: Which alignment

    Returns:
        generalization_results: Dict with HC→HC and HC→CVD accuracies
    """
    print(f"\n{'='*80}")
    print(f"Cross-Subject Generalization (Alignment: {alignment})")
    print(f"{'='*80}\n")

    from run_model_comparison import (
        LDADecoder, RidgeDecoder, KernelRidgeDecoder,
        SVMDecoder, MLPDecoder, ForwardEncodingDecoder
    )

    model_map = {
        'LDA': LDADecoder,
        'Ridge': RidgeDecoder,
        'KernelRidge': KernelRidgeDecoder,
        'SVM': SVMDecoder,
        'MLP': MLPDecoder,
        'ForwardEncoding': ForwardEncodingDecoder
    }

    models = ['LDA', 'Ridge', 'SVM', 'MLP', 'ForwardEncoding']  # Skip KernelRidge (too slow)
    generalization_results = {}

    for model_name in models:
        print(f"\nModel: {model_name}")

        model_class = model_map[model_name]
        uses_labels = model_name in ['LDA', 'SVM', 'MLP', 'ForwardEncoding']

        # Test on each ROI
        hc_to_hc_scores = []
        hc_to_cvd_scores = []

        for roi in ROIS:
            print(f"  ROI: {roi}")

            # Load HC data
            hc_amplitudes = []
            for subject in HC_SUBJECTS:
                try:
                    amp = load_amplitudes(baseline_dir, subject, roi, alignment)
                    hc_amplitudes.append(amp)
                except FileNotFoundError:
                    continue

            if len(hc_amplitudes) < 3:
                print("    SKIP (not enough HC subjects)")
                continue

            # --- HC→HC (LOSO) ---
            for test_idx in range(len(hc_amplitudes)):
                train_indices = [i for i in range(len(hc_amplitudes)) if i != test_idx]

                # Pool training data
                X_train_list = []
                y_train_list = []

                labels = np.arange(8)
                hue_angles = labels_to_hue(labels)

                for train_idx in train_indices:
                    amp = hc_amplitudes[train_idx]
                    n_runs, n_colors, n_voxels = amp.shape

                    X_train_list.append(amp.reshape(-1, n_voxels))

                    if uses_labels:
                        y_train_list.append(np.tile(labels, n_runs))
                    else:
                        y_train_list.append(np.tile(hue_angles, n_runs))

                X_train = np.vstack(X_train_list)
                y_train = np.concatenate(y_train_list)

                # Test data
                test_amp = hc_amplitudes[test_idx]
                X_test = test_amp.reshape(-1, n_voxels)

                if uses_labels:
                    y_test = np.tile(labels, test_amp.shape[0])
                else:
                    y_test = np.tile(hue_angles, test_amp.shape[0])

                # Train and predict
                model = model_class()
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                # Compute accuracy
                if uses_labels:
                    acc = np.mean(y_test == y_pred)
                else:
                    y_pred_labels = hue_to_labels(y_pred)
                    y_test_labels = hue_to_labels(y_test)
                    acc = np.mean(y_test_labels == y_pred_labels)

                hc_to_hc_scores.append(acc)

            # --- HC→CVD ---
            # Train on all HC
            X_train_list = []
            y_train_list = []

            for amp in hc_amplitudes:
                n_runs, n_colors, n_voxels = amp.shape
                X_train_list.append(amp.reshape(-1, n_voxels))

                if uses_labels:
                    y_train_list.append(np.tile(labels, n_runs))
                else:
                    y_train_list.append(np.tile(hue_angles, n_runs))

            X_train = np.vstack(X_train_list)
            y_train = np.concatenate(y_train_list)

            model = model_class()
            model.fit(X_train, y_train)

            # Test on CVD subjects
            for cvd_subject in CVD_SUBJECTS:
                try:
                    cvd_amp = load_amplitudes(baseline_dir, cvd_subject, roi, alignment)

                    X_test = cvd_amp.reshape(-1, n_voxels)

                    if uses_labels:
                        y_test = np.tile(labels, cvd_amp.shape[0])
                    else:
                        y_test = np.tile(hue_angles, cvd_amp.shape[0])

                    y_pred = model.predict(X_test)

                    if uses_labels:
                        acc = np.mean(y_test == y_pred)
                    else:
                        y_pred_labels = hue_to_labels(y_pred)
                        y_test_labels = hue_to_labels(y_test)
                        acc = np.mean(y_test_labels == y_pred_labels)

                    hc_to_cvd_scores.append(acc)

                except FileNotFoundError:
                    continue

        # Compute statistics
        hc_to_hc_mean = np.mean(hc_to_hc_scores)
        hc_to_cvd_mean = np.mean(hc_to_cvd_scores)

        difference = hc_to_hc_mean - hc_to_cvd_mean

        # Bootstrap difference test
        n_bootstrap = 1000
        boot_diffs = []

        for _ in range(n_bootstrap):
            sampled_hc = np.random.choice(hc_to_hc_scores, size=len(hc_to_hc_scores), replace=True)
            sampled_cvd = np.random.choice(hc_to_cvd_scores, size=len(hc_to_cvd_scores), replace=True)

            boot_diff = np.mean(sampled_hc) - np.mean(sampled_cvd)
            boot_diffs.append(boot_diff)

        boot_diffs = np.array(boot_diffs)
        ci_diff_lower = np.percentile(boot_diffs, 2.5)
        ci_diff_upper = np.percentile(boot_diffs, 97.5)

        # Mann-Whitney U test
        u_stat, p_value = stats.mannwhitneyu(hc_to_hc_scores, hc_to_cvd_scores, alternative='two-sided')

        generalization_results[model_name] = {
            'hc_to_hc': {
                'scores': hc_to_hc_scores,
                'mean': float(hc_to_hc_mean),
                'std': float(np.std(hc_to_hc_scores))
            },
            'hc_to_cvd': {
                'scores': hc_to_cvd_scores,
                'mean': float(hc_to_cvd_mean),
                'std': float(np.std(hc_to_cvd_scores))
            },
            'difference': {
                'mean': float(difference),
                'ci_lower': float(ci_diff_lower),
                'ci_upper': float(ci_diff_upper),
                'mann_whitney_u': float(u_stat),
                'p_value': float(p_value)
            }
        }

        print(f"  HC→HC: {hc_to_hc_mean:.3f} ± {np.std(hc_to_hc_scores):.3f}")
        print(f"  HC→CVD: {hc_to_cvd_mean:.3f} ± {np.std(hc_to_cvd_scores):.3f}")
        print(f"  Difference: {difference:+.3f}, 95% CI: [{ci_diff_lower:+.3f}, {ci_diff_upper:+.3f}], p={p_value:.4f}")

    return generalization_results


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validation tests for decoder models"
    )
    parser.add_argument('--baseline_dir', type=str, required=True,
                       help='Path to full_dataset_C010')
    parser.add_argument('--performance_dir', type=str, required=True,
                       help='Directory with performance results')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory')
    parser.add_argument('--alignment', type=str, default='procrustes',
                       choices=['raw', 'procrustes'],
                       help='Which alignment to test')
    parser.add_argument('--tests', nargs='+',
                       default=['permutation', 'bootstrap', 'reliability', 'generalization'],
                       help='Which tests to run')

    args = parser.parse_args()

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"Validation Tests")
    print(f"{'='*80}")
    print(f"Baseline: {args.baseline_dir}")
    print(f"Performance: {args.performance_dir}")
    print(f"Output: {output_path}")
    print(f"Tests: {args.tests}")
    print(f"{'='*80}\n")

    # Load performance data
    performance_files = list(Path(args.performance_dir).glob("sub-*_performance_raw.json"))
    performance_data = []

    for perf_file in performance_files:
        with open(perf_file, 'r') as f:
            performance_data.append(json.load(f))

    print(f"Loaded {len(performance_data)} performance files")

    # Run tests
    results = {}

    if 'permutation' in args.tests:
        results['permutation_test'] = run_permutation_test(
            args.baseline_dir,
            args.performance_dir,
            args.alignment
        )

        # Save
        output_file = output_path / 'permutation_test.json'
        with open(output_file, 'w') as f:
            json.dump(results['permutation_test'], f, indent=2)
        print(f"\nSaved: {output_file}")

    if 'bootstrap' in args.tests:
        results['bootstrap_ci'] = bootstrap_ci_group(
            performance_data,
            args.alignment,
            N_BOOTSTRAP
        )

        # Save
        output_file = output_path / 'bootstrap_ci.json'
        with open(output_file, 'w') as f:
            json.dump(results['bootstrap_ci'], f, indent=2)
        print(f"\nSaved: {output_file}")

    if 'reliability' in args.tests:
        results['reliability'] = split_half_reliability(
            performance_data,
            args.alignment,
            N_SPLIT_HALF
        )

        # Save
        output_file = output_path / 'reliability.json'
        with open(output_file, 'w') as f:
            json.dump(results['reliability'], f, indent=2)
        print(f"\nSaved: {output_file}")

    if 'generalization' in args.tests:
        results['cross_subject_generalization'] = cross_subject_generalization(
            args.baseline_dir,
            args.alignment
        )

        # Save
        output_file = output_path / 'cross_subject_generalization.json'
        with open(output_file, 'w') as f:
            json.dump(results['cross_subject_generalization'], f, indent=2)
        print(f"\nSaved: {output_file}")

    print(f"\n{'='*80}")
    print(f"All validation tests complete!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
