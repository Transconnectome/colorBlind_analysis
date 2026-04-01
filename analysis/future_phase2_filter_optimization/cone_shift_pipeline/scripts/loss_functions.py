#!/usr/bin/env python3
"""
loss_functions.py — Modular loss functions for cone-shift fitting.

Provides pluggable loss classes for the cone-shift pipeline:
  - DeltaRDM_V1V2_Equal: ΔRDM loss combining V1 + V2 with equal weights.

Each loss class implements:
  - compute(): evaluate loss at a given δθ
  - permutation_null(): exact 8! permutation test for statistical inference

Design:
  Loss functions operate in voxel space (no SRM), comparing:
    ΔRDM_sim(δ) = RDM(C(θ+δ)@W_HC) - RDM(C(θ)@W_HC)   [simulation]
    ΔRDM_obs    = RDM_CVD - RDM_HC_mean                   [observation]
  using configurable similarity metrics (cosine, pearson, spearman).
"""

import numpy as np
from abc import ABC, abstractmethod
from itertools import permutations
from scipy.spatial.distance import squareform
from scipy.stats import pearsonr, spearmanr

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from diagnostic_delta_rdm import (
    compute_delta_rdm_obs,
    compute_delta_rdm_sim,
    cosine_similarity,
    precompute_hc_W,
)


# ============================================================================
# Similarity metric dispatch
# ============================================================================

