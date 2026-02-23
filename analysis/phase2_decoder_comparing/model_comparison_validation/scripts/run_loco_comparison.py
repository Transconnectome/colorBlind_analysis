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
        --models LDA Ridge KernelRidge SVM MLP ForwardEncoding HybridMLP HybridSVR \
        --alignment procrustes \
        --permutations 0

Alignment options:
    raw        - amplitudes_raw.npy (n_voxels features)
    procrustes - amplitudes_procrustes.npy (n_voxels features)
    srm        - amplitudes_srm.npy (k=3-4 features, HC-only SRM)
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
    load_amplitudes as _load_amplitudes_base,
    labels_to_hue, hue_to_labels, circular_diff_deg,
    HUE_ANGLES
)
from utils import (get_model_architecture, get_model_defaults,
                   get_subject_group)

from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor

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
# Circular Statistics Utilities
# ============================================================================

def circular_distance(y_true, y_pred):
    """
    Compute circular distance in degrees.

    Args:
        y_true: True hue angles (degrees, 0-359)
        y_pred: Predicted hue angles (degrees, 0-359)

    Returns:
        Circular distance (0-180 degrees)
    """
    diff = np.abs(y_true - y_pred)
    return np.minimum(diff, 360 - diff)


def circular_mse(y_true, y_pred):
    """
    Circular mean squared error.

    Args:
        y_true: True hue angles (degrees, 0-359)
        y_pred: Predicted hue angles (degrees, 0-359)

    Returns:
        Mean squared circular distance
    """
    return np.mean(circular_distance(y_true, y_pred) ** 2)


# ============================================================================
# Data Loading (extended for SRM alignment)
# ============================================================================

def load_amplitudes(baseline_dir, subject, roi, alignment='procrustes'):
    """
    Load amplitudes with SRM support.

    Args:
        baseline_dir: Path to full_dataset_C010
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        alignment: 'raw', 'procrustes', or 'srm'

    Returns:
        amplitudes: (n_runs, n_colors, n_features) array
    """
    if alignment == 'srm':
        subject_roi_dir = Path(baseline_dir) / f"sub-{subject}" / roi
        amp_path = subject_roi_dir / "amplitudes_srm.npy"
        if not amp_path.exists():
            raise FileNotFoundError(f"SRM amplitudes not found: {amp_path}")
        return np.load(amp_path)  # (6, 8, k)
    else:
        return _load_amplitudes_base(baseline_dir, subject, roi, alignment)


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
# Hybrid Degree Models: MLP/SVR → 6 channels → FE template matching → degree
# ============================================================================

class HybridDegreeMLPDecoder:
    """
    Hybrid degree model: MLP regression to 6 channel activations,
    then FE template matching to continuous hue degree.

    Reverses the standard hybrid (FE→MLP→label):
      Voxel → MLP (regression) → 6 channels → template matching → continuous hue
    """

    def __init__(self, n_channels=6, hidden_layer_sizes=(64, 32), alpha=0.1):
        self.n_channels = n_channels
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.mlp = None
        self.basis_full = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) brain patterns
            y_labels: (n_samples,) color labels (0-7)
        """
        self.basis_full = create_basis_functions(n_channels=self.n_channels)  # (360, 6)

        # Target: basis_functions at each sample's hue angle → (n_samples, 6)
        targets = np.array([self.basis_full[HUE_ANGLES[int(l)]] for l in y_labels])

        self.mlp = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            alpha=self.alpha,
            activation='relu',
            solver='adam',
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.2,
            random_state=42,
        )
        self.mlp.fit(X, targets)

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.mlp is None:
            raise RuntimeError("Model not fitted yet")

        channel_pred = self.mlp.predict(X)  # (n_samples, 6)

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            # Correlate predicted channels with all 360 templates
            pred = channel_pred[i]
            correlations = np.array([
                np.corrcoef(pred, self.basis_full[h])[0, 1]
                if np.std(pred) > 1e-10 else 0.0
                for h in range(360)
            ])
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues


class HybridDegreeSVRDecoder:
    """
    Hybrid degree model: SVR regression to 6 channel activations,
    then FE template matching to continuous hue degree.

    Same architecture as HybridDegreeMLPDecoder but uses SVR.
    """

    def __init__(self, n_channels=6, C=1.0, epsilon=0.1):
        self.n_channels = n_channels
        self.C = C
        self.epsilon = epsilon
        self.svr = None
        self.basis_full = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) brain patterns
            y_labels: (n_samples,) color labels (0-7)
        """
        self.basis_full = create_basis_functions(n_channels=self.n_channels)  # (360, 6)

        # Target: basis_functions at each sample's hue angle → (n_samples, 6)
        targets = np.array([self.basis_full[HUE_ANGLES[int(l)]] for l in y_labels])

        self.svr = MultiOutputRegressor(
            SVR(C=self.C, epsilon=self.epsilon, kernel='rbf', gamma='scale')
        )
        self.svr.fit(X, targets)

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.svr is None:
            raise RuntimeError("Model not fitted yet")

        channel_pred = self.svr.predict(X)  # (n_samples, 6)

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            pred = channel_pred[i]
            correlations = np.array([
                np.corrcoef(pred, self.basis_full[h])[0, 1]
                if np.std(pred) > 1e-10 else 0.0
                for h in range(360)
            ])
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues


