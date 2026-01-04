#!/usr/bin/env python3
"""
Hyperalignment Core Implementation
===================================

HC-only common space construction + CVD out-of-sample projection

Author: Automated
Date: 2025-12-18
"""

import numpy as np
from scipy.linalg import orthogonal_procrustes
from pathlib import Path
import glob
from typing import Dict, Tuple, List
import matplotlib.pyplot as plt
import seaborn as sns


class Hyperalignment:
    """
    Hyperalignment for fMRI color representation analysis.

    Constructs a shared representational space from HC subjects,
    then projects CVD subjects as out-of-sample alignment.
    """

    def __init__(self, n_iter: int = 10, regularization: float = 0.01):
        """
        Args:
            n_iter: Number of iterations for hyperalignment convergence
            regularization: Ridge regularization for rotation estimation
        """
        self.n_iter = n_iter
        self.regularization = regularization
        self.common_space = None
        self.R_hc = {}  # HC rotation matrices
        self.R_cvd = {}  # CVD rotation matrices
        self.convergence_history = []

    def regularized_procrustes(self, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
        """
        Orthogonal Procrustes with ridge regularization.

        Solves: min_R ||X @ R - Y||_F^2 subject to R.T @ R = I

        Args:
            X: (T, p) source matrix
            Y: (T, p) target matrix

        Returns:
            R: (p, p) orthogonal rotation matrix
        """
        # Cross-covariance with regularization
        M = X.T @ Y + self.regularization * np.eye(X.shape[1])

        # SVD
        U, s, Vt = np.linalg.svd(M, full_matrices=False)
        R = U @ Vt

        # Ensure proper rotation (det = +1)
        if np.linalg.det(R) < 0:
            U[:, -1] *= -1
            R = U @ Vt

        return R

    def fit(self, data_hc: Dict[str, np.ndarray], verbose: bool = True):
        """
        Construct HC-only common space via iterative alignment.

        Args:
            data_hc: {'sub-02': X_02, 'sub-03': X_03, ...}
                     Each X is (T, p) - run-level patterns
            verbose: Print convergence info

        Algorithm:
            1. Initialize common_space = first HC subject
            2. For n_iter iterations:
                a. Align each HC to current common_space
                b. Update common_space = mean of aligned HC
                c. Check convergence
        """
        subjects = list(data_hc.keys())
        n_subjects = len(subjects)
        T, p = data_hc[subjects[0]].shape

        if verbose:
            print(f"\n{'='*60}")
            print(f"HC-only Hyperalignment")
            print(f"{'='*60}")
            print(f"  HC subjects: {n_subjects}")
            print(f"  Data shape: T={T}, p={p}")
            print(f"  T/p ratio: {T/p:.2%}")
            print(f"  Regularization: {self.regularization}")
            print(f"  Iterations: {self.n_iter}")

        # Initialize with first subject
        self.common_space = data_hc[subjects[0]].copy()

        # Iterative alignment
        for iteration in range(self.n_iter):
            aligned_hc = []

            # Align each HC to common space
            for subj in subjects:
                X = data_hc[subj]
                R = self.regularized_procrustes(X, self.common_space)
                self.R_hc[subj] = R
                aligned_hc.append(X @ R)

            # Update common space (mean of aligned)
            new_common_space = np.mean(aligned_hc, axis=0)

            # Compute convergence (Frobenius norm change)
            change = np.linalg.norm(new_common_space - self.common_space, 'fro')
            self.convergence_history.append(change)
            self.common_space = new_common_space

            if verbose:
                print(f"  Iter {iteration+1:2d}: change = {change:.6f}")

            # Early stopping
            if change < 1e-6:
                if verbose:
                    print(f"  ✅ Converged at iteration {iteration+1}")
                break

        if verbose:
            print(f"\n✅ HC common space constructed!")
            print(f"   Shape: {self.common_space.shape}")

        return self

    def transform_cvd(self, data_cvd: Dict[str, np.ndarray],
                      verbose: bool = True) -> Dict[str, Dict]:
        """
        Project CVD subjects to HC common space (out-of-sample).

        Args:
            data_cvd: {'sub-08': X_08, 'sub-09': X_09, ...}
                      Each X is (T, p)
            verbose: Print projection info

        Returns:
            results: {subject_id: {
                'aligned': (T, p) aligned data,
                'rotation': (p, p) rotation matrix,
                'disparity': scalar - distance to common space
            }}
        """
        results = {}

        if verbose:
            print(f"\n{'='*60}")
            print(f"CVD Projection to HC Common Space")
            print(f"{'='*60}")

        for subj_id, X_cvd in data_cvd.items():
            # Find optimal rotation to common space
            R = self.regularized_procrustes(X_cvd, self.common_space)
            X_aligned = X_cvd @ R

            # Compute Procrustes disparity
            disparity = np.linalg.norm(self.common_space - X_aligned, 'fro') / \
                       np.linalg.norm(self.common_space, 'fro')

            results[subj_id] = {
                'aligned': X_aligned,
                'rotation': R,
                'disparity': disparity
            }
            self.R_cvd[subj_id] = R

            if verbose:
                print(f"  {subj_id}: disparity = {disparity:.4f}")

        if verbose:
            print(f"\n✅ CVD projection complete!")

        return results

    def plot_convergence(self, save_path: str = None):
        """Plot convergence history."""
        plt.figure(figsize=(8, 5))
        plt.plot(self.convergence_history, 'o-', linewidth=2)
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Change in Common Space (Frobenius)', fontsize=12)
        plt.title('Hyperalignment Convergence', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.yscale('log')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   Saved: {save_path}")
        plt.close()


class CommonSpaceAnalyzer:
    """
    Analyze patterns in the common representational space.
    """

    def __init__(self, common_space: np.ndarray, T: int = 48, n_colors: int = 8):
        """
        Args:
            common_space: (T, p) - HC common space from hyperalignment
            T: Number of observations (runs × colors)
            n_colors: Number of colors
        """
        self.common_space = common_space
        self.T = T
        self.n_colors = n_colors
        self.n_runs = T // n_colors
        self.p = common_space.shape[1]

    def get_color_patterns(self, data: np.ndarray = None) -> np.ndarray:
        """
        Average across runs to get color patterns.

        Args:
            data: (T, p) - if None, use common_space

        Returns:
            color_patterns: (n_colors, p)
        """
        if data is None:
            data = self.common_space

        # Reshape to (n_runs, n_colors, p)
        patterns = data.reshape(self.n_runs, self.n_colors, self.p)

        # Average across runs
        color_patterns = patterns.mean(axis=0)  # (n_colors, p)

        return color_patterns

    def compute_rdm(self, data: np.ndarray = None, metric: str = 'correlation') -> np.ndarray:
        """
        Compute Representational Dissimilarity Matrix (RDM).

        Args:
            data: (T, p) - if None, use common_space
            metric: 'correlation', 'euclidean', or 'cosine'

        Returns:
            rdm: (n_colors, n_colors) dissimilarity matrix
        """
        from scipy.spatial.distance import pdist, squareform

        color_patterns = self.get_color_patterns(data)
        rdm = squareform(pdist(color_patterns, metric=metric))

        return rdm

    def compute_color_disparities(self, X_hc: np.ndarray, X_cvd: np.ndarray) -> np.ndarray:
        """
        Compute per-color distortion between HC and CVD in common space.

        Args:
            X_hc: (T, p) - HC data in common space
            X_cvd: (T, p) - CVD data in common space (aligned)

        Returns:
            disparities: (n_colors,) - RMS distortion per color
        """
        hc_colors = self.get_color_patterns(X_hc)
        cvd_colors = self.get_color_patterns(X_cvd)

        # RMS per color
        disparities = np.sqrt(((hc_colors - cvd_colors)**2).mean(axis=1))

        return disparities

    def plot_rdm_comparison(self, rdm_hc: np.ndarray, rdm_cvd: np.ndarray,
                           cvd_id: str, save_path: str = None):
        """
        Plot HC vs CVD RDM comparison.

        Args:
            rdm_hc: (8, 8) - HC RDM in common space
            rdm_cvd: (8, 8) - CVD RDM in common space
            cvd_id: Subject ID for title
            save_path: Where to save figure
        """
        colors = ['Red', 'Orange', 'Yellow', 'Chartreuse',
                  'Green', 'Cyan', 'Blue', 'Magenta']

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # HC RDM
        im1 = axes[0].imshow(rdm_hc, cmap='hot', vmin=0, vmax=2)
        axes[0].set_title('HC Common Space', fontsize=12, fontweight='bold')
        axes[0].set_xticks(range(8))
        axes[0].set_yticks(range(8))
        axes[0].set_xticklabels(colors, rotation=45, ha='right')
        axes[0].set_yticklabels(colors)
        plt.colorbar(im1, ax=axes[0])

        # CVD RDM
        im2 = axes[1].imshow(rdm_cvd, cmap='hot', vmin=0, vmax=2)
        axes[1].set_title(f'{cvd_id} (Aligned)', fontsize=12, fontweight='bold')
        axes[1].set_xticks(range(8))
        axes[1].set_yticks(range(8))
        axes[1].set_xticklabels(colors, rotation=45, ha='right')
        axes[1].set_yticklabels(colors)
        plt.colorbar(im2, ax=axes[1])

        # Difference
        rdm_diff = rdm_cvd - rdm_hc
        vmax_diff = np.abs(rdm_diff).max()
        im3 = axes[2].imshow(rdm_diff, cmap='RdBu_r', vmin=-vmax_diff, vmax=vmax_diff)
        axes[2].set_title('Difference (CVD - HC)', fontsize=12, fontweight='bold')
        axes[2].set_xticks(range(8))
        axes[2].set_yticks(range(8))
        axes[2].set_xticklabels(colors, rotation=45, ha='right')
        axes[2].set_yticklabels(colors)
        plt.colorbar(im3, ax=axes[2])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   Saved: {save_path}")
        plt.close()

    def plot_color_distortions(self, disparities_dict: Dict[str, np.ndarray],
                               save_path: str = None):
        """
        Plot color-specific distortions for all CVD subjects.

        Args:
            disparities_dict: {cvd_id: disparities (8,)}
            save_path: Where to save figure
        """
        colors = ['Red', 'Orange', 'Yellow', 'Chartreuse',
                  'Green', 'Cyan', 'Blue', 'Magenta']

        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(len(colors))
        width = 0.25

        for i, (cvd_id, disparities) in enumerate(disparities_dict.items()):
            ax.bar(x + i*width, disparities, width, label=cvd_id)

        ax.set_xlabel('Color', fontsize=12)
        ax.set_ylabel('Distortion (RMS in Common Space)', fontsize=12)
        ax.set_title('Color-Specific Distortions: CVD vs HC Common Space',
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x + width)
        ax.set_xticklabels(colors, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   Saved: {save_path}")
        plt.close()


def load_amplitudes(subject_id: str, roi: str, dataset: str = 'deoblique_v2',
                   timestamp: str = 'baseline81_deob_determin') -> np.ndarray:
    """
    Load amplitudes_z.npy for a subject and ROI.

    Args:
        subject_id: '02', '03', etc.
        roi: 'V1', 'V2', 'V3', 'hV4'
        dataset: Dataset name
        timestamp: Analysis timestamp

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels)
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*' / 'amplitudes_z.npy')

    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No amplitudes_z.npy found for sub-{subject_id} {roi} in {base_path}")

    amp_path = Path(matches[0])

    amplitudes = np.load(amp_path)
    print(f"  Loaded sub-{subject_id} {roi}: {amplitudes.shape}")

    return amplitudes


if __name__ == '__main__':
    print("Hyperalignment Core Module")
    print("Import and use Hyperalignment and CommonSpaceAnalyzer classes")
