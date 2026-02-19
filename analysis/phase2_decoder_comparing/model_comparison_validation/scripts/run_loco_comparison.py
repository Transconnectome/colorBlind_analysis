#!/usr/bin/env python3
"""
Leave-One-Color-Out (LOCO) Decoder Comparison

Tests whether models can interpolate a held-out color from the other 7.
This verifies that the model captures the relative structure between colors,
not just cross-run consistency (which LORO tests).

Protocol:
- For each held-out color (8 folds):
  - Train on 7 colors × 6 runs = 42 samples
  - Test on held-out color × 6 runs = 6 samples
  - Measure circular error between predicted and true hue

Permutation test:
- Shuffle 7 training color labels within each run (7! = 5040 per run)
- Tests whether the systematic hue-pattern relationship matters for interpolation

Usage:
    python run_loco_comparison.py \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir ./results \
        --subject 01 \
        --rois V1 V2 V3 V4 \
        --models LDA Ridge KernelRidge SVM MLP ForwardEncoding \
        --alignment procrustes \
        --permutations 0
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Import decoders from run_model_comparison
project_root = Path(__file__).resolve().parents[4]
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from run_model_comparison import (
    LDADecoder, RidgeDecoder, KernelRidgeDecoder,
    SVMDecoder, MLPDecoder, ForwardEncodingDecoder,
    load_amplitudes, labels_to_hue, hue_to_labels, circular_diff_deg,
    HUE_ANGLES
)
from utils import (get_model_architecture, get_model_defaults,
                   get_subject_group)

# Import basis function utility
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "utils_color_decoding",
    project_root / "analysis" / "utils" / "utils_color_decoding.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
create_basis_functions = _mod.create_basis_functions


# ============================================================================
# LOCO-adapted ForwardEncoding
# ============================================================================

class LOCOForwardEncodingDecoder:
    """
    ForwardEncoding adapted for LOCO: fits on N-1 training colors,
    predicts using all 8 color templates (can predict held-out color).
    """

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights = None
        self.predict_basis = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_voxels) — n_samples = n_runs × n_train_colors
            y_labels: (n_samples,) color labels (subset of 0-7)
        """
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_voxels = X.shape[1]

        # Group by label and average (respects shuffled labels in permutation test)
        mean_patterns = np.zeros((n_train_colors, n_voxels))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        # Build basis from training colors' hue angles
        basis_full = create_basis_functions(n_channels=self.n_channels)  # (360, n_channels)
        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        self.train_basis = basis_full[train_hues]  # (n_train_colors, n_channels)

        # For prediction: use ALL 360 hues for continuous reconstruction
        self.predict_basis = basis_full  # (360, n_channels) - CONTINUOUS RECONSTRUCTION!

        # Encoding weights: W = (C^T C + αI)^-1 C^T B
        C = self.train_basis
        B = mean_patterns

        if self.alpha > 0:
            self.weights = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            self.weights = np.linalg.pinv(C) @ B

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°) using 360 templates"""
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        channel_responses = self.weights @ X.T  # (n_channels, n_samples)

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            predicted_response = channel_responses[:, i]

            # Compare against ALL 360 hues (continuous reconstruction)
            # Use correlation as similarity metric (Brouwer & Heeger 2009)
            correlations = []
            for hue in range(360):
                template = self.predict_basis[hue]
                # Safe correlation calculation
                corr_matrix = np.corrcoef(predicted_response, template)
                if corr_matrix.shape == (2, 2):
                    corr = corr_matrix[0, 1]
                else:
                    # Fallback to dot product if correlation fails
                    corr = np.dot(predicted_response, template) / (
                        np.linalg.norm(predicted_response) * np.linalg.norm(template) + 1e-10
                    )
                correlations.append(corr)

            # Select best matching hue (0-359°)
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues  # Continuous hues (0-359°), not discrete labels!


# ============================================================================
# LOCO Cross-Validation
# ============================================================================

def loco_cv(amplitudes, model_class, model_name):
    """
    Leave-One-Color-Out cross-validation

    Args:
        amplitudes: (n_runs=6, n_colors=8, n_voxels)
        model_class: Decoder class
        model_name: Model name string

    Returns:
        fold_results: List of dicts, one per held-out color
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    all_labels = np.arange(n_colors)
    all_hues = np.array(HUE_ANGLES)

    uses_label = model_name in ['LDA', 'SVM', 'MLP', 'ForwardEncoding']
    fold_results = []

    for test_color in range(n_colors):
        train_colors = np.array([c for c in range(n_colors) if c != test_color])
        test_hue = all_hues[test_color]

        # Build training data: 6 runs × 7 colors
        X_train = amplitudes[:, train_colors, :].reshape(-1, n_voxels)  # (42, n_voxels)
        X_test = amplitudes[:, test_color, :]  # (6, n_voxels)

        if uses_label:
            y_train = np.tile(train_colors, n_runs)
        else:
            train_hues = all_hues[train_colors]
            y_train = np.tile(train_hues, n_runs)

        # Train model
        model = model_class()
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_test)  # (6,) — one prediction per run

        # Convert to hue for evaluation
        if uses_label:
            # ForwardEncoding now returns continuous hues (0-359°)
            # Other models (LDA, SVM, MLP) still return discrete labels
            if model_name == 'ForwardEncoding':
                pred_hues = y_pred  # Already continuous hues!
            else:
                pred_hues = labels_to_hue(y_pred)  # Discrete labels → 8 hues
        else:
            pred_hues = y_pred

        # Circular error per run
        errors = np.abs(circular_diff_deg(pred_hues, test_hue))

        # "Adjacent accuracy": is predicted hue within 45° of true?
        adjacent_correct = np.mean(errors <= 45)

        # Nearest color analysis: which training color was predicted?
        pred_labels = hue_to_labels(pred_hues)

        fold_results.append({
            'test_color': int(test_color),
            'test_hue': float(test_hue),
            'pred_hues': pred_hues.tolist(),
            'errors_per_run': errors.tolist(),
            'mae': float(np.mean(errors)),
            'medae': float(np.median(errors)),
            'adjacent_acc': float(adjacent_correct),
            'pred_labels': pred_labels.tolist()
        })

    return fold_results