# ============================================================================
# Per-Run Ensemble FE Decoders
# ============================================================================

class FE_EnsembleDecoder:
    """ForwardEncoding with per-run W estimation + ensemble prediction.

    Instead of averaging 6 runs into mean patterns and fitting a single W,
    fits W separately for each run (7 colors → W_run). At prediction time,
    all 6 W's produce independent hue predictions, combined via circular mean.
    """

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights_list = None  # list of W per run
        self.predict_basis = None

    def _fit_single_w(self, patterns, labels):
        """Fit encoding weights from a single run's patterns."""
        basis_full = create_basis_functions(n_channels=self.n_channels)
        train_hues = np.array([HUE_ANGLES[l] for l in labels])
        C = basis_full[train_hues]
        B = patterns

        if self.alpha > 0:
            W = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            W = np.linalg.pinv(C) @ B
        return W

    def fit(self, X, y_labels):
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        self.predict_basis = create_basis_functions(n_channels=self.n_channels)
        self.weights_list = []

        for r in range(n_runs):
            run_X = X[r * n_train_colors : (r + 1) * n_train_colors]
            run_labels = y_labels[r * n_train_colors : (r + 1) * n_train_colors]

            # Sort by label to ensure consistent ordering
            sort_idx = np.argsort(run_labels)
            run_X = run_X[sort_idx]
            run_labels = run_labels[sort_idx]

            W = self._fit_single_w(run_X, run_labels)
            self.weights_list.append(W)

    def _predict_single(self, W, x):
        """Predict hue for a single sample using one W."""
        channel_response = W @ x
        correlations = np.array([
            np.corrcoef(channel_response, self.predict_basis[h])[0, 1]
            if np.std(channel_response) > 1e-10 else 0.0
            for h in range(360)
        ])
        return np.argmax(correlations)

    def predict(self, X):
        if self.weights_list is None:
            raise RuntimeError("Model not fitted yet")

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            preds_rad = []
            for W in self.weights_list:
                h = self._predict_single(W, X[i])
                preds_rad.append(np.deg2rad(h))

            # Circular mean of ensemble predictions
            x_mean = np.mean(np.cos(preds_rad))
            y_mean = np.mean(np.sin(preds_rad))
            y_pred_hues[i] = np.rad2deg(np.arctan2(y_mean, x_mean)) % 360

        return y_pred_hues


class FE_EnsembleRidgeDecoder(FE_EnsembleDecoder):
    """Per-run W ensemble with Ridge-regularized encoding."""

    def __init__(self, alpha=1.0, n_channels=6):
        super().__init__(alpha=alpha, n_channels=n_channels)


