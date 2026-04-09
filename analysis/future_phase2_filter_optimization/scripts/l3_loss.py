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
from retinal_cortical import get_design_matrix_rc  # noqa: E402
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


# ============================================================================
# L3_MachadoV1V2_V2 (Gen-4.5) — Information-richer loss
# ============================================================================
#
# Diagnostic motivation (sub-09 deep validation, Tasks #19–22):
#     Gen-4 v1's L₃ = L₁(cosine) − λ_scale·L_scale − λ_ROI·L_ROI was
#     numerically stable but (i) carried almost no signed-direction info,
#     (ii) could not distinguish protan from deutan at joint V1+V2, and
#     (iii) let V2 anti-fit cancel V1 signal via the simple 0.5/0.5 mean.
#
# Gen-4.5 adds three terms on top of the v1 loss:
#     L_sign      discrete sign-match between ΔRDM_sim and ΔRDM_obs,
#                 rescaled to [-1, +1] (chance = 0)
#     L_fam       joint-L₁ margin of the TARGET family over the OTHER
#                 family (protan vs deutan, or vice versa)
#     V2 floor    asymmetric penalty that discourages the joint score
#                 from being satisfied by a V2 anti-fit (L₁_V2 < τ)
#
# Full loss (maximised):
#     L_total = L₁_joint_floor(target)
#               + λ_sign · L_sign_joint(target)
#               + λ_fam  · (L₁_joint_floor(target) − L₁_joint_floor(other))
#               − λ_scale · L_scale
#               − λ_ROI   · L_ROI
#
# where
#     L₁_joint_floor(fam) = 0.5·L₁_V1(fam) + 0.5·L₁_V2(fam)
#                           − κ · max(0, τ − L₁_V2(fam))
#     L_sign_joint(fam)   = 0.5·(L_sign_V1(fam) + L_sign_V2(fam))
#     L_sign_ROI(fam)     = 2·mean[sign(ΔRDM_sim)==sign(ΔRDM_obs)] − 1
#
# Defaults (user-approved, 2026-04-06):
#     λ_sign = 0.30, λ_fam = 0.50, τ = −0.02, κ = 0.5,
#     λ_scale = 0.01, λ_ROI = 0.005, metric = 'cosine'
#
# Selection gate (to be enforced in step4_summary_v2):
#     (1) Δλ stability (reuse Task #19 pass band)
#     (2) L_sign_joint ≥ 0.25       (chance + 25%)
#     (3) L_fam > 0                 (target family dominates)
#     (4) L₁_V1(target) > 0 AND L₁_V2(target) > −0.02
#
# ============================================================================


