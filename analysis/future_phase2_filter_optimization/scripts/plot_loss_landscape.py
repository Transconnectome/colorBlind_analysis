"""plot_loss_landscape.py — 2-component loss landscape contourf for identifiability check.

Loads the 26×51 phase_a_2component grid (β_s ∈ [0,50], β_c ∈ [−50,50])
and plots contourf + argmin for sub-08 and sub-09 (hV4, LOCO-primary loss).

Loss: L = 1.0·l_vuln + 0.5·l_rank + 0.2·l_rdm + 0.1·l_smooth
(weights from manifest; argmin = (38,−14) sub-08, (6,−22) sub-09)

Saves: results/identifiability/loss_landscape_sub08_sub09.pdf/.png
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.linalg import eigh

RESULTS = Path(__file__).resolve().parent.parent / 'results'
LANDSCAPE_DIR = RESULTS / 'fits' / 'phase_a_2component'
OUT_DIR = RESULTS / 'identifiability'
OUT_DIR.mkdir(exist_ok=True)

WEIGHTS = dict(alpha=1.0, beta=0.5, delta=0.2, epsilon=0.1)

CASES = [
    dict(sid='08', family='deutan', argmin=(38.0, -14.0), color='#E07B2C'),
    dict(sid='09', family='protan', argmin=(6.0, -22.0),  color='#2D8E8B'),
]


def load_landscape(sid: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns bs_grid (N,M), bc_grid (N,M), loss_grid (N,M)."""
    path = LANDSCAPE_DIR / f'sub-{sid}_V4_2component_landscape.json'
    with open(path) as f:
        cells = json.load(f)

    bs_unique = sorted(set(c['params'][0] for c in cells))
    bc_unique = sorted(set(c['params'][1] for c in cells))
    N, M = len(bs_unique), len(bc_unique)

    bs_idx = {v: i for i, v in enumerate(bs_unique)}
    bc_idx = {v: j for j, v in enumerate(bc_unique)}

    bs_arr = np.array(bs_unique)
    bc_arr = np.array(bc_unique)
    loss_arr = np.full((N, M), np.nan)

    for c in cells:
        i = bs_idx[c['params'][0]]
        j = bc_idx[c['params'][1]]
        loss_arr[i, j] = (WEIGHTS['alpha'] * c['l_vuln'] +
                          WEIGHTS['beta']  * c['l_rank'] +
                          WEIGHTS['delta'] * c['l_rdm'] +
                          WEIGHTS['epsilon'] * c['l_smooth'])

    BS, BC = np.meshgrid(bs_arr, bc_arr, indexing='ij')
    return BS, BC, loss_arr


def hessian_condition(loss_arr: np.ndarray, argmin_ij: tuple[int, int]) -> float:
    """Approximate condition number from finite-difference Hessian at argmin."""
    i0, j0 = argmin_ij
    N, M = loss_arr.shape
    H = np.zeros((2, 2))
    eps = 1  # step in index units

    # d²L/d(bs)²
    if 0 < i0 < N - 1:
        H[0, 0] = loss_arr[i0+1, j0] - 2*loss_arr[i0, j0] + loss_arr[i0-1, j0]
    # d²L/d(bc)²
    if 0 < j0 < M - 1:
        H[1, 1] = loss_arr[i0, j0+1] - 2*loss_arr[i0, j0] + loss_arr[i0, j0-1]
    # d²L/d(bs)d(bc)
    if 0 < i0 < N-1 and 0 < j0 < M-1:
        H[0, 1] = H[1, 0] = (loss_arr[i0+1, j0+1] - loss_arr[i0+1, j0-1]
                              - loss_arr[i0-1, j0+1] + loss_arr[i0-1, j0-1]) / 4.0

    eigenvalues = np.linalg.eigvalsh(H)
    eigenvalues = eigenvalues[eigenvalues > 1e-12]
    if len(eigenvalues) < 2:
        return np.inf
    return float(eigenvalues[-1] / eigenvalues[0])


