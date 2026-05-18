#!/usr/bin/env python3
"""3-component forward model: cascade (Machado retinal Δλ) → (2-comp cortical β_s, β_c).

Captures both retinal cone-shift and cortical opponent rotation as stimulus-space
angular distortions, jointly fit. Differs from R+C 2-stage (rejected as filter form
2026-05-16) because (a) here it is used as a *fitting* model class, not as the
final filter cascade, and (b) the cortical term is the 2-comp form (CIELab
cosine) not opponent-gain g.

Mathematical form (per color, 8-vector):
    Step 1: hue_shifted_retinal = hue_normal + dt_retinal(Δλ, family)
    Step 2: dt_cortical = β_s·cos(hue_shifted - 90°) + β_c·cos(hue_shifted - axis°)
    Step 3: final_hue = hue_shifted_retinal + dt_cortical
    Output: dt_total = wrap(final_hue - hue_normal) ∈ [-180, +180]
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
from typing import Tuple

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from machado_simulator import machado_shifted_hue
from forward_models.two_component import CONF_AXIS_STOCKMAN


def dt_3comp_8colors(cvd_type: str,
                     delta_lambda: float,
                     beta_s: float,
                     beta_c: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cascade retinal (Δλ) → cortical (β_s, β_c) for the 8 experimental hues.

    Returns:
        dt_total: (8,) wrapped δθ in [-180, +180]
        dt_retinal: (8,) Machado-only retinal δθ
        dt_cortical: (8,) 2-comp cortical δθ applied at retinal-shifted hue
    """
    hue_normal, hue_shifted_retinal, dt_retinal = machado_shifted_hue(
        float(delta_lambda), cvd_type)
    hue_normal = np.asarray(hue_normal, dtype=float)
    hue_shifted_retinal = np.asarray(hue_shifted_retinal, dtype=float)
    dt_retinal = np.asarray(dt_retinal, dtype=float)

    theta_conf = CONF_AXIS_STOCKMAN[cvd_type]
    dt_cortical = (beta_s * np.cos(np.radians(hue_shifted_retinal - 90.0))
                   + beta_c * np.cos(np.radians(hue_shifted_retinal - theta_conf)))

    final_hue = (hue_shifted_retinal + dt_cortical) % 360.0
    dt_total = (final_hue - hue_normal + 180.0) % 360.0 - 180.0
    return dt_total, dt_retinal, dt_cortical


def forward_3comp_full(theta_cielab: float,
                       cvd_type: str,
                       delta_lambda: float,
                       beta_s: float,
                       beta_c: float) -> Tuple[float, float]:
    """Forward map for a single CIELab hue (used for pre-image continuous solving).

    Linear interpolation of the 8-color δθ across hue (since model is defined
    on the 8 anchors; for arbitrary θ use the 2-comp cosine form on retinal-
    shifted hue directly).
    """
    hue_normal_8, hue_shifted_8, dt_retinal_8 = machado_shifted_hue(
        float(delta_lambda), cvd_type)
    hue_normal_8 = np.asarray(hue_normal_8, dtype=float)
    hue_shifted_8 = np.asarray(hue_shifted_8, dtype=float)
    dt_retinal_8 = np.asarray(dt_retinal_8, dtype=float)

    # Interpolate retinal shift at arbitrary θ using nominal hue anchors
    anchors = np.arange(0.0, 360.0, 45.0)
    diffs = (anchors - theta_cielab + 180.0) % 360.0 - 180.0
    idx = int(np.argmin(np.abs(diffs)))
    idx_next = (idx + 1) % 8
    gap_anchor = (anchors[idx_next] - anchors[idx]) % 360.0
    if gap_anchor == 0:
        gap_anchor = 360.0
    d = (theta_cielab - anchors[idx]) % 360.0
    t = float(np.clip(d / gap_anchor, 0.0, 1.0))

    # Interpolate retinal-shifted hue
    h_shift_anchor = hue_shifted_8[idx]
    h_shift_next = hue_shifted_8[idx_next]
    # Use wrapping-aware interpolation
    delta = (h_shift_next - h_shift_anchor + 180.0) % 360.0 - 180.0
    hue_shifted_retinal = (h_shift_anchor + t * delta) % 360.0

    theta_conf = CONF_AXIS_STOCKMAN[cvd_type]
    dt_cortical = (beta_s * np.cos(np.radians(hue_shifted_retinal - 90.0))
                   + beta_c * np.cos(np.radians(hue_shifted_retinal - theta_conf)))

    final_hue = (hue_shifted_retinal + dt_cortical) % 360.0
    dt_total = (final_hue - theta_cielab + 180.0) % 360.0 - 180.0
    return float(final_hue), float(dt_total)


def pre_image_3comp(theta_target: float,
                    cvd_type: str,
                    delta_lambda: float,
                    beta_s: float,
                    beta_c: float,
                    n_grid: int = 1440) -> Tuple[float, float]:
    """Find θ_pre such that forward(θ_pre) ≈ θ_target."""
    from scipy.optimize import brentq

    def _wrap180(x):
        return (x + 180.0) % 360.0 - 180.0

    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)

    def residual(t):
        h, _ = forward_3comp_full(float(t) % 360.0, cvd_type,
                                  delta_lambda, beta_s, beta_c)
        return _wrap180(h - theta_target)

    res_grid = np.array([residual(t) for t in grid])
    i_min = int(np.argmin(np.abs(res_grid)))
    theta_pre = float(grid[i_min])

    step = 360.0 / n_grid * 3
    lo, hi = theta_pre - step, theta_pre + step
    try:
        if residual(lo) * residual(hi) < 0:
            theta_pre = brentq(residual, lo, hi) % 360.0
    except Exception:
        pass

    return theta_pre % 360.0, residual(theta_pre)