# ============================================================================
# Permutation Test for LOCO
# ============================================================================

def loco_permutation_test(amplitudes, model_class, model_name,
                          observed_mae, n_permutations=1000):
    """
    Permutation test for LOCO: shuffle 7 training color labels within each run

    Args:
        amplitudes: (n_runs=6, n_colors=8, n_voxels)
        model_class: Decoder class
        model_name: Model name
        observed_mae: Observed MAE from real LOCO
        n_permutations: Number of permutations

    Returns:
        results: Dict with null distribution, p-value, z-score
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    all_hues = np.array(HUE_ANGLES)
    uses_label = model_name in ['LDA', 'SVM', 'MLP', 'ForwardEncoding']

    null_distribution = []

    for iteration in range(n_permutations):
        fold_errors = []

        for test_color in range(n_colors):
            train_colors = np.array([c for c in range(n_colors) if c != test_color])
            test_hue = all_hues[test_color]

            # Shuffle training color assignment within each run
            X_train_list = []
            y_train_list = []

            for run in range(n_runs):
                shuffled_order = np.random.permutation(len(train_colors))
                run_patterns = amplitudes[run, train_colors, :]  # (7, n_voxels)

                X_train_list.append(run_patterns)

                if uses_label:
                    # Assign shuffled labels
                    y_train_list.append(train_colors[shuffled_order])
                else:
                    train_hues = all_hues[train_colors]
                    y_train_list.append(train_hues[shuffled_order])

            X_train = np.vstack(X_train_list)  # (42, n_voxels)
            y_train = np.concatenate(y_train_list)

            X_test = amplitudes[:, test_color, :]  # (6, n_voxels)

            # Train and predict
            model = model_class()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            if uses_label:
                # ForwardEncoding now returns continuous hues
                if model_name == 'ForwardEncoding':
                    pred_hues = y_pred  # Already continuous hues!
                else:
                    pred_hues = labels_to_hue(y_pred)
            else:
                pred_hues = y_pred

            errors = np.abs(circular_diff_deg(pred_hues, test_hue))
            fold_errors.extend(errors.tolist())

        null_mae = np.mean(fold_errors)
        null_distribution.append(null_mae)

    null_distribution = np.array(null_distribution)

    # p-value: proportion of null ≤ observed (lower MAE = better)
    p_value = (null_distribution <= observed_mae).sum() / n_permutations

    # z-score (negative z = better than null)
    null_mean = np.mean(null_distribution)
    null_std = np.std(null_distribution)
    z_score = (observed_mae - null_mean) / null_std if null_std > 0 else 0

    return {
        'observed_mae': float(observed_mae),
        'null_mean': float(null_mean),
        'null_std': float(null_std),
        'p_value': float(p_value),
        'z_score': float(z_score),
        'n_permutations': n_permutations
    }


# ============================================================================
# Main
# ============================================================================

def run_single_subject_roi(baseline_dir, subject, roi, alignment, models,
                           n_permutations=0):
    """Run LOCO for a single subject-ROI"""
    print(f"\n{'='*60}")
    print(f"LOCO: sub-{subject} | {roi} | {alignment}")
    print(f"{'='*60}")

    try:
        amplitudes = load_amplitudes(baseline_dir, subject, roi, alignment)
        print(f"Loaded: {amplitudes.shape}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return None

    model_map = {
        'LDA': LDADecoder,
        'Ridge': RidgeDecoder,
        'KernelRidge': KernelRidgeDecoder,
        'SVM': SVMDecoder,
        'MLP': MLPDecoder,
        'ForwardEncoding': LOCOForwardEncodingDecoder
    }

    results = {}

    for model_name in models:
        if model_name not in model_map:
            continue

        print(f"\n--- {model_name} ---")
        model_class = model_map[model_name]

        try:
            # Run LOCO
            fold_results = loco_cv(amplitudes, model_class, model_name)
            overall_mae = np.mean([f['mae'] for f in fold_results])
            overall_adj_acc = np.mean([f['adjacent_acc'] for f in fold_results])

            print(f"  MAE: {overall_mae:.1f}°  Adjacent acc: {overall_adj_acc:.3f}")

            result_entry = {
                'fold_results': fold_results,
                'overall_mae': float(overall_mae),
                'overall_adjacent_acc': float(overall_adj_acc)
            }

            # Permutation test (if requested)
            if n_permutations > 0:
                print(f"  Permutation test ({n_permutations} iter)...", end=' ',
                      flush=True)
                perm_results = loco_permutation_test(
                    amplitudes, model_class, model_name,
                    overall_mae, n_permutations
                )
                result_entry['permutation'] = perm_results
                print(f"p={perm_results['p_value']:.4f}, z={perm_results['z_score']:.2f}")

            results[model_name] = result_entry

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Leave-One-Color-Out (LOCO) decoder comparison"
    )
    parser.add_argument('--baseline_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'])
    parser.add_argument('--models', nargs='+',
                        default=['LDA', 'Ridge', 'KernelRidge', 'SVM',
                                 'MLP', 'ForwardEncoding'])
    parser.add_argument('--alignment', type=str, default='procrustes',
                        choices=['raw', 'procrustes'])
    parser.add_argument('--permutations', type=int, default=0,
                        help='Number of permutations (0=skip)')

    args = parser.parse_args()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"LOCO Decoder Comparison")
    print(f"{'='*80}")
    print(f"Subject: sub-{args.subject}")
    print(f"ROIs: {args.rois}")
    print(f"Models: {args.models}")
    print(f"Alignment: {args.alignment}")
    print(f"Permutations: {args.permutations}")
    print(f"Output: {output_path}")
    print(f"{'='*80}\n")

    all_results = {}
    for roi in args.rois:
        results = run_single_subject_roi(
            args.baseline_dir, args.subject, roi,
            args.alignment, args.models, args.permutations
        )
        if results is not None:
            all_results[roi] = results

    # Save
    output_file = output_path / f"sub-{args.subject}_loco.json"

    # Build model architecture and default HP info
    model_architectures = {}
    model_defaults = {}
    for model_name in args.models:
        model_architectures[model_name] = get_model_architecture(model_name)
        model_defaults[model_name] = get_model_defaults(model_name)

    save_data = {
        'subject': args.subject,
        'subject_group': get_subject_group(args.subject),
        'rois': args.rois,
        'models': args.models,
        'alignment': args.alignment,
        'n_permutations': args.permutations,
        'settings': {
            'baseline_dir': str(args.baseline_dir),
            'dataset_name': Path(args.baseline_dir).name,
            'n_runs': 6,
            'n_colors': 8,
            'cv_method': 'LOCO (Leave-One-Color-Out)',
            'hp_tuning': False,
            'hp_tuning_note': 'LOCO uses default hyperparameters. '
                              'With only 7 training colors per fold, '
                              'nested HP tuning would be unreliable.'
        },
        'hyperparameters': model_defaults,
        'model_architectures': model_architectures,
        'results': all_results,
        'timestamp': timestamp,
        'datetime': datetime.now().isoformat()
    }

    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)

    # Save config.json (one per output_dir, safe to overwrite — identical across subjects)
    config_file = output_path / 'config.json'
    config_data = {
        'description': 'LOCO decoder comparison',
        'baseline_dir': str(args.baseline_dir),
        'dataset_name': Path(args.baseline_dir).name,
        'alignment': args.alignment,
        'models': args.models,
        'rois': args.rois,
        'n_permutations': args.permutations,
        'cv_method': 'LOCO (Leave-One-Color-Out)',
        'hp_tuning': False,
        'n_runs': 6,
        'n_colors': 8,
        'created': datetime.now().isoformat()
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Saved: {output_file}")
    print(f"Config: {config_file}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
