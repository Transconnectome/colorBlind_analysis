#!/usr/bin/env python3
"""
Decoder Model Comparison: Ridge vs Forward Encoding vs MLP

Tests whether Procrustes alignment particularly helps linear models.

Main Questions:
1. Ridge vs Forward Encoding: Which linear model is better?
2. Linear vs Non-linear: Does alignment help linear models more?

Models (Phase 1):
- Ridge Regression (linear)
- Forward Encoding 6-channel (linear)
- Small MLP (non-linear)

Protocol:
- Leave-One-Run-Out (LORO) cross-validation
- Nested hyperparameter tuning on train set only
- Circular metrics for hue reconstruction
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import warnings
from datetime import datetime

# ML libraries
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV
from scipy.stats import pearsonr

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "analysis"))

from utils.utils_color_decoding import (
    evaluate_reconstruction,
    create_basis_functions,
    circular_diff_deg
)

warnings.filterwarnings('ignore')


# ============================================================================
# Data Loading
# ============================================================================

def load_baseline_amplitudes(subject, roi, timestamp, dataset, base_dir, aligned=False):
    """
    Load amplitudes_z.npy from baseline results or aligned results

    Args:
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        timestamp: Baseline timestamp
        dataset: Dataset name
        base_dir: Base directory
        aligned: If True, load from aligned_amplitudes directory

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels) array
    """
    if aligned:
        # Load from aligned results
        aligned_dir = Path(base_dir) / "analysis" / "validation" / "results" / "aligned_amplitudes" / timestamp
        amplitudes_path = aligned_dir / f"sub-{subject}" / roi / "amplitudes_z.npy"
    else:
        # Load from baseline results
        baseline_dir = Path(base_dir) / "analysis" / "phase1_preprocess_decoding" / dataset / "results" / "baseline_decoding" / timestamp
        amplitudes_path = baseline_dir / f"sub-{subject}" / roi / "amplitudes_z.npy"

    if not amplitudes_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amplitudes_path}")

    amplitudes = np.load(amplitudes_path)
    return amplitudes


# ============================================================================
# Decoder Models
# ============================================================================

class RidgeDecoder:
    """Ridge Regression decoder for hue prediction"""

    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.model = None

    def fit(self, X, y_hue):
        """
        Args:
            X: (n_samples, n_voxels) brain patterns
            y_hue: (n_samples,) hue angles in degrees [0, 360)
        """
        # Convert hue to sin/cos for continuity (0° = 360°)
        y_sin = np.sin(np.deg2rad(y_hue))
        y_cos = np.cos(np.deg2rad(y_hue))
        y_circular = np.column_stack([y_sin, y_cos])

        self.model = Ridge(alpha=self.alpha)
        self.model.fit(X, y_circular)

    def predict(self, X):
        """
        Returns:
            y_pred_hue: (n_samples,) predicted hue angles in degrees [0, 360)
        """
        if self.model is None:
            raise RuntimeError("Model not fitted yet")

        y_pred_circular = self.model.predict(X)
        y_pred_sin = y_pred_circular[:, 0]
        y_pred_cos = y_pred_circular[:, 1]

        # Convert back to hue angles
        y_pred_hue = np.rad2deg(np.arctan2(y_pred_sin, y_pred_cos))
        y_pred_hue = np.mod(y_pred_hue, 360)  # Ensure [0, 360)

        return y_pred_hue

    @staticmethod
    def get_param_grid():
        return {'alpha': [0.01, 0.1, 1, 10, 100, 1000]}


class ForwardEncodingDecoder:
    """
    Forward Encoding Model with 6-channel basis functions

    Uses existing evaluate_reconstruction() from utils_color_decoding.py
    """

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights = None  # Encoding weights (n_channels, n_voxels)
        self.basis_functions = None  # (n_colors, n_channels)
        self.label2hue = None

    def fit(self, X, y_labels, label2hue_deg):
        """
        Args:
            X: (n_samples, n_voxels) brain patterns
            y_labels: (n_samples,) color labels (0-7)
            label2hue_deg: Dict mapping color labels to hue angles
        """
        self.label2hue = label2hue_deg
        n_voxels = X.shape[1]

        # Reshape X to (n_runs, n_colors, n_voxels) for evaluate_reconstruction
        # Assuming X is concatenated from multiple runs
        n_colors = 8
        n_runs = len(X) // n_colors

        if len(X) % n_colors != 0:
            raise ValueError(f"X length {len(X)} not divisible by n_colors {n_colors}")

        amplitudes_train = X.reshape(n_runs, n_colors, n_voxels)

        # Create basis functions
        hue_values = np.array([label2hue_deg[f'color_{i+1}'] for i in range(n_colors)])
        self.basis_functions = create_basis_functions(hue_values, n_channels=self.n_channels)

        # Estimate encoding weights using training data
        # Average over runs to get mean pattern per color
        mean_patterns = amplitudes_train.mean(axis=0)  # (n_colors, n_voxels)

        # W = (C^T C + alpha*I)^-1 C^T B
        # where C = basis_functions (n_colors, n_channels)
        #       B = mean_patterns (n_colors, n_voxels)
        C = self.basis_functions
        B = mean_patterns

        # Ridge regression for encoding weights
        if self.alpha > 0:
            weights = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            # Use pseudo-inverse if no regularization
            weights = np.linalg.pinv(C) @ B

        self.weights = weights  # (n_channels, n_voxels)

    def predict(self, X):
        """
        Returns:
            y_pred_hue: (n_samples,) predicted hue angles
        """
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        # Predict channel responses: R = W^T X^T
        # X: (n_samples, n_voxels)
        # weights: (n_channels, n_voxels)
        channel_responses = self.weights @ X.T  # (n_channels, n_samples)

        # For each sample, find best matching hue by correlating with basis functions
        n_samples = X.shape[0]
        y_pred_hue = np.zeros(n_samples)

        # Generate test hues (0-359 degrees)
        test_hues = np.arange(0, 360)
        test_basis = create_basis_functions(test_hues, n_channels=self.n_channels)

        for i in range(n_samples):
            # Correlate predicted channel response with all possible basis functions
            predicted_response = channel_responses[:, i]
            correlations = test_basis @ predicted_response

            # Find hue with maximum correlation
            best_hue_idx = np.argmax(correlations)
            y_pred_hue[i] = test_hues[best_hue_idx]

        return y_pred_hue

    @staticmethod
    def get_param_grid():
        return {'alpha': [0, 10, 50, 100, 200]}


class MLPDecoder:
    """
    Small MLP for hue prediction (non-linear model)

    Uses strong regularization to prevent overfitting with limited voxels
    """

    def __init__(self, hidden_layer_sizes=(64,), alpha=0.1, max_iter=500):
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.max_iter = max_iter
        self.model = None

    def fit(self, X, y_hue):
        """
        Args:
            X: (n_samples, n_voxels) brain patterns
            y_hue: (n_samples,) hue angles in degrees [0, 360)
        """
        # Convert hue to sin/cos for continuity
        y_sin = np.sin(np.deg2rad(y_hue))
        y_cos = np.cos(np.deg2rad(y_hue))
        y_circular = np.column_stack([y_sin, y_cos])

        self.model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            alpha=self.alpha,
            activation='relu',
            solver='adam',
            learning_rate='adaptive',
            max_iter=self.max_iter,
            early_stopping=True,
            validation_fraction=0.2,
            random_state=42,
            verbose=False
        )

        self.model.fit(X, y_circular)

    def predict(self, X):
        """
        Returns:
            y_pred_hue: (n_samples,) predicted hue angles in degrees [0, 360)
        """
        if self.model is None:
            raise RuntimeError("Model not fitted yet")

        y_pred_circular = self.model.predict(X)
        y_pred_sin = y_pred_circular[:, 0]
        y_pred_cos = y_pred_circular[:, 1]

        # Convert back to hue angles
        y_pred_hue = np.rad2deg(np.arctan2(y_pred_sin, y_pred_cos))
        y_pred_hue = np.mod(y_pred_hue, 360)  # Ensure [0, 360)

        return y_pred_hue

    @staticmethod
    def get_param_grid():
        return {
            'hidden_layer_sizes': [(64,), (64, 32)],
            'alpha': [0.01, 0.1, 1.0],
            'max_iter': [500]
        }


# ============================================================================
# Metrics
# ============================================================================

def compute_classification_metrics(y_true_hue, y_pred_hue, thresholds=[45, 90]):
    """
    Compute classification accuracy at different thresholds

    Args:
        y_true_hue: (n_samples,) true hue angles
        y_pred_hue: (n_samples,) predicted hue angles
        thresholds: List of acceptable error thresholds in degrees

    Returns:
        metrics: Dict with acc_45, acc_90, acc_exact
    """
    errors = np.abs(circular_diff_deg(y_true_hue, y_pred_hue))

    metrics = {}
    for thresh in thresholds:
        acc = np.mean(errors <= thresh)
        metrics[f'acc_{thresh}'] = float(acc)

    # Exact match (0 degrees error - very rare)
    metrics['acc_exact'] = float(np.mean(errors == 0))

    return metrics


def compute_reconstruction_metrics(y_true_hue, y_pred_hue):
    """
    Compute reconstruction error metrics

    Args:
        y_true_hue: (n_samples,) true hue angles
        y_pred_hue: (n_samples,) predicted hue angles

    Returns:
        metrics: Dict with mae, medae, errors
    """
    errors = np.abs(circular_diff_deg(y_true_hue, y_pred_hue))

    metrics = {
        'mae': float(np.mean(errors)),
        'medae': float(np.median(errors)),
        'errors': errors.tolist()
    }

    return metrics


# ============================================================================
# Cross-validation with nested hyperparameter tuning
# ============================================================================

def loro_cv_ridge(amplitudes_z, label2hue_deg):
    """Leave-One-Run-Out CV for Ridge decoder"""
    n_runs, n_colors, n_voxels = amplitudes_z.shape
    fold_results = []

    # Convert labels to hue angles
    hue_angles = np.array([label2hue_deg[f'color_{i+1}'] for i in range(n_colors)])

    for test_run in range(n_runs):
        # Split train/test
        train_runs = [r for r in range(n_runs) if r != test_run]
        X_train = amplitudes_z[train_runs].reshape(-1, n_voxels)
        y_train = np.tile(hue_angles, len(train_runs))

        X_test = amplitudes_z[test_run]
        y_test = hue_angles

        # Nested CV for hyperparameter tuning (on train set only)
        param_grid = RidgeDecoder.get_param_grid()
        best_alpha = param_grid['alpha'][0]  # Default

        if len(train_runs) >= 3:  # Need at least 3 folds for inner CV
            # Create dummy model for GridSearchCV
            def ridge_scorer(y_true_circular, y_pred_circular):
                # Convert circular back to hue for scoring
                y_true_hue = np.rad2deg(np.arctan2(y_true_circular[:, 0], y_true_circular[:, 1]))
                y_pred_hue = np.rad2deg(np.arctan2(y_pred_circular[:, 0], y_pred_circular[:, 1]))
                errors = np.abs(circular_diff_deg(y_true_hue, y_pred_hue))
                return -np.mean(errors)  # Negative MAE for maximization

            from sklearn.metrics import make_scorer
            scorer = make_scorer(ridge_scorer, greater_is_better=True)

            # Prepare circular targets for inner CV
            y_train_sin = np.sin(np.deg2rad(y_train))
            y_train_cos = np.cos(np.deg2rad(y_train))
            y_train_circular = np.column_stack([y_train_sin, y_train_cos])

            from sklearn.multioutput import MultiOutputRegressor
            inner_cv = GridSearchCV(
                MultiOutputRegressor(Ridge()),
                {'estimator__alpha': param_grid['alpha']},
                cv=3,
                scoring=scorer,
                n_jobs=1
            )

            try:
                inner_cv.fit(X_train, y_train_circular)
                best_alpha = inner_cv.best_params_['estimator__alpha']
            except:
                # If inner CV fails, use default
                pass

        # Train final model with best params
        model = RidgeDecoder(alpha=best_alpha)
        model.fit(X_train, y_train)

        # Test on held-out run
        y_pred = model.predict(X_test)

        # Compute metrics
        class_metrics = compute_classification_metrics(y_test, y_pred)
        recon_metrics = compute_reconstruction_metrics(y_test, y_pred)

        fold_results.append({
            'test_run': test_run,
            'best_params': {'alpha': best_alpha},
            **class_metrics,
            **recon_metrics
        })

    return fold_results


def loro_cv_forward_encoding(amplitudes_z, label2hue_deg):
    """Leave-One-Run-Out CV for Forward Encoding decoder"""
    n_runs, n_colors, n_voxels = amplitudes_z.shape
    fold_results = []

    # Convert labels to hue angles
    hue_angles = np.array([label2hue_deg[f'color_{i+1}'] for i in range(n_colors)])
    labels = np.arange(n_colors)

    for test_run in range(n_runs):
        # Split train/test
        train_runs = [r for r in range(n_runs) if r != test_run]
        X_train = amplitudes_z[train_runs].reshape(-1, n_voxels)
        y_train_labels = np.tile(labels, len(train_runs))

        X_test = amplitudes_z[test_run]
        y_test = hue_angles

        # Try different alpha values (simple grid search on train set)
        param_grid = ForwardEncodingDecoder.get_param_grid()
        best_alpha = 0
        best_score = -np.inf

        for alpha in param_grid['alpha']:
            # Simple leave-one-out on train runs for tuning
            tune_scores = []
            for tune_run in train_runs:
                tune_train_runs = [r for r in train_runs if r != tune_run]
                X_tune_train = amplitudes_z[tune_train_runs].reshape(-1, n_voxels)
                y_tune_train_labels = np.tile(labels, len(tune_train_runs))

                X_tune_test = amplitudes_z[tune_run]
                y_tune_test = hue_angles

                # Train and evaluate
                model_tune = ForwardEncodingDecoder(alpha=alpha)
                model_tune.fit(X_tune_train, y_tune_train_labels, label2hue_deg)
                y_tune_pred = model_tune.predict(X_tune_test)

                # Score
                errors = np.abs(circular_diff_deg(y_tune_test, y_tune_pred))
                tune_scores.append(-np.mean(errors))  # Negative MAE

            mean_score = np.mean(tune_scores)
            if mean_score > best_score:
                best_score = mean_score
                best_alpha = alpha

        # Train final model with best alpha
        model = ForwardEncodingDecoder(alpha=best_alpha)
        model.fit(X_train, y_train_labels, label2hue_deg)

        # Test on held-out run
        y_pred = model.predict(X_test)

        # Compute metrics
        class_metrics = compute_classification_metrics(y_test, y_pred)
        recon_metrics = compute_reconstruction_metrics(y_test, y_pred)

        fold_results.append({
            'test_run': test_run,
            'best_params': {'alpha': best_alpha},
            **class_metrics,
            **recon_metrics
        })

    return fold_results


def loro_cv_mlp(amplitudes_z, label2hue_deg):
    """Leave-One-Run-Out CV for MLP decoder"""
    n_runs, n_colors, n_voxels = amplitudes_z.shape
    fold_results = []

    # Convert labels to hue angles
    hue_angles = np.array([label2hue_deg[f'color_{i+1}'] for i in range(n_colors)])

    for test_run in range(n_runs):
        # Split train/test
        train_runs = [r for r in range(n_runs) if r != test_run]
        X_train = amplitudes_z[train_runs].reshape(-1, n_voxels)
        y_train = np.tile(hue_angles, len(train_runs))

        X_test = amplitudes_z[test_run]
        y_test = hue_angles

        # Nested CV for hyperparameter tuning
        param_grid = MLPDecoder.get_param_grid()
        best_params = {
            'hidden_layer_sizes': (64,),
            'alpha': 0.1,
            'max_iter': 500
        }

        if len(train_runs) >= 3:
            # Simple grid search with leave-one-out on train runs
            best_score = -np.inf

            for hidden in param_grid['hidden_layer_sizes']:
                for alpha in param_grid['alpha']:
                    tune_scores = []

                    for tune_run in train_runs:
                        tune_train_runs = [r for r in train_runs if r != tune_run]
                        X_tune_train = amplitudes_z[tune_train_runs].reshape(-1, n_voxels)
                        y_tune_train = np.tile(hue_angles, len(tune_train_runs))

                        X_tune_test = amplitudes_z[tune_run]
                        y_tune_test = hue_angles

                        # Train and evaluate
                        model_tune = MLPDecoder(
                            hidden_layer_sizes=hidden,
                            alpha=alpha,
                            max_iter=500
                        )
                        model_tune.fit(X_tune_train, y_tune_train)
                        y_tune_pred = model_tune.predict(X_tune_test)

                        # Score
                        errors = np.abs(circular_diff_deg(y_tune_test, y_tune_pred))
                        tune_scores.append(-np.mean(errors))

                    mean_score = np.mean(tune_scores)
                    if mean_score > best_score:
                        best_score = mean_score
                        best_params = {
                            'hidden_layer_sizes': hidden,
                            'alpha': alpha,
                            'max_iter': 500
                        }

        # Train final model with best params
        model = MLPDecoder(**best_params)
        model.fit(X_train, y_train)

        # Test on held-out run
        y_pred = model.predict(X_test)

        # Compute metrics
        class_metrics = compute_classification_metrics(y_test, y_pred)
        recon_metrics = compute_reconstruction_metrics(y_test, y_pred)

        fold_results.append({
            'test_run': test_run,
            'best_params': best_params,
            **class_metrics,
            **recon_metrics
        })

    return fold_results


# ============================================================================
# Main Comparison
# ============================================================================

def run_model_comparison(subject, rois, timestamp, dataset, base_dir, aligned, models, output_dir):
    """
    Run decoder model comparison for a subject

    Args:
        subject: Subject ID
        rois: List of ROI names
        timestamp: Baseline timestamp
        dataset: Dataset name
        base_dir: Base directory
        aligned: Whether to use aligned data
        models: List of model names to compare
        output_dir: Output directory
    """
    # Color mapping (8 colors, 45° spacing)
    label2hue_deg = {
        'color_1': 0,      # Red
        'color_2': 45,     # Orange
        'color_3': 90,     # Yellow
        'color_4': 135,    # Green
        'color_5': 180,    # Cyan
        'color_6': 225,    # Blue
        'color_7': 270,    # Purple
        'color_8': 315     # Magenta
    }

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"Decoder Model Comparison")
    print(f"{'='*80}")
    print(f"Subject: sub-{subject}")
    print(f"ROIs: {rois}")
    print(f"Timestamp: {timestamp}")
    print(f"Aligned: {aligned}")
    print(f"Models: {models}")
    print(f"{'='*80}\n")

    # Results storage
    all_results = {}

    # Process each ROI
    for roi in rois:
        print(f"\n{'='*60}")
        print(f"Processing ROI: {roi}")
        print(f"{'='*60}\n")

        # Load amplitudes
        try:
            amplitudes_z = load_baseline_amplitudes(
                subject, roi, timestamp, dataset, base_dir, aligned
            )
            print(f"Loaded amplitudes: shape={amplitudes_z.shape}")
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            continue

        roi_results = {}

        # Run each model
        for model_name in models:
            print(f"\n--- Running {model_name} ---")

            try:
                if model_name == 'ridge':
                    fold_results = loro_cv_ridge(amplitudes_z, label2hue_deg)
                elif model_name == 'forward_encoding':
                    fold_results = loro_cv_forward_encoding(amplitudes_z, label2hue_deg)
                elif model_name == 'mlp':
                    fold_results = loro_cv_mlp(amplitudes_z, label2hue_deg)
                else:
                    print(f"Unknown model: {model_name}")
                    continue

                roi_results[model_name] = fold_results

                # Print summary
                acc_45_values = [f['acc_45'] for f in fold_results]
                mae_values = [f['mae'] for f in fold_results]

                print(f"Accuracy (45°): {np.mean(acc_45_values):.3f} ± {np.std(acc_45_values):.3f}")
                print(f"MAE: {np.mean(mae_values):.2f}° ± {np.std(mae_values):.2f}°")

            except Exception as e:
                print(f"ERROR in {model_name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        all_results[roi] = roi_results

    # Save results
    output_filename = f"sub-{subject}_performance_raw.json"
    output_filepath = output_path / output_filename

    results_data = {
        'subject': subject,
        'rois': rois,
        'timestamp': timestamp,
        'dataset': dataset,
        'aligned': aligned,
        'models': models,
        'label2hue_deg': label2hue_deg,
        'results': all_results,
        'datetime': datetime.now().isoformat()
    }

    with open(output_filepath, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved: {output_filepath}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Decoder model comparison for color decoding"
    )
    parser.add_argument('--subject', type=str, required=True,
                       help='Subject ID (e.g., 01)')
    parser.add_argument('--rois', nargs='+', required=True,
                       help='ROI names (e.g., V1 V2 V3 hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                       help='Baseline timestamp')
    parser.add_argument('--dataset', type=str, default='method3_header_mi',
                       help='Dataset name')
    parser.add_argument('--base_dir', type=str,
                       default='/scratch/connectome/haba6030/colorBlind',
                       help='Base directory')
    parser.add_argument('--aligned', type=str, default='False',
                       choices=['True', 'False'],
                       help='Use aligned data (True/False)')
    parser.add_argument('--models', nargs='+',
                       default=['ridge', 'forward_encoding', 'mlp'],
                       help='Models to compare')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory')

    args = parser.parse_args()

    # Convert string to boolean
    aligned = args.aligned == 'True'

    # Run comparison
    run_model_comparison(
        subject=args.subject,
        rois=args.rois,
        timestamp=args.timestamp,
        dataset=args.dataset,
        base_dir=args.base_dir,
        aligned=aligned,
        models=args.models,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