def plot_landscape(ax, BS, BC, loss_arr, case, show_ylabel=True):
    bs_arr = BS[:, 0]
    bc_arr = BC[0, :]

    # Clip extreme values for display
    vmin, vmax = np.nanpercentile(loss_arr, 2), np.nanpercentile(loss_arr, 98)
    loss_clipped = np.clip(loss_arr, vmin, vmax)

    cf = ax.contourf(BC, BS, loss_clipped, levels=30, cmap='viridis_r')
    ax.contour(BC, BS, loss_clipped, levels=15, colors='white', linewidths=0.4, alpha=0.5)

    # Mark argmin
    bs0, bc0 = case['argmin']
    ax.scatter([bc0], [bs0], color='red', marker='*', s=200, zorder=5,
               label=f'argmin ({bs0:.0f}°, {bc0:.0f}°)')

    # HC ‖β̂‖ reference circle
    theta_range = np.linspace(0, np.pi, 200)  # bs≥0 constraint
    for r, ls in [(49, '--'), (65.3, '--'), (54.8, '-')]:
        bc_circ = r * np.cos(theta_range)
        bs_circ = r * np.sin(theta_range)
        mask = (bs_circ >= 0) & (bs_circ <= 50) & (bc_circ >= -50) & (bc_circ <= 50)
        if ls == '-':
            ax.plot(bc_circ[mask], bs_circ[mask], 'w-', lw=1.5, alpha=0.8,
                    label='HC ‖β̂‖ mean (54.8°)')
        else:
            ax.plot(bc_circ[mask], bs_circ[mask], 'w--', lw=0.8, alpha=0.5)

    # CVD norm
    bs0, bc0 = case['argmin']
    norm_cvd = np.sqrt(bs0**2 + bc0**2)
    theta_c = np.linspace(0, np.pi, 200)
    bc_c = norm_cvd * np.cos(theta_c)
    bs_c = norm_cvd * np.sin(theta_c)
    mask = (bs_c >= 0) & (bs_c <= 50) & (bc_c >= -50) & (bc_c <= 50)
    ax.plot(bc_c[mask], bs_c[mask], color=case['color'], lw=1.5, ls='-.', alpha=0.9,
            label=f'sub-{case["sid"]} ‖β̂‖={norm_cvd:.1f}°')

    sid = case['sid']
    family = case['family']
    ax.set_title(f'sub-{sid} ({family})\nargmin: β_s={case["argmin"][0]:.0f}°, β_c={case["argmin"][1]:.0f}°',
                 fontsize=10)
    ax.set_xlabel('β_c (°)', fontsize=9)
    if show_ylabel:
        ax.set_ylabel('β_s (°)', fontsize=9)
    ax.set_xlim(-50, 50)
    ax.set_ylim(0, 50)
    ax.legend(fontsize=7, loc='upper right')
    ax.axvline(0, color='white', lw=0.5, alpha=0.4)

    # Compute & report condition number
    i0 = np.argmin(np.abs(bs_arr - case['argmin'][0]))
    j0 = np.argmin(np.abs(bc_arr - case['argmin'][1]))
    cond = hessian_condition(loss_arr, (i0, j0))
    ax.text(0.02, 0.05, f'Hessian cond={cond:.1f}',
            transform=ax.transAxes, fontsize=8, color='yellow',
            bbox=dict(facecolor='black', alpha=0.5, pad=2))
    return cf, cond


def main():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('2-Component Loss Landscape (hV4, LOCO-primary)\nContourf: lower = better fit',
                 fontsize=11)

    results_summary = {}
    for ax, case in zip(axes, CASES):
        BS, BC, loss_arr = load_landscape(case['sid'])
        show_ylabel = (case['sid'] == '08')
        cf, cond = plot_landscape(ax, BS, BC, loss_arr, case, show_ylabel=show_ylabel)
        results_summary[f"sub-{case['sid']}"] = {
            'argmin': case['argmin'],
            'hessian_condition_number': round(cond, 2),
            'norm_cvd': round(float(np.sqrt(case['argmin'][0]**2 + case['argmin'][1]**2)), 2),
            'hc_norm_mean': 54.8,
            'hc_norm_range': [49.0, 65.3],
        }

    plt.colorbar(cf, ax=axes[1], label='Loss (lower=better)', shrink=0.8)
    plt.tight_layout()

    for ext in ['pdf', 'png']:
        out = OUT_DIR / f'loss_landscape_sub08_sub09.{ext}'
        plt.savefig(out, dpi=150, bbox_inches='tight')
        print(f'Saved: {out}')

    # Save summary JSON
    with open(OUT_DIR / 'identifiability_summary.json', 'w') as f:
        json.dump(results_summary, f, indent=2)
    print('Summary:')
    print(json.dumps(results_summary, indent=2))


if __name__ == '__main__':
    main()
