"""sub08_bc_bootstrap.py — Bootstrap V4 LOCO β_c CI for sub-08 + axis 180° flip test.

Two related questions:

  (a) Is β_c sign stable for sub-08 V4 LOCO under resampling?
      Approach: bootstrap over 8 colors (with replacement), recompute MSE per cell,
      find argmin → record β_c. Repeat N=2000 times. Report CI.

  (b) Does an axis 180° flip recover Brettel sign?
      Approach: re-evaluate the landscape with θ_conf = 150°+180° = 330°.
      Mathematically cos(θ - 330°) = -cos(θ - 150°), so this trivially flips
      β_c sign. The test exposes whether the DIRECTIONAL relationship between
      neural V4 LOCO and behavioral P2a-max is preserved under axis flip.

      Concretely: compute delta_theta profile at our argmin AND at P2a-max
      under both axis conventions. If profiles still disagree under flipped axis,
      the dissociation is NOT a convention artifact.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

OUT = _THIS_DIR.parent / 'results'
FILE_PREFIX = 'LIT2Neural_'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

CASES = {
    'sub-08_axis150': {
        'landscape': 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
        'axis': 150.0, 'family': 'deutan',
        'canonical': (38.0, -14.0),
        'p2a_max':   (26.0, +34.0),
    },
    'sub-08_axisCIELab175p7': {
        'landscape': 'results/axis_3way/sub-08_V4_CIELab175p7_landscape.json',
        'axis': 175.7, 'family': 'deutan',
        'canonical': (38.0, -14.0),
        'p2a_max':   (26.0, +34.0),
    },
}


def load_landscape(path):
    d = json.load(open(path))
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    bs = np.array([c['bs'] for c in cells])
    bc = np.array([c['bc'] for c in cells])
    vuln_sim = np.array([c['vuln_sim'] for c in cells])  # (n_cells, 8)
    # Original components from axis_3way (matching pre-bootstrap fit policy)
    l_topk = np.array([c['l_topk'] for c in cells])
    tikh = np.array([c['tikh'] for c in cells])
    ccc_raw = np.array([c['ccc'] for c in cells])  # for ccc bootstrap
    return bs, bc, vuln_sim, vuln_obs, l_topk, tikh, ccc_raw, cells


def lins_ccc(x, y):
    """Lin's concordance correlation coefficient."""
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    if sx < 1e-10 or sy < 1e-10:
        return 0.0
    cov = np.mean((x - mx) * (y - my))
    return 2 * cov / (sx**2 + sy**2 + (mx - my)**2)


def bootstrap_bc_ci(bs, bc, vuln_sim, vuln_obs, l_topk, tikh,
                     n_boot=2000, seed=42):
    """Bootstrap: resample 8 colors with replacement, recompute L_combined
    per cell, find argmin, record (β_s, β_c).

    L_combined ≈ l_ccc + l_topk + tikh (matches axis_3way landscape policy).
    l_ccc and tikh are recomputed under resampling; l_topk is approximated
    as constant (categorical top-k depends weakly on resampling — kept fixed).
    """
    rng = np.random.default_rng(seed)
    n_cells = vuln_sim.shape[0]

    bs_boot = np.empty(n_boot)
    bc_boot = np.empty(n_boot)
    for k in range(n_boot):
        idx = rng.integers(0, 8, size=8)
        # Resampled vuln_obs and per-cell vuln_sim
        obs_b = vuln_obs[idx]
        sim_b = vuln_sim[:, idx]  # (n_cells, 8)
        # Recompute l_ccc per cell (1 − CCC) / 2
        ccc_arr = np.empty(n_cells)
        for j in range(n_cells):
            ccc_arr[j] = lins_ccc(sim_b[j], obs_b)
        l_ccc_arr = (1.0 - ccc_arr) / 2.0
        L = l_ccc_arr + l_topk + tikh
        sort_key = L * 1e6 + (bs**2 + bc**2)
        i_min = int(np.argmin(sort_key))
        bs_boot[k] = bs[i_min]
        bc_boot[k] = bc[i_min]
    return bs_boot, bc_boot


