#!/usr/bin/env python3
"""
Utility Functions for Model Comparison

Shared helper functions used across all scripts.
"""

import numpy as np
from pathlib import Path


# ============================================================================
# Constants
# ============================================================================

HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']

HUE_ANGLES = [i * 45 for i in range(8)]  # 0, 45, 90, ..., 315


# ============================================================================
# Circular Math
# ============================================================================

def circular_diff_deg(hue1, hue2):
    """
    Compute circular difference in degrees

    Args:
        hue1, hue2: Hue angles in degrees (0-360)

    Returns:
        diff: Difference in degrees, range [-180, 180]
    """
    diff = hue1 - hue2
    diff = np.mod(diff + 180, 360) - 180
    return diff


def labels_to_hue(labels):
    """
    Convert labels (0-7) to hue angles (0, 45, ..., 315)

    Args:
        labels: Array of color labels (0-7)

    Returns:
        hues: Array of hue angles in degrees
    """
    return np.array([HUE_ANGLES[int(l)] for l in labels])


def hue_to_labels(hue_angles):
    """
    Convert hue angles to nearest labels (0-7)

    Args:
        hue_angles: Array of hue angles in degrees

    Returns:
        labels: Array of nearest color labels (0-7)
    """
    labels = []
    for hue in hue_angles:
        diffs = [abs(circular_diff_deg(hue, target_hue)) for target_hue in HUE_ANGLES]
        labels.append(np.argmin(diffs))
    return np.array(labels)


# ============================================================================
# Data Loading
# ============================================================================

def load_amplitudes(baseline_dir, subject, roi, alignment='raw'):
    """
    Load amplitudes from full_dataset_C010 structure

    Args:
        baseline_dir: Path to full_dataset_C010
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        alignment: 'raw' or 'procrustes'

    Returns:
        amplitudes: (n_runs=6, n_colors=8, n_voxels) array
    """
    subject_roi_dir = Path(baseline_dir) / f"sub-{subject}" / roi

    if alignment == 'raw':
        amp_path = subject_roi_dir / "amplitudes_raw.npy"
    elif alignment == 'procrustes':
        amp_path = subject_roi_dir / "amplitudes_procrustes.npy"
    else:
        raise ValueError(f"Unknown alignment: {alignment}. Use 'raw' or 'procrustes'")

    if not amp_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amp_path}")

    return np.load(amp_path)


# ============================================================================
# Statistics
# ============================================================================

def bootstrap_ci(data, n_bootstrap=1000, ci_percentiles=[2.5, 97.5]):
    """
    Compute bootstrap confidence interval

    Args:
        data: Array of values
        n_bootstrap: Number of bootstrap iterations
        ci_percentiles: Percentiles for CI (e.g., [2.5, 97.5] for 95% CI)

    Returns:
        mean: Mean of data
        ci_lower: Lower CI bound
        ci_upper: Upper CI bound
    """
    bootstrap_means = []

    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means = np.array(bootstrap_means)

    mean = np.mean(data)
    ci_lower = np.percentile(bootstrap_means, ci_percentiles[0])
    ci_upper = np.percentile(bootstrap_means, ci_percentiles[1])

    return mean, ci_lower, ci_upper


def spearman_brown_correction(r):
    """
    Spearman-Brown correction for split-half reliability

    Args:
        r: Split-half correlation

    Returns:
        r_corrected: Full-length reliability
    """
    if (1 + r) <= 0:
        return 0
    return 2 * r / (1 + r)


# ============================================================================
# Model Type Classification
# ============================================================================

def is_linear_model(model_name):
    """Check if model is linear"""
    linear_models = ['LDA', 'Ridge', 'ForwardEncoding']
    return model_name in linear_models


def is_nonlinear_model(model_name):
    """Check if model is non-linear"""
    nonlinear_models = ['KernelRidge', 'SVM', 'MLP']
    return model_name in nonlinear_models


def uses_labels(model_name):
    """Check if model uses discrete labels (vs continuous hue)"""
    label_models = ['LDA', 'SVM', 'MLP', 'ForwardEncoding']
    return model_name in label_models


# ============================================================================
# Chance Levels
# ============================================================================

def get_chance_level(metric='acc_exact'):
    """
    Get chance level for a given metric

    Args:
        metric: Metric name

    Returns:
        chance: Chance level (0-1 for accuracy, degrees for MAE)
    """
    chance_levels = {
        'acc_exact': 1/8,      # 12.5% (8 colors)
        'acc_45': 3/8,         # 37.5% (3 out of 8 within 45°)
        'acc_90': 5/8,         # 62.5% (5 out of 8 within 90°)
        'mae': 90,             # 90 degrees (random guess)
        'medae': 90
    }

    return chance_levels.get(metric, 0)


# ============================================================================
# Summary Statistics
# ============================================================================

def compute_summary_stats(values):
    """
    Compute comprehensive summary statistics

    Args:
        values: Array of values

    Returns:
        stats_dict: Dictionary with mean, std, median, range, etc.
    """
    values = np.array(values)

    return {
        'mean': float(np.mean(values)),
        'std': float(np.std(values)),
        'median': float(np.median(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'range': [float(np.min(values)), float(np.max(values))],
        'n': len(values)
    }


# ============================================================================
# Group Classification
# ============================================================================

def get_subject_group(subject):
    """
    Get group (HC or CVD) for a subject

    Args:
        subject: Subject ID (e.g., '01')

    Returns:
        group: 'HC' or 'CVD'
    """
    return 'HC' if subject in HC_SUBJECTS else 'CVD'


def filter_by_group(subjects, group):
    """
    Filter subjects by group

    Args:
        subjects: List of subject IDs
        group: 'HC' or 'CVD'

    Returns:
        filtered: List of subjects in that group
    """
    if group == 'HC':
        return [s for s in subjects if s in HC_SUBJECTS]
    elif group == 'CVD':
        return [s for s in subjects if s in CVD_SUBJECTS]
    else:
        return subjects


if __name__ == '__main__':
    # Test utilities
    print("Utility Functions Test")
    print("="*80)

    # Test circular math
    print("\nCircular Math:")
    print(f"  circular_diff_deg(10, 350) = {circular_diff_deg(10, 350)}°  (expected: 20°)")
    print(f"  circular_diff_deg(350, 10) = {circular_diff_deg(350, 10)}°  (expected: -20°)")

    # Test label/hue conversion
    print("\nLabel/Hue Conversion:")
    labels = np.array([0, 2, 4, 6])
    hues = labels_to_hue(labels)
    print(f"  labels_to_hue([0,2,4,6]) = {hues}")
    print(f"  hue_to_labels({hues}) = {hue_to_labels(hues)}")

    # Test chance levels
    print("\nChance Levels:")
    for metric in ['acc_exact', 'acc_45', 'acc_90', 'mae']:
        print(f"  {metric}: {get_chance_level(metric)}")

    # Test group classification
    print("\nGroup Classification:")
    print(f"  get_subject_group('01') = {get_subject_group('01')}")
    print(f"  get_subject_group('08') = {get_subject_group('08')}")

    print("\n" + "="*80)
