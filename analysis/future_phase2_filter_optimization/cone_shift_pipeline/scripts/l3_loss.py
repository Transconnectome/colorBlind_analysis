#!/usr/bin/env python3
"""
l3_loss.py — L₃ joint V1+V2 cone-shift loss (Gen-4, Machado-anchored).

Loss structure (maximised):
    L₃(Δλ_V1, Δλ_V2) = L₁ − λ_scale · L_scale − λ_ROI · L_ROI

where
    L₁_ROI(Δλ)  = similarity(ΔRDM_sim(Δλ), ΔRDM_obs)   ∈ [-1, 1]
    L₁          = 0.5 · L₁_V1 + 0.5 · L₁_V2
    L_scale     = [max(0, |Δλ_V1|−Δλ_max)]² + [max(0, |Δλ_V2|−Δλ_max)]²
    L_ROI       = (Δλ_V1 − Δλ_V2)² / 2
    Δλ_max      = 20 nm (Machado physiological ceiling)

Defaults: λ_scale = 0.01, λ_ROI = 0.005, similarity = 'cosine'.

Permutation null:
    Exact 8! joint label permutation of ΔRDM_obs (rows/cols of the 8×8 RDM),
    with the SAME permutation applied to V1 and V2 simultaneously. L_scale
    and L_ROI do not depend on the label permutation so they are kept fixed
    at their observed values.

Two p-values are produced:
    label_perm_p            — P(null L₃ ≥ observed L₃)
    baseline_improvement_p  — P(null (L₃−L₃_baseline) ≥ observed improvement)
                              with L₃_baseline evaluated at Δλ=0 for both ROIs.

This module reuses diagnostic_delta_rdm helpers:
    compute_delta_rdm_sim, compute_delta_rdm_obs, cosine_similarity
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from itertools import permutations
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from scipy.spatial.distance import squareform
from scipy.stats import pearsonr, spearmanr

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_obs,
    compute_delta_rdm_sim,
    cosine_similarity,
)
from utils_distortion_models import get_design_matrix  # noqa: E402

# ============================================================================
# Similarity dispatch
# ============================================================================


def _similarity(a: np.ndarray, b: np.ndarray, metric: str = 'cosine') -> float:
    """Compute similarity between two vectors. Higher = more similar."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if metric == 'cosine':
        return cosine_similarity(a, b)
    if metric == 'pearson':
        if np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        r, _ = pearsonr(a, b)
        return float(r) if np.isfinite(r) else 0.0
    if metric == 'spearman':
        if np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        r, _ = spearmanr(a, b)
        return float(r) if np.isfinite(r) else 0.0
    raise ValueError(f'Unknown metric: {metric}')


# ============================================================================
# Abstract base class
# ============================================================================


class BaseLoss(ABC):
    """Abstract base for cone-shift loss functions (Gen-4)."""

    name: str = 'base'

    @abstractmethod
    def compute(self, *args, **kwargs) -> dict:
        """Evaluate loss at a single parameterisation."""

    @abstractmethod
    def permutation_null(self, *args, **kwargs) -> dict:
        """Compute the joint V1+V2 exact permutation null."""


# ============================================================================
# L₃ Machado V1+V2 loss (Gen-4 primary)
# ============================================================================