class FE_EnsembleGaussMLDecoder:
    """Per-run W ensemble + Gaussian ML decoding with within-color noise.

    Key difference from FE_GaussianMLDecoder: noise variance is estimated from
    WITHIN-color run-to-run variability (6 runs × 7 colors = 42 observations),
    not from across-color residuals (only 7 points).
    """

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights_list = None
        self.predict_basis = None
        self.noise_var = None  # (n_channels,) within-color noise
        self.scale = None      # (n_channels,) mean channel magnitude

    def fit(self, X, y_labels):
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        basis_full = create_basis_functions(n_channels=self.n_channels)
        self.predict_basis = basis_full
        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])

        # Step 1: Fit per-run W
        self.weights_list = []
        for r in range(n_runs):
            run_X = X[r * n_train_colors : (r + 1) * n_train_colors]
            run_labels = y_labels[r * n_train_colors : (r + 1) * n_train_colors]
            sort_idx = np.argsort(run_labels)
            run_X = run_X[sort_idx]
            run_labels = run_labels[sort_idx]

            C = basis_full[np.array([HUE_ANGLES[l] for l in run_labels])]
            B = run_X
            if self.alpha > 0:
                W = np.linalg.solve(
                    C.T @ C + self.alpha * np.eye(self.n_channels),
                    C.T @ B
                )
            else:
                W = np.linalg.pinv(C) @ B
            self.weights_list.append(W)

        # Step 2: Estimate within-color noise from run-to-run variability
        # For each color, compute channel responses across 6 runs → variance
        all_channel_responses = np.zeros((n_runs, n_train_colors, self.n_channels))
        for r, W in enumerate(self.weights_list):
            run_X = X[r * n_train_colors : (r + 1) * n_train_colors]
            run_labels = y_labels[r * n_train_colors : (r + 1) * n_train_colors]
            sort_idx = np.argsort(run_labels)
            run_X = run_X[sort_idx]
            all_channel_responses[r] = (W @ run_X.T).T  # (n_train_colors, n_channels)

        # Within-color variance: var across runs for each color, then average
        # all_channel_responses: (n_runs, n_colors, n_channels)
        per_color_var = np.var(all_channel_responses, axis=0)  # (n_colors, n_channels)
        self.noise_var = np.mean(per_color_var, axis=0)  # (n_channels,)
        self.noise_var = np.maximum(self.noise_var, 1e-10)

        # Step 3: Estimate scale from mean channel responses vs expected basis
        mean_channel = np.mean(all_channel_responses, axis=0)  # (n_colors, n_channels)
        expected = basis_full[train_hues]  # (n_colors, n_channels)
        # Per-channel scale
        expected_abs_mean = np.mean(np.abs(expected), axis=0) + 1e-10
        observed_abs_mean = np.mean(np.abs(mean_channel), axis=0)
        self.scale = observed_abs_mean / expected_abs_mean

    def predict(self, X):
        if self.weights_list is None:
            raise RuntimeError("Model not fitted yet")

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples)
        inv_var = 1.0 / self.noise_var

        for i in range(n_samples):
            # Ensemble: average channel responses across all W's
            channel_responses = np.array([W @ X[i] for W in self.weights_list])
            obs = np.mean(channel_responses, axis=0)  # (n_channels,)

            # Gaussian ML: argmax log-likelihood
            log_liks = np.zeros(360)
            for h in range(360):
                template = self.predict_basis[h] * self.scale
                diff = obs - template
                log_liks[h] = -0.5 * np.sum(diff**2 * inv_var)
            y_pred_hues[i] = np.argmax(log_liks)

        return y_pred_hues


# ============================================================================
# Per-Run Ensemble Hybrid Degree Models
# ============================================================================

