"""two_component.py — Canonical 2-component forward model (single source of truth).

Mathematical definition (CIE 170-1:2006 Stockman opponent space):
    h_base   = stockman_opponent_hue(θ_CIELab)            # CIELab → opponent hue
    dt       = β_s · cos(h_base − 90°) + β_c · cos(h_base − θ_conf_stockman)
    θ_perceived_CIELab = (θ_CIELab + dt) mod 360°

Frame mixing caveat:
    `dt` is computed in Stockman opponent space units but accumulated in CIELab.
    This is a documented approximation (FORWARD_MODEL_AUDIT.md §3-3 #2).
    Both fitting and visualization use the same approximation, so internal
    self-consistency is preserved. P0 action item: implement Stockman→CIELab
    inverse mapping for full frame consistency. Until P0 is resolved, this
    formula is the single source of truth.

History:
    Pre-2026-05-10: dt_2comp was duplicated in 3 files (visualize_filter_candidates.py,
        loco_distortion_fit.py, comprehensive_2component_analysis.py) plus a
        WRONG variant in visualize_phase3_preimage.py (CIELab-direct, no h_base).
        Same nominal (β_s, β_c) produced different visualizations across files.
    2026-05-10 (P1): consolidated here. Callers must `from forward_models import dt_2comp`.
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from typing import Tuple, Union

# ---------------------------------------------------------------------------
# Path setup — locate machado_simulator
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _THIS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from machado_simulator import machado_shifted_hue_at, machado_shifted_hue  # noqa: E402

# ---------------------------------------------------------------------------
# Stockman convention confusion axes
# ---------------------------------------------------------------------------
# Per CIE / Hering opponent process model (deg in Stockman opponent space):
#   protan: 16°  (L-cone confusion line)
#   deutan: 150° (M-cone confusion line)
#   normal: 83°  (placeholder; no confusion for HC)
CONF_AXIS_STOCKMAN = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}


def _scalar(x):
    return float(np.atleast_1d(x)[0])


def dt_2comp(theta_cielab: float,
             cvd_type: str,
             beta_s: float,
             beta_c: float,
             *,
             L_star: float = 75.0,
             chroma: float = 40.0) -> float:
    """Compute δθ for 2-component model at a single CIELab hue angle.

    Args:
        theta_cielab: CIELab hue angle (deg, [0, 360))
        cvd_type: 'protan', 'deutan', or 'normal'
        beta_s: simulation-axis (S-cone, h=90°) rotation magnitude (deg)
        beta_c: confusion-axis rotation magnitude (deg)
        L_star, chroma: CIELab L*, C* of the experimental ring

    Returns:
        δθ in degrees (CIELab accumulation convention)
    """
    h_base, _, _ = machado_shifted_hue_at(
        0.0, cvd_type, float(theta_cielab),
        L_star=L_star, chroma=chroma,
    )
    h_base = _scalar(h_base)
    theta_conf = CONF_AXIS_STOCKMAN[cvd_type]
    dt = (beta_s * np.cos(np.radians(h_base - 90.0))
          + beta_c * np.cos(np.radians(h_base - theta_conf)))
    return float(dt)


def forward_2comp(theta_cielab: float,
                  cvd_type: str,
                  beta_s: float,
                  beta_c: float,
                  **kwargs) -> Tuple[float, float]:
    """Forward map: CVD-perceived θ given input CIELab θ.

    Returns:
        (theta_perceived_cielab, dt)
    """
    dt = dt_2comp(theta_cielab, cvd_type, beta_s, beta_c, **kwargs)
    theta_perceived = (float(theta_cielab) + dt) % 360.0
    return theta_perceived, dt


def pre_image_2comp(theta_target: float,
                    cvd_type: str,
                    beta_s: float,
                    beta_c: float,
                    *,
                    n_grid: int = 1440,
                    refine: bool = True,
                    **kwargs) -> Tuple[float, float]:
    """Pre-image: solve for θ_pre such that forward(θ_pre) ≈ θ_target.

    Args:
        theta_target: desired CVD-perceived CIELab hue (deg)
        cvd_type: 'protan', 'deutan', 'normal'
        beta_s, beta_c: model parameters
        n_grid: dense grid resolution for initial bracket
        refine: apply brentq local refine if sign change exists

    Returns:
        (theta_pre, signed_residual_deg)
    """
    from scipy.optimize import brentq

    def _wrap180(x):
        return (x + 180.0) % 360.0 - 180.0

    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)

    def residual(t):
        pred, _ = forward_2comp(float(t) % 360.0, cvd_type, beta_s, beta_c, **kwargs)
        return _wrap180(pred - theta_target)

    res_grid = np.array([residual(t) for t in grid])
    i_min = int(np.argmin(np.abs(res_grid)))
    theta_pre = float(grid[i_min])

    if refine:
        step = 360.0 / n_grid * 3
        lo, hi = grid[i_min] - step, grid[i_min] + step
        try:
            f_lo, f_hi = residual(lo), residual(hi)
            if f_lo * f_hi < 0:
                theta_pre = brentq(lambda t: residual(t), lo, hi) % 360.0
        except Exception:
            pass

    return theta_pre % 360.0, residual(theta_pre)


def dt_2comp_8colors(cvd_type: str,
                    beta_s: float,
                    beta_c: float) -> np.ndarray:
    """Vectorized δθ for the 8 experimental colors (legacy interface).

    Used by `loco_distortion_fit.get_shifted_design('2component')` and
    `comprehensive_2component_analysis.two_component_delta_theta`.

    Returns:
        delta_theta: (8,) array — δθ for c1..c8 at CIELab angles 0,45,...,315°
    """
    hue_base, _, _ = machado_shifted_hue(0.0, cvd_type)
    hue_base = np.asarray(hue_base, dtype=float)
    theta_conf = CONF_AXIS_STOCKMAN[cvd_type]
    dt = (beta_s * np.cos(np.radians(hue_base - 90.0))
          + beta_c * np.cos(np.radians(hue_base - theta_conf)))
    return dt
