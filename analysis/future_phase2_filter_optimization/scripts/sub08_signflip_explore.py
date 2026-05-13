"""sub08_signflip_explore.py — 다각도 sub-08 β_c sign 탐색.

The question: Is sub-08 V4 β_c sign POSITIVE (consistent with P2a-max +34, Brettel
deutan +) or NEGATIVE (consistent with phase_a V4/V1 LOCO 2-comp)? Currently both
appear in different loss formulations.

Approaches:
  (1) Multi-metric argmin on sub-08 V4 landscape (axis_3way Stockman 150°):
      L_ccc, L_pearson_rescaled, L_rdm_cosine, L_spearman, L_pearson_raw, L_ccc+l_topk
      — each metric finds its own argmin; tabulate β_c signs.
  (2) Loss-independent direct projection:
      Project observed `vuln_obs` onto 2-component basis (β_s·cos(θ-90°), β_c·cos(θ-150°))
      via least-squares. This gives β with no loss-prior.
  (3) HC LOO comparison:
      For each HC (sub-01..06), find argmin under L_combined; where do HCs cluster?
      If sub-08 (40, +22) overlaps HC cluster → not CVD-specific.
  (4) Local minimum structure:
      Find all local minima of L_combined (8-neighbor); report top-3 minima
      coordinates, separation.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

_PHASE2 = _THIS_DIR.parent
OUT = _PHASE2 / 'results'
PREFIX = 'LIT2Neural_signflip_'

LANDSCAPE_SUB08 = _PHASE2 / 'results' / 'axis_3way' / 'sub-08_V4_Stockman150_landscape.json'
HC_LOO_DIR = _PHASE2 / 'results' / 'fits' / 'phase_a_2component_hc_sanity'

HUE_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
AXIS_CONF = 150.0  # Stockman deutan

# Reference points
P2A_MAX_08 = (26.0, +34.0)
PHASE_A_08 = (38.0, -14.0)   # canonical V4 LOCO 2-comp
LCOMB_BOOT_08 = (40.0, +22.0)  # L_combined bootstrap median


# ---------- metrics ----------
def lins_ccc(x, y):
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    if sx < 1e-10 or sy < 1e-10:
        return 0.0
    cov = np.mean((x - mx) * (y - my))
    return 2 * cov / (sx**2 + sy**2 + (mx - my)**2)


def metric_pearson_raw(sim, obs):
    if np.std(sim) < 1e-10:
        return 1.0
    r, _ = pearsonr(sim, obs)
    return float(1.0 - r) / 2 if np.isfinite(r) else 1.0


def metric_pearson_rescaled(sim, obs):
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 1.0
    sim_z = (sim - sim.mean()) / sim.std()
    obs_z = (obs - obs.mean()) / obs.std()
    r, _ = pearsonr(sim_z, obs_z)
    return float(1.0 - r) / 2 if np.isfinite(r) else 1.0


def metric_spearman(sim, obs):
    if np.std(sim) < 1e-10:
        return 1.0
    r, _ = spearmanr(sim, obs)
    return float(1.0 - r) / 2 if np.isfinite(r) else 1.0


def metric_rdm_cosine(sim, obs):
    iu = np.triu_indices(len(sim), k=1)
    rdm_s = np.abs(sim[:, None] - sim[None, :])[iu]
    rdm_o = np.abs(obs[:, None] - obs[None, :])[iu]
    nsim, nobs = np.linalg.norm(rdm_s), np.linalg.norm(rdm_o)
    if nsim < 1e-10 or nobs < 1e-10:
        return 1.0
    return float(1.0 - np.dot(rdm_s, rdm_o) / (nsim * nobs)) / 2


def metric_ccc(sim, obs):
    return (1.0 - lins_ccc(sim, obs)) / 2


def metric_mse(sim, obs):
    return float(np.mean((sim - obs) ** 2))


# ---------- 1: multi-metric argmin on sub-08 V4 ----------
def multi_metric_argmin(landscape_path):
    d = json.load(open(landscape_path))
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    bs = np.array([c['bs'] for c in cells])
    bc = np.array([c['bc'] for c in cells])
    sim = np.array([c['vuln_sim'] for c in cells])
    l_topk = np.array([c['l_topk'] for c in cells])
    tikh = np.array([c['tikh'] for c in cells])

    metrics = {
        'L_ccc':            np.array([metric_ccc(s, vuln_obs) for s in sim]),
        'L_pearson_raw':    np.array([metric_pearson_raw(s, vuln_obs) for s in sim]),
        'L_pearson_resc':   np.array([metric_pearson_rescaled(s, vuln_obs) for s in sim]),
        'L_spearman':       np.array([metric_spearman(s, vuln_obs) for s in sim]),
        'L_rdm_cosine':     np.array([metric_rdm_cosine(s, vuln_obs) for s in sim]),
        'L_mse':            np.array([metric_mse(s, vuln_obs) for s in sim]),
    }
    metrics['L_combined'] = metrics['L_ccc'] + l_topk + tikh
    metrics['L_ccc+ltopk'] = metrics['L_ccc'] + l_topk

    results = {}
    for name, L in metrics.items():
        # No tie-break by amplitude (we want raw metric argmin)
        idx = int(np.argmin(L))
        results[name] = {
            'bs': float(bs[idx]), 'bc': float(bc[idx]),
            'L_min': float(L[idx]),
            'sign': '+' if bc[idx] > 0 else ('-' if bc[idx] < 0 else '0'),
        }
    # Also with Tikh tie-break (matches actual fit policy)
    for name in list(metrics.keys()):
        L = metrics[name]
        sort_key = L * 1e6 + (bs**2 + bc**2)
        idx = int(np.argmin(sort_key))
        results[f'{name}_tikhTie'] = {
            'bs': float(bs[idx]), 'bc': float(bc[idx]),
            'L_min': float(L[idx]),
            'sign': '+' if bc[idx] > 0 else ('-' if bc[idx] < 0 else '0'),
        }
    return results, vuln_obs, bs, bc, sim


# ---------- 2: loss-independent direct projection ----------
def direct_projection(vuln_obs):
    """Fit vuln_obs ≈ a·cos(θ-90°) + b·cos(θ-AXIS_CONF) + c (constant).
    Returns least-squares (β_s, β_c) — NO loss minimization."""
    # Design matrix
    th = np.deg2rad(HUE_8)
    X = np.column_stack([
        np.cos(th - np.pi/2),                       # β_s basis
        np.cos(th - np.deg2rad(AXIS_CONF)),         # β_c basis
        np.ones_like(th),                           # constant (mean)
    ])
    # Least squares
    coef, *_ = np.linalg.lstsq(X, vuln_obs, rcond=None)
    beta_s_lsq, beta_c_lsq, const = coef
    # Reconstruction
    pred = X @ coef
    r, _ = pearsonr(pred, vuln_obs)
    return {
        'beta_s_lsq': float(beta_s_lsq),
        'beta_c_lsq': float(beta_c_lsq),
        'constant':   float(const),
        'pearson_r':  float(r) if np.isfinite(r) else 0.0,
        'sign':       '+' if beta_c_lsq > 0 else ('-' if beta_c_lsq < 0 else '0'),
    }


# ---------- 3: HC LOO argmin under each metric ----------
def hc_argmin_distribution(hc_dir, metric_name='L_combined'):
    """For each HC (01..06), find V4 2-comp argmin under L_combined."""
    hc_results = {}
    for k in range(1, 7):
        path = hc_dir / f'sub-0{k}_V4_2component.json'
        if not path.exists():
            continue
        d = json.load(open(path))
        # The hc_sanity landscape uses the phase_a L_fit, not L_combined
        # We need raw (bs, bc, vuln_sim) to recompute L_combined
        # But HC sanity files don't include vuln_obs (HC has no CVD target)
        # Use the recorded best_params (phase_a L_fit argmin)
        bp = d.get('best_params')
        if bp:
            hc_results[f'sub-0{k}'] = {
                'bs_phase_a': float(bp[0]),
                'bc_phase_a': float(bp[1]),
                'sign': '+' if bp[1] > 0 else ('-' if bp[1] < 0 else '0'),
            }
    return hc_results


# ---------- 4: Local minima of L_combined ----------
def find_local_minima(L_grid, bs_vals, bc_vals, top_n=5):
    """Find local minima in 2D loss grid using 8-neighbor comparison."""
    nbc, nbs = L_grid.shape
    minima = []
    for j in range(1, nbc - 1):
        for i in range(1, nbs - 1):
            center = L_grid[j, i]
            neighbors = L_grid[j-1:j+2, i-1:i+2].copy()
            neighbors[1, 1] = np.inf  # exclude center
            if center < neighbors.min():
                minima.append({
                    'bs': float(bs_vals[i]), 'bc': float(bc_vals[j]),
                    'L': float(center),
                })
    minima.sort(key=lambda m: m['L'])
    return minima[:top_n]


# ---------- Main ----------
def main():
    print('=' * 100)
    print('SUB-08 V4 β_c SIGN FLIP EXPLORATION')
    print('Axis = Stockman 150° (deutan canonical)')
    print('=' * 100)

    # (1) Multi-metric argmin
    results, vuln_obs, bs, bc, sim = multi_metric_argmin(LANDSCAPE_SUB08)
    print('\n--- (1) Multi-metric argmin on sub-08 V4 landscape ---')
    print(f'  {"metric":<28s}  {"argmin":<14s}  {"L_min":>7s}  sign')
    for name, r in results.items():
        marker = '+' if name.endswith('_tikhTie') else ' '
        print(f'  {marker}{name:<27s}  ({r["bs"]:>3.0f}°, {r["bc"]:>+4.0f}°)  '
              f'{r["L_min"]:>7.3f}   {r["sign"]}')

    # (2) Direct projection (loss-independent)
    proj = direct_projection(vuln_obs)
    print('\n--- (2) Direct least-squares projection onto 2-comp basis ---')
    print(f'  vuln_obs ≈ ({proj["beta_s_lsq"]:+.1f})·cos(θ-90°) '
          f'+ ({proj["beta_c_lsq"]:+.1f})·cos(θ-150°) + ({proj["constant"]:+.2f})')
    print(f'  Pearson r reconstruction = {proj["pearson_r"]:+.3f}')
    print(f'  β_c sign (loss-independent): {proj["sign"]}')

    # (3) HC distribution
    hc = hc_argmin_distribution(HC_LOO_DIR)
    print('\n--- (3) HC LOO V4 phase_a 2-comp argmin (sub-01..06) ---')
    print(f'  {"subject":<10s}  {"argmin":<14s}  sign')
    bc_pos_count = 0; bc_neg_count = 0
    for sid, r in hc.items():
        print(f'  {sid:<10s}  ({r["bs_phase_a"]:>3.0f}°, {r["bc_phase_a"]:>+4.0f}°)   '
              f'{r["sign"]}')
        if r['sign'] == '+': bc_pos_count += 1
        elif r['sign'] == '-': bc_neg_count += 1
    print(f'  → HC sign distribution: + = {bc_pos_count}, − = {bc_neg_count}')

    # (4) Local minima
    bs_vals = sorted(set(bs))
    bc_vals = sorted(set(bc))
    L_grid = np.full((len(bc_vals), len(bs_vals)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_vals)}
    bc_idx = {v: i for i, v in enumerate(bc_vals)}
    L_arr = np.array([c['L_combined'] for c in json.load(open(LANDSCAPE_SUB08))['cells']])
    for k, (b, c, L) in enumerate(zip(bs, bc, L_arr)):
        L_grid[bc_idx[c], bs_idx[b]] = L
    minima = find_local_minima(L_grid, bs_vals, bc_vals, top_n=5)
    print('\n--- (4) Top-5 local minima of L_combined (8-neighbor) ---')
    print(f'  {"rank":<5s}  {"argmin":<14s}  {"L":>7s}  sign')
    for r, m in enumerate(minima, 1):
        sign = '+' if m['bc'] > 0 else ('-' if m['bc'] < 0 else '0')
        print(f'  {r:<5d}  ({m["bs"]:>3.0f}°, {m["bc"]:>+4.0f}°)  {m["L"]:>7.3f}   {sign}')

    # Summary
    print('\n' + '=' * 100)
    print('SIGN VERDICT SUMMARY')
    print('=' * 100)
    pos = sum(1 for n, r in results.items() if r['sign'] == '+' and not n.endswith('_tikhTie'))
    neg = sum(1 for n, r in results.items() if r['sign'] == '-' and not n.endswith('_tikhTie'))
    print(f'  Metrics (no tie-break) yielding β_c > 0: {pos}/{8}')
    print(f'  Metrics (no tie-break) yielding β_c < 0: {neg}/{8}')
    print(f'  Direct projection (loss-independent): β_c = {proj["beta_c_lsq"]:+.2f} ({proj["sign"]})')
    print(f'  HC LOO under phase_a L_fit: +{bc_pos_count} / −{bc_neg_count}')
    print(f'  Top local minima signs: {[m["bc"] for m in minima[:3]]}')

    summary = {
        'subject': 'sub-08',
        'axis': AXIS_CONF,
        'reference_points': {
            'P2a_max': P2A_MAX_08,
            'phase_a_canonical': PHASE_A_08,
            'L_combined_bootstrap': LCOMB_BOOT_08,
        },
        'multi_metric_argmin': results,
        'direct_projection': proj,
        'hc_loo_phase_a': hc,
        'local_minima_top5': minima,
        'sign_verdict': {
            'pos_count_no_tie': pos,
            'neg_count_no_tie': neg,
            'direct_proj_sign': proj['sign'],
            'hc_pos': bc_pos_count,
            'hc_neg': bc_neg_count,
        },
    }
    out_json = OUT / f'{PREFIX}sub08_signflip.json'
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nWrote {out_json}')

    # ---------- Visualization ----------
    _render_signflip_fig(results, proj, hc, minima, L_grid, bs_vals, bc_vals,
                          vuln_obs)


def _render_signflip_fig(results, proj, hc, minima, L_grid, bs_vals, bc_vals,
                         vuln_obs):
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(2, 3, hspace=0.30, wspace=0.25,
                          left=0.05, right=0.97, top=0.94, bottom=0.06)

    # Panel A — Multi-metric argmin scatter
    ax = fig.add_subplot(gs[0, 0])
    extent = [min(bs_vals)-1, max(bs_vals)+1, min(bc_vals)-1, max(bc_vals)+1]
    ax.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
              cmap='RdBu_r', alpha=0.4,
              vmin=np.nanpercentile(L_grid, 5),
              vmax=np.nanpercentile(L_grid, 95))
    base_metrics = [n for n in results if not n.endswith('_tikhTie')]
    colors = plt.cm.Set1(np.linspace(0, 1, len(base_metrics)))
    for name, col in zip(base_metrics, colors):
        r = results[name]
        ax.plot(r['bs'], r['bc'], 'o', mfc=col, mec='black', ms=10, mew=0.8,
                label=f'{name} ({r["bs"]:.0f},{r["bc"]:+.0f})')
    # References
    ax.plot(*P2A_MAX_08, marker='*', mfc='gold', mec='black', ms=22, mew=0.8,
            label=f'P2a-max ({P2A_MAX_08[0]:.0f},{P2A_MAX_08[1]:+.0f})')
    ax.plot(*PHASE_A_08, marker='s', mfc='none', mec='red', ms=14, mew=1.6,
            label=f'phase_a §3 ({PHASE_A_08[0]:.0f},{PHASE_A_08[1]:+.0f})')
    ax.axhline(0, color='gray', lw=0.4)
    ax.axvline(0, color='gray', lw=0.4)
    ax.set_xlabel(r'$\beta_s$ (°)')
    ax.set_ylabel(r'$\beta_c$ (°)')
    ax.set_title('Panel A — Multi-metric argmin', fontweight='bold')
    ax.legend(fontsize=6, loc='upper right')

    # Panel B — sign verdict bar
    ax = fig.add_subplot(gs[0, 1])
    sign_counts = {'β_c > 0': 0, 'β_c < 0': 0, 'β_c = 0': 0}
    for name in base_metrics:
        s = results[name]['sign']
        if s == '+': sign_counts['β_c > 0'] += 1
        elif s == '-': sign_counts['β_c < 0'] += 1
        else: sign_counts['β_c = 0'] += 1
    bars = ax.bar(sign_counts.keys(), sign_counts.values(),
                   color=['#3CB371', '#DC143C', '#888888'], alpha=0.8)
    for b, v in zip(bars, sign_counts.values()):
        ax.text(b.get_x() + b.get_width()/2, v + 0.05, str(v),
                ha='center', fontsize=10, fontweight='bold')
    ax.set_ylabel('# metrics')
    ax.set_title('Panel B — β_c sign distribution\n(across 8 raw metrics)',
                 fontweight='bold')
    ax.set_ylim(0, max(sign_counts.values()) + 1.5)

    # Panel C — Direct projection
    ax = fig.add_subplot(gs[0, 2])
    th = np.deg2rad(HUE_8)
    X = np.column_stack([
        np.cos(th - np.pi/2),
        np.cos(th - np.deg2rad(AXIS_CONF)),
        np.ones_like(th),
    ])
    coef = np.array([proj['beta_s_lsq'], proj['beta_c_lsq'], proj['constant']])
    pred = X @ coef
    ax.plot(HUE_8, vuln_obs, 'ko-', ms=7, label='Observed vuln')
    ax.plot(HUE_8, pred, 's-', color='#1f77b4', ms=6, lw=1.5,
            label=fr'LSQ fit ($\beta_s$={proj["beta_s_lsq"]:+.1f}, '
                  fr'$\beta_c$={proj["beta_c_lsq"]:+.1f})')
    ax.axhline(0, color='gray', lw=0.4)
    ax.set_xticks(HUE_8)
    ax.set_xticklabels(['R','O','Y','G','C','B','P','M'])
    ax.set_xlabel('Hue')
    ax.set_ylabel('vuln')
    ax.set_title(f'Panel C — Loss-independent projection\n'
                 f'r={proj["pearson_r"]:+.2f}, β_c sign = {proj["sign"]}',
                 fontweight='bold')
    ax.legend(fontsize=7)
    ax.spines[['top','right']].set_visible(False)

    # Panel D — HC LOO distribution
    ax = fig.add_subplot(gs[1, 0])
    hc_bs = [r['bs_phase_a'] for r in hc.values()]
    hc_bc = [r['bc_phase_a'] for r in hc.values()]
    ax.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
              cmap='RdBu_r', alpha=0.4,
              vmin=np.nanpercentile(L_grid, 5),
              vmax=np.nanpercentile(L_grid, 95))
    ax.scatter(hc_bs, hc_bc, c='cyan', s=80, edgecolors='black', linewidth=0.8,
               label=f'HC sub-01..06 (n={len(hc_bs)})')
    for sid, r in hc.items():
        ax.annotate(sid.replace('sub-', ''), (r['bs_phase_a'], r['bc_phase_a']),
                    xytext=(3, 3), textcoords='offset points', fontsize=6)
    ax.plot(*PHASE_A_08, marker='s', mfc='none', mec='red', ms=14, mew=1.6,
            label='sub-08 phase_a')
    ax.plot(*LCOMB_BOOT_08, marker='o', mfc='white', mec='black', ms=14, mew=1.5,
            label='sub-08 L_comb boot')
    ax.plot(*P2A_MAX_08, marker='*', mfc='gold', mec='black', ms=20, mew=0.7,
            label='P2a-max')
    ax.axhline(0, color='gray', lw=0.4)
    ax.axvline(0, color='gray', lw=0.4)
    ax.set_xlabel(r'$\beta_s$ (°)')
    ax.set_ylabel(r'$\beta_c$ (°)')
    ax.set_title('Panel D — HC LOO argmin vs sub-08 candidates',
                 fontweight='bold')
    ax.legend(fontsize=6, loc='best')

    # Panel E — Local minima
    ax = fig.add_subplot(gs[1, 1])
    ax.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
              cmap='RdBu_r', alpha=0.5,
              vmin=np.nanpercentile(L_grid, 5),
              vmax=np.nanpercentile(L_grid, 95))
    for rank, m in enumerate(minima, 1):
        col = plt.cm.viridis(1 - rank/6)
        ax.plot(m['bs'], m['bc'], 'D', mfc=col, mec='black', ms=10, mew=0.7)
        ax.annotate(f'#{rank}', (m['bs'], m['bc']),
                    xytext=(4, 4), textcoords='offset points',
                    fontsize=7, fontweight='bold')
    ax.axhline(0, color='gray', lw=0.4)
    ax.axvline(0, color='gray', lw=0.4)
    ax.set_xlabel(r'$\beta_s$ (°)')
    ax.set_ylabel(r'$\beta_c$ (°)')
    ax.set_title(f'Panel E — Top-{len(minima)} local minima L_combined',
                 fontweight='bold')

    # Panel F — Verdict text
    ax = fig.add_subplot(gs[1, 2])
    ax.axis('off')
    pos_n = sum(1 for n in base_metrics if results[n]['sign'] == '+')
    neg_n = sum(1 for n in base_metrics if results[n]['sign'] == '-')
    text = f"""SIGN VERDICT — sub-08 V4 β_c