class L3_MachadoV1V2(BaseLoss):
    """Gen-4 loss: ΔRDM similarity for V1+V2 with scale & ROI regularisers.

    Designed to be evaluated on a 2-D (Δλ_V1, Δλ_V2) grid during
    step2_finetune_l3.

    Attributes:
        lam_scale:        weight on L_scale (physiological hinge)
        lam_roi:          weight on L_ROI (cross-ROI consistency)
        delta_lambda_max: Δλ hinge threshold in nm (default 20)
        metric:           similarity metric for L₁ ('cosine' default)
    """

    name = 'l3_machado_v1v2'
    rois = ('V1', 'V2')
    weights = {'V1': 0.5, 'V2': 0.5}

    def __init__(self,
                 lam_scale: float = 0.01,
                 lam_roi: float = 0.005,
                 delta_lambda_max: float = 20.0,
                 metric: str = 'cosine',
                 model_name: str = 'machado_1way',
                 fixed_alphas: Optional[Dict[str, float]] = None):
        self.lam_scale = float(lam_scale)
        self.lam_roi = float(lam_roi)
        self.delta_lambda_max = float(delta_lambda_max)
        self.metric = metric
        self.model_name = model_name
        # For machado_alpha_free: α is frozen per-ROI at Stage-1 anchor while
        # Stage-2 sweeps only Δλ jointly. Ignored for machado_1way.
        self.fixed_alphas: Dict[str, float] = dict(fixed_alphas or {})

    def set_fixed_alphas(self, alphas: Dict[str, float]) -> None:
        """Update the frozen α per ROI (used before each subject in Stage 2)."""
        self.fixed_alphas = dict(alphas or {})

    # ------------------------------------------------------------------
    # Regularisers
    # ------------------------------------------------------------------

    def l_scale(self, delta_v1: float, delta_v2: float) -> float:
        """Physiological hinge at |Δλ| = Δλ_max."""
        s1 = max(0.0, abs(delta_v1) - self.delta_lambda_max) ** 2
        s2 = max(0.0, abs(delta_v2) - self.delta_lambda_max) ** 2
        return float(s1 + s2)

    def l_roi(self, delta_v1: float, delta_v2: float) -> float:
        """Cross-ROI consistency: (Δλ_V1 − Δλ_V2)² / 2."""
        return float(0.5 * (delta_v1 - delta_v2) ** 2)

    # ------------------------------------------------------------------
    # Δ-design-matrix helpers
    # ------------------------------------------------------------------

    def _design_matrix(self, delta_lambda: float, cvd_type: str,
                       roi: Optional[str] = None) -> np.ndarray:
        """Build C(θ+δθ) for the given Δλ via the registered Machado model.

        For ``machado_alpha_free`` the α hyper-parameter is frozen at the
        Stage-1 per-ROI anchor (via ``fixed_alphas``) while Stage-2 sweeps
        only Δλ jointly across (V1, V2).
        """
        if self.model_name == 'machado_alpha_free':
            alpha = float(self.fixed_alphas.get(roi, 1.0))
            return get_design_matrix(
                self.model_name,
                [float(delta_lambda), alpha],
                cvd_type=cvd_type)
        return get_design_matrix(self.model_name, [float(delta_lambda)],
                                 cvd_type=cvd_type)

    def _l1_per_roi(self,
                    delta_lambda: float,
                    cvd_type: str,
                    hc_W_roi: Dict[str, np.ndarray],
                    C_baseline: np.ndarray,
                    delta_rdm_obs_roi: np.ndarray,
                    roi: Optional[str] = None) -> float:
        """L₁ for a single ROI at a given Δλ."""
        C_shifted = self._design_matrix(delta_lambda, cvd_type, roi=roi)
        delta_sim, _ = compute_delta_rdm_sim(
            hc_W_roi, C_shifted, C_baseline, distance='correlation')
        return float(_similarity(delta_sim, delta_rdm_obs_roi, self.metric))

    # ------------------------------------------------------------------
    # Core compute
    # ------------------------------------------------------------------

    def compute(self,
                delta_lambda_v1: float,
                delta_lambda_v2: float,
                cvd_type: str,
                hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                C_baseline: np.ndarray,
                delta_rdm_obs_dicts: Dict[str, np.ndarray],
                **kwargs) -> dict:
        """Evaluate L₃ at a single (Δλ_V1, Δλ_V2) point.

        Args:
            delta_lambda_v1, delta_lambda_v2: candidate shifts (nm)
            cvd_type: 'protan', 'deutan', or 'normal'
            hc_W_dicts: {ROI: {HC_subj: (K, V_s)}} precomputed weights
            C_baseline: (8, K) baseline design matrix
            delta_rdm_obs_dicts: {ROI: (28,)} observed ΔRDM vectors

        Returns:
            dict with L₃ components.
        """
        l1_v1 = self._l1_per_roi(delta_lambda_v1, cvd_type,
                                 hc_W_dicts['V1'], C_baseline,
                                 delta_rdm_obs_dicts['V1'], roi='V1')
        l1_v2 = self._l1_per_roi(delta_lambda_v2, cvd_type,
                                 hc_W_dicts['V2'], C_baseline,
                                 delta_rdm_obs_dicts['V2'], roi='V2')
        l1 = (self.weights['V1'] * l1_v1
              + self.weights['V2'] * l1_v2)

        l_scale = self.l_scale(delta_lambda_v1, delta_lambda_v2)
        l_roi = self.l_roi(delta_lambda_v1, delta_lambda_v2)
        l3 = l1 - self.lam_scale * l_scale - self.lam_roi * l_roi

        return {
            'l3': float(l3),
            'l1': float(l1),
            'l1_V1': float(l1_v1),
            'l1_V2': float(l1_v2),
            'l_scale': float(l_scale),
            'l_roi': float(l_roi),
            'delta_v1': float(delta_lambda_v1),
            'delta_v2': float(delta_lambda_v2),
            'delta_bar': float(0.5 * (delta_lambda_v1 + delta_lambda_v2)),
            'lam_scale': self.lam_scale,
            'lam_roi': self.lam_roi,
            'metric': self.metric,
            'delta_lambda_max': self.delta_lambda_max,
        }

    # ------------------------------------------------------------------
    # Permutation null
    # ------------------------------------------------------------------

    def permutation_null(self,
                         best_delta_v1: float,
                         best_delta_v2: float,
                         cvd_type: str,
                         hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                         C_baseline: np.ndarray,
                         delta_rdm_obs_dicts: Dict[str, np.ndarray],
                         baseline_l3: Optional[float] = None,
                         **kwargs) -> dict:
        """Exact 8! joint V1+V2 permutation of ΔRDM_obs labels.

        L_scale and L_ROI are NOT permutation-dependent, so they remain at the
        observed values across the null. This means we permute only L₁ and then
        add the (fixed) regulariser contributions to obtain the null L₃.

        Args:
            best_delta_v1, best_delta_v2: fitted Δλ (argmax L₃)
            cvd_type: 'protan' / 'deutan' / 'normal'
            hc_W_dicts: {ROI: {HC_subj: (K, V_s)}}
            C_baseline: (8, K) baseline design matrix
            delta_rdm_obs_dicts: {ROI: (28,)} observed ΔRDM
            baseline_l3: L₃ at Δλ=0 for both ROIs (for improvement p-value)

        Returns:
            dict with observed L₃, null distribution stats, and both p-values.
        """
        n_colors = 8

        # Simulated ΔRDMs at fitted shift (frozen across permutations)
        delta_sim_v1, _ = compute_delta_rdm_sim(
            hc_W_dicts['V1'],
            self._design_matrix(best_delta_v1, cvd_type, roi='V1'),
            C_baseline,
            distance='correlation')
        delta_sim_v2, _ = compute_delta_rdm_sim(
            hc_W_dicts['V2'],
            self._design_matrix(best_delta_v2, cvd_type, roi='V2'),
            C_baseline,
            distance='correlation')

        obs_v1 = delta_rdm_obs_dicts['V1']
        obs_v2 = delta_rdm_obs_dicts['V2']

        # Unpermuted L₁
        obs_l1_v1 = _similarity(delta_sim_v1, obs_v1, self.metric)
        obs_l1_v2 = _similarity(delta_sim_v2, obs_v2, self.metric)
        obs_l1 = (self.weights['V1'] * obs_l1_v1
                  + self.weights['V2'] * obs_l1_v2)

        # Regulariser constants (L_scale / L_ROI do not depend on permutation)
        l_scale_const = self.l_scale(best_delta_v1, best_delta_v2)
        l_roi_const = self.l_roi(best_delta_v1, best_delta_v2)
        reg_penalty = (self.lam_scale * l_scale_const
                       + self.lam_roi * l_roi_const)

        obs_l3 = obs_l1 - reg_penalty

        # Exact 8! permutations
        square_v1 = squareform(obs_v1)
        square_v2 = squareform(obs_v2)

        null_l1 = np.empty(np.math.factorial(n_colors), dtype=float)
        idx_tri = np.triu_indices(n_colors, k=1)

        for i, perm in enumerate(permutations(range(n_colors))):
            perm = list(perm)
            v1_perm = square_v1[np.ix_(perm, perm)][idx_tri]
            v2_perm = square_v2[np.ix_(perm, perm)][idx_tri]
            s1 = _similarity(delta_sim_v1, v1_perm, self.metric)
            s2 = _similarity(delta_sim_v2, v2_perm, self.metric)
            null_l1[i] = self.weights['V1'] * s1 + self.weights['V2'] * s2

        null_l3 = null_l1 - reg_penalty

        # p-value 1: label permutation on L₃ directly
        label_perm_p = float(
            (np.sum(null_l3 >= obs_l3) + 1) / (len(null_l3) + 1)
        )

        result = {
            'observed_l3': float(obs_l3),
            'observed_l1': float(obs_l1),
            'observed_l1_V1': float(obs_l1_v1),
            'observed_l1_V2': float(obs_l1_v2),
            'l_scale_const': float(l_scale_const),
            'l_roi_const': float(l_roi_const),
            'reg_penalty': float(reg_penalty),
            'null_l3_mean': float(np.mean(null_l3)),
            'null_l3_std': float(np.std(null_l3)),
            'null_l3_size': int(null_l3.size),
            'label_perm_p': label_perm_p,
        }

        # p-value 2: improvement over Δλ = 0 baseline
        if baseline_l3 is not None:
            obs_improvement = obs_l3 - float(baseline_l3)
            null_improvement = null_l3 - float(baseline_l3)
            baseline_improvement_p = float(
                (np.sum(null_improvement >= obs_improvement) + 1)
                / (len(null_improvement) + 1)
            )
            result['baseline_l3'] = float(baseline_l3)
            result['observed_improvement'] = float(obs_improvement)
            result['baseline_improvement_p'] = baseline_improvement_p

        return result


# ============================================================================
# Convenience: compute L₃ at baseline (Δλ = 0) for both ROIs
# ============================================================================


def baseline_l3(loss: L3_MachadoV1V2,
                cvd_type: str,
                hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                C_baseline: np.ndarray,
                delta_rdm_obs_dicts: Dict[str, np.ndarray]) -> dict:
    """Evaluate L₃ at Δλ_V1 = Δλ_V2 = 0."""
    return loss.compute(0.0, 0.0, cvd_type,
                        hc_W_dicts, C_baseline, delta_rdm_obs_dicts)
