#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ml_forward_model.py
-------------------
Machine Learning / Deep Learning alternatives to B&H (2009) linear forward model

Implements multiple models:
1. Ridge Regression (baseline, similar to B&H but with regularization)
2. Multi-Layer Perceptron (MLP) - captures nonlinearity
3. CNN-based model - spatial structure awareness
4. Attention-based model - learns to weight important voxels
5. Ensemble - combines multiple models

All models use the same interface:
    model.fit(voxels, channels)  # voxels: (n_samples, n_voxels), channels: (n_samples, n_channels)
    channels_pred = model.predict(voxels)
"""

import numpy as np
import pickle
import os
import sys
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt


# ============================================================================
# Color Space Configuration
# ============================================================================

# Corrected Lab hue values for PILOT data
# These were computed from the actual RGB values in colorBlind_pilotTest.py
# NOT from the IRB document (which had incorrect values)
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.142053052572436,   # Cyan-ish (IRB incorrectly said 178.57°)
    'color_2': 287.979026187069735,   # Blue-purple (IRB incorrectly said 310.77°)
    'color_3': 305.226546308759566,   # Purple (IRB incorrectly said 316.10°)
    'color_4': 330.204721787408289,   # Pink (IRB incorrectly said 333.86°)
    'color_5': 35.269500805260478,    # Orange-red (IRB incorrectly said 54.50°)
    'color_6': 73.365061454288877,    # Yellow-orange (IRB incorrectly said 68.45°)
    'color_7': 125.585145639335096,   # Green-yellow (IRB incorrectly said 130.78°)
    'color_8': 143.909094545652778,   # Green (IRB incorrectly said 153.72°)
}

# MAIN experiment uses uniform 45° spacing (8 colors evenly distributed)
# Starting from 0° and going clockwise
LABEL2HUE_DEG_MAIN = {
    'color_1': 0.0,      # Red
    'color_2': 45.0,     # Orange
    'color_3': 90.0,     # Yellow
    'color_4': 135.0,    # Yellow-Green
    'color_5': 180.0,    # Cyan
    'color_6': 225.0,    # Blue
    'color_7': 270.0,    # Purple
    'color_8': 315.0,    # Magenta
}

# NOTE: Pilot data has non-uniform spacing (gaps from 18.3° to 105.8°)
# This makes reconstruction harder. Main experiment should perform better.


# ============================================================================
# PyTorch-based models (optional, requires torch)
# ============================================================================

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. Only Ridge regression will work.")
    sys.stdout.flush()


# ============================================================================
# Base Model Class
# ============================================================================

class ForwardModel:
    """Base class for forward encoding models"""

    def __init__(self, n_channels=6):
        self.n_channels = n_channels
        self.scaler = StandardScaler()

    def fit(self, voxels, channels):
        """
        Fit the forward model

        Parameters
        ----------
        voxels : ndarray (n_samples, n_voxels)
            Voxel responses
        channels : ndarray (n_samples, n_channels)
            Channel responses (ground truth)
        """
        raise NotImplementedError

    def predict(self, voxels):
        """
        Predict channel responses from voxels

        Parameters
        ----------
        voxels : ndarray (n_samples, n_voxels)
            Voxel responses

        Returns
        -------
        channels_pred : ndarray (n_samples, n_channels)
            Predicted channel responses
        """
        raise NotImplementedError

    def score(self, voxels, channels):
        """Compute R² score"""
        pred = self.predict(voxels)
        return r2_score(channels, pred)


# ============================================================================
# 1. Ridge Regression (Baseline)
# ============================================================================

class RidgeForwardModel(ForwardModel):
    """
    Ridge regression forward model (linear with L2 regularization)
    Similar to B&H but with regularization to prevent overfitting
    """

    def __init__(self, n_channels=6, alpha=1.0, fit_intercept=True):
        super().__init__(n_channels)
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.model = None

    def fit(self, voxels, channels):
        """Fit ridge regression"""
        # Normalize voxels
        voxels_norm = self.scaler.fit_transform(voxels)

        # Fit model
        self.model = Ridge(alpha=self.alpha, fit_intercept=self.fit_intercept)
        self.model.fit(voxels_norm, channels)

        return self

    def predict(self, voxels):
        """Predict channels"""
        voxels_norm = self.scaler.transform(voxels)
        return self.model.predict(voxels_norm)


class RidgeCVForwardModel(ForwardModel):
    """
    Ridge with automatic alpha selection via cross-validation
    """

    def __init__(self, n_channels=6, alphas=None, fit_intercept=True):
        super().__init__(n_channels)
        if alphas is None:
            alphas = np.logspace(-3, 3, 20)
        self.alphas = alphas
        self.fit_intercept = fit_intercept
        self.model = None

    def fit(self, voxels, channels):
        """Fit ridge regression with CV"""
        voxels_norm = self.scaler.fit_transform(voxels)

        self.model = RidgeCV(alphas=self.alphas, fit_intercept=self.fit_intercept)
        self.model.fit(voxels_norm, channels)

        print(f"  Best alpha: {self.model.alpha_:.4f}")
        sys.stdout.flush()
        return self

    def predict(self, voxels):
        """Predict channels"""
        voxels_norm = self.scaler.transform(voxels)
        return self.model.predict(voxels_norm)


# ============================================================================
# 2. Multi-Layer Perceptron (MLP)
# ============================================================================

if TORCH_AVAILABLE:
    class MLPForwardModel(ForwardModel):
        """
        Multi-layer perceptron for nonlinear voxel -> channel mapping
        """

        def __init__(self, n_channels=6, hidden_dims=[512, 256, 128],
                     dropout=0.3, lr=1e-3, epochs=100, batch_size=32,
                     device='cpu'):
            super().__init__(n_channels)
            self.hidden_dims = hidden_dims
            self.dropout = dropout
            self.lr = lr
            self.epochs = epochs
            self.batch_size = batch_size
            self.device = device
            self.model = None

        def _build_model(self, n_voxels):
            """Build MLP architecture"""
            layers = []

            # Input layer
            layers.append(nn.Linear(n_voxels, self.hidden_dims[0]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(self.dropout))

            # Hidden layers
            for i in range(len(self.hidden_dims) - 1):
                layers.append(nn.Linear(self.hidden_dims[i], self.hidden_dims[i+1]))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(self.dropout))

            # Output layer
            layers.append(nn.Linear(self.hidden_dims[-1], self.n_channels))

            return nn.Sequential(*layers)

        def fit(self, voxels, channels):
            """Train MLP"""
            # Normalize
            voxels_norm = self.scaler.fit_transform(voxels)

            # Build model
            n_voxels = voxels.shape[1]
            self.model = self._build_model(n_voxels).to(self.device)

            # Prepare data
            X = torch.FloatTensor(voxels_norm).to(self.device)
            y = torch.FloatTensor(channels).to(self.device)
            dataset = TensorDataset(X, y)
            loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

            # Train
            optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
            criterion = nn.MSELoss()

            self.model.train()
            for epoch in range(self.epochs):
                total_loss = 0
                for batch_X, batch_y in loader:
                    optimizer.zero_grad()
                    pred = self.model(batch_X)
                    loss = criterion(pred, batch_y)
                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()

                if (epoch + 1) % 20 == 0:
                    print(f"  Epoch {epoch+1}/{self.epochs}, Loss: {total_loss/len(loader):.4f}")
                    sys.stdout.flush()

            return self

        def predict(self, voxels):
            """Predict channels"""
            voxels_norm = self.scaler.transform(voxels)
            X = torch.FloatTensor(voxels_norm).to(self.device)

            self.model.eval()
            with torch.no_grad():
                pred = self.model(X)

            return pred.cpu().numpy()


# ============================================================================
# 3. CNN-based Model (Spatial Structure Awareness)
# ============================================================================

if TORCH_AVAILABLE:
    class CNNForwardModel(ForwardModel):
        """
        CNN-based model that treats voxels with spatial structure
        Note: Requires voxel positions or 3D reshaping
        For now, uses 1D convolutions on sorted voxels
        """

        def __init__(self, n_channels=6, conv_channels=[64, 128, 256],
                     kernel_size=5, lr=1e-3, epochs=100, batch_size=32,
                     device='cpu'):
            super().__init__(n_channels)
            self.conv_channels = conv_channels
            self.kernel_size = kernel_size
            self.lr = lr
            self.epochs = epochs
            self.batch_size = batch_size
            self.device = device
            self.model = None

        def _build_model(self, n_voxels):
            """Build 1D CNN architecture"""

            class CNN1D(nn.Module):
                def __init__(self, n_voxels, conv_channels, kernel_size, n_channels):
                    super().__init__()

                    # Conv layers
                    layers = []
                    in_ch = 1
                    for out_ch in conv_channels:
                        layers.append(nn.Conv1d(in_ch, out_ch, kernel_size, padding=kernel_size//2))
                        layers.append(nn.ReLU())
                        layers.append(nn.MaxPool1d(2))
                        in_ch = out_ch

                    self.conv = nn.Sequential(*layers)

                    # Calculate size after convolutions
                    self.pool_factor = 2 ** len(conv_channels)
                    fc_input_size = (n_voxels // self.pool_factor) * conv_channels[-1]

                    # FC layers
                    self.fc = nn.Sequential(
                        nn.Flatten(),
                        nn.Linear(fc_input_size, 256),
                        nn.ReLU(),
                        nn.Dropout(0.3),
                        nn.Linear(256, n_channels)
                    )

                def forward(self, x):
                    # x: (batch, n_voxels) -> (batch, 1, n_voxels)
                    x = x.unsqueeze(1)
                    x = self.conv(x)
                    x = self.fc(x)
                    return x

            return CNN1D(n_voxels, self.conv_channels, self.kernel_size, self.n_channels)

        def fit(self, voxels, channels):
            """Train CNN"""
            voxels_norm = self.scaler.fit_transform(voxels)

            n_voxels = voxels.shape[1]
            self.model = self._build_model(n_voxels).to(self.device)

            X = torch.FloatTensor(voxels_norm).to(self.device)
            y = torch.FloatTensor(channels).to(self.device)
            dataset = TensorDataset(X, y)
            loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

            optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
            criterion = nn.MSELoss()

            self.model.train()
            for epoch in range(self.epochs):
                total_loss = 0
                for batch_X, batch_y in loader:
                    optimizer.zero_grad()
                    pred = self.model(batch_X)
                    loss = criterion(pred, batch_y)
                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()

                if (epoch + 1) % 20 == 0:
                    print(f"  Epoch {epoch+1}/{self.epochs}, Loss: {total_loss/len(loader):.4f}")
                    sys.stdout.flush()

            return self

        def predict(self, voxels):
            """Predict channels"""
            voxels_norm = self.scaler.transform(voxels)
            X = torch.FloatTensor(voxels_norm).to(self.device)

            self.model.eval()
            with torch.no_grad():
                pred = self.model(X)

            return pred.cpu().numpy()


# ============================================================================
# 4. Attention-based Model
# ============================================================================

if TORCH_AVAILABLE:
    class AttentionForwardModel(ForwardModel):
        """
        Attention-based model that learns to weight important voxels
        """

        def __init__(self, n_channels=6, n_heads=8, hidden_dim=256,
                     lr=1e-3, epochs=100, batch_size=32, device='cpu'):
            super().__init__(n_channels)
            self.n_heads = n_heads
            self.hidden_dim = hidden_dim
            self.lr = lr
            self.epochs = epochs
            self.batch_size = batch_size
            self.device = device
            self.model = None

        def _build_model(self, n_voxels):
            """Build attention-based architecture"""

            class AttentionModel(nn.Module):
                def __init__(self, n_voxels, hidden_dim, n_heads, n_channels):
                    super().__init__()

                    # Project voxels to hidden dimension
                    self.input_proj = nn.Linear(n_voxels, hidden_dim)

                    # Multi-head attention
                    self.attention = nn.MultiheadAttention(
                        embed_dim=hidden_dim,
                        num_heads=n_heads,
                        batch_first=True
                    )

                    # Feed-forward network
                    self.ff = nn.Sequential(
                        nn.Linear(hidden_dim, hidden_dim * 2),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(hidden_dim * 2, hidden_dim)
                    )

                    # Output layer
                    self.output = nn.Linear(hidden_dim, n_channels)

                    # Layer norm
                    self.ln1 = nn.LayerNorm(hidden_dim)
                    self.ln2 = nn.LayerNorm(hidden_dim)

                def forward(self, x):
                    # x: (batch, n_voxels)
                    x = self.input_proj(x).unsqueeze(1)  # (batch, 1, hidden_dim)

                    # Self-attention
                    attn_out, _ = self.attention(x, x, x)
                    x = self.ln1(x + attn_out)

                    # Feed-forward
                    ff_out = self.ff(x)
                    x = self.ln2(x + ff_out)

                    # Output
                    x = x.squeeze(1)  # (batch, hidden_dim)
                    return self.output(x)

            return AttentionModel(n_voxels, self.hidden_dim, self.n_heads, self.n_channels)

        def fit(self, voxels, channels):
            """Train attention model"""
            voxels_norm = self.scaler.fit_transform(voxels)

            n_voxels = voxels.shape[1]
            self.model = self._build_model(n_voxels).to(self.device)

            X = torch.FloatTensor(voxels_norm).to(self.device)
            y = torch.FloatTensor(channels).to(self.device)
            dataset = TensorDataset(X, y)
            loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

            optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
            criterion = nn.MSELoss()

            self.model.train()
            for epoch in range(self.epochs):
                total_loss = 0
                for batch_X, batch_y in loader:
                    optimizer.zero_grad()
                    pred = self.model(batch_X)
                    loss = criterion(pred, batch_y)
                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()

                if (epoch + 1) % 20 == 0:
                    print(f"  Epoch {epoch+1}/{self.epochs}, Loss: {total_loss/len(loader):.4f}")
                    sys.stdout.flush()

            return self

        def predict(self, voxels):
            """Predict channels"""
            voxels_norm = self.scaler.transform(voxels)
            X = torch.FloatTensor(voxels_norm).to(self.device)

            self.model.eval()
            with torch.no_grad():
                pred = self.model(X)

            return pred.cpu().numpy()


# ============================================================================
# 5. Ensemble Model
# ============================================================================

class EnsembleForwardModel(ForwardModel):
    """
    Ensemble of multiple models - combines predictions
    """

    def __init__(self, models, weights=None):
        """
        Parameters
        ----------
        models : list of ForwardModel
            List of fitted models
        weights : array-like, optional
            Weights for each model (default: equal weights)
        """
        super().__init__(models[0].n_channels)
        self.models = models

        if weights is None:
            weights = np.ones(len(models)) / len(models)
        self.weights = np.array(weights)

    def fit(self, voxels, channels):
        """Fit all models in ensemble"""
        for i, model in enumerate(self.models):
            print(f"\nTraining model {i+1}/{len(self.models)}: {model.__class__.__name__}")
            sys.stdout.flush()
            model.fit(voxels, channels)
        return self

    def predict(self, voxels):
        """Predict using weighted average"""
        preds = np.stack([model.predict(voxels) for model in self.models])
        return np.average(preds, axis=0, weights=self.weights)


# ============================================================================
# Evaluation and Comparison
# ============================================================================

def evaluate_forward_model(model, voxels_train, channels_train,
                          voxels_test, channels_test):
    """
    Evaluate a forward model

    Returns
    -------
    metrics : dict
        Dictionary with evaluation metrics
    """
    # Fit
    model.fit(voxels_train, channels_train)

    # Predict
    pred_test = model.predict(voxels_test)
    pred_train = model.predict(voxels_train)

    # Metrics
    metrics = {
        'r2_train': r2_score(channels_train, pred_train),
        'r2_test': r2_score(channels_test, pred_test),
        'mse_train': mean_squared_error(channels_train, pred_train),
        'mse_test': mean_squared_error(channels_test, pred_test),
        'pred_test': pred_test,
        'pred_train': pred_train
    }

    return metrics


def leave_one_run_out_cv(model_class, voxels, channels, n_runs,
                         model_kwargs=None, verbose=True):
    """
    Leave-one-run-out cross-validation

    Parameters
    ----------
    model_class : class
        Model class (e.g., MLPForwardModel)
    voxels : ndarray (n_total_samples, n_voxels)
        All voxel responses (stacked across runs)
    channels : ndarray (n_total_samples, n_channels)
        All channel responses
    n_runs : int
        Number of runs
    model_kwargs : dict, optional
        Keyword arguments for model initialization

    Returns
    -------
    results : dict
        Cross-validation results
    """
    if model_kwargs is None:
        model_kwargs = {}

    n_samples_per_run = len(voxels) // n_runs

    all_preds = []
    all_true = []
    all_r2 = []

    for test_run in range(n_runs):
        if verbose:
            print(f"\nCV Fold {test_run+1}/{n_runs} (test run: {test_run+1})")
            sys.stdout.flush()

        # Split data
        test_idx = slice(test_run * n_samples_per_run,
                        (test_run + 1) * n_samples_per_run)
        train_idx = np.concatenate([
            np.arange(0, test_run * n_samples_per_run),
            np.arange((test_run + 1) * n_samples_per_run, len(voxels))
        ])

        voxels_train = voxels[train_idx]
        voxels_test = voxels[test_idx]
        channels_train = channels[train_idx]
        channels_test = channels[test_idx]

        # Train and evaluate
        model = model_class(**model_kwargs)
        metrics = evaluate_forward_model(
            model, voxels_train, channels_train,
            voxels_test, channels_test
        )

        all_preds.append(metrics['pred_test'])
        all_true.append(channels_test)
        all_r2.append(metrics['r2_test'])

        if verbose:
            print(f"  R² (test): {metrics['r2_test']:.4f}")
            sys.stdout.flush()

    # Aggregate results
    results = {
        'predictions': np.vstack(all_preds),
        'ground_truth': np.vstack(all_true),
        'r2_per_fold': all_r2,
        'mean_r2': np.mean(all_r2),
        'std_r2': np.std(all_r2)
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"Mean R² across folds: {results['mean_r2']:.4f} ± {results['std_r2']:.4f}")
        sys.stdout.flush()

    return results


def compare_models(models_dict, voxels, channels, n_runs):
    """
    Compare multiple models using LOOCV

    Parameters
    ----------
    models_dict : dict
        Dictionary mapping model names to (model_class, model_kwargs)
    voxels, channels : ndarray
        Data
    n_runs : int
        Number of runs

    Returns
    -------
    comparison : dict
        Comparison results
    """
    results = {}

    for name, (model_class, kwargs) in models_dict.items():
        print(f"\n{'='*60}")
        print(f"Evaluating: {name}")
        print(f"{'='*60}")
        sys.stdout.flush()

        results[name] = leave_one_run_out_cv(
            model_class, voxels, channels, n_runs,
            model_kwargs=kwargs, verbose=True
        )

    # Summary comparison
    print(f"\n{'='*60}")
    print("SUMMARY COMPARISON")
    print(f"{'='*60}")
    print(f"{'Model':<30} {'Mean R²':<15} {'Std R²':<15}")
    print("-" * 60)
    sys.stdout.flush()

    for name, result in results.items():
        print(f"{name:<30} {result['mean_r2']:<15.4f} {result['std_r2']:<15.4f}")

    sys.stdout.flush()
    return results


# ============================================================================
# Visualization
# ============================================================================

def plot_model_comparison(comparison_results, save_path=None):
    """Plot comparison of different models"""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # R² comparison
    names = list(comparison_results.keys())
    r2_means = [comparison_results[name]['mean_r2'] for name in names]
    r2_stds = [comparison_results[name]['std_r2'] for name in names]

    axes[0].bar(range(len(names)), r2_means, yerr=r2_stds, capsize=5)
    axes[0].set_xticks(range(len(names)))
    axes[0].set_xticklabels(names, rotation=45, ha='right')
    axes[0].set_ylabel('R² Score')
    axes[0].set_title('Model Comparison (Leave-One-Run-Out CV)')
    axes[0].grid(axis='y', alpha=0.3)

    # Prediction scatter for best model
    best_name = max(names, key=lambda n: comparison_results[n]['mean_r2'])
    best_result = comparison_results[best_name]

    pred = best_result['predictions'].ravel()
    true = best_result['ground_truth'].ravel()

    axes[1].scatter(true, pred, alpha=0.3, s=10)
    axes[1].plot([true.min(), true.max()], [true.min(), true.max()],
                 'r--', label='Perfect prediction')
    axes[1].set_xlabel('True Channel Response')
    axes[1].set_ylabel('Predicted Channel Response')
    axes[1].set_title(f'Best Model: {best_name}\nR² = {best_result["mean_r2"]:.4f}')
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved comparison plot: {save_path}")
        sys.stdout.flush()

    return fig


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == '__main__':
    print("ML/DL Forward Model Implementations")
    print("=" * 60)
    sys.stdout.flush()

    # Simulate data
    np.random.seed(42)
    n_runs = 6
    n_colors = 8
    n_voxels = 1000
    n_channels = 6

    # Generate synthetic data
    n_samples = n_runs * n_colors
    voxels = np.random.randn(n_samples, n_voxels)
    channels = np.random.randn(n_samples, n_channels)

    # Define models to compare
    models_to_test = {
        'Ridge (alpha=1.0)': (RidgeForwardModel, {'alpha': 1.0}),
        'Ridge (CV)': (RidgeCVForwardModel, {'alphas': np.logspace(-3, 3, 10)}),
    }

    if TORCH_AVAILABLE:
        models_to_test.update({
            'MLP': (MLPForwardModel, {
                'hidden_dims': [256, 128],
                'epochs': 50,
                'lr': 1e-3
            }),
            'Attention': (AttentionForwardModel, {
                'hidden_dim': 128,
                'n_heads': 4,
                'epochs': 50,
                'lr': 1e-3
            }),
        })

    # Compare models
    results = compare_models(models_to_test, voxels, channels, n_runs)

    # Plot
    plot_model_comparison(results, save_path='model_comparison.png')

    print("\nDone!")