References:
  • P2a-max:           β_c = +34 (behavioral)
  • phase_a §3:        β_c = −14 (V4 LOCO MSE-based)
  • L_comb bootstrap:  β_c = +22 (CCC-based, 100% consistent)

Multi-metric argmin (no tie-break):
  • β_c > 0:  {pos_n}/{len(base_metrics)} metrics
  • β_c < 0:  {neg_n}/{len(base_metrics)} metrics

Direct LSQ projection (loss-independent):
  • β_c = {proj['beta_c_lsq']:+.2f}  ({proj['sign']})
  • r = {proj['pearson_r']:+.3f}

HC LOO sign distribution:
  • β_c > 0: {sum(1 for r in hc.values() if r['sign']=='+')}/{len(hc)}
  • β_c < 0: {sum(1 for r in hc.values() if r['sign']=='-')}/{len(hc)}

Top local minima β_c signs:
  #1: {'+' if minima[0]['bc']>0 else '-'}   #2: {'+' if minima[1]['bc']>0 else '-'}
  #3: {'+' if minima[2]['bc']>0 else '-'}
"""
    ax.text(0.0, 0.95, text, ha='left', va='top', family='monospace',
            fontsize=8, transform=ax.transAxes)

    fig.suptitle('sub-08 V4 β_c sign-flip exploration — multi-metric & loss-independent',
                 fontsize=11, fontweight='bold')

    out_png = OUT / f'{PREFIX}sub08_signflip.png'
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {out_png.name} (+pdf)')


if __name__ == '__main__':
    main()