class L3_MachadoV1V2_V2(L3_MachadoV1V2):
    """Gen-4.5 loss: L₃ + L_sign + L_fam + V2 floor penalty.

    Subclass of ``L3_MachadoV1V2`` that reuses the v1 regularisers
    (``l_scale``, ``l_roi``) and Machado design-matrix helpers while
    overriding ``compute`` via the new entry-point :meth:`compute_v2`
    (kept separate from the v1 ``compute`` so existing scripts that
    depend on ``L3_MachadoV1V2.compute`` are unaffected).

    Attributes:
        lam_sign:         weight on L_sign_joint (default 0.30)
        lam_fam:          weight on L_fam margin (default 0.50)
        tau_v2_floor:     V2 L₁ floor threshold (default -0.02)
        kappa_v2_floor:   V2 floor penalty coefficient (default 0.5)
    """

    name = 'l3_machado_v1v2_v2'

    def __init__(self,
                 lam_scale: float = 0.01,
                 lam_roi: float = 0.005,
                 lam_sign: float = 0.30,
                 lam_fam: float = 0.50,
                 tau_v2_floor: float = -0.02,
                 kappa_v2_floor: float = 0.5,
                 delta_lambda_max: float = 20.0,
                 metric: str = 'cosine',
                 model_name: str = 'machado_1way',
                 fixed_alphas: Optional[Dict[str, float]] = None):
        super().__init__(lam_scale=lam_scale,
                         lam_roi=lam_roi,
                         delta_lambda_max=delta_lambda_max,
                         metric=metric,
                         model_name=model_name,
                         fixed_alphas=fixed_alphas)
        self.lam_sign = float(lam_sign)
        self.lam_fam = float(lam_fam)
        self.tau_v2_floor = float(tau_v2_floor)
        self.kappa_v2_floor = float(kappa_v2_floor)

    # ------------------------------------------------------------------
    # New scoring primitives
    # ------------------------------------------------------------------

    @staticmethod
    def sign_match_score(delta_sim: np.ndarray,
                         delta_obs: np.ndarray) -> float:
        """Discrete sign-match fraction rescaled to [-1, +1].

        Ties (== 0) are counted as sign = negative consistently on both
        sides (via strict ``> 0``), so zero-valued pairs on one side
        only will be treated as mismatches — this is the conservative
        choice for a tie-breaking policy.

        Returns:
            2·mean[sign(a)==sign(b)] − 1   ∈ [-1, +1], chance = 0.
        """
        a = np.asarray(delta_sim, dtype=float)
        b = np.asarray(delta_obs, dtype=float)
        sa = a > 0
        sb = b > 0
        match_frac = float(np.mean(sa == sb))
        return 2.0 * match_frac - 1.0

    def _l1_and_sign_per_roi(self,
                              delta_lambda: float,
                              cvd_type: str,
                              hc_W_roi: Dict[str, np.ndarray],
                              C_baseline: np.ndarray,
                              delta_rdm_obs_roi: np.ndarray,
                              roi: Optional[str] = None
                              ) -> tuple[float, float]:
        """Return (L₁, L_sign) for a single ROI at a given Δλ under family."""
        C_shifted = self._design_matrix(delta_lambda, cvd_type, roi=roi)
        delta_sim, _ = compute_delta_rdm_sim(
            hc_W_roi, C_shifted, C_baseline, distance='correlation')
        l1 = float(_similarity(delta_sim, delta_rdm_obs_roi, self.metric))
        l_sign = self.sign_match_score(delta_sim, delta_rdm_obs_roi)
        return l1, l_sign

    def joint_l1_with_floor(self, l1_v1: float, l1_v2: float) -> float:
        """L₁_joint with asymmetric V2 floor penalty.

            L₁_joint_floor = 0.5·L₁_V1 + 0.5·L₁_V2
                             − κ · max(0, τ − L₁_V2)
        """
        mean = (self.weights['V1'] * l1_v1
                + self.weights['V2'] * l1_v2)
        floor_violation = max(0.0, self.tau_v2_floor - l1_v2)
        return mean - self.kappa_v2_floor * floor_violation

    # ------------------------------------------------------------------
    # Core compute (v2)
    # ------------------------------------------------------------------

    def compute_v2(self,
                   delta_lambda_v1: float,
                   delta_lambda_v2: float,
                   target_family: str,
                   other_family: str,
                   hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                   C_baseline: np.ndarray,
                   delta_rdm_obs_dicts: Dict[str, np.ndarray],
                   **kwargs) -> dict:
        """Evaluate Gen-4.5 L_total at a single (Δλ_V1, Δλ_V2) point.

        Args:
            delta_lambda_v1, delta_lambda_v2: candidate shifts (nm)
            target_family: native CVD type (e.g., 'protan' for sub-09)
            other_family:  the alternative family for L_fam margin
            hc_W_dicts:    {ROI: {HC_subj: (K, V_s)}}
            C_baseline:    (8, K) baseline design matrix
            delta_rdm_obs_dicts: {ROI: (28,)} observed ΔRDM vectors

        Returns:
            dict with L_total, L₁_joint_floor(target/other), L_sign_joint,
            L_fam, L_scale, L_ROI, per-ROI L₁ under each family, and
            L_sign per ROI under target family.
        """
        # --- Target family: need L₁ AND L_sign per ROI
        l1_t_v1, ls_t_v1 = self._l1_and_sign_per_roi(
            delta_lambda_v1, target_family,
            hc_W_dicts['V1'], C_baseline,
            delta_rdm_obs_dicts['V1'], roi='V1')
        l1_t_v2, ls_t_v2 = self._l1_and_sign_per_roi(
            delta_lambda_v2, target_family,
            hc_W_dicts['V2'], C_baseline,
            delta_rdm_obs_dicts['V2'], roi='V2')

        # --- Other family: L₁ only (sign not used in the margin term)
        l1_o_v1, _ = self._l1_and_sign_per_roi(
            delta_lambda_v1, other_family,
            hc_W_dicts['V1'], C_baseline,
            delta_rdm_obs_dicts['V1'], roi='V1')
        l1_o_v2, _ = self._l1_and_sign_per_roi(
            delta_lambda_v2, other_family,
            hc_W_dicts['V2'], C_baseline,
            delta_rdm_obs_dicts['V2'], roi='V2')

        # --- Joint assembly
        l1_joint_target = self.joint_l1_with_floor(l1_t_v1, l1_t_v2)
        l1_joint_other = self.joint_l1_with_floor(l1_o_v1, l1_o_v2)
        l_sign_joint = 0.5 * (ls_t_v1 + ls_t_v2)
        l_fam = l1_joint_target - l1_joint_other

        l_scale_val = self.l_scale(delta_lambda_v1, delta_lambda_v2)
        l_roi_val = self.l_roi(delta_lambda_v1, delta_lambda_v2)

        l_total = (l1_joint_target
                   + self.lam_sign * l_sign_joint
                   + self.lam_fam * l_fam
                   - self.lam_scale * l_scale_val
                   - self.lam_roi * l_roi_val)

        return {
            'l_total': float(l_total),
            'l1_joint_target': float(l1_joint_target),
            'l1_joint_other': float(l1_joint_other),
            'l_sign_joint': float(l_sign_joint),
            'l_fam': float(l_fam),
            'l_scale': float(l_scale_val),
            'l_roi': float(l_roi_val),
            # Per-ROI target-family breakdown
            'l1_V1_target': float(l1_t_v1),
            'l1_V2_target': float(l1_t_v2),
            'l_sign_V1_target': float(ls_t_v1),
            'l_sign_V2_target': float(ls_t_v2),
            # Per-ROI other-family breakdown (for diagnostics)
            'l1_V1_other': float(l1_o_v1),
            'l1_V2_other': float(l1_o_v2),
            # Parameters
            'delta_v1': float(delta_lambda_v1),
            'delta_v2': float(delta_lambda_v2),
            'delta_bar': float(0.5 * (delta_lambda_v1 + delta_lambda_v2)),
            'target_family': target_family,
            'other_family': other_family,
            'lam_scale': self.lam_scale,
            'lam_roi': self.lam_roi,
            'lam_sign': self.lam_sign,
            'lam_fam': self.lam_fam,
            'tau_v2_floor': self.tau_v2_floor,
            'kappa_v2_floor': self.kappa_v2_floor,
            'metric': self.metric,
        }

    # Override v1 compute so accidental calls raise a clear error
    def compute(self, *args, **kwargs) -> dict:  # type: ignore[override]
        raise NotImplementedError(
            'L3_MachadoV1V2_V2 uses compute_v2(target_family, other_family, '
            '...). Use compute_v2 instead of compute.')

    # Override v1 permutation_null similarly (not implemented in v2 yet)
    def permutation_null(self, *args, **kwargs) -> dict:  # type: ignore[override]
        raise NotImplementedError(
            'L3_MachadoV1V2_V2 permutation_null is not implemented yet; '
            'rely on sign/family/floor gate in step4_summary_v2 for '
            'significance assessment.')