def axis_flip_delta_theta(bs, bc, axis_conf):
    """Compute δθ profile at given (β_s, β_c, axis_conf)."""
    return (bs * np.cos(np.radians(HUE_8 - 90.0))
            + bc * np.cos(np.radians(HUE_8 - axis_conf)))


def main():
    results = {}
    for label, info in CASES.items():
        path = Path(info['landscape'])
        if not path.exists():
            print(f'SKIP {path}'); continue
        bs, bc, vuln_sim, vuln_obs, l_topk, tikh, ccc_raw, cells = load_landscape(path)

        # ----- (a) Bootstrap β_c CI -----
        bs_boot, bc_boot = bootstrap_bc_ci(bs, bc, vuln_sim, vuln_obs,
                                            l_topk, tikh, n_boot=2000)
        bs_median = float(np.median(bs_boot))
        bc_median = float(np.median(bc_boot))
        bc_ci_lo, bc_ci_hi = np.percentile(bc_boot, [2.5, 97.5])
        frac_bc_neg = float((bc_boot < 0).mean())
        frac_bc_pos = float((bc_boot > 0).mean())
        sign_consistency = max(frac_bc_neg, frac_bc_pos)

        # Where does the bootstrap cloud sit relative to canonical / P2a-max?
        canon_bs, canon_bc = info['canonical']
        p2a_bs, p2a_bc = info['p2a_max']
        frac_near_canon = float(((bs_boot - canon_bs)**2 + (bc_boot - canon_bc)**2 < 100).mean())
        frac_near_p2amax = float(((bs_boot - p2a_bs)**2 + (bc_boot - p2a_bc)**2 < 100).mean())

        # ----- (b) Axis flip — δθ profiles -----
        axis = info['axis']
        axis_flipped = (axis + 180.0) % 360.0
        # Canonical V4 LOCO (β_s, β_c) at axis vs axis_flipped
        canon_dtheta_at = axis_flip_delta_theta(canon_bs, canon_bc, axis)
        # Equivalent (β_s, -β_c) at axis_flipped should give SAME profile:
        canon_dtheta_at_flip = axis_flip_delta_theta(canon_bs, -canon_bc, axis_flipped)
        # Sanity check: identical
        assert np.allclose(canon_dtheta_at, canon_dtheta_at_flip, atol=1e-9)
        # P2a-max profile at axis
        p2a_dtheta = axis_flip_delta_theta(p2a_bs, p2a_bc, axis)

        # Cosine similarity between canonical and P2a-max δθ profiles (axis-invariant)
        cos_sim = float(np.dot(canon_dtheta_at, p2a_dtheta) /
                        (np.linalg.norm(canon_dtheta_at) * np.linalg.norm(p2a_dtheta) + 1e-9))

        print(f'\n=== {label} (axis={axis}°, family={info["family"]}) ===')
        print(f'  Bootstrap N=2000:')
        print(f'    β_s median = {bs_median:.1f}°,  β_c median = {bc_median:.1f}°  '
              f'[CI {bc_ci_lo:.1f}, {bc_ci_hi:.1f}]')
        print(f'    frac(β_c<0) = {frac_bc_neg:.3f}   frac(β_c>0) = {frac_bc_pos:.3f}'
              f'   → sign consistency = {sign_consistency:.3f}')
        print(f'    frac near canonical (within 10°) = {frac_near_canon:.3f}')
        print(f'    frac near P2a-max  (within 10°) = {frac_near_p2amax:.3f}')
        print(f'\n  Axis flip:')
        print(f'    canon δθ at axis={axis}°:      {canon_dtheta_at.round(1).tolist()}')
        print(f'    P2a-max δθ at axis={axis}°:    {p2a_dtheta.round(1).tolist()}')
        print(f'    cos similarity canon ↔ P2a-max δθ: {cos_sim:+.3f}')
        print(f'    (axis flip simply renames β_c → −β_c; δθ profile is invariant)')

        results[label] = {
            'axis': axis,
            'axis_flipped': axis_flipped,
            'family': info['family'],
            'bootstrap': {
                'n_boot': 2000,
                'bs_median': bs_median,
                'bc_median': bc_median,
                'bc_ci_2p5':  float(bc_ci_lo),
                'bc_ci_97p5': float(bc_ci_hi),
                'frac_bc_negative':  frac_bc_neg,
                'frac_bc_positive':  frac_bc_pos,
                'sign_consistency':  sign_consistency,
                'frac_near_canonical':  frac_near_canon,
                'frac_near_p2amax':     frac_near_p2amax,
                'bs_boot_samples': bs_boot.tolist()[:200],  # truncate for json
                'bc_boot_samples': bc_boot.tolist()[:200],
            },
            'axis_flip_test': {
                'canon_delta_theta_axis': canon_dtheta_at.tolist(),
                'p2a_max_delta_theta_axis': p2a_dtheta.tolist(),
                'cos_similarity': cos_sim,
                'note': 'Axis 180° flip negates β_c but leaves δθ profile invariant. '
                        'Therefore neural-behavioral δθ disagreement (cos < 1) is '
                        'NOT resolvable by axis convention.',
            },
        }

    with open(OUT / 'sub08_bc_bootstrap.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nWrote {OUT / "sub08_bc_bootstrap.json"}')

    # ---- Visualization ----
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    fig, axs = plt.subplots(1, 2, figsize=(13, 5))

    # Left: bootstrap scatter
    ax = axs[0]
    for label, r in results.items():
        if 'bootstrap' not in r: continue
        bs_s = np.array(r['bootstrap']['bs_boot_samples'])
        bc_s = np.array(r['bootstrap']['bc_boot_samples'])
        ax.scatter(bs_s, bc_s, alpha=0.35, s=14,
                   label=f'{label} (N=200 shown)')
    canon = CASES['sub-08_axis150']['canonical']
    p2a = CASES['sub-08_axis150']['p2a_max']
    ax.plot(*canon, 's', mfc='none', mec='red', ms=14, mew=2,
            label=f'canonical §3 ({canon[0]:.0f},{canon[1]:+.0f})')
    ax.plot(*p2a, '*', mfc='gold', mec='black', ms=20, mew=0.7,
            label=f'P2a-max ({p2a[0]:.0f},{p2a[1]:+.0f})')
    ax.axhline(0, color='gray', lw=0.5)
    ax.axvline(0, color='gray', lw=0.5)
    ax.set_xlabel(r'$\beta_s$ (°)')
    ax.set_ylabel(r'$\beta_c$ (°)')
    ax.set_title('sub-08 V4 bootstrap argmin distribution\n(2000 color-resampled MSE refits)')
    ax.legend(fontsize=8, loc='best')

    # Right: δθ profile comparison
    ax = axs[1]
    r0 = results['sub-08_axis150']
    canon_dt = np.array(r0['axis_flip_test']['canon_delta_theta_axis'])
    p2a_dt = np.array(r0['axis_flip_test']['p2a_max_delta_theta_axis'])
    x = HUE_8
    ax.plot(x, canon_dt, 'o-', color='red', lw=2, ms=8,
            label=f'V4 LOCO canonical (38,−14)')
    ax.plot(x, p2a_dt, '*-', color='goldenrod', lw=2, ms=12,
            label=f'P2a-max (26,+34)')
    ax.axhline(0, color='gray', lw=0.5)
    ax.set_xlabel('Hue angle (°)')
    ax.set_ylabel(r'$\delta\theta$ (°)')
    ax.set_title(f'sub-08 δθ profile: neural vs behavioral\n'
                 f'cos similarity = {r0["axis_flip_test"]["cos_similarity"]:+.3f}')
    ax.set_xticks(HUE_8)
    ax.legend()
    ax.grid(alpha=0.3)

    fig.suptitle('Sub-08 β_c sign stability + axis 180° flip diagnostic',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        out = OUT / f'fig_sub08_bc_bootstrap.{ext}'
        fig.savefig(out, dpi=180, bbox_inches='tight')
        print(f'wrote {out}')
    plt.close(fig)


if __name__ == '__main__':
    main()
