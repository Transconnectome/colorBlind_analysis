#!/usr/bin/env python3
"""
CVD Cross-Decoding Using Existing SRM-Aligned Data (RT-1)

Tests whether individual CVD subjects can be decoded in the HC common space.
Uses pre-computed SRM-aligned amplitudes (no BrainIAK or mpirun needed).

Logic:
1. Load existing SRM-aligned data (dict: {subject_id: (8, k)})
2. HC baseline (LOSO): Train LDA on 6 HC, test on 1 HC
3. CVD test: Train LDA on all 7 HC, test on each CVD individually
4. Permutation test per CVD subject (1000 iterations)

Usage:
    python run_cvd_cross_decoding.py \
        --srm_dir /path/to/combined_with_aligned \
        --output_dir /path/to/results/cvd_cross_decoding \
        --alignment procrustes \
        --n_permutations 1000
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
from datetime import datetime

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import accuracy_score

# ============================================================================
# Configuration
# ============================================================================

HC_SUBJECTS = [f"sub-{i:02d}" for i in range(1, 8)]   # sub-01 ~ sub-07
CVD_SUBJECTS = [f"sub-{i:02d}" for i in range(8, 11)]  # sub-08 ~ sub-10

ROIS = ['V1', 'V2', 'V3', 'V4']

# SRM K values per ROI (from validation)
SRM_K = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 4}

N_COLORS = 8


# ============================================================================
# Data Loading
# ============================================================================

def load_srm_aligned(srm_dir, roi, alignment='procrustes'):
    """
    Load SRM-aligned amplitudes from combined_with_aligned directory.

    Args:
        srm_dir: Path to combined_with_aligned directory
        roi: ROI name (e.g., 'V1')
        alignment: 'procrustes' or 'raw'

    Returns:
        data: dict {subject_id: (8, k)} run-averaged betas in SRM space
    """
    filename = f"{roi}_{alignment}_aligned_amplitudes.npy"
    filepath = Path(srm_dir) / filename

    if not filepath.exists():
        raise FileNotFoundError(f"SRM aligned data not found: {filepath}")

    data = np.load(filepath, allow_pickle=True).item()
    return data


# ============================================================================
# Cross-Decoding
# ============================================================================

def hc_loso_decoding(data, hc_subjects):
    """
    HC baseline: Leave-One-Subject-Out cross-validation.

    Args:
        data: dict {subject_id: (8, k)}
        hc_subjects: list of HC subject IDs

    Returns:
        per_subject_acc: dict {subject_id: accuracy}
    """
    labels = np.arange(N_COLORS)
    per_subject_acc = {}

    for test_idx, test_subj in enumerate(hc_subjects):
        train_subjects = [s for s in hc_subjects if s != test_subj]

        # Pool training data
        X_train = np.vstack([data[s] for s in train_subjects])
        y_train = np.tile(labels, len(train_subjects))

        # Test data
        X_test = data[test_subj]
        y_test = labels

        # LDA
        lda = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
        lda.fit(X_train, y_train)
        y_pred = lda.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        per_subject_acc[test_subj] = acc

    return per_subject_acc


def cvd_cross_decoding(data, hc_subjects, cvd_subjects):
    """
    Train LDA on all HC, test on each CVD individually.

    Args:
        data: dict {subject_id: (8, k)}
        hc_subjects: list of HC subject IDs
        cvd_subjects: list of CVD subject IDs

    Returns:
        per_subject_acc: dict {subject_id: accuracy}
    """
    labels = np.arange(N_COLORS)

    # Train on all HC
    X_train = np.vstack([data[s] for s in hc_subjects])
    y_train = np.tile(labels, len(hc_subjects))

    lda = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
    lda.fit(X_train, y_train)

    per_subject_acc = {}
    for cvd_subj in cvd_subjects:
        X_test = data[cvd_subj]
        y_test = labels

        y_pred = lda.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        per_subject_acc[cvd_subj] = acc

    return per_subject_acc


def permutation_test_cvd(data, hc_subjects, cvd_subject, n_permutations=1000):
    """
    Permutation test for a single CVD subject.

    Shuffles training labels to build null distribution.

    Args:
        data: dict {subject_id: (8, k)}
        hc_subjects: list of HC subject IDs
        cvd_subject: Single CVD subject ID
        n_permutations: Number of permutations

    Returns:
        observed_acc: Observed accuracy
        p_value: Permutation p-value
        null_mean: Mean of null distribution
        null_std: Std of null distribution
    """
    labels = np.arange(N_COLORS)

    # Train on all HC
    X_train = np.vstack([data[s] for s in hc_subjects])
    y_train = np.tile(labels, len(hc_subjects))

    # Observed
    lda = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
    lda.fit(X_train, y_train)
    y_pred = lda.predict(data[cvd_subject])
    observed_acc = float(accuracy_score(labels, y_pred))

    # Null distribution
    null_accs = []
    rng = np.random.RandomState(42)

    for _ in range(n_permutations):
        y_perm = rng.permutation(y_train)

        lda_perm = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
        lda_perm.fit(X_train, y_perm)
        y_pred_perm = lda_perm.predict(data[cvd_subject])
        null_acc = float(accuracy_score(labels, y_pred_perm))
        null_accs.append(null_acc)

    null_accs = np.array(null_accs)
    p_value = float((null_accs >= observed_acc).sum() / n_permutations)

    return observed_acc, p_value, float(np.mean(null_accs)), float(np.std(null_accs))


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CVD cross-decoding using existing SRM-aligned data (RT-1)"
    )
    parser.add_argument('--srm_dir', type=str, required=True,
                       help='Path to combined_with_aligned directory')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory')
    parser.add_argument('--alignment', type=str, default='procrustes',
                       choices=['procrustes', 'raw'],
                       help='Which SRM alignment to use')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'],
                       help='ROI names')
    parser.add_argument('--n_permutations', type=int, default=1000,
                       help='Number of permutations per CVD subject')

    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"CVD Cross-Decoding (RT-1)")
    print(f"{'='*80}")
    print(f"SRM dir: {args.srm_dir}")
    print(f"Alignment: {args.alignment}")
    print(f"ROIs: {args.rois}")
    print(f"Permutations: {args.n_permutations}")
    print(f"Output: {output_path}")
    print(f"{'='*80}\n")

    all_results = {}

    for roi in args.rois:
        print(f"\n--- ROI: {roi} ---")

        try:
            data = load_srm_aligned(args.srm_dir, roi, args.alignment)
        except FileNotFoundError as e:
            print(f"  SKIP: {e}")
            continue

        k_srm = data[HC_SUBJECTS[0]].shape[1] if HC_SUBJECTS[0] in data else 0
        print(f"  SRM k={k_srm}, loaded {len(data)} subjects")

        # Check all required subjects are present
        missing = [s for s in HC_SUBJECTS + CVD_SUBJECTS if s not in data]
        if missing:
            print(f"  WARNING: Missing subjects: {missing}")

        # Filter to available subjects
        hc_avail = [s for s in HC_SUBJECTS if s in data]
        cvd_avail = [s for s in CVD_SUBJECTS if s in data]

        if len(hc_avail) < 3:
            print(f"  SKIP: Not enough HC subjects ({len(hc_avail)})")
            continue

        # HC LOSO baseline
        print(f"  HC LOSO ({len(hc_avail)} subjects)...")
        hc_loso = hc_loso_decoding(data, hc_avail)
        hc_mean = np.mean(list(hc_loso.values()))
        print(f"    Mean acc: {hc_mean:.3f}")
        for s, a in hc_loso.items():
            print(f"    {s}: {a:.3f}")

        # CVD cross-decoding
        print(f"  CVD cross-decoding ({len(cvd_avail)} subjects)...")
        cvd_cross = cvd_cross_decoding(data, hc_avail, cvd_avail)
        for s, a in cvd_cross.items():
            print(f"    {s}: {a:.3f}")

        # Permutation tests for CVD
        print(f"  Permutation tests ({args.n_permutations} perms)...")
        cvd_perm = {}
        for cvd_subj in cvd_avail:
            obs_acc, p_val, null_mean, null_std = permutation_test_cvd(
                data, hc_avail, cvd_subj, args.n_permutations)
            cvd_perm[cvd_subj] = {
                'observed_acc': obs_acc,
                'p_value': p_val,
                'null_mean': null_mean,
                'null_std': null_std
            }
            sig = "*" if p_val < 0.05 else ""
            print(f"    {cvd_subj}: acc={obs_acc:.3f}, p={p_val:.4f} {sig}")

        all_results[roi] = {
            'k_srm': int(k_srm),
            'hc_loso': hc_loso,
            'hc_mean': float(hc_mean),
            'cvd_cross': cvd_cross,
            'cvd_perm': cvd_perm,
            'chance': float(1.0 / N_COLORS),
            'n_hc': len(hc_avail),
            'n_cvd': len(cvd_avail)
        }

    # Save results
    output_file = output_path / f'cvd_cross_decoding_{args.alignment}.json'
    results_data = {
        'alignment': args.alignment,
        'n_permutations': args.n_permutations,
        'results': all_results,
        'timestamp': datetime.now().isoformat()
    }

    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved: {output_file}")
    print(f"{'='*80}\n")

    # Summary table
    print("\nSUMMARY")
    print(f"{'ROI':<6} {'k':>3} {'HC mean':>8} {'CVD sub-08':>10} {'CVD sub-09':>10} {'CVD sub-10':>10}")
    print("-" * 55)
    for roi, res in all_results.items():
        row = f"{roi:<6} {res['k_srm']:>3} {res['hc_mean']:>8.3f}"
        for cvd_subj in CVD_SUBJECTS:
            if cvd_subj in res['cvd_cross']:
                acc = res['cvd_cross'][cvd_subj]
                p = res['cvd_perm'][cvd_subj]['p_value']
                sig = "*" if p < 0.05 else " "
                row += f" {acc:>8.3f}{sig}"
            else:
                row += f" {'N/A':>9}"
        print(row)
    print(f"\nChance = {1.0/N_COLORS:.3f} (1/{N_COLORS})")
    print("* = p < 0.05")


if __name__ == '__main__':
    main()