class HybridMLP_Ensemble:
    """Per-run MLP → 6 channels + ensemble prediction.

    Each run trains an independent MLP regressor (7 colors → 6 channel activations).
    At prediction time, all 6 MLPs produce channel predictions, which are ensembled
    via circular mean after template matching.

    Tests whether per-run diversity helps MLP overcome small-sample overfitting
    (7 training colors/run vs 42 pooled).
    """

    def __init__(self, n_channels=6, hidden_layer_sizes=(64, 32), alpha=0.1):
        self.n_channels = n_channels
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.mlp_list = None
        self.basis_full = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) — n_samples = n_runs × n_train_colors
            y_labels: (n_samples,) color labels (subset of 0-7)
        """
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        self.basis_full = create_basis_functions(n_channels=self.n_channels)
        self.mlp_list = []

        for r in range(n_runs):
            run_X = X[r * n_train_colors : (r + 1) * n_train_colors]
            run_labels = y_labels[r * n_train_colors : (r + 1) * n_train_colors]

            # Sort by label for consistency
            sort_idx = np.argsort(run_labels)
            run_X = run_X[sort_idx]
            run_labels = run_labels[sort_idx]

            # Target: basis functions at training color hues
            targets = np.array([self.basis_full[HUE_ANGLES[int(l)]] for l in run_labels])

            # Train MLP for this run
            mlp = MLPRegressor(
                hidden_layer_sizes=self.hidden_layer_sizes,
                alpha=self.alpha,
                activation='relu',
                solver='adam',
                learning_rate='adaptive',
                max_iter=500,
                early_stopping=True,
                validation_fraction=0.2,
                random_state=42,
            )
            mlp.fit(run_X, targets)
            self.mlp_list.append(mlp)

    def _predict_single(self, mlp, x):
        """Predict hue for a single sample using one MLP."""
        channel_pred = mlp.predict(x.reshape(1, -1))[0]  # (6,)

        # Template matching
        correlations = np.array([
            np.corrcoef(channel_pred, self.basis_full[h])[0, 1]
            if np.std(channel_pred) > 1e-10 else 0.0
            for h in range(360)
        ])
        return np.argmax(correlations)

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.mlp_list is None:
            raise RuntimeError("Model not fitted yet")

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            preds_rad = []
            for mlp in self.mlp_list:
                h = self._predict_single(mlp, X[i])
                preds_rad.append(np.deg2rad(h))

            # Circular mean of ensemble predictions
            x_mean = np.mean(np.cos(preds_rad))
            y_mean = np.mean(np.sin(preds_rad))
            y_pred_hues[i] = np.rad2deg(np.arctan2(y_mean, x_mean)) % 360

        return y_pred_hues


class HybridSVR_Ensemble:
    """Per-run SVR → 6 channels + ensemble prediction.

    Each run trains an independent MultiOutput SVR (7 colors → 6 channel activations).
    At prediction time, all 6 SVRs produce channel predictions, which are ensembled
    via circular mean after template matching.

    Tests whether per-run diversity helps SVR overcome small-sample overfitting
    (7 training colors/run vs 42 pooled).
    """

    def __init__(self, n_channels=6, C=1.0, epsilon=0.1):
        self.n_channels = n_channels
        self.C = C
        self.epsilon = epsilon
        self.svr_list = None
        self.basis_full = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) — n_samples = n_runs × n_train_colors
            y_labels: (n_samples,) color labels (subset of 0-7)
        """
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        self.basis_full = create_basis_functions(n_channels=self.n_channels)
        self.svr_list = []

        for r in range(n_runs):
            run_X = X[r * n_train_colors : (r + 1) * n_train_colors]
            run_labels = y_labels[r * n_train_colors : (r + 1) * n_train_colors]

            # Sort by label for consistency
            sort_idx = np.argsort(run_labels)
            run_X = run_X[sort_idx]
            run_labels = run_labels[sort_idx]

            # Target: basis functions at training color hues
            targets = np.array([self.basis_full[HUE_ANGLES[int(l)]] for l in run_labels])

            # Train SVR for this run
            svr = MultiOutputRegressor(
                SVR(C=self.C, epsilon=self.epsilon, kernel='rbf', gamma='scale')
            )
            svr.fit(run_X, targets)
            self.svr_list.append(svr)

    def _predict_single(self, svr, x):
        """Predict hue for a single sample using one SVR."""
        channel_pred = svr.predict(x.reshape(1, -1))[0]  # (6,)

        # Template matching
        correlations = np.array([
            np.corrcoef(channel_pred, self.basis_full[h])[0, 1]
            if np.std(channel_pred) > 1e-10 else 0.0
            for h in range(360)
        ])
        return np.argmax(correlations)

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.svr_list is None:
            raise RuntimeError("Model not fitted yet")

        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            preds_rad = []
            for svr in self.svr_list:
                h = self._predict_single(svr, X[i])
                preds_rad.append(np.deg2rad(h))

            # Circular mean of ensemble predictions
            x_mean = np.mean(np.cos(preds_rad))
            y_mean = np.mean(np.sin(preds_rad))
            y_pred_hues[i] = np.rad2deg(np.arctan2(y_mean, x_mean)) % 360

        return y_pred_hues


# ============================================================================
# Sequential Training Models (One model, incremental updates)
# ============================================================================

