"""rc_2stage.py — Sequential R+C 2-stage forward & pre-image.

Composition (per advisor reframe 2026-05-16):
    Stage 1 (retinal): θ_stim → h_retinal(θ_stim, Δλ, family)
        via machado_shifted_hue_at(Δλ, family, θ_stim) → returns h_retinal
    Stage 2 (cortical): h_retinal → h_retinal + δθ_cortical
        where δθ_cortical = β_s · cos(h_retinal − 90°) + β_c · cos(h_retinal − axis°)

Full forward:
    θ_perceived = h_retinal + β_s · cos(h_retinal − 90°) + β_c · cos(h_retinal − axis°)

Special cases:
    Δλ = 0 → h_retinal = h_base = 2-comp standalone (sub-08 cortical-dominant limit)
    β_s = β_c = 0 → pure Machado (sub-09 retinal-dominant limit)

Pre-image:
    Given θ_HC_target, solve θ_pre such that forward(θ_pre) ≈ θ_HC_target.
    Numerical search over [0, 360°) with optional brentq refinement.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
from scipy.optimize import brentq

_THIS = Path(__file__).resolve().parent
_PHASE2 = _THIS.parent
for _p in [_PHASE2, _PHASE2.parent / 'future_phase1_forward_model' / 'scripts']:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from machado_simulator import machado_shifted_hue_at  # noqa: E402

# CIELab confusion axis (Stockman-derived) per family — same as 2-comp standalone
CONF_AXIS_STOCKMAN = {'deutan': 150.0, 'protan': 16.0, 'normal': 0.0}


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def forward_rc_2stage(theta_stim: float,
                      family: str,
                      delta_lambda: float,
                      beta_s: float,
                      beta_c: float,
                      axis_conf: float | None = None,
                      L_star: float = 75.0,
                      chroma: float = 40.0) -> Tuple[float, float]:
    """R+C 2-stage forward (revised — convention-consistent with 2-comp standalone).

    Stage 1 (retinal): δθ_retinal from Machado at Δλ (cone-fundamentals diff,
                       treated as approximate CIELab δθ — consistent with
                       existing pipeline convention).
    Stage 2 (cortical): δθ_cortical = β_s·cos(h_retinal − 90°) + β_c·cos(h_retinal − axis°)
                        Uses h_retinal (post-retinal projection) as cosine argument.

    Total CIELab δθ = δθ_retinal + δθ_cortical
    theta_perceived  = theta_stim + total δθ  (matches forward_2comp convention)

    Δλ=0 reduces to forward_2comp(theta_stim, family, β_s, β_c).
    β_s=β_c=0 reduces to pure Machado(theta_stim, Δλ, family).
    """
    hb, hr, dt_retinal = machado_shifted_hue_at(
        float(delta_lambda), family, float(theta_stim),
        L_star=L_star, chroma=chroma,
    )
    hb = float(hb if not hasattr(hb, '__len__') else hb[0])
    hr = float(hr if not hasattr(hr, '__len__') else hr[0])
    dt_retinal = float(dt_retinal if not hasattr(dt_retinal, '__len__') else dt_retinal[0])
    axis = CONF_AXIS_STOCKMAN[family] if axis_conf is None else float(axis_conf)
    # Stage 2: cortical rotation indexed by post-retinal hue
    dt_cortical = (beta_s * np.cos(np.radians(hr - 90.0))
                   + beta_c * np.cos(np.radians(hr - axis)))
    total_dt = dt_retinal + dt_cortical
    theta_perceived = (float(theta_stim) + total_dt) % 360.0
    return theta_perceived, total_dt


def forward_rc_2stage_8colors(family: str,
                               delta_lambda: float,
                               beta_s: float,
                               beta_c: float,
                               axis_conf: float | None = None) -> np.ndarray:
    """Vectorized δθ for 8 colors at 0, 45, ..., 315°."""
    thetas = np.arange(0, 360, 45, dtype=float)
    dts = np.zeros(8)
    for i, t in enumerate(thetas):
        _, dts[i] = forward_rc_2stage(t, family, delta_lambda, beta_s, beta_c, axis_conf)
    return dts


def pre_image_rc_2stage(theta_target: float,
                         family: str,
                         delta_lambda: float,
                         beta_s: float,
                         beta_c: float,
                         axis_conf: float | None = None,
                         n_grid: int = 1440,
                         refine: bool = True) -> Tuple[float, float]:
    """Inverse: find θ_pre such that forward_rc_2stage(θ_pre) ≈ θ_target.

    Returns:
        (theta_pre, signed_residual) — pre-image angle and forward residual.
        |residual| < 0.5° is considered "exact" given 0.25° grid resolution.
    """
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)

    def residual(t):
        perceived, _ = forward_rc_2stage(float(t) % 360.0, family,
                                          delta_lambda, beta_s, beta_c, axis_conf)
        return _wrap180(perceived - theta_target)

    res_grid = np.array([residual(t) for t in grid])
    # Find candidate by minimum |residual|
    i_best = int(np.argmin(np.abs(res_grid)))
    theta_pre = float(grid[i_best])

    if refine:
        step = 360.0 / n_grid * 4
        lo, hi = grid[i_best] - step, grid[i_best] + step
        try:
            f_lo, f_hi = residual(lo), residual(hi)
            if f_lo * f_hi < 0:
                theta_pre = brentq(lambda t: residual(t), lo, hi) % 360.0
        except Exception:
            pass

    return theta_pre % 360.0, residual(theta_pre)


def test_pre_image_8colors(family: str,
                            delta_lambda: float,
                            beta_s: float,
                            beta_c: float,
                            axis_conf: float | None = None,
                            tol_deg: float = 1.0) -> dict:
    """Test 8/8 pre-image exactness across HC target ring."""
    targets = np.arange(0, 360, 45, dtype=float)
    results = []
    for t in targets:
        theta_pre, resid = pre_image_rc_2stage(
            float(t), family, delta_lambda, beta_s, beta_c, axis_conf)
        results.append({
            'theta_target': float(t),
            'theta_pre': theta_pre,
            'residual_deg': float(resid),
            'exact': abs(resid) < tol_deg,
            'delta_filter': _wrap180(theta_pre - t),
        })
    n_exact = sum(r['exact'] for r in results)
    max_err = max(abs(r['residual_deg']) for r in results)
    mean_abs_delta = float(np.mean([abs(r['delta_filter']) for r in results]))
    return {
        'family': family,
        'delta_lambda': delta_lambda,
        'beta_s': beta_s,
        'beta_c': beta_c,
        'n_exact_of_8': n_exact,
        'max_residual_deg': max_err,
        'pass_8_8': n_exact == 8,
        'mean_abs_delta_filter': mean_abs_delta,
        'per_color': results,
    }


if __name__ == '__main__':
    import json

    print('=== R+C 2-stage pre-image smoke tests ===\n')

    # Sub-08 deutan: Δλ=2.5 retinal small + 2-comp (38, -14) cortical dominant
    print('--- Sub-08 deutan (Δλ=2.5, β_s=38, β_c=-14) ---')
    r8 = test_pre_image_8colors('deutan', 2.5, 38.0, -14.0)
    print(f"  exact: {r8['n_exact_of_8']}/8, max err: {r8['max_residual_deg']:.3f}°, "
          f"mean |δ|: {r8['mean_abs_delta_filter']:.1f}°")
    print(f"  PASS 8/8: {r8['pass_8_8']}")

    # Sub-08 deutan with Δλ=0 (pure 2-comp standalone)
    print('\n--- Sub-08 deutan Δλ=0 (pure 2-comp) ---')
    r8z = test_pre_image_8colors('deutan', 0.0, 38.0, -14.0)
    print(f"  exact: {r8z['n_exact_of_8']}/8, max err: {r8z['max_residual_deg']:.3f}°")

    # Sub-09 protan: Δλ=19.5 retinal dominant + cortical (0,0) (advisor's PREDICTION)
    print('\n--- Sub-09 protan Δλ=19.5, β_s=0, β_c=0 (R+C decomp predicted residual) ---')
    r9a = test_pre_image_8colors('protan', 19.5, 0.0, 0.0)
    print(f"  exact: {r9a['n_exact_of_8']}/8, max err: {r9a['max_residual_deg']:.3f}°, "
          f"mean |δ|: {r9a['mean_abs_delta_filter']:.1f}°")
    print(f"  PASS 8/8: {r9a['pass_8_8']}")

    # Sub-09 protan with 2-comp (6, -22) — V4-LOCO 2-comp standalone fit
    print('\n--- Sub-09 protan Δλ=19.5, β_s=6, β_c=-22 (R+C 2-stage with V4-LOCO Stage 2) ---')
    r9b = test_pre_image_8colors('protan', 19.5, 6.0, -22.0)
    print(f"  exact: {r9b['n_exact_of_8']}/8, max err: {r9b['max_residual_deg']:.3f}°, "
          f"mean |δ|: {r9b['mean_abs_delta_filter']:.1f}°")
    print(f"  PASS 8/8: {r9b['pass_8_8']}")

    # Detailed per-color trace
    print('\n--- Sub-09 per-color detail (Δλ=19.5, β=0,0) ---')
    print(f"{'tgt':<6} {'pre':<8} {'resid':<10} {'δ_filter':<10} {'exact'}")
    for r in r9a['per_color']:
        print(f"{r['theta_target']:<6.0f} {r['theta_pre']:<8.2f} "
              f"{r['residual_deg']:+.4f}    {r['delta_filter']:+.2f}     {r['exact']}")
