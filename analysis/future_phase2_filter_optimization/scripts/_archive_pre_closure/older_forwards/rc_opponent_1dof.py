"""rc_opponent_1dof.py — Tregillus-faithful R+C 1-DOF forward.

Forward model (Tregillus 2021 / Emery 2022 / Robinson 2023):

    Retinal stage:    hue_ret = machado_shifted_hue(Δλ, family)
    Opponent decomp:  rg_base = cos(θ_base),  by_base = sin(θ_base)
                      rg_ret  = cos(θ_ret),   by_ret  = sin(θ_ret)
    Cortical R-G gain on retinal-induced change:
                      rg' = rg_ret + g·(rg_ret - rg_base)       (L-M channel)
                      by' = by_ret                              (B-Y channel unchanged)
    Output:           hue_final = atan2(by', rg')
                      δθ = wrap(hue_final - hue_base)

g convention (Tregillus convention):
    g =  0  : pure retinal (no cortical compensation)
    g = -1  : full opponent compensation (rg' = rg_base; R-G channel reset to baseline)
    g < -1  : over-shoot (anti-direction past baseline)
    g >  0  : anti-Machado (amplifies retinal R-G error)

Differs from rc_1dof.py (which uses uniform-across-hue linear scaling
δθ_RC = (2-g)·δθ_Machado). The Tregillus form is L-M-channel selective:
B-Y component is preserved, so the operation is non-linear in hue.

Grid: g ∈ [-2.0, +2.0], step 0.05 → 81 points.

Reference: see notebooklm prior-works mapping & retinal_cortical.machado_with_opponent_gain.
"""
from __future__ import annotations
import sys
import json
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from retinal_cortical import machado_with_opponent_gain  # Tregillus forward
from rc_1dof import delta_machado as _delta_machado_lin  # for cross-check

HUE_CANON = np.arange(0, 360, 45, dtype=float)  # 8 canonical hues
G_MIN, G_MAX, G_STEP = -2.0, 2.0, 0.05  # 81 grid points


def forward_rc_opp(delta_lambda: float, g: float, cvd_family: str) -> np.ndarray:
    """Tregillus-faithful R+C forward.

    Returns δθ as wrapped 8-vec in [-180, 180].
    Uses retinal_cortical.machado_with_opponent_gain (R-G selective gain).
    """
    _, _, delta_theta = machado_with_opponent_gain(
        delta_lambda, g, cvd_family, alpha=None)
    return np.asarray(delta_theta, dtype=float)


def g_grid() -> np.ndarray:
    return np.arange(G_MIN, G_MAX + G_STEP / 2, G_STEP)