class ForwardEncodingSequential:
    """
    ForwardEncoding with sequential/incremental training.

    Instead of averaging 6 runs or creating 6 independent models,
    trains a single W matrix by incrementally accumulating data:
    run1 → run1+2 → run1+2+3 → ... → all 6 runs

    This mimics continuous learning where the model updates as new data arrives.
    Final W is identical to pooled training (42 samples), but the learning
    process is sequential.
    """

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights = None
        self.predict_basis = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) — n_samples = n_runs × n_train_colors
            y_labels: (n_samples,) color labels (subset of 0-7)
        """
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        basis_full = create_basis_functions(n_channels=self.n_channels)
        self.predict_basis = basis_full

        # Sequential training: accumulate data run-by-run
        for r in range(n_runs):
            # Accumulated data up to current run
            X_so_far = X[: (r + 1) * n_train_colors]
            y_so_far = y_labels[: (r + 1) * n_train_colors]

            # Group by label and average within accumulated data
            mean_patterns = np.zeros((n_train_colors, X.shape[1]))
            for i, label in enumerate(unique_labels):
                mask = y_so_far == label
                if np.any(mask):
                    mean_patterns[i] = X_so_far[mask].mean(axis=0)

            # Build basis from training colors
            train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
            train_basis = basis_full[train_hues]

            # Update W with accumulated data
            C = train_basis
            B = mean_patterns

            if self.alpha > 0:
                self.weights = np.linalg.solve(
                    C.T @ C + self.alpha * np.eye(self.n_channels),
                    C.T @ B
                )
            else:
                self.weights = np.linalg.pinv(C) @ B

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        channel_responses = self.weights @ X.T  # (n_channels, n_samples)
        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            predicted_response = channel_responses[:, i]
            # Template matching against all 360 hues
            correlations = np.array([
                np.corrcoef(predicted_response, self.predict_basis[h])[0, 1]
                if np.std(predicted_response) > 1e-10 else 0.0
                for h in range(360)
            ])
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues


class HybridMLPSequential:
    """
    ForwardEncoding (pooled) + MLP (sequential training with warm_start).

    Stage 1: ForwardEncoding extracts 6-channel responses using pooled data (42 samples)
    Stage 2: MLP trains sequentially on run1, then run2, ..., run6 using warm_start=True

    This mimics how the brain might continuously update its readout while the
    encoding structure remains stable.
    """

    def __init__(self, fe_alpha=0, n_channels=6,
                 hidden_layer_sizes=(64, 32), mlp_alpha=0.1):
        self.fe_alpha = fe_alpha
        self.n_channels = n_channels
        self.hidden_layer_sizes = hidden_layer_sizes
        self.mlp_alpha = mlp_alpha
        self.weights = None  # FE weights
        self.mlp = None
        self.basis_full = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) — n_samples = n_runs × n_train_colors
            y_labels: (n_samples,) color labels (subset of 0-7)
        """
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        # Stage 1: FE encoding with pooled data (like ForwardEncodingSequential final W)
        self.basis_full = create_basis_functions(n_channels=self.n_channels)

        # Pooled training for FE
        mean_patterns = np.zeros((n_train_colors, X.shape[1]))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        train_basis = self.basis_full[train_hues]

        C = train_basis
        B = mean_patterns

        if self.fe_alpha > 0:
            self.weights = np.linalg.solve(
                C.T @ C + self.fe_alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            self.weights = np.linalg.pinv(C) @ B

        # Extract 6-channel responses for all samples
        channel_responses = self.weights @ X.T  # (n_channels, n_samples)
        channel_responses = channel_responses.T  # (n_samples, n_channels)

        # Stage 2: MLP sequential training with warm_start
        self.mlp = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            alpha=self.mlp_alpha,
            activation='relu',
            solver='adam',
            learning_rate='adaptive',
            max_iter=500,
            warm_start=True,  # Enable sequential learning
            random_state=42,
        )

        # Sequential training run-by-run
        for r in range(n_runs):
            run_channels = channel_responses[r * n_train_colors : (r + 1) * n_train_colors]
            run_labels = y_labels[r * n_train_colors : (r + 1) * n_train_colors]

            # Target: basis function values at true hue angles
            targets = np.array([self.basis_full[HUE_ANGLES[int(l)]] for l in run_labels])

            # Sequential fit (updates existing weights when warm_start=True)
            self.mlp.fit(run_channels, targets)

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.weights is None or self.mlp is None:
            raise RuntimeError("Model not fitted yet")

        # Stage 1: Extract channel responses
        channel_responses = self.weights @ X.T  # (n_channels, n_samples)
        channel_responses = channel_responses.T  # (n_samples, n_channels)

        # Stage 2: MLP predicts 6-channel targets
        channel_pred = self.mlp.predict(channel_responses)  # (n_samples, 6)

        # Stage 3: Template matching
        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            correlations = np.array([
                np.corrcoef(channel_pred[i], self.basis_full[h])[0, 1]
                if np.std(channel_pred[i]) > 1e-10 else 0.0
                for h in range(360)
            ])
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues


