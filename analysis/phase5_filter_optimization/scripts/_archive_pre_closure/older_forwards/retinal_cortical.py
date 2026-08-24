#!/usr/bin/env python3
"""
retinal_cortical.py — 2-stage retinal + cortical compensation model.

Model (v2 — compensation amplifies retinal-induced change):
    1. hue_base, hue_ret = machado_shifted_hue(Δλ, cvd_type)
    2. rg_base = cos(hue_base),  by_base = sin(hue_base)     # baseline opponent
    3. rg_ret  = cos(hue_ret),   by_ret  = sin(hue_ret)      # retinal opponent
    4. rg' = rg_ret + g * (rg_ret - rg_base)                  # amplify R-G change
       by' = by_ret                                            # B-Y unchanged
    5. hue_final = atan2(by', rg')
    6. C_final = basis_full[round(hue_final)]

Key structural property:
    At Δλ=0: rg_ret = rg_base → rg' = rg_base regardless of g.
    Compensation has ZERO effect without retinal deficit.
    This is by construction — no penalty needed to enforce it.

Motivation (Tregillus et al.):
    Post-receptoral R-G gain overcompensation produces neural distance
    expansion despite retinal L-M separation reduction. The gain factor g
    amplifies only the retinal-induced R-G change, not the absolute level.

Public API:
    machado_with_opponent_gain(delta_lambda, g, cvd_type, alpha=None)
    get_design_matrix_rc(delta_lambda, g, cvd_type, ...)
    opponent_gain_diagnostic(delta_lambda, g, cvd_type, alpha=None)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

_PHASE2_DIR = Path(__file__).resolve().parent.parent
for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'phase4_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from machado_simulator import machado_shifted_hue, machado_shifted_hue_at  # noqa: E402
from utils_forward_model import N_CHANNELS, create_basis_full  # noqa: E402


def _wrap_angle(x: np.ndarray) -> np.ndarray:
    """Wrap angle differences to [-180, 180]."""
    return (x + 180.0) % 360.0 - 180.0


def machado_with_opponent_gain(
    delta_lambda: float,
    g: float,
    cvd_type: str,
    alpha: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Machado retinal shift + opponent R-G gain on retinal-induced change.

    Compensation structure:
        rg' = rg_ret + g * (rg_ret - rg_base)
        by' = by_ret                              (B-Y unchanged)

    At Δλ=0, rg_ret = rg_base, so rg' = rg_base regardless of g.

    Args:
        delta_lambda: cone shift in nm (>= 0)
        g: opponent R-G gain factor (0 = retinal only)
        cvd_type: 'protan', 'deutan', or 'normal'
        alpha: optional severity (None = coupled to delta_lambda)

    Returns:
        hue_baseline: (8,) normal-vision hue angles in degrees
        hue_final:    (8,) compensated hue angles in [0, 360)
        delta_theta:  (8,) wrapped difference in [-180, 180]
    """
    hue_baseline, hue_retinal, _ = machado_shifted_hue(
        delta_lambda, cvd_type, alpha=alpha)

    if g == 0.0 or delta_lambda == 0.0:
        # No gain or no retinal shift → retinal output is final
        hue_final = hue_retinal % 360.0
    else:
        theta_base_rad = np.radians(hue_baseline)
        theta_ret_rad = np.radians(hue_retinal)

        rg_base = np.cos(theta_base_rad)
        by_base = np.sin(theta_base_rad)
        rg_ret = np.cos(theta_ret_rad)
        by_ret = np.sin(theta_ret_rad)

        # Amplify retinal-induced R-G change
        rg_final = rg_ret + g * (rg_ret - rg_base)
        by_final = by_ret  # B-Y channel unchanged

        hue_final = np.degrees(np.arctan2(by_final, rg_final)) % 360.0

    delta_theta = _wrap_angle(hue_final - hue_baseline)
    return hue_baseline, hue_final, delta_theta


