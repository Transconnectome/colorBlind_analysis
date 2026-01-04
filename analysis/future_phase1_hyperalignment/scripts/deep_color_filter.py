#!/usr/bin/env python3
"""
Deep Learning Color Filter for CVD Simulation
==============================================

Learn a neural network filter that transforms HC color representations
into CVD color representations in the common hyperalignment space.

WHY HYPERALIGNMENT IS BETTER FOR DEEP LEARNING:
-----------------------------------------------
✅ Single unified coordinate system for all subjects
✅ Can pool all HC and CVD data together
✅ Simple loss: ||Filter(HC_common) - CVD_common||^2
✅ Generalizes to new CVD subjects via projection
✅ Interpretable: "distortion in canonical color space"

vs. Procrustes (pairwise):
❌ Different coordinate system for each HC-CVD pair
❌ Cannot pool data (incompatible coordinates)
❌ Need separate model for each pair
❌ No generalization to new subjects

Author: Automated
Date: 2025-12-18
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import json


# ========== Dataset ==========

class CommonSpaceDataset(Dataset):
    """
    Dataset of HC → CVD transformations in common space.

    Each sample is (HC_pattern, CVD_pattern, color_idx, cvd_type)
    All patterns are in the SAME coordinate system (common space).
    """

    def __init__(self, hc_data: np.ndarray, cvd_data_dict: Dict[str, np.ndarray],
                 cvd_types: Dict[str, str], n_runs: int = 6, n_colors: int = 8):
        """
        Args:
            hc_data: (T, p) - HC common space patterns
            cvd_data_dict: {cvd_id: (T, p) aligned CVD patterns}
            cvd_types: {cvd_id: 'deutan' or 'protan'}
            n_runs: Number of runs
            n_colors: Number of colors
        """
        self.n_runs = n_runs
        self.n_colors = n_colors
        self.p = hc_data.shape[1]

        # Reshape to (n_runs, n_colors, p)
        self.hc_patterns = hc_data.reshape(n_runs, n_colors, self.p)

        self.cvd_patterns = {}
        self.cvd_ids = []
        self.cvd_type_map = {}

        for cvd_id, cvd_data in cvd_data_dict.items():
            self.cvd_patterns[cvd_id] = cvd_data.reshape(n_runs, n_colors, self.p)
            self.cvd_ids.append(cvd_id)
            self.cvd_type_map[cvd_id] = cvd_types[cvd_id]

        # Create index: (cvd_idx, run_idx, color_idx)
        self.indices = []
        for cvd_idx, cvd_id in enumerate(self.cvd_ids):
            for run_idx in range(n_runs):
                for color_idx in range(n_colors):
                    self.indices.append((cvd_idx, run_idx, color_idx, cvd_id))

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        cvd_idx, run_idx, color_idx, cvd_id = self.indices[idx]

        # HC pattern for this color (same across all CVD)
        hc_pattern = self.hc_patterns[run_idx, color_idx, :]  # (p,)

        # CVD pattern for this color
        cvd_pattern = self.cvd_patterns[cvd_id][run_idx, color_idx, :]  # (p,)

        # CVD type encoding (deutan=0, protan=1)
        cvd_type = 0 if self.cvd_type_map[cvd_id] == 'deutan' else 1

        return {
            'hc': torch.FloatTensor(hc_pattern),
            'cvd': torch.FloatTensor(cvd_pattern),
            'color_idx': color_idx,
            'cvd_type': cvd_type,
            'cvd_id': cvd_id
        }


# ========== Neural Network Architectures ==========

class ColorFilterMLP(nn.Module):
    """
    Simple MLP filter: HC_common → CVD_common

    Architecture: p → 512 → 256 → 512 → p
    """

    def __init__(self, p: int, hidden_dims: List[int] = [512, 256, 512]):
        super().__init__()
        self.p = p

        layers = []
        in_dim = p
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.Dropout(0.2))
            in_dim = hidden_dim

        layers.append(nn.Linear(in_dim, p))  # Output layer

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        Args:
            x: (batch_size, p) - HC patterns in common space

        Returns:
            y: (batch_size, p) - Predicted CVD patterns in common space
        """
        return self.network(x)