class HybridSVRSequential:
    """
    ForwardEncoding (pooled) + SVR (incremental data accumulation).

    Stage 1: ForwardEncoding extracts 6-channel responses using pooled data (42 samples)
    Stage 2: SVR trains incrementally (run1 → run1+2 → ... → all runs)

    Note: SVR doesn't support warm_start, so we use incremental data accumulation
    (refit with growing dataset). Final model sees all data, but training is sequential.
    """

    def __init__(self, fe_alpha=0, n_channels=6, C=1.0, epsilon=0.1):
        self.fe_alpha = fe_alpha
        self.n_channels = n_channels
        self.C = C
        self.epsilon = epsilon
        self.weights = None  # FE weights
        self.svr = None
        self.basis_full = None

    def fit(self, X, y_labels):
        """
        Args:
            X: (n_samples, n_features) — n_samples = n_runs × n_train_colors
            y_labels: (n_samples,) color labels (subset of 0-7)
        """
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_samples = X.shape[0]
        n_runs = n_samples // n_train_colors

        # Stage 1: FE encoding with pooled data
        self.basis_full = create_basis_functions(n_channels=self.n_channels)

        mean_patterns = np.zeros((n_train_colors, X.shape[1]))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        train_basis = self.basis_full[train_hues]

        C_matrix = train_basis
        B_matrix = mean_patterns

        if self.fe_alpha > 0:
            self.weights = np.linalg.solve(
                C_matrix.T @ C_matrix + self.fe_alpha * np.eye(self.n_channels),
                C_matrix.T @ B_matrix
            )
        else:
            self.weights = np.linalg.pinv(C_matrix) @ B_matrix

        # Extract 6-channel responses for all samples
        channel_responses = self.weights @ X.T  # (n_channels, n_samples)
        channel_responses = channel_responses.T  # (n_samples, n_channels)

        # Stage 2: SVR incremental training (accumulate data run-by-run)
        for r in range(n_runs):
            # Accumulated data up to current run
            channels_so_far = channel_responses[: (r + 1) * n_train_colors]
            labels_so_far = y_labels[: (r + 1) * n_train_colors]

            # Target: basis function values at true hue angles
            targets_so_far = np.array([
                self.basis_full[HUE_ANGLES[int(l)]] for l in labels_so_far
            ])

            # Refit SVR with accumulated data
            self.svr = MultiOutputRegressor(
                SVR(C=self.C, epsilon=self.epsilon, kernel='rbf', gamma='scale')
            )
            self.svr.fit(channels_so_far, targets_so_far)

    def predict(self, X):
        """Returns: (n_samples,) predicted HUE ANGLES (0-359°)"""
        if self.weights is None or self.svr is None:
            raise RuntimeError("Model not fitted yet")

        # Stage 1: Extract channel responses
        channel_responses = self.weights @ X.T  # (n_channels, n_samples)
        channel_responses = channel_responses.T  # (n_samples, n_channels)

        # Stage 2: SVR predicts 6-channel targets
        channel_pred = self.svr.predict(channel_responses)  # (n_samples, 6)

        # Stage 3: Template matching
        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            correlations = np.array([
                np.corrcoef(channel_pred[i], self.basis_full[h])[0, 1]
                if np.std(channel_pred[i]) > 1e-10 else 0.0
                for h in range(360)
            ])
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues


# ============================================================================
# Alternative FE Decoding Methods (Single-W, deprecated — see Result 7)
# ============================================================================

class FE_PopulationVectorDecoder:
    """ForwardEncoding + Population Vector decoding (circular weighted mean)"""

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights = None
        self.channel_centers = None

    def fit(self, X, y_labels):
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_voxels = X.shape[1]

        mean_patterns = np.zeros((n_train_colors, n_voxels))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        basis_full = create_basis_functions(n_channels=self.n_channels)
        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        train_basis = basis_full[train_hues]

        C = train_basis
        B = mean_patterns

        if self.alpha > 0:
            self.weights = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            self.weights = np.linalg.pinv(C) @ B

        self.channel_centers = np.linspace(0, 360, self.n_channels, endpoint=False)

    def predict(self, X):
        channel_responses = self.weights @ X.T  # (6, n_samples)
        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples)

        for i in range(n_samples):
            r = np.maximum(channel_responses[:, i], 0)  # half-wave rectify
            if r.sum() < 1e-10:
                y_pred_hues[i] = 0
                continue
            angles_rad = np.deg2rad(self.channel_centers)
            x_mean = np.sum(r * np.cos(angles_rad)) / np.sum(r)
            y_mean = np.sum(r * np.sin(angles_rad)) / np.sum(r)
            y_pred_hues[i] = np.rad2deg(np.arctan2(y_mean, x_mean)) % 360

        return y_pred_hues