def _similarity(a, b, metric='cosine'):
    """Compute similarity between two vectors.

    Args:
        a, b: (n,) arrays
        metric: 'cosine', 'pearson', or 'spearman'

    Returns:
        similarity: float (higher = more similar)
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if metric == 'cosine':
        return cosine_similarity(a, b)
    elif metric == 'pearson':
        if np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        r, _ = pearsonr(a, b)
        return float(r) if np.isfinite(r) else 0.0
    elif metric == 'spearman':
        if np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        r, _ = spearmanr(a, b)
        return float(r) if np.isfinite(r) else 0.0
    else:
        raise ValueError(f'Unknown metric: {metric}')


# ============================================================================
# Abstract base class
# ============================================================================

class BaseLoss(ABC):
    """Abstract base for cone-shift loss functions."""

    name: str

    @abstractmethod
    def compute(self, C_shifted, C_baseline,
                hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts,
                **kwargs):
        """Evaluate loss at a given shift.

        Args:
            C_shifted: (8, K) shifted design matrix
            C_baseline: (8, K) original design matrix
            hc_W_dicts: dict {roi: {subj: (K, V_s)}} precomputed weights
            hc_amps_dicts: dict {roi: {subj: (6, 8, V_s)}} amplitudes
            delta_rdm_obs_dicts: dict {roi: (28,)} observed ΔRDM

        Returns:
            dict with 'combined', per-ROI losses, and 'metric'
        """

    @abstractmethod
    def permutation_null(self, C_shifted, C_baseline,
                         hc_W_dicts, hc_amps_dicts,
                         amp_cvd_dicts, hc_amps_dicts_raw,
                         baseline_combined=None):
        """Compute exact permutation null distribution.

        Returns:
            dict with 'observed', 'null_distribution', 'label_perm_p',
                 'baseline_improvement_p', 'null_size'
        """


# ============================================================================
# ΔRDM V1+V2 Equal-weight loss
# ============================================================================

class DeltaRDM_V1V2_Equal(BaseLoss):
    """ΔRDM loss combining V1 and V2 with equal weights.

    Loss = 0.5 * similarity(ΔRDM_sim_V1, ΔRDM_obs_V1)
         + 0.5 * similarity(ΔRDM_sim_V2, ΔRDM_obs_V2)

    Higher loss = better match (similarity-based, not error-based).
    """

    name = 'delta_rdm_v1v2_equal'
    rois = ['V1', 'V2']
    weights = {'V1': 0.5, 'V2': 0.5}

    def __init__(self, metric='cosine'):
        """
        Args:
            metric: 'cosine' (default), 'pearson', or 'spearman'
        """
        self.metric = metric

    def compute(self, C_shifted, C_baseline,
                hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts,
                **kwargs):
        """Evaluate combined V1+V2 ΔRDM similarity at a given shift.

        Returns:
            dict with 'combined', 'V1', 'V2', 'metric'
        """
        result = {'metric': self.metric}
        combined = 0.0

        for roi in self.rois:
            # Compute simulated ΔRDM for this ROI
            delta_sim, _ = compute_delta_rdm_sim(
                hc_W_dicts[roi], C_shifted, C_baseline,
                distance='correlation')

            # Compare with observed
            sim = _similarity(delta_sim, delta_rdm_obs_dicts[roi],
                              self.metric)
            result[roi] = float(sim)
            combined += self.weights[roi] * sim

        result['combined'] = float(combined)
        return result

    def permutation_null(self, C_shifted, C_baseline,
                         hc_W_dicts, hc_amps_dicts,
                         amp_cvd_dicts, hc_amps_dicts_raw,
                         baseline_combined=None):
        """Exact 8! permutation test with joint V1+V2 permutation.

        Permutes CVD color labels (rows/cols of RDM), applying the SAME
        permutation to both V1 and V2 simultaneously.

        Two p-values:
          1. label_perm_p: P(null_combined >= obs_combined)
          2. baseline_improvement_p: P(null_improvement >= obs_improvement)
             where improvement = combined - baseline_combined

        Args:
            C_shifted: (8, K) optimal shifted design matrix
            C_baseline: (8, K) original design matrix
            hc_W_dicts: dict {roi: {subj: (K, V_s)}}
            hc_amps_dicts: not used (kept for interface)
            amp_cvd_dicts: dict {roi: (6, 8, V_s)} CVD amplitudes
            hc_amps_dicts_raw: dict {roi: {subj: (6, 8, V_s)}}
            baseline_combined: float, combined loss at δ=0

        Returns:
            dict with permutation results
        """
        n_colors = 8

        # Compute simulated ΔRDM at optimal shift (fixed across perms)
        delta_sim = {}
        for roi in self.rois:
            ds, _ = compute_delta_rdm_sim(
                hc_W_dicts[roi], C_shifted, C_baseline,
                distance='correlation')
            delta_sim[roi] = ds

        # Compute observed (unpermuted) ΔRDM and loss
        delta_obs_unperm = {}
        for roi in self.rois:
            d_obs, _, _, _ = compute_delta_rdm_obs(
                amp_cvd_dicts[roi], hc_amps_dicts_raw[roi],
                distance='correlation')
            delta_obs_unperm[roi] = d_obs

        obs_per_roi = {}
        obs_combined = 0.0
        for roi in self.rois:
            s = _similarity(delta_sim[roi], delta_obs_unperm[roi],
                            self.metric)
            obs_per_roi[roi] = float(s)
            obs_combined += self.weights[roi] * s

        # Exact 8! permutations
        null_combined = []
        all_perms = list(permutations(range(n_colors)))

        for perm in all_perms:
            perm = list(perm)
            perm_combined = 0.0

            for roi in self.rois:
                # Permute ΔRDM_obs: reorder rows/cols of the RDM
                # ΔRDM is upper triangle of 8x8 matrix
                # Convert to square, permute, extract upper triangle
                rdm_obs_sq = squareform(delta_obs_unperm[roi])
                rdm_perm = rdm_obs_sq[np.ix_(perm, perm)]
                delta_obs_perm = rdm_perm[np.triu_indices(n_colors, k=1)]

                s = _similarity(delta_sim[roi], delta_obs_perm, self.metric)
                perm_combined += self.weights[roi] * s

            null_combined.append(perm_combined)

        null_combined = np.array(null_combined)

        # P-value 1: label permutation
        label_perm_p = float(
            (np.sum(null_combined >= obs_combined) + 1) /
            (len(null_combined) + 1)
        )

        # P-value 2: baseline improvement
        result = {
            'observed_combined': float(obs_combined),
            'observed_per_roi': obs_per_roi,
            'null_distribution_mean': float(np.mean(null_combined)),
            'null_distribution_std': float(np.std(null_combined)),
            'null_distribution_size': len(null_combined),
            'label_perm_p': label_perm_p,
        }

        if baseline_combined is not None:
            obs_improvement = obs_combined - baseline_combined
            null_improvement = null_combined - baseline_combined
            baseline_improvement_p = float(
                (np.sum(null_improvement >= obs_improvement) + 1) /
                (len(null_improvement) + 1)
            )
            result['baseline_combined'] = float(baseline_combined)
            result['improvement'] = float(obs_improvement)
            result['baseline_improvement_p'] = baseline_improvement_p

        return result