class ColorFilterResidual(nn.Module):
    """
    Residual filter: predicts distortion Δ, output = input + Δ

    Hypothesis: CVD patterns are HC patterns + systematic distortion
    """

    def __init__(self, p: int, hidden_dims: List[int] = [512, 256, 512]):
        super().__init__()
        self.p = p

        layers = []
        in_dim = p
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.Dropout(0.2))
            in_dim = hidden_dim

        layers.append(nn.Linear(in_dim, p))  # Residual output

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        Args:
            x: (batch_size, p) - HC patterns

        Returns:
            y: (batch_size, p) - HC + predicted distortion
        """
        delta = self.network(x)
        return x + delta


class ColorFilterConditional(nn.Module):
    """
    Conditional filter: includes CVD type (deutan vs protan) as input.

    Input: [HC_pattern (p), cvd_type (1)] → CVD_pattern (p)
    """

    def __init__(self, p: int, hidden_dims: List[int] = [512, 256, 512]):
        super().__init__()
        self.p = p

        layers = []
        in_dim = p + 1  # +1 for CVD type
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.Dropout(0.2))
            in_dim = hidden_dim

        layers.append(nn.Linear(in_dim, p))

        self.network = nn.Sequential(*layers)

    def forward(self, x, cvd_type):
        """
        Args:
            x: (batch_size, p) - HC patterns
            cvd_type: (batch_size,) - CVD type (0=deutan, 1=protan)

        Returns:
            y: (batch_size, p) - Predicted CVD patterns
        """
        cvd_type = cvd_type.unsqueeze(1).float()  # (batch_size, 1)
        x_cond = torch.cat([x, cvd_type], dim=1)  # (batch_size, p+1)
        return self.network(x_cond)


# ========== Loss Functions ==========

class ColorFilterLoss(nn.Module):
    """
    Multi-component loss for color filter learning.

    Components:
    1. Reconstruction: ||predicted - target||^2
    2. Structure: preserve HC RDM structure in CVD space
    3. Smoothness: regularize filter complexity
    """

    def __init__(self, lambda_structure: float = 0.1, lambda_smooth: float = 0.01):
        super().__init__()
        self.lambda_structure = lambda_structure
        self.lambda_smooth = lambda_smooth
        self.mse = nn.MSELoss()

    def compute_rdm(self, patterns: torch.Tensor) -> torch.Tensor:
        """
        Compute pairwise correlation distances.

        Args:
            patterns: (batch_size, p)

        Returns:
            rdm: (batch_size, batch_size)
        """
        # Normalize
        patterns_norm = patterns - patterns.mean(dim=1, keepdim=True)
        patterns_norm = patterns_norm / (patterns_norm.std(dim=1, keepdim=True) + 1e-8)

        # Correlation matrix
        corr = torch.mm(patterns_norm, patterns_norm.t()) / patterns.shape[1]

        # Correlation distance
        rdm = 1 - corr

        return rdm

    def forward(self, predicted: torch.Tensor, target: torch.Tensor,
                hc_input: torch.Tensor) -> Tuple[torch.Tensor, Dict]:
        """
        Args:
            predicted: (batch_size, p) - model output
            target: (batch_size, p) - true CVD patterns
            hc_input: (batch_size, p) - HC input patterns

        Returns:
            loss: scalar
            loss_dict: breakdown of components
        """
        # 1. Reconstruction loss
        loss_recon = self.mse(predicted, target)

        # 2. Structure preservation (RDM similarity)
        # Encourage predicted CVD to maintain HC structure
        rdm_hc = self.compute_rdm(hc_input)
        rdm_pred = self.compute_rdm(predicted)
        loss_structure = self.mse(rdm_pred, rdm_hc)

        # 3. Smoothness (L2 regularization on output change)
        loss_smooth = torch.mean((predicted - hc_input)**2)

        # Total loss
        loss = loss_recon + \
               self.lambda_structure * loss_structure + \
               self.lambda_smooth * loss_smooth

        loss_dict = {
            'total': loss.item(),
            'recon': loss_recon.item(),
            'structure': loss_structure.item(),
            'smooth': loss_smooth.item()
        }

        return loss, loss_dict


# ========== Training ==========

class ColorFilterTrainer:
    """
    Trainer for color filter models.
    """

    def __init__(self, model: nn.Module, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        self.model = model.to(device)
        self.device = device
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_recon': [],
            'val_recon': []
        }

    def train(self, train_loader: DataLoader, val_loader: DataLoader,
              n_epochs: int = 100, lr: float = 1e-3,
              lambda_structure: float = 0.1, lambda_smooth: float = 0.01):
        """
        Train the color filter model.
        """
        criterion = ColorFilterLoss(lambda_structure, lambda_smooth)
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10, verbose=True
        )

        print(f"\n{'='*70}")
        print("Training Color Filter")
        print(f"{'='*70}")
        print(f"  Device: {self.device}")
        print(f"  Epochs: {n_epochs}")
        print(f"  Learning rate: {lr}")
        print(f"  Lambda structure: {lambda_structure}")
        print(f"  Lambda smooth: {lambda_smooth}")

        best_val_loss = float('inf')

        for epoch in range(n_epochs):
            # Training
            self.model.train()
            train_losses = []
            train_recons = []

            for batch in train_loader:
                hc = batch['hc'].to(self.device)
                cvd = batch['cvd'].to(self.device)

                optimizer.zero_grad()

                # Forward
                if isinstance(self.model, ColorFilterConditional):
                    cvd_type = batch['cvd_type'].to(self.device)
                    predicted = self.model(hc, cvd_type)
                else:
                    predicted = self.model(hc)

                # Loss
                loss, loss_dict = criterion(predicted, cvd, hc)

                # Backward
                loss.backward()
                optimizer.step()

                train_losses.append(loss_dict['total'])
                train_recons.append(loss_dict['recon'])

            # Validation
            self.model.eval()
            val_losses = []
            val_recons = []

            with torch.no_grad():
                for batch in val_loader:
                    hc = batch['hc'].to(self.device)
                    cvd = batch['cvd'].to(self.device)

                    if isinstance(self.model, ColorFilterConditional):
                        cvd_type = batch['cvd_type'].to(self.device)
                        predicted = self.model(hc, cvd_type)
                    else:
                        predicted = self.model(hc)

                    loss, loss_dict = criterion(predicted, cvd, hc)

                    val_losses.append(loss_dict['total'])
                    val_recons.append(loss_dict['recon'])

            # Metrics
            train_loss = np.mean(train_losses)
            val_loss = np.mean(val_losses)
            train_recon = np.mean(train_recons)
            val_recon = np.mean(val_recons)

            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_recon'].append(train_recon)
            self.history['val_recon'].append(val_recon)

            # Scheduler
            scheduler.step(val_loss)

            # Print
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"  Epoch {epoch+1:3d}: "
                      f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, "
                      f"val_recon={val_recon:.4f}")

            # Save best
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.best_epoch = epoch + 1
                self.best_state = self.model.state_dict().copy()

        print(f"\n✅ Training complete!")
        print(f"   Best validation loss: {best_val_loss:.4f} at epoch {self.best_epoch}")

        # Load best model
        self.model.load_state_dict(self.best_state)

    def plot_history(self, save_path: str = None):
        """Plot training history."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # Total loss
        axes[0].plot(self.history['train_loss'], label='Train', linewidth=2)
        axes[0].plot(self.history['val_loss'], label='Val', linewidth=2)
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Total Loss')
        axes[0].set_title('Training History: Total Loss')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Reconstruction loss
        axes[1].plot(self.history['train_recon'], label='Train', linewidth=2)
        axes[1].plot(self.history['val_recon'], label='Val', linewidth=2)
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Reconstruction Loss')
        axes[1].set_title('Training History: Reconstruction Loss')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   Saved: {save_path}")
        plt.close()

    def save_model(self, path: str):
        """Save model and training history."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'best_state_dict': self.best_state,
            'history': self.history,
            'best_epoch': self.best_epoch
        }, path)
        print(f"   Saved: {path}")


if __name__ == '__main__':
    print("Deep Color Filter Module")
    print("Use for learning CVD color transformations in common space")
