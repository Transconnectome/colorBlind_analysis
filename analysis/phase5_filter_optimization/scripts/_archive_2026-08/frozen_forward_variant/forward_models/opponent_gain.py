"""opponent_gain.py — Two-channel opponent gain forward model.

Mechanism (cortical gain layered on Machado anomalous retina):
    1. CIELab(L*, C*, θ) → XYZ → LMS using *normal* Stockman cones (baseline)
       and CIELab → XYZ → LMS_machado using Machado-anomalous cones (Δλ shift on
       L for protan, M for deutan).
    2. Compute Stockman opponent on both:
         (rg_n,  by_n)  ← LMS_normal     (baseline; "what HC opponent stage receives")
         (rg_m,  by_m)  ← LMS_machado    (post-retinal CVD signal)
    3. Apply post-receptoral gains (two channels, independent):
         rg' = g_LM · rg_m
         by' = g_S  · by_m
    4. Recover perceived hue via the project's frame-mixing convention
       (see `two_component.py` lines 7–14):
         h_base    = atan2(by_n, rg_n)             # Stockman opponent hue at θ_in
         h_perceived = atan2(by', rg')             # opponent hue after retina + gain
         δθ        = wrap(h_perceived − h_base, 180)
         θ_perceived_CIELab = (θ_CIELab + δθ) mod 360°

Why this is equivalent to the task spec's "inverse_opponent":
    Multiplying RG/YB axes by gain factors is exactly the simplification of
    Ingling & Tsou-style 2-DOF cortical gain. The luminance channel is
    preserved (gain-only on chromatic channels), so the "inverse_opponent" of
    a gain-only transform reduces algebraically to the atan2 above — no 3×3
    matrix inversion needed.

Identity properties (verified by module self-test at the bottom):
    - forward(θ, 'deutan', Δλ=0, g_LM=1, g_S=1)   ↔ (θ, 0.0)              for all θ
    - forward(θ, 'deutan', Δλ, g_LM=1, g_S=1).dθ  ↔ machado_shifted_hue_at(Δλ, 'deutan', θ).δθ
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import numpy as np

# ----------------------------------------------------------------------------
# Path setup — reach stockman_cone_shift and machado_simulator
# ----------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _THIS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# `machado_simulator` adds phase4_forward_model/scripts to sys.path on
# import, which makes `stockman_cone_shift` importable below.
from machado_simulator import (  # noqa: E402
    machado_mixed_fundamentals,
    machado_shifted_hue_at,
    _load_stockman_grid,
)
from stockman_cone_shift import (  # noqa: E402
    _compute_spectral_shift_lms,
    lab_to_xyz,
    lms_to_opponent,
)


def _wrap180(x: float) -> float:
    """Wrap a signed angle (deg) to [-180, 180]."""
    return float((x + 180.0) % 360.0 - 180.0)


def _lab_from_theta(theta_deg, L_star: float, chroma: float) -> np.ndarray:
    """Build CIELab (N, 3) at given hue angle(s)."""
    theta_deg = np.atleast_1d(np.asarray(theta_deg, dtype=float))
    theta_rad = np.deg2rad(theta_deg)
    return np.column_stack([
        np.full_like(theta_deg, L_star),
        chroma * np.cos(theta_rad),
        chroma * np.sin(theta_rad),
    ])


def _opponent_from_cones(L_a: np.ndarray, M_a: np.ndarray, S_a: np.ndarray,
                         xyz_inputs: np.ndarray) -> Tuple[float, float]:
    """Compute Stockman opponent (rg, by) at xyz_inputs using given cones.

    Reuses `_compute_spectral_shift_lms` which rebuilds the XYZ→LMS matrix
    from the (possibly shifted) cone fundamentals exactly as Machado simulator
    does. This guarantees Δλ=0 → identity.
    """
    wl, _, _, _, _, _, M_xyz2lms = _load_stockman_grid()
    lms = _compute_spectral_shift_lms(wl, L_a, M_a, S_a, M_xyz2lms, xyz_inputs)
    rg, by = lms_to_opponent(lms)
    return float(np.ravel(rg)[0]), float(np.ravel(by)[0])


def forward_opponent_gain(
    theta_cielab: float,
    cvd_type: str,
    delta_lambda: float,
    g_LM: float,
    g_S: float,
    *,
    L_star: float = 75.0,
    chroma: float = 40.0,
) -> Tuple[float, float]:
    """Forward map: CVD-perceived CIELab θ given Δλ + (g_LM, g_S).

    Args:
        theta_cielab: input CIELab hue angle (deg, [0, 360))
        cvd_type: 'protan', 'deutan', or 'normal'
        delta_lambda: retinal cone shift (nm, Machado 1-way; α coupled to Δλ)
        g_LM: post-receptoral L−M (R-G) channel gain (1.0 = no gain)
        g_S:  post-receptoral S − (L+M)/2 (B-Y) channel gain (1.0 = no gain)
        L_star, chroma: CIELab L*, C* of the experimental ring (default 75, 40)

    Returns:
        (theta_perceived_cielab, dt)  with dt = wrap(θ_perceived − θ_in, 180).
    """
    # Build CIELab → XYZ → input
    lab = _lab_from_theta(float(theta_cielab), L_star, chroma)
    xyz = lab_to_xyz(lab)

    # Baseline (normal cones) opponent at θ_in
    wl, L_n, M_n, S_n, _, _, _ = _load_stockman_grid()
    rg_n, by_n = _opponent_from_cones(L_n, M_n, S_n, xyz)
    h_base = float(np.rad2deg(np.arctan2(by_n, rg_n)) % 360.0)

    # CVD retinal stage: Machado-anomalous cones at θ_in
    if cvd_type == 'normal' or float(delta_lambda) == 0.0:
        L_a, M_a, S_a = L_n, M_n, S_n
    else:
        L_a, M_a, S_a = machado_mixed_fundamentals(
            float(delta_lambda), cvd_type, wl, L_n, M_n, S_n)
    rg_m, by_m = _opponent_from_cones(L_a, M_a, S_a, xyz)

    # Cortical gain stage (two channels, independent)
    rg_p = float(g_LM) * rg_m
    by_p = float(g_S) * by_m

    # Recover perceived hue via opponent atan2 (Ingling & Tsou simplification)
    h_percept = float(np.rad2deg(np.arctan2(by_p, rg_p)) % 360.0)

    # Frame-mixing: accumulate δθ in CIELab (matches two_component.py convention)
    dt = _wrap180(h_percept - h_base)
    theta_perceived = (float(theta_cielab) + dt) % 360.0
    return theta_perceived, dt


def pre_image_opponent_gain(
    theta_target: float,
    cvd_type: str,
    delta_lambda: float,
    g_LM: float,
    g_S: float,
    *,
    n_grid: int = 1440,
    refine: bool = True,
    L_star: float = 75.0,
    chroma: float = 40.0,
) -> Tuple[float, float]:
    """Pre-image: solve for θ_pre such that forward(θ_pre) ≈ θ_target.

    Mirrors `pre_image_2comp` exactly (numerical grid + brentq refine).

    Returns:
        (theta_pre, signed_residual_deg)
    """
    from scipy.optimize import brentq

    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)

    def residual(t):
        pred, _ = forward_opponent_gain(
            float(t) % 360.0, cvd_type, delta_lambda, g_LM, g_S,
            L_star=L_star, chroma=chroma)
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


# ----------------------------------------------------------------------------
# Self-test: identity properties
# ----------------------------------------------------------------------------

def _self_test() -> None:
    """Verify two non-negotiable identities (see module docstring)."""
    print('opponent_gain self-test')
    print('=' * 60)

    # (1) Trivial identity: Δλ=0, g_LM=g_S=1 → forward(θ) == θ, dt == 0
    print('\n(1) Δλ=0, g_LM=g_S=1 must give (θ, 0) for all θ:')
    ok1 = True
    for theta in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]:
        th_p, dt = forward_opponent_gain(theta, 'deutan', 0.0, 1.0, 1.0)
        err = abs(_wrap180(th_p - theta))
        status = 'OK' if (err < 1e-6 and abs(dt) < 1e-6) else 'FAIL'
        if err >= 1e-6 or abs(dt) >= 1e-6:
            ok1 = False
        print(f'   θ={theta:5.1f}  →  θ_p={th_p:6.2f}  dt={dt:+7.3f}°  [{status}]')

    # (2) Δλ=14, g_LM=g_S=1 must match machado_shifted_hue_at(14, 'deutan', θ).dθ
    print('\n(2) Δλ=14, g_LM=g_S=1 must match machado_shifted_hue_at dθ:')
    ok2 = True
    for theta in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]:
        _, dt_og = forward_opponent_gain(theta, 'deutan', 14.0, 1.0, 1.0)
        _, _, dt_ms = machado_shifted_hue_at(14.0, 'deutan', theta)
        dt_ms_s = float(np.atleast_1d(dt_ms)[0])
        err = abs(_wrap180(dt_og - dt_ms_s))
        status = 'OK' if err < 1e-4 else 'FAIL'
        if err >= 1e-4:
            ok2 = False
        print(f'   θ={theta:5.1f}  og dt={dt_og:+7.3f}°  machado dt={dt_ms_s:+7.3f}°  '
              f'|Δ|={err:6.4f}°  [{status}]')

    print('\nResult: identity (1) = ' + ('PASS' if ok1 else 'FAIL') +
          ' | identity (2) = ' + ('PASS' if ok2 else 'FAIL'))


if __name__ == '__main__':
    _self_test()