def fit_rc_opp_g(delta_lambda: float, cvd_family: str, loss_fn) -> dict:
    """Grid search g ∈ [-2, +2] for given Δλ under Tregillus opponent forward.

    Args:
        delta_lambda: cone shift in nm (>=0)
        cvd_family:   'protan' | 'deutan'
        loss_fn:      callable (delta_8vec) -> float

    Returns:
        dict — keys identical to rc_1dof.fit_rc_g for downstream consistency:
          g_best, loss_best, loss_at_g0 (analogue of loss_at_g1 ≡ HC-like),
          boundary_low, boundary_high, misspecified,
          grid_min, grid_max, grid_step, grid, losses
    """
    grid = g_grid()
    losses = np.zeros_like(grid)
    for i, g in enumerate(grid):
        delta = forward_rc_opp(delta_lambda, g, cvd_family)
        losses[i] = float(loss_fn(delta))
    best_idx = int(np.argmin(losses))
    # In Tregillus convention g=0 is the HC-like / pure retinal pass-through.
    idx_g0 = int(np.searchsorted(grid, 0.0))
    return {
        'g_best': float(grid[best_idx]),
        'loss_best': float(losses[best_idx]),
        'loss_at_g0': float(losses[idx_g0]),
        'boundary_low': bool(best_idx == 0),
        'boundary_high': bool(best_idx == len(grid) - 1),
        'misspecified': bool(best_idx == 0 or best_idx == len(grid) - 1),
        'grid_min': float(grid[0]),
        'grid_max': float(grid[-1]),
        'grid_step': float(G_STEP),
        'grid': grid.tolist(),
        'losses': losses.tolist(),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    print("=" * 78)
    print("rc_opponent_1dof self-test (Tregillus forward)")
    print("=" * 78)
    results = {}

    # Test 1: Δλ=0 → δθ identically zero for ALL g (by construction of opponent forward)
    test1_pass = True
    for g in [-2.0, -1.0, 0.0, 1.0, 2.0]:
        for fam in ['protan', 'deutan']:
            dt = forward_rc_opp(0.0, g, fam)
            if np.max(np.abs(dt)) > 1e-6:
                test1_pass = False
                print(f"  FAIL Δλ=0 g={g} {fam}: |δθ|max = {np.max(np.abs(dt))}")
    results['t1_dl0'] = {'pass': test1_pass}
    print(f"[T1] Δλ=0 → δθ=0 for all g: {'PASS' if test1_pass else 'FAIL'}")

    # Test 2: g=0 with Δλ>0 → δθ should equal pure retinal Machado
    dt_g0 = forward_rc_opp(10.0, 0.0, 'protan')
    dt_machado = _delta_machado_lin(10.0, 'protan')
    diff = float(np.max(np.abs(dt_g0 - dt_machado)))
    t2_pass = diff < 1e-3
    results['t2_g0_eq_machado'] = {'pass': t2_pass, 'max_diff_deg': diff,
                                    'dt_g0': dt_g0.tolist(),
                                    'dt_machado': dt_machado.tolist()}
    print(f"[T2] g=0 Δλ=10 protan → δθ = pure Machado retinal "
          f"(max diff {diff:.4f}°): {'PASS' if t2_pass else 'FAIL'}")

    # Test 3: g=-1 with Δλ>0 → δθ should be SMALLER than g=0 (partial compensation)
    dt_gm1 = forward_rc_opp(10.0, -1.0, 'protan')
    rms_g0 = float(np.sqrt(np.mean(dt_g0 ** 2)))
    rms_gm1 = float(np.sqrt(np.mean(dt_gm1 ** 2)))
    t3_pass = rms_gm1 < rms_g0
    results['t3_compensation'] = {
        'pass': t3_pass, 'rms_g0_deg': rms_g0, 'rms_gm1_deg': rms_gm1,
        'ratio': rms_gm1 / rms_g0 if rms_g0 > 0 else None,
    }
    print(f"[T3] g=-1 RMS ({rms_gm1:.2f}°) < g=0 RMS ({rms_g0:.2f}°): "
          f"{'PASS' if t3_pass else 'FAIL'}")

    # Test 4: g=+1 with Δλ>0 → |δθ| should be LARGER than g=0 (anti-direction amplifies)
    dt_gp1 = forward_rc_opp(10.0, 1.0, 'protan')
    rms_gp1 = float(np.sqrt(np.mean(dt_gp1 ** 2)))
    t4_pass = rms_gp1 > rms_g0
    results['t4_anti_machado'] = {
        'pass': t4_pass, 'rms_gp1_deg': rms_gp1, 'rms_g0_deg': rms_g0,
    }
    print(f"[T4] g=+1 RMS ({rms_gp1:.2f}°) > g=0 RMS ({rms_g0:.2f}°): "
          f"{'PASS' if t4_pass else 'FAIL'}")

    # Test 5: Grid search with loss = sum δθ² should drive g close to -1 (compensation)
    def dummy_loss(delta):
        return float(np.sum(delta ** 2))
    fit = fit_rc_opp_g(10.0, 'protan', dummy_loss)
    t5_pass = -1.5 <= fit['g_best'] <= -0.5  # should land near -1
    results['t5_grid_compensation'] = {
        'pass': t5_pass, 'g_best': fit['g_best'], 'loss_best': fit['loss_best'],
    }
    print(f"[T5] Grid sum δθ²: g_best={fit['g_best']:.3f} (expect near -1): "
          f"{'PASS' if t5_pass else 'FAIL'}")

    # Test 6: Boundary detection — anti-loss should push to grid_high (g=+2)
    def anti_loss(delta):
        return -float(np.sum(delta ** 2))
    fit2 = fit_rc_opp_g(10.0, 'protan', anti_loss)
    t6_pass = fit2['boundary_high']
    results['t6_boundary_high'] = {
        'pass': t6_pass, 'g_best': fit2['g_best'],
        'boundary_high': fit2['boundary_high'],
    }
    print(f"[T6] Boundary detect (high): g_best={fit2['g_best']:.2f}, "
          f"flag={fit2['boundary_high']}: {'PASS' if t6_pass else 'FAIL'}")

    # Test 7: Tregillus g=-1 ↔ current convention g=2 (full compensation)
    # Cross-check: full compensation magnitudes
    from rc_1dof import forward_rc as forward_rc_lin
    dt_lin_full = forward_rc_lin(10.0, 2.0, 'protan')  # current g=2 → δθ=0 by linearity
    rms_lin_full = float(np.sqrt(np.mean(dt_lin_full ** 2)))
    # Tregillus g=-1: full R-G compensation BUT B-Y preserved → δθ != 0 generally
    rms_tre_full = rms_gm1  # from t3
    results['t7_convention_comparison'] = {
        'note': 'Current g=2 → δθ=0 exact (linear); Tregillus g=-1 → δθ ≠ 0 in general (B-Y unchanged)',
        'rms_linear_g2_deg': rms_lin_full,
        'rms_tregillus_gm1_deg': rms_tre_full,
        'tregillus_is_partial': bool(rms_tre_full > 1e-3),
    }
    print(f"[T7] Convention compare: linear g=2 RMS={rms_lin_full:.4f}, "
          f"Tregillus g=-1 RMS={rms_tre_full:.4f} (partial, B-Y preserved)")

    all_pass = all(r.get('pass', True) for r in results.values()
                   if 'pass' in r)
    print(f"\n{'=' * 78}")
    print(f"Self-test: {'ALL PASS' if all_pass else 'FAILURES'}")
    print(f"{'=' * 78}")

    # Subject preview table
    print("\n--- Tregillus R+C forward magnitudes per subject × Δλ source × g ---")
    print(f"{'Subj':<8} {'Fam':<7} {'Δλ src':<12} {'g':<6} "
          f"{'RMS δθ':<10} {'max|δθ|':<10}")
    subjects = [
        ('sub-08', 'deutan', {'DPS': 6.0, 'Boehm': 8.0, 'JND_L': 6.5}),
        ('sub-09', 'protan', {'DPS': 10.0, 'Boehm': 3.0, 'JND_L': 1.5}),
    ]
    for subj, fam, sources in subjects:
        for src, dl in sources.items():
            for g in [-1.0, -0.5, 0.0, 0.5, 1.0]:
                dt = forward_rc_opp(dl, g, fam)
                rms = float(np.sqrt(np.mean(dt ** 2)))
                ma = float(np.max(np.abs(dt)))
                print(f"{subj:<8} {fam:<7} {src:<12} {g:<6.2f} {rms:<10.2f} {ma:<10.2f}")

    return results, all_pass


if __name__ == "__main__":
    results, all_pass = self_test()
    OUT_DIR = SCRIPT_DIR.parent / "results" / "s5_tregillus"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clean = {}
    for k, v in results.items():
        clean[k] = {kk: vv for kk, vv in v.items()
                    if kk not in ('grid', 'losses')}
    with open(OUT_DIR / "self_test_results.json", 'w') as f:
        json.dump({'all_pass': all_pass, 'tests': clean}, f, indent=2)
    print(f"\nSaved: {OUT_DIR / 'self_test_results.json'}")
    sys.exit(0 if all_pass else 1)
