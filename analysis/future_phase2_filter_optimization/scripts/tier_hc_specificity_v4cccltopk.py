"""tier_hc_specificity_v4cccltopk.py — HC specificity check + HC landscape maps.

For V4-CCC + l_topk wretrained loss (current BEST):
  L = 1.0·L_ccc + 0.5·l_topk(V4, K=3) + 0.1·L_smooth

For each HC subject (sub-01..06):
  1. Load HC LOO landscape (vuln_sim per cell cached from HC sanity work)
  2. Load HC's own LOCO vuln target
  3. Compute V4-CCC + l_topk loss per cell
  4. Find HC argmin (β_s, β_c, norm)
  5. Render landscape figure

HC specificity (bootstrap CI):
  - Collect 6 HC argmin norms
  - Bootstrap 10000 resamples of mean → boot_frac per CVD filter
  - Verdict: ✓✓ ≥0.975 | ~~ 0.90-0.975 | ✗ <0.90

Output: results/CANDIDATE/v4ccc_ltopk/
"""
from __future__ import annotations
import json
import sys
import csv
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from old_formula_refit import load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
HC_SANITY = _PHASE2 / 'results' / 'fits' / 'phase_a_2component_hc_sanity'
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'v4ccc_ltopk'
OUT.mkdir(parents=True, exist_ok=True)

HC_SUBJECTS = ['01', '02', '03', '04', '05', '06']  # sub-07 V4 has 16 voxels (nan risk)
LAMBDA_TOPK = 0.5
K_TOPK = 3


def ccc_value(sim, obs):
    sim = np.asarray(sim); obs = np.asarray(obs)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std(); sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


def l_topk_jaccard(sim, obs, K=K_TOPK):
    s = np.asarray(sim); o = np.asarray(obs)
    top_s = set(np.argsort(s)[:K].tolist())
    top_o = set(np.argsort(o)[:K].tolist())
    inter = len(top_s & top_o); union = len(top_s | top_o)
    return 1.0 - (inter / union)


def grid_to_arr(cells, key, key_for_bs='bs', key_for_bc='bc'):
    bs_all = sorted(set(c[key_for_bs] for c in cells))
    bc_all = sorted(set(c[key_for_bc] for c in cells))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for c in cells:
        arr[bc_idx[c[key_for_bc]], bs_idx[c[key_for_bs]]] = c[key]
    return np.array(bs_all), np.array(bc_all), arr


def load_hc_landscape(hc_id):
    fn = HC_SANITY / f'sub-{hc_id}_V4_2component.json'
    d = json.load(open(fn))
    return d  # has 'landscape' with vuln_sim per cell


def render_hc_landscape(hc_id, cells, best, vuln_obs, out_path):
    """Cells with bs, bc, L_combined. Render landscape colored by L_combined."""
    bs, bc, arr = grid_to_arr(cells, 'L_combined')
    arr_finite = arr[np.isfinite(arr)]
    vmin = float(np.percentile(arr_finite, 1))
    vmax = float(np.percentile(arr_finite, 95))

    fig, ax = plt.subplots(figsize=(5.8, 4.8), dpi=150)
    im = ax.pcolormesh(bs, bc, arr, cmap='RdBu_r', vmin=vmin, vmax=vmax,
                       shading='nearest', rasterized=True)
    ax.plot(best['bs'], best['bc'], '*', color='white', ms=14,
            markeredgecolor='black', markeredgewidth=0.8, zorder=10)

    bs_arr = np.array(bs); bc_arr = np.array(bc)
    if best['bs'] >= np.median(bs_arr):
        lbl_x, lbl_ha = best['bs'] - 2, 'right'
    else:
        lbl_x, lbl_ha = best['bs'] + 2, 'left'
    if best['bc'] >= np.median(bc_arr):
        lbl_y, lbl_va = best['bc'] - 3, 'top'
    else:
        lbl_y, lbl_va = best['bc'] + 3, 'bottom'
    ax.text(lbl_x, lbl_y,
            f"HC argmin: β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
            f"norm={best['norm']:.1f}°\n"
            f"L_combined={best['L_combined']:.3f}\n"
            f"(range [{arr_finite.min():.2f}, {arr_finite.max():.2f}])",
            fontsize=7, color='white', ha=lbl_ha, va=lbl_va, zorder=11,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.65, lw=0))
    ax.set_xlabel('β_s — S-cone shift (°)')
    ax.set_ylabel('β_c — confusion rotation (°)')
    ax.set_title(
        f"HC sub-{hc_id} V4 LOO — V4-CCC+l_topk landscape (wretrained)\n"
        f"argmin (BLUE = cold)",
        fontweight='bold', fontsize=10)
    cb = fig.colorbar(im, ax=ax, extend='both')
    cb.set_label(f'L_combined (vmin={vmin:.2f}, vmax={vmax:.2f})')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)