# ============================================================================
# L3_RetinalCortical — 2-stage retinal + cortical compensation (Gen-4.5rc)
# ============================================================================
#
# Motivation (sub-08 deutan):
#     Machado retinal-only predicts ΔRDM compression but observed ΔRDM shows
#     expansion (cosine = -0.340). Tregillus et al. show cortical R-G gain
#     overcompensation can reverse the sign. This loss evaluates a 3-DOF model
#     (Δλ_V1, Δλ_V2, g) where g is a shared opponent R-G gain.
#
# Loss (maximised):
#     L₃_rc = L₁ − λ_scale · L_scale − λ_ROI · L_ROI
#                 − λ_couple · g² / (|Δλ_bar| + ε_couple)
#                 − λ_dom   · L_dom
#
# where
#     L₁          = 0.5 · cos(ΔRDM_pred_V1, ΔRDM_obs_V1)
#                   + 0.5 · cos(ΔRDM_pred_V2, ΔRDM_obs_V2)
#     L_scale     = [max(0, |Δλ_V1|−20)]² + [max(0, |Δλ_V2|−20)]²
#     L_ROI       = (Δλ_V1 − Δλ_V2)² / 2
#     L_couple    = g² / (|Δλ_bar| + ε_couple)   (coupling: g penalised when Δλ small)
#     L_dom       = max(0, dom_ratio − τ)²        (dominance ratio penalty)
#     dom_ratio   = ||ΔRDM_comp|| / max(||ΔRDM_ret||, ε_dom)
#     ΔRDM_comp   = ΔRDM_pred − ΔRDM_ret          (gain-only contribution)
#
# ΔRDM_pred uses C_final from retinal_cortical.get_design_matrix_rc
# which applies Machado shift + opponent R-G gain before basis lookup.
#
# At g=0 this reverts to the Gen-4 v1 L₃ (sanity check).
# ============================================================================


