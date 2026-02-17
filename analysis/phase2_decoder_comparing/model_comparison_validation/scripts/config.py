#!/usr/bin/env python3
"""
Configuration for Model Comparison

Central configuration file for all model comparison scripts.
"""

from pathlib import Path

# ============================================================================
# Paths
# ============================================================================

# Local paths (for development and analysis)
LOCAL_BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
LOCAL_BASELINE_DIR = LOCAL_BASE / "analysis/phase1_preprocess_decoding/results/full_dataset_C010"
LOCAL_OUTPUT_DIR = LOCAL_BASE / "analysis/phase2_decoder_comparing/model_comparison_validation/results"

# Server paths (for SLURM jobs)
SERVER_BASE = Path("/scratch/connectome/haba6030/colorBlind")
SERVER_BASELINE_DIR = SERVER_BASE / "derivatives/phase1_results/full_dataset_C010"
SERVER_OUTPUT_DIR = SERVER_BASE / "analysis/phase2_decoder_comparing/model_comparison_validation/results"

# ============================================================================
# Subjects and ROIs
# ============================================================================

HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]   # sub-01 ~ sub-07 (7 subjects)
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]  # sub-08 ~ sub-10 (3 subjects)
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']

# ============================================================================
# Experimental Parameters
# ============================================================================

N_RUNS = 6
N_COLORS = 8
COLOR_LABELS = list(range(8))  # 0-7

# Color names (for reference)
COLOR_NAMES = {
    0: 'red',
    1: 'orange',
    2: 'yellow',
    3: 'green',
    4: 'cyan',
    5: 'blue',
    6: 'purple',
    7: 'magenta'
}

# Hue angles in degrees (0-360)
HUE_ANGLES = [i * 45 for i in range(8)]  # [0, 45, 90, 135, 180, 225, 270, 315]

# ============================================================================
# Model Hyperparameters
# ============================================================================

# LDA (Linear Discriminant Analysis)
LDA_PARAMS = {
    'solver': ['svd', 'lsqr', 'eigen'],
    'shrinkage': [None, 'auto', 0.1, 0.5, 0.9]  # Only for lsqr/eigen
}

# Ridge Regression
RIDGE_PARAMS = {
    'alpha': [0.01, 0.1, 1, 10, 100]
}

# Kernel Ridge Regression
KERNEL_RIDGE_PARAMS = {
    'alpha': [0.01, 0.1, 1, 10],
    'gamma': [0.001, 0.01, 0.1, 1],  # RBF kernel width
    'kernel': ['rbf']
}

# SVM (Support Vector Machine)
SVM_PARAMS = {
    'C': [0.1, 1, 10, 100],
    'gamma': [0.001, 0.01, 0.1, 1],
    'kernel': ['rbf'],
    'probability': [True]  # For calibration
}

# MLP (Multi-Layer Perceptron)
MLP_PARAMS = {
    'hidden_layer_sizes': [(32,), (64,), (64, 32)],
    'alpha': [0.001, 0.01, 0.1],  # L2 regularization
    'early_stopping': [True],
    'validation_fraction': [0.2],
    'max_iter': [500]
}

# Forward Encoding (6-channel)
# No hyperparameters (analytical solution)
FORWARD_ENCODING_N_CHANNELS = 6

# ============================================================================
# Validation Parameters
# ============================================================================

# Permutation test
N_PERMUTATIONS = 1000
PERMUTATION_ALPHA = 0.05

# Bootstrap
N_BOOTSTRAP = 1000
BOOTSTRAP_CI = [2.5, 97.5]  # 95% CI

# Split-half reliability
N_SPLIT_HALF_ITERATIONS = 1000

# Cross-subject generalization
GENERALIZATION_CV = 'LOSO'  # Leave-One-Subject-Out

# ============================================================================
# Performance Metrics
# ============================================================================

# Classification metrics
ACCURACY_TYPES = ['exact', '45deg', '90deg']

# Exact: predicted == true (chance = 1/8 = 0.125)
# 45deg: predicted in [true-45, true, true+45] (chance ≈ 0.25)
# 90deg: predicted in [true-90, ..., true+90] (chance ≈ 0.375)

# Reconstruction metrics
RECONSTRUCTION_METRICS = ['MAE', 'MedAE', 'correlation']

# MAE: Mean Absolute Error (circular, in degrees)
# MedAE: Median Absolute Error (circular, in degrees)
# correlation: Pearson r between predicted and true hues

# ============================================================================
# Visualization Settings
# ============================================================================

# Figure sizes
FIG_SIZE_SINGLE = (8, 6)
FIG_SIZE_MULTI = (18, 12)
FIG_SIZE_COMPREHENSIVE = (20, 14)

# DPI
DPI = 300

# Colors for groups
COLOR_HC = 'steelblue'
COLOR_CVD = 'coral'

# Colors for alignment
COLOR_BEFORE = 'lightcoral'
COLOR_AFTER = 'skyblue'

# Colors for model types
COLOR_LINEAR = 'steelblue'
COLOR_NONLINEAR = 'darkorange'

# Model colors (individual)
MODEL_COLORS = {
    'LDA': '#1f77b4',
    'Ridge': '#ff7f0e',
    'KernelRidge': '#2ca02c',
    'SVM': '#d62728',
    'MLP': '#9467bd',
    'ForwardEncoding': '#8c564b'
}

# Matplotlib style
MATPLOTLIB_STYLE = 'seaborn-v0_8-whitegrid'

# Font sizes
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 12
FONT_SIZE_TICK = 10
FONT_SIZE_LEGEND = 10

# ============================================================================
# Utility Functions
# ============================================================================

def get_baseline_dir(use_server=False):
    """Get baseline directory based on environment"""
    return SERVER_BASELINE_DIR if use_server else LOCAL_BASELINE_DIR


def get_output_dir(use_server=False):
    """Get output directory based on environment"""
    return SERVER_OUTPUT_DIR if use_server else LOCAL_OUTPUT_DIR


def get_subject_roi_path(baseline_dir, subject, roi):
    """
    Get path to subject-ROI data

    Args:
        baseline_dir: Base directory (full_dataset_C010)
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')

    Returns:
        Path object
    """
    return Path(baseline_dir) / f"sub-{subject}" / roi


def load_amplitudes(baseline_dir, subject, roi, alignment='raw'):
    """
    Load amplitudes from baseline directory

    Args:
        baseline_dir: Base directory (full_dataset_C010)
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        alignment: 'raw' or 'procrustes'

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels) array
    """
    import numpy as np

    subject_roi_dir = get_subject_roi_path(baseline_dir, subject, roi)

    if alignment == 'raw':
        amp_path = subject_roi_dir / "amplitudes_raw.npy"
    elif alignment == 'procrustes':
        amp_path = subject_roi_dir / "amplitudes_procrustes.npy"
    else:
        raise ValueError(f"Unknown alignment: {alignment}. Use 'raw' or 'procrustes'")

    if not amp_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amp_path}")

    return np.load(amp_path)


if __name__ == "__main__":
    # Test configuration
    print("Configuration Test")
    print("=" * 80)
    print(f"Local baseline: {LOCAL_BASELINE_DIR}")
    print(f"Local output: {LOCAL_OUTPUT_DIR}")
    print(f"HC subjects: {HC_SUBJECTS}")
    print(f"CVD subjects: {CVD_SUBJECTS}")
    print(f"ROIs: {ROIS}")
    print(f"N runs: {N_RUNS}, N colors: {N_COLORS}")
    print("=" * 80)
