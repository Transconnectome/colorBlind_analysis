"""S5 helper: two_comp.py — 2-Component forward model (β_s, β_c).

δθ(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)

  θ_conf:
    protan: 16°
    deutan: 150°

  β_s : S-cone cardinal amplitude (Krauskopf 1982)
  β_c : confusion-axis amplitude (Stockman cone fundamentals confusion line)
"""
import numpy as np

HUE_CANON = np.arange(0, 360, 45, dtype=float)
THETA_CONF = {'protan': 16.0, 'deutan': 150.0}

BS_GRID = np.arange(0.0, 50.0 + 1e-9, 2.0)        # 26 points
BC_GRID = np.arange(-50.0, 50.0 + 1e-9, 2.0)      # 51 points


def forward_2comp(beta_s: float, beta_c: float, cvd_family: str,
                   hues: np.ndarray = HUE_CANON) -> np.ndarray:
    """δθ(c) 8-vec for 2-Component cortical rotation model."""
    theta_conf = THETA_CONF[cvd_family]
    rad = np.deg2rad(hues)
    rad_s = np.deg2rad(hues - 90.0)
    rad_c = np.deg2rad(hues - theta_conf)
    delta = beta_s * np.cos(rad_s) + beta_c * np.cos(rad_c)
    return delta


def grid_2comp() -> tuple:
    return BS_GRID, BC_GRID


def fit_2comp(cvd_family: str, loss_fn) -> dict:
    """Grid search (β_s, β_c) for given loss function callable."""
    losses = np.zeros((len(BS_GRID), len(BC_GRID)))
    for i, bs in enumerate(BS_GRID):
        for j, bc in enumerate(BC_GRID):
            delta = forward_2comp(bs, bc, cvd_family)
            losses[i, j] = float(loss_fn(delta))
    best_idx = np.unravel_index(np.argmin(losses), losses.shape)
    bs_best = float(BS_GRID[best_idx[0]])
    bc_best = float(BC_GRID[best_idx[1]])
    return {
        'beta_s_best': bs_best,
        'beta_c_best': bc_best,
        'loss_best': float(losses[best_idx]),
        'loss_at_zero': float(losses[0, np.searchsorted(BC_GRID, 0.0)]),
        'boundary_bs': bool(best_idx[0] == 0 or best_idx[0] == len(BS_GRID) - 1),
        'boundary_bc': bool(best_idx[1] == 0 or best_idx[1] == len(BC_GRID) - 1),
        'delta_theta_at_best': forward_2comp(bs_best, bc_best, cvd_family).tolist(),
    }


if __name__ == "__main__":
    # Quick sanity check
    print("2-Component forward — sanity")
    print(f"  Grid: β_s {len(BS_GRID)} pts, β_c {len(BC_GRID)} pts = {len(BS_GRID) * len(BC_GRID)} combinations")
    print(f"\nHC baseline (β_s=0, β_c=0): δθ = {forward_2comp(0, 0, 'protan').round(3).tolist()}")
    print(f"S-cone only (β_s=20, β_c=0) protan: δθ = {forward_2comp(20, 0, 'protan').round(2).tolist()}")
    print(f"Confusion-axis only (β_s=0, β_c=20) protan: δθ = {forward_2comp(0, 20, 'protan').round(2).tolist()}")
    print(f"Sub-09 Cycle 12-like (β_s=30, β_c=26) protan: δθ = {forward_2comp(30, 26, 'protan').round(2).tolist()}")