class L3_RetinalCortical(L3_MachadoV1V2):
    """2-stage loss: Machado retinal shift + opponent R-G gain.

    Subclass of ``L3_MachadoV1V2`` that adds a shared gain parameter ``g``
    and two extra regularisers (coupling penalty + dominance ratio).

    Coupling penalty:  L_couple = g² / (|Δλ_bar| + ε_couple)
        At Δλ=0: penalty ∝ g²/ε_couple (strongly penalises nonzero g).
        At large Δλ: penalty → g²/Δλ (g is affordable when retinal shift exists).

    Attributes:
        lam_couple:   weight on coupling penalty (default 0.01)
        couple_eps:   ε in denominator (default 1.0 nm)
        lam_dom:      weight on L_dom dominance penalty (default 0.005)
        dom_tau:      dominance ratio ceiling (default 1.5)
        dom_eps:      floor for ||ΔRDM_ret|| in dominance ratio (default 0.01)
    """

    name = 'l3_retinal_cortical'

    def __init__(self,
                 lam_couple: float = 0.01,
                 couple_eps: float = 1.0,
                 lam_dom: float = 0.005,
                 dom_tau: float = 1.5,
                 dom_eps: float = 0.01,
                 **kwargs):
        super().__init__(**kwargs)
        self.lam_couple = float(lam_couple)
        self.couple_eps = float(couple_eps)
        self.lam_dom = float(lam_dom)
        self.dom_tau = float(dom_tau)
        self.dom_eps = float(dom_eps)

    # ------------------------------------------------------------------
    # Design matrix with gain
    # ------------------------------------------------------------------

    def _design_matrix_rc(self, delta_lambda: float, g: float,
                          cvd_type: str, roi: Optional[str] = None
                          ) -> np.ndarray:
        """Build C_final with Machado shift + opponent R-G gain."""
        alpha = None
        if self.model_name == 'machado_alpha_free':
            alpha = float(self.fixed_alphas.get(roi, 1.0))
        return get_design_matrix_rc(float(delta_lambda), float(g),
                                    cvd_type, alpha=alpha)

    # ------------------------------------------------------------------
    # Dominance penalty
    # ------------------------------------------------------------------

    def _l_dom_per_roi(self,
                       delta_rdm_pred: np.ndarray,
                       delta_rdm_ret: Optional[np.ndarray]) -> float:
        """Dominance ratio penalty for one ROI.

        L_dom = max(0, ||ΔRDM_comp|| / max(||ΔRDM_ret||, ε) − τ)²
        where ΔRDM_comp = ΔRDM_pred − ΔRDM_ret.

        Returns 0.0 if delta_rdm_ret is None (L_dom disabled) or
        if ||ΔRDM_ret|| < ε (no retinal signal to constrain against).
        """
        if delta_rdm_ret is None:
            return 0.0
        norm_ret = float(np.linalg.norm(delta_rdm_ret))
        if norm_ret < self.dom_eps:
            return 0.0
        delta_comp = delta_rdm_pred - delta_rdm_ret
        norm_comp = float(np.linalg.norm(delta_comp))
        ratio = norm_comp / max(norm_ret, self.dom_eps)
        return float(max(0.0, ratio - self.dom_tau) ** 2)

    # ------------------------------------------------------------------
    # Core compute
    # ------------------------------------------------------------------

    def compute_rc(self,
                   delta_v1: float,
                   delta_v2: float,
                   g: float,
                   cvd_type: str,
                   hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                   C_baseline: np.ndarray,
                   delta_rdm_obs_dicts: Dict[str, np.ndarray],
                   delta_rdm_ret_cache: Optional[Dict[str, np.ndarray]] = None,
                   ) -> dict:
        """Evaluate L₃_rc at (Δλ_V1, Δλ_V2, g).

        Args:
            delta_v1, delta_v2: candidate shifts (nm) per ROI
            g: opponent R-G gain factor
            cvd_type: 'protan', 'deutan', or 'normal'
            hc_W_dicts: {ROI: {HC_subj: (K, V_s)}}
            C_baseline: (8, K) baseline design matrix
            delta_rdm_obs_dicts: {ROI: (28,)} observed ΔRDM vectors
            delta_rdm_ret_cache: {ROI: (28,)} retinal-only ΔRDM at this Δλ.
                If provided, used for L_dom. If None, L_dom = 0.

        Returns:
            dict with l3_rc and all component scores.
        """
        deltas = {'V1': float(delta_v1), 'V2': float(delta_v2)}

        # Per-ROI ΔRDM_pred and L₁ with gain-aware design matrix
        l1_per_roi = {}
        sign_per_roi = {}
        dom_per_roi = {}
        cosine_ret_per_roi = {}
        cosine_full_per_roi = {}
        sign_ret_per_roi = {}
        sign_full_per_roi = {}

        for roi in self.rois:
            dl = deltas[roi]
            C_final = self._design_matrix_rc(dl, g, cvd_type, roi=roi)
            delta_sim, _ = compute_delta_rdm_sim(
                hc_W_dicts[roi], C_final, C_baseline, distance='correlation')
            obs = delta_rdm_obs_dicts[roi]

            l1_val = float(_similarity(delta_sim, obs, self.metric))
            l1_per_roi[roi] = l1_val

            # Sign agreement
            a_signs = delta_sim > 0
            b_signs = obs > 0
            sign_full_per_roi[roi] = float(np.mean(a_signs == b_signs))

            # Cosine
            cosine_full_per_roi[roi] = float(cosine_similarity(delta_sim, obs))

            # Dominance penalty
            drdm_ret = (delta_rdm_ret_cache or {}).get(roi)
            dom_per_roi[roi] = self._l_dom_per_roi(delta_sim, drdm_ret)

            # Retinal-only diagnostics
            if drdm_ret is not None:
                cosine_ret_per_roi[roi] = float(
                    cosine_similarity(drdm_ret, obs))
                r_signs = drdm_ret > 0
                sign_ret_per_roi[roi] = float(np.mean(r_signs == b_signs))
            else:
                cosine_ret_per_roi[roi] = None
                sign_ret_per_roi[roi] = None

        # Joint L₁
        l1 = sum(self.weights[r] * l1_per_roi[r] for r in self.rois)

        # Regularisers
        l_scale = self.l_scale(delta_v1, delta_v2)
        l_roi = self.l_roi(delta_v1, delta_v2)
        delta_bar = 0.5 * (delta_v1 + delta_v2)
        l_couple = float(g ** 2) / (abs(delta_bar) + self.couple_eps)
        l_dom = sum(self.weights[r] * dom_per_roi[r] for r in self.rois)

        l3_rc = (l1
                 - self.lam_scale * l_scale
                 - self.lam_roi * l_roi
                 - self.lam_couple * l_couple
                 - self.lam_dom * l_dom)

        return {
            'l3_rc': float(l3_rc),
            'l1': float(l1),
            'l1_V1': float(l1_per_roi['V1']),
            'l1_V2': float(l1_per_roi['V2']),
            'l_scale': float(l_scale),
            'l_roi': float(l_roi),
            'l_couple': float(l_couple),
            'l_dom': float(l_dom),
            'dominance_V1': float(dom_per_roi['V1']),
            'dominance_V2': float(dom_per_roi['V2']),
            'cosine_retinal_only_V1': cosine_ret_per_roi.get('V1'),
            'cosine_retinal_only_V2': cosine_ret_per_roi.get('V2'),
            'cosine_full_V1': float(cosine_full_per_roi['V1']),
            'cosine_full_V2': float(cosine_full_per_roi['V2']),
            'sign_agree_retinal_V1': sign_ret_per_roi.get('V1'),
            'sign_agree_retinal_V2': sign_ret_per_roi.get('V2'),
            'sign_agree_full_V1': float(sign_full_per_roi['V1']),
            'sign_agree_full_V2': float(sign_full_per_roi['V2']),
            'delta_v1': float(delta_v1),
            'delta_v2': float(delta_v2),
            'g': float(g),
            'delta_bar': float(delta_bar),
            'lam_scale': self.lam_scale,
            'lam_roi': self.lam_roi,
            'lam_couple': self.lam_couple,
            'couple_eps': self.couple_eps,
            'lam_dom': self.lam_dom,
            'dom_tau': self.dom_tau,
            'metric': self.metric,
        }

    # ------------------------------------------------------------------
    # Permutation null
    # ------------------------------------------------------------------

    def permutation_null_rc(self,
                            best_dv1: float,
                            best_dv2: float,
                            best_g: float,
                            cvd_type: str,
                            hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                            C_baseline: np.ndarray,
                            delta_rdm_obs_dicts: Dict[str, np.ndarray],
                            baseline_l3: Optional[float] = None,
                            ) -> dict:
        """Exact 8! joint V1+V2 permutation with C_final frozen at (Δλ*, g*).

        Freezes ΔRDM_pred at the fitted (Δλ_V1*, Δλ_V2*, g*), then permutes
        ΔRDM_obs labels. L_scale, L_ROI, L_gain are permutation-independent
        and stay fixed.

        Args:
            best_dv1, best_dv2: fitted Δλ per ROI
            best_g: fitted opponent gain
            cvd_type: 'protan' / 'deutan' / 'normal'
            hc_W_dicts: {ROI: {HC_subj: (K, V_s)}}
            C_baseline: (8, K) baseline design matrix
            delta_rdm_obs_dicts: {ROI: (28,)} observed ΔRDM
            baseline_l3: L₃_rc at (0, 0, 0) for improvement p-value

        Returns:
            dict with observed L₃_rc, null stats, p-values.
        """
        n_colors = 8
        deltas = {'V1': float(best_dv1), 'V2': float(best_dv2)}

        # Frozen ΔRDM_pred per ROI
        delta_sim_frozen = {}
        for roi in self.rois:
            C_final = self._design_matrix_rc(
                deltas[roi], best_g, cvd_type, roi=roi)
            ds, _ = compute_delta_rdm_sim(
                hc_W_dicts[roi], C_final, C_baseline, distance='correlation')
            delta_sim_frozen[roi] = ds

        # Unpermuted L₁
        obs_l1 = {}
        for roi in self.rois:
            obs_l1[roi] = _similarity(
                delta_sim_frozen[roi],
                delta_rdm_obs_dicts[roi],
                self.metric)
        obs_l1_joint = sum(self.weights[r] * obs_l1[r] for r in self.rois)

        # Fixed regulariser penalty
        l_scale_const = self.l_scale(best_dv1, best_dv2)
        l_roi_const = self.l_roi(best_dv1, best_dv2)
        delta_bar = 0.5 * (best_dv1 + best_dv2)
        l_couple_const = float(best_g ** 2) / (abs(delta_bar) + self.couple_eps)
        reg_penalty = (self.lam_scale * l_scale_const
                       + self.lam_roi * l_roi_const
                       + self.lam_couple * l_couple_const)
        # L_dom is also fixed (ΔRDM_pred frozen), but we skip it in the null
        # to isolate the label-permutation effect on L₁ only.
        obs_l3 = obs_l1_joint - reg_penalty

        # Exact 8! permutations
        obs_squares = {roi: squareform(delta_rdm_obs_dicts[roi])
                       for roi in self.rois}
        idx_tri = np.triu_indices(n_colors, k=1)
        null_l1 = np.empty(np.math.factorial(n_colors), dtype=float)

        for i, perm in enumerate(permutations(range(n_colors))):
            perm = list(perm)
            s_total = 0.0
            for roi in self.rois:
                obs_perm = obs_squares[roi][np.ix_(perm, perm)][idx_tri]
                s = _similarity(delta_sim_frozen[roi], obs_perm, self.metric)
                s_total += self.weights[roi] * s
            null_l1[i] = s_total

        null_l3 = null_l1 - reg_penalty

        label_perm_p = float(
            (np.sum(null_l3 >= obs_l3) + 1) / (len(null_l3) + 1))

        result = {
            'observed_l3_rc': float(obs_l3),
            'observed_l1': float(obs_l1_joint),
            'observed_l1_V1': float(obs_l1['V1']),
            'observed_l1_V2': float(obs_l1['V2']),
            'l_scale_const': float(l_scale_const),
            'l_roi_const': float(l_roi_const),
            'l_couple_const': float(l_couple_const),
            'reg_penalty': float(reg_penalty),
            'null_l3_mean': float(np.mean(null_l3)),
            'null_l3_std': float(np.std(null_l3)),
            'null_l3_size': int(null_l3.size),
            'label_perm_p': label_perm_p,
        }

        if baseline_l3 is not None:
            obs_improvement = obs_l3 - float(baseline_l3)
            null_improvement = null_l3 - float(baseline_l3)
            baseline_improvement_p = float(
                (np.sum(null_improvement >= obs_improvement) + 1)
                / (len(null_improvement) + 1))
            result['baseline_l3'] = float(baseline_l3)
            result['observed_improvement'] = float(obs_improvement)
            result['baseline_improvement_p'] = baseline_improvement_p

        return result