def machado_with_2d_rotation(
    delta_lambda: float,
    g_rg: float,
    g_yb: float,
    cvd_type: str,
    alpha: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Machado retinal shift + 2-axis cortical rescale (R-G and B-Y).

    Compensation structure (symmetric extension of R+C):
        rg' = rg_ret + g_rg * (rg_ret - rg_base)
        by' = by_ret + g_yb * (by_ret - by_base)

    At Δλ=0, both axes collapse to baseline regardless of (g_rg, g_yb).
    g_yb=0 reduces to standard R+C model (`machado_with_opponent_gain`).

    Motivation:
        notion §6-5 records sub-08 R+C g=±2.25 (extreme). Hypothesis:
        single-axis g absorbs B-Y axis distortion; adding g_yb may
        normalize g_rg into Tregillus-compatible range (20-40%).

    Args:
        delta_lambda: cone shift in nm (>= 0)
        g_rg: opponent R-G gain factor on retinal-induced change
        g_yb: opponent B-Y gain factor on retinal-induced change
        cvd_type: 'protan', 'deutan', or 'normal'
        alpha: optional severity (None = coupled to delta_lambda)

    Returns:
        hue_baseline: (8,) normal-vision hue angles in degrees
        hue_final:    (8,) compensated hue angles in [0, 360)
        delta_theta:  (8,) wrapped difference in [-180, 180]
    """
    hue_baseline, hue_retinal, _ = machado_shifted_hue(
        delta_lambda, cvd_type, alpha=alpha)

    if (g_rg == 0.0 and g_yb == 0.0) or delta_lambda == 0.0:
        hue_final = hue_retinal % 360.0
    else:
        theta_base_rad = np.radians(hue_baseline)
        theta_ret_rad = np.radians(hue_retinal)

        rg_base = np.cos(theta_base_rad)
        by_base = np.sin(theta_base_rad)
        rg_ret = np.cos(theta_ret_rad)
        by_ret = np.sin(theta_ret_rad)

        rg_final = rg_ret + g_rg * (rg_ret - rg_base)
        by_final = by_ret + g_yb * (by_ret - by_base)

        hue_final = np.degrees(np.arctan2(by_final, rg_final)) % 360.0

    delta_theta = _wrap_angle(hue_final - hue_baseline)
    return hue_baseline, hue_final, delta_theta


def machado_with_opponent_gain_at(
    delta_lambda: float,
    g: float,
    cvd_type: str,
    theta_deg: float | np.ndarray,
    alpha: float | None = None,
    L_star: float = 75.0,
    chroma: float = 40.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """R+C model at **arbitrary** CIELab input angle(s).

    Same opponent-gain logic as ``machado_with_opponent_gain`` but evaluates
    at custom CIELab angles instead of the 8 hardcoded stimuli.

    Args:
        delta_lambda: cone shift in nm (>= 0)
        g: opponent R-G gain factor (0 = retinal only)
        cvd_type: 'protan', 'deutan', or 'normal'
        theta_deg: hue angle(s) in degrees [0, 360). Scalar or 1-D array.
        alpha: optional severity (None = coupled to delta_lambda)
        L_star: CIELab lightness (default 75.0)
        chroma: CIELab chroma (default 40.0)

    Returns:
        hue_baseline: (N,) normal-vision hue angles in degrees
        hue_final:    (N,) compensated hue angles in [0, 360)
        delta_theta:  (N,) wrapped difference in [-180, 180]
    """
    hue_baseline, hue_retinal, _ = machado_shifted_hue_at(
        delta_lambda, cvd_type, theta_deg, alpha=alpha,
        L_star=L_star, chroma=chroma)

    if g == 0.0 or delta_lambda == 0.0:
        hue_final = hue_retinal % 360.0
    else:
        theta_base_rad = np.radians(hue_baseline)
        theta_ret_rad = np.radians(hue_retinal)

        rg_base = np.cos(theta_base_rad)
        rg_ret = np.cos(theta_ret_rad)
        by_ret = np.sin(theta_ret_rad)

        rg_final = rg_ret + g * (rg_ret - rg_base)
        by_final = by_ret

        hue_final = np.degrees(np.arctan2(by_final, rg_final)) % 360.0

    delta_theta = _wrap_angle(hue_final - hue_baseline)
    return hue_baseline, hue_final, delta_theta


def get_design_matrix_rc(
    delta_lambda: float,
    g: float,
    cvd_type: str,
    n_channels: int = N_CHANNELS,
    basis_type: str = 'fe',
    alpha: float | None = None,
) -> np.ndarray:
    """Build C_final with retinal shift + cortical opponent gain.

    Args:
        delta_lambda: cone shift in nm
        g: opponent R-G gain factor
        cvd_type: 'protan', 'deutan', or 'normal'
        n_channels: number of basis channels (default 6)
        basis_type: 'fe' or 'lf'
        alpha: optional Machado severity

    Returns:
        C_final: (8, K) design matrix at compensated hue angles
    """
    _, hue_final, _ = machado_with_opponent_gain(
        delta_lambda, g, cvd_type, alpha=alpha)
    basis_full = create_basis_full(n_channels, basis_type=basis_type)
    idx = np.round(hue_final).astype(int) % 360
    return basis_full[idx]


def opponent_gain_diagnostic(
    delta_lambda: float,
    g: float,
    cvd_type: str,
    alpha: float | None = None,
) -> dict:
    """Diagnostic info for the retinal + cortical model.

    Returns dict with hue angles and opponent projections before/after gain.
    """
    hue_baseline, hue_retinal, _ = machado_shifted_hue(
        delta_lambda, cvd_type, alpha=alpha)

    theta_base_rad = np.radians(hue_baseline)
    theta_ret_rad = np.radians(hue_retinal)

    rg_base = np.cos(theta_base_rad)
    rg_ret = np.cos(theta_ret_rad)
    by_ret = np.sin(theta_ret_rad)

    # R-G change from retinal shift
    drg_retinal = rg_ret - rg_base

    # Compensated
    rg_final = rg_ret + g * drg_retinal
    by_final = by_ret.copy()
    hue_final = np.degrees(np.arctan2(by_final, rg_final)) % 360.0

    return {
        'hue_baseline_deg': hue_baseline.tolist(),
        'hue_retinal_deg': (hue_retinal % 360.0).tolist(),
        'hue_final_deg': hue_final.tolist(),
        'rg_baseline': rg_base.tolist(),
        'rg_retinal': rg_ret.tolist(),
        'rg_final': rg_final.tolist(),
        'drg_retinal': drg_retinal.tolist(),
        'by_retinal': by_ret.tolist(),
        'by_final': by_final.tolist(),
        'delta_lambda_nm': float(delta_lambda),
        'g': float(g),
        'cvd_type': cvd_type,
    }