def main():
    print(f'OUTDIR: {OUT}')
    print(f'HC subjects: {HC_SUBJECTS}')
    print(f'Loss: L = 1·L_ccc + {LAMBDA_TOPK}·l_topk + 0.1·L_smooth')
    print()

    hc_argmins = {}
    for hc_id in HC_SUBJECTS:
        print(f'=== HC sub-{hc_id} ===', flush=True)
        d = load_hc_landscape(hc_id)
        ls = d['landscape']
        # vuln_obs = HC i's own LOCO vuln target
        try:
            vuln_obs = np.array(load_cvd_loco_target(hc_id, 'V4'))
        except Exception as e:
            print(f'  Failed to load vuln_obs: {e} — using baseline as proxy')
            vuln_obs = np.array(d['baseline']['vuln_baseline'])
        print(f'  vuln_obs top-3 idx: {np.argsort(vuln_obs)[:3].tolist()}')

        # For each cell, recompute V4-CCC + l_topk loss using vuln_obs
        out_cells = []
        for c in ls:
            sim = np.asarray(c['vuln_sim'])
            ccc = ccc_value(sim, vuln_obs)
            l_ccc = (1.0 - ccc) / 2.0
            lt = l_topk_jaccard(sim, vuln_obs, K=K_TOPK)
            l_smooth = c['l_smooth']  # cached, doesn't depend on target
            L_combined = 1.0 * l_ccc + LAMBDA_TOPK * lt + 0.1 * l_smooth
            bs, bc = c['params']
            out_cells.append({
                'bs': float(bs), 'bc': float(bc),
                'l_ccc': float(l_ccc), 'l_topk': float(lt),
                'l_smooth': float(l_smooth),
                'L_combined': float(L_combined),
                'ccc': float(ccc),
                'spearman_r': float(c['spearman_r']),
            })
        best = min(out_cells, key=lambda x: x['L_combined'])
        norm = float(np.hypot(best['bs'], best['bc']))
        best['norm'] = norm
        hc_argmins[hc_id] = best
        print(f'  argmin: β=({best["bs"]:.0f}, {best["bc"]:+.0f}) norm={norm:.1f}°  '
              f'L={best["L_combined"]:.3f}  ρ={best["spearman_r"]:.3f}')

        # Render landscape
        out_path = OUT / f'hc_landscape_sub-{hc_id}_V4_V4CCCltopk.png'
        render_hc_landscape(hc_id, out_cells, best, vuln_obs, out_path)

    # Save HC argmins CSV
    csv_path = OUT / 'hc_argmins.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['hc_id', 'bs', 'bc', 'norm', 'l_ccc', 'l_topk',
                    'l_smooth', 'L_combined', 'spearman_r', 'ccc'])
        for hc, a in hc_argmins.items():
            w.writerow([f'sub-{hc}', a['bs'], a['bc'], round(a['norm'], 2),
                        round(a['l_ccc'], 4), round(a['l_topk'], 4),
                        round(a['l_smooth'], 4), round(a['L_combined'], 4),
                        round(a['spearman_r'], 3), round(a['ccc'], 3)])

    # Bootstrap CI specificity
    norms = np.array([a['norm'] for a in hc_argmins.values()])
    print(f'\n=== HC norms ===')
    print(f'  values: {norms.round(1).tolist()}')
    print(f'  mean={norms.mean():.2f}, std={norms.std(ddof=1):.2f}')
    print(f'  range [{norms.min():.2f}, {norms.max():.2f}]')

    # Bootstrap
    rng = np.random.default_rng(42)
    n_boot = 10000
    boot_means = rng.choice(norms, size=(n_boot, len(norms)), replace=True).mean(axis=1)
    print(f'  bootstrap mean dist: [{np.percentile(boot_means, 2.5):.2f}, '
          f'{np.percentile(boot_means, 97.5):.2f}] (95% CI)')

    # Specificity check for candidate filters
    candidates = [
        ('BEST sub-08 V4-CCC+l_topk', 44, 28),
        ('BEST sub-09 V4-CCC alone', 30, 46),
        ('Tier 2 sub-08 V4-CCC+SRM RDM', 50, 24),
        ('Tier 2 sub-09 V4-CCC+SRM RDM', 34, 44),
        ('Previous best sub-08 V4-CCC alone', 16, 40),
        ('§3 canonical sub-08', 38, -14),
        ('Phase A LOCO sub-09', 6, -22),
    ]
    spec_rows = []
    print(f'\n=== Specificity check (vs HC bootstrap CI, n_boot={n_boot}) ===')
    for name, bs, bc in candidates:
        cvd_norm = float(np.hypot(bs, bc))
        boot_frac = float((boot_means < cvd_norm).mean())
        if boot_frac >= 0.975:
            verdict = '✓✓ both sig'
        elif boot_frac >= 0.90:
            verdict = '~~ marginal'
        else:
            verdict = '✗ inside HC CI'
        spec_rows.append({
            'filter': name, 'bs': bs, 'bc': bc, 'cvd_norm': cvd_norm,
            'boot_frac': boot_frac, 'verdict': verdict,
        })
        print(f'  {name:42s}  β=({bs:+.0f}, {bc:+.0f})  '
              f'norm={cvd_norm:.1f}°  boot_frac={boot_frac:.4f}  {verdict}')

    # Save specificity CSV
    spec_csv = OUT / 'hc_specificity.csv'
    with open(spec_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['filter', 'bs', 'bc', 'cvd_norm', 'hc_mean', 'hc_std',
                    'hc_min', 'hc_max', 'boot_frac', 'verdict'])
        for r in spec_rows:
            w.writerow([r['filter'], r['bs'], r['bc'],
                        round(r['cvd_norm'], 2),
                        round(float(norms.mean()), 2),
                        round(float(norms.std(ddof=1)), 2),
                        round(float(norms.min()), 2),
                        round(float(norms.max()), 2),
                        round(r['boot_frac'], 4), r['verdict']])
    print(f'\nWrote {csv_path}')
    print(f'Wrote {spec_csv}')

    # Summary md
    md = []
    md.append('# HC Specificity — V4-CCC + l_topk wretrained')
    md.append('')
    md.append(f'**Loss**: `L = 1·L_ccc + {LAMBDA_TOPK}·l_topk(V4, K=3) + 0.1·L_smooth`')
    md.append(f'**Simulator**: wretrained')
    md.append(f'**HC pool**: sub-01..06 (sub-07 V4 excluded — 16 voxels nan risk)')
    md.append('')
    md.append('## HC argmins under V4-CCC + l_topk loss')
    md.append('')
    md.append('| HC | argmin (β_s, β_c) | norm | L_combined | ρ | l_topk | CCC |')
    md.append('|---|---|---|---|---|---|---|')
    for hc, a in hc_argmins.items():
        md.append(f"| sub-{hc} | ({a['bs']:.0f}, {a['bc']:+.0f}) | {a['norm']:.1f}° | "
                  f"{a['L_combined']:.3f} | {a['spearman_r']:.3f} | "
                  f"{a['l_topk']:.3f} | {a['ccc']:.3f} |")
    md.append('')
    md.append(f'**HC mean norm**: {norms.mean():.2f}°  std: {norms.std(ddof=1):.2f}°  '
              f'range [{norms.min():.1f}, {norms.max():.1f}]')
    md.append('')
    md.append(f'## Bootstrap CI (n_boot={n_boot})')
    md.append('')
    md.append('| Filter | (β_s, β_c) | norm | boot_frac | Verdict |')
    md.append('|---|---|---|---|---|')
    for r in spec_rows:
        md.append(f"| {r['filter']} | ({r['bs']:+.0f}, {r['bc']:+.0f}) | "
                  f"{r['cvd_norm']:.1f}° | {r['boot_frac']:.4f} | {r['verdict']} |")
    md.append('')
    md.append('## Files')
    md.append('- `hc_argmins.csv` — per-HC argmin under V4-CCC+l_topk')
    md.append('- `hc_specificity.csv` — per-candidate specificity bootstrap result')
    md.append('- `hc_landscape_sub-XX_V4_V4CCCltopk.png/pdf` — per-HC landscape (6 figs)')
    (OUT / 'hc_specificity_summary.md').write_text('\n'.join(md))
    print(f'Wrote {OUT / "hc_specificity_summary.md"}')


if __name__ == '__main__':
    main()