class FE_RidgeEncodingDecoder:
    """ForwardEncoding with Ridge-regularized encoding weights, correlation decoding"""

    def __init__(self, alpha=1.0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights = None
        self.predict_basis = None

    def fit(self, X, y_labels):
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_voxels = X.shape[1]

        mean_patterns = np.zeros((n_train_colors, n_voxels))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        basis_full = create_basis_functions(n_channels=self.n_channels)
        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        train_basis = basis_full[train_hues]

        self.predict_basis = basis_full

        C = train_basis
        B = mean_patterns
        # Always use Ridge regularization
        self.weights = np.linalg.solve(
            C.T @ C + self.alpha * np.eye(self.n_channels),
            C.T @ B
        )

    def predict(self, X):
        """Correlation-based template matching (same as LOCOForwardEncodingDecoder)"""
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        channel_responses = self.weights @ X.T
        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            predicted_response = channel_responses[:, i]
            correlations = []
            for hue in range(360):
                template = self.predict_basis[hue]
                corr_matrix = np.corrcoef(predicted_response, template)
                if corr_matrix.shape == (2, 2):
                    corr = corr_matrix[0, 1]
                else:
                    corr = np.dot(predicted_response, template) / (
                        np.linalg.norm(predicted_response) * np.linalg.norm(template) + 1e-10
                    )
                correlations.append(corr)
            y_pred_hues[i] = np.argmax(correlations)

        return y_pred_hues


class FE_GaussianMLDecoder:
    """ForwardEncoding + Gaussian ML decoding (diagonal covariance)"""

    def __init__(self, alpha=0, n_channels=6):
        self.alpha = alpha
        self.n_channels = n_channels
        self.weights = None
        self.predict_basis = None
        self.noise_var = None
        self.scale = None

    def fit(self, X, y_labels):
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_voxels = X.shape[1]

        mean_patterns = np.zeros((n_train_colors, n_voxels))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        basis_full = create_basis_functions(n_channels=self.n_channels)
        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        train_basis = basis_full[train_hues]

        self.predict_basis = basis_full

        C = train_basis
        B = mean_patterns

        if self.alpha > 0:
            self.weights = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            self.weights = np.linalg.pinv(C) @ B

        # Estimate noise statistics from training residuals
        channel_responses = self.weights @ mean_patterns.T  # (6, n_train_colors)
        expected = train_basis.T  # (6, n_train_colors)

        residuals = channel_responses - expected  # (6, n_train_colors)
        self.noise_var = np.var(residuals, axis=1)  # (6,)
        self.noise_var = np.maximum(self.noise_var, 1e-10)

        # Per-channel scale: ratio of observed to expected magnitude
        expected_mean = np.mean(np.abs(expected), axis=1) + 1e-10
        observed_mean = np.mean(np.abs(channel_responses), axis=1)
        self.scale = observed_mean / expected_mean

    def predict(self, X):
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        channel_responses = self.weights @ X.T  # (6, n_samples)
        n_samples = X.shape[0]
        y_pred_hues = np.zeros(n_samples)

        inv_var = 1.0 / self.noise_var  # (6,)

        for i in range(n_samples):
            obs = channel_responses[:, i]  # (6,)
            log_liks = np.zeros(360)
            for h in range(360):
                template = self.predict_basis[h] * self.scale
                diff = obs - template
                log_liks[h] = -0.5 * np.sum(diff**2 * inv_var)
            y_pred_hues[i] = np.argmax(log_liks)

        return y_pred_hues


class FE_RidgeRegressorDecoder:
    """ForwardEncoding + Ridge regression from channels to hue (sin/cos)"""

    def __init__(self, alpha=0, n_channels=6, ridge_alpha=1.0):
        self.alpha = alpha
        self.n_channels = n_channels
        self.ridge_alpha = ridge_alpha
        self.weights = None
        self.ridge_sin = None
        self.ridge_cos = None

    def fit(self, X, y_labels):
        unique_labels = np.sort(np.unique(y_labels))
        n_train_colors = len(unique_labels)
        n_voxels = X.shape[1]

        mean_patterns = np.zeros((n_train_colors, n_voxels))
        for i, label in enumerate(unique_labels):
            mask = y_labels == label
            mean_patterns[i] = X[mask].mean(axis=0)

        basis_full = create_basis_functions(n_channels=self.n_channels)
        train_hues = np.array([HUE_ANGLES[l] for l in unique_labels])
        train_basis = basis_full[train_hues]

        C = train_basis
        B = mean_patterns

        if self.alpha > 0:
            self.weights = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            self.weights = np.linalg.pinv(C) @ B

        # Train Ridge regressors from channel space to sin/cos of hue
        train_hues_rad = np.deg2rad([HUE_ANGLES[l] for l in unique_labels])
        channel_train = self.weights @ mean_patterns.T  # (6, n_train)
        X_ch = channel_train.T  # (n_train, 6)
        y_sin = np.sin(train_hues_rad)
        y_cos = np.cos(train_hues_rad)

        from sklearn.linear_model import Ridge
        self.ridge_sin = Ridge(alpha=self.ridge_alpha).fit(X_ch, y_sin)
        self.ridge_cos = Ridge(alpha=self.ridge_alpha).fit(X_ch, y_cos)

    def predict(self, X):
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        channel_responses = self.weights @ X.T  # (6, n_samples)
        X_ch = channel_responses.T  # (n_samples, 6)

        pred_sin = self.ridge_sin.predict(X_ch)
        pred_cos = self.ridge_cos.predict(X_ch)
        y_pred_hues = np.rad2deg(np.arctan2(pred_sin, pred_cos)) % 360

        return y_pred_hues


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

    # Models that take label inputs (0-7) rather than continuous hue
    uses_label = model_name in ['LDA', 'SVM', 'MLP', 'ForwardEncoding',
                                'HybridMLP', 'HybridSVR',
                                'HybridMLP_Ensemble', 'HybridSVR_Ensemble',
                                'FE_PopVec', 'FE_RidgeEnc', 'FE_GaussML', 'FE_RidgeReg',
                                'FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']
    # Models that output continuous hue angles (0-359°) directly
    outputs_continuous = model_name in ['ForwardEncoding', 'HybridMLP', 'HybridSVR',
                                        'HybridMLP_Ensemble', 'HybridSVR_Ensemble',
                                        'FE_PopVec', 'FE_RidgeEnc', 'FE_GaussML', 'FE_RidgeReg',
                                        'FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']
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
        if outputs_continuous:
            pred_hues = y_pred  # Already continuous hues (0-359°)
        elif uses_label:
            pred_hues = labels_to_hue(y_pred)  # Discrete labels → 8 hues
        else:
            pred_hues = y_pred  # Ridge/KernelRidge return continuous hue

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
    uses_label = model_name in ['LDA', 'SVM', 'MLP', 'ForwardEncoding',
                                'HybridMLP', 'HybridSVR',
                                'HybridMLP_Ensemble', 'HybridSVR_Ensemble',
                                'FE_PopVec', 'FE_RidgeEnc', 'FE_GaussML', 'FE_RidgeReg',
                                'FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']
    outputs_continuous = model_name in ['ForwardEncoding', 'HybridMLP', 'HybridSVR',
                                        'HybridMLP_Ensemble', 'HybridSVR_Ensemble',
                                        'FE_PopVec', 'FE_RidgeEnc', 'FE_GaussML', 'FE_RidgeReg',
                                        'FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']

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

            if outputs_continuous:
                pred_hues = y_pred
            elif uses_label:
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
        'ForwardEncoding': LOCOForwardEncodingDecoder,
        'HybridMLP': HybridDegreeMLPDecoder,
        'HybridSVR': HybridDegreeSVRDecoder,
        'HybridMLP_Ensemble': HybridMLP_Ensemble,
        'HybridSVR_Ensemble': HybridSVR_Ensemble,
        'FE_PopVec': FE_PopulationVectorDecoder,
        'FE_RidgeEnc': FE_RidgeEncodingDecoder,
        'FE_GaussML': FE_GaussianMLDecoder,
        'FE_RidgeReg': FE_RidgeRegressorDecoder,
        'FE_Ensemble': FE_EnsembleDecoder,
        'FE_EnsembleRidge': FE_EnsembleRidgeDecoder,
        'FE_EnsembleGaussML': FE_EnsembleGaussMLDecoder,
        # Sequential training models (one model, incremental updates)
        'FE_Sequential': ForwardEncodingSequential,
        'HybridMLP_Sequential': HybridMLPSequential,
        'HybridSVR_Sequential': HybridSVRSequential,
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
                        choices=['raw', 'procrustes', 'srm'])
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
