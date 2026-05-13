"""permutation_specificity_test.py — alternative specificity diagnostics for CVD.

Key idea: instead of HC-pool comparison (which fails under any norm/Δ_L metric due
to HC LOO random walk), use INTRA-SUBJECT permutation tests asking
  "Is this CVD's vuln_obs structured enough that the cone-shift model fits it
   much better than random?"

Tests:
  Test A: Label permutation Δ_L test
    - Shuffle vuln_obs's 8 color labels → recompute L_combined per cell
    - Find argmin → Δ_L_perm = L(β=0) − L(argmin)
    - p_A = P(Δ_L_perm ≥ Δ_L_obs)  [n=1000 perms]

  Test B: Argmin location stability under permutation
    - For each permutation: how often does argmin land near observed (β_s, β_c)?
    - p_B = P(perm argmin within ±5° of obs argmin)
    - Low p_B = observed argmin is structurally meaningful

  Test C: SNR at argmin
    - SNR = (L_baseline − L_argmin) / std(L across grid)
    - Subject-internal effect size, not HC-comparison

Applied to both losses (CCC + CCC+l_topk) for both CVD subjects.

Output: results/CANDIDATE/specificity_alternatives/
"""
from __future__ import annotations
import json
import sys
import csv
import time
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
SRC = _PHASE2 / 'results' / 'old_formula'
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'specificity_alternatives'
OUT.mkdir(parents=True, exist_ok=True)

K_TOPK = 3
TIKH_NORM = 32400.0
LAMBDA_TOPK = 0.5
N_PERM = 1000
RNG_SEED = 42

# BEST argmins for reference
BEST = {
    '08': {'cvd_type': 'deutan', 'color': '#E07B2C',
           'ccc_alone': (16.0, 40.0),     # V4-CCC alone
           'ccc_ltopk': (44.0, 28.0)},     # V4-CCC + l_topk (CURRENT BEST)
    '09': {'cvd_type': 'protan', 'color': '#2D8E8B',
           'ccc_alone': (30.0, 46.0),
           'ccc_ltopk': (30.0, 46.0)},     # same as alone (l_topk no effect)
}


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


def compute_L_per_cell(vuln_sims_cached, vuln_obs, tikhs_cached, loss='ccc_ltopk'):
    """Vectorized loss computation per cell given a (possibly permuted) vuln_obs.

    vuln_sims_cached: (N_cells, 8)  cached vuln_sim per cell
    vuln_obs: (8,)  observed (or permuted)
    tikhs_cached: (N_cells,)  cached Tikhonov term
    loss: 'ccc_alone' or 'ccc_ltopk'

    Returns: L per cell (N_cells,)
    """
    N = vuln_sims_cached.shape[0]
    # CCC vectorized
    sim = vuln_sims_cached  # (N, 8)
    obs = vuln_obs  # (8,)
    msim = sim.mean(axis=1, keepdims=True)
    mobs = obs.mean()
    ssim = sim.std(axis=1)
    sobs = obs.std()
    # Pearson r per row
    sim_c = sim - msim
    obs_c = obs - mobs
    cov = (sim_c * obs_c).sum(axis=1) / 8
    denom_r = ssim * sobs
    r = np.where(denom_r > 1e-10, cov / denom_r, 0.0)
    # CCC formula
    ssim_sq = ssim ** 2
    sobs_sq = sobs ** 2
    bias_sq = (msim.flatten() - mobs) ** 2
    denom = ssim_sq + sobs_sq + bias_sq
    ccc = np.where(denom > 1e-10, 2 * r * ssim * sobs / denom, 0.0)
    L_ccc = (1.0 - ccc) / 2.0

    if loss == 'ccc_alone':
        return L_ccc + 0.1 * tikhs_cached

    # CCC + l_topk
    # Top-K Jaccard per cell — vectorized
    K = K_TOPK
    top_s_idx = np.argsort(sim, axis=1)[:, :K]  # (N, K)
    top_o_idx = np.argsort(obs)[:K]              # (K,)
    top_o_set = set(top_o_idx.tolist())
    # Per cell: intersection count
    inter_counts = np.array([
        len(top_o_set & set(top_s_idx[i].tolist())) for i in range(N)
    ])
    # Union: |top_s| + |top_o| − intersection = 2K − inter
    union_counts = 2 * K - inter_counts
    l_topk = 1.0 - (inter_counts / union_counts)

    L_combined = L_ccc + LAMBDA_TOPK * l_topk + 0.1 * tikhs_cached
    return L_combined


def find_baseline_cell(cells):
    """Find cell with bs=0, bc=0 (baseline)."""
    for i, c in enumerate(cells):
        if abs(c['bs']) < 0.5 and abs(c['bc']) < 0.5:
            return i
    raise ValueError("(0,0) cell not in landscape")


def run_subject(sid, n_perm=N_PERM, rng_seed=RNG_SEED):
    print(f'\n=== sub-{sid} ===', flush=True)
    # Load cached V4-CCC landscape
    fn = SRC / f'sub-{sid}_V4_V4ccc_landscape.json'
    cells = json.load(open(fn))
    cells = cells if isinstance(cells, list) else cells.get('cells', cells)
    vuln_obs = np.array(load_cvd_loco_target(sid, 'V4'))

    # Cache arrays
    N_cells = len(cells)
    vuln_sims = np.array([c['vuln_sim'] for c in cells])  # (N, 8)
    tikhs = np.array([(c['bs']**2 + c['bc']**2) / TIKH_NORM for c in cells])
    bss = np.array([c['bs'] for c in cells])
    bcs = np.array([c['bc'] for c in cells])

    baseline_idx = find_baseline_cell(cells)
    print(f'  baseline cell (β=0,0) index: {baseline_idx}', flush=True)
    print(f'  vuln_obs top-3 negative idx: {np.argsort(vuln_obs)[:3].tolist()}', flush=True)

    results = {}
    rng = np.random.default_rng(rng_seed)
    perm_indices = [rng.permutation(8) for _ in range(n_perm)]

    for loss_name in ['ccc_alone', 'ccc_ltopk']:
        print(f'\n  --- Loss: {loss_name} ---', flush=True)
        # Observed (true vuln_obs)
        L_obs = compute_L_per_cell(vuln_sims, vuln_obs, tikhs, loss_name)
        L_baseline_obs = L_obs[baseline_idx]
        argmin_idx_obs = int(np.argmin(L_obs))
        L_argmin_obs = L_obs[argmin_idx_obs]
        delta_L_obs = L_baseline_obs - L_argmin_obs
        argmin_bs_obs = bss[argmin_idx_obs]
        argmin_bc_obs = bcs[argmin_idx_obs]
        snr_obs = delta_L_obs / np.std(L_obs)

        print(f'  observed: argmin=({argmin_bs_obs:.0f}, {argmin_bc_obs:+.0f})  '
              f'Δ_L={delta_L_obs:.4f}  SNR={snr_obs:.3f}', flush=True)

        # Permutation test
        t0 = time.time()
        delta_L_perm = np.zeros(n_perm)
        argmin_bs_perm = np.zeros(n_perm)
        argmin_bc_perm = np.zeros(n_perm)
        for p, perm in enumerate(perm_indices):
            vuln_perm = vuln_obs[perm]
            L_perm = compute_L_per_cell(vuln_sims, vuln_perm, tikhs, loss_name)
            L_baseline_perm = L_perm[baseline_idx]
            argmin_idx_p = int(np.argmin(L_perm))
            delta_L_perm[p] = L_baseline_perm - L_perm[argmin_idx_p]
            argmin_bs_perm[p] = bss[argmin_idx_p]
            argmin_bc_perm[p] = bcs[argmin_idx_p]
        elapsed = time.time() - t0
        print(f'  {n_perm} perms done in {elapsed:.1f}s', flush=True)

        # p-values
        p_A = float((delta_L_perm >= delta_L_obs).mean())
        # Test B: argmin within ±5°
        near_obs = (np.abs(argmin_bs_perm - argmin_bs_obs) <= 5) & \
                   (np.abs(argmin_bc_perm - argmin_bc_obs) <= 5)
        p_B = float(near_obs.mean())  # fraction of perms landing near obs
        # SNR perm distribution
        snr_perm = delta_L_perm / np.std(L_obs)  # using observed std as ref
        p_SNR = float((snr_perm >= snr_obs).mean())

        print(f'  Test A (Δ_L permutation): p_A = {p_A:.4f}  '
              f'(perm mean Δ_L = {delta_L_perm.mean():.4f}, '
              f'95th pct = {np.percentile(delta_L_perm, 95):.4f})', flush=True)
        print(f'  Test B (argmin stability): p_B = {p_B:.4f}  '
              f'({int(near_obs.sum())}/{n_perm} perms within ±5° of obs argmin)', flush=True)
        print(f'  Test C (SNR): obs={snr_obs:.3f}, perm 95th={np.percentile(snr_perm, 95):.3f}  '
              f'p_C = {p_SNR:.4f}', flush=True)

        results[loss_name] = {
            'observed': {
                'argmin_bs': float(argmin_bs_obs),
                'argmin_bc': float(argmin_bc_obs),
                'L_baseline': float(L_baseline_obs),
                'L_argmin': float(L_argmin_obs),
                'delta_L': float(delta_L_obs),
                'snr': float(snr_obs),
                'std_L_grid': float(np.std(L_obs)),
            },
            'perm': {
                'n_perm': n_perm,
                'delta_L_mean': float(delta_L_perm.mean()),
                'delta_L_std': float(delta_L_perm.std()),
                'delta_L_95th': float(np.percentile(delta_L_perm, 95)),
                'delta_L_max': float(delta_L_perm.max()),
                'p_A_delta_L': p_A,
                'p_B_argmin_stability': p_B,
                'p_C_snr': p_SNR,
                'snr_perm_95th': float(np.percentile(snr_perm, 95)),
            },
            'delta_L_perm_values': delta_L_perm.tolist(),
            'argmin_bs_perm': argmin_bs_perm.tolist(),
            'argmin_bc_perm': argmin_bc_perm.tolist(),
        }

    return results, vuln_obs


def render_perm_distributions(all_results, out_path):
    """4 panels (2 subjects × 2 losses): null delta_L histogram + observed line."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), dpi=150)
    fig.suptitle('Permutation test — Δ_L null distribution (n=1000 label shuffles)\n'
                 'CVD-specificity via subject-internal structure',
                 fontsize=11, fontweight='bold', y=0.998)

    for i_sub, sid in enumerate(['08', '09']):
        info = BEST[sid]
        for i_loss, loss_name in enumerate(['ccc_alone', 'ccc_ltopk']):
            ax = axes[i_sub, i_loss]
            r = all_results[sid][loss_name]
            perm_vals = np.array(r['delta_L_perm_values'])
            obs_val = r['observed']['delta_L']
            p_A = r['perm']['p_A_delta_L']
            p_B = r['perm']['p_B_argmin_stability']

            ax.hist(perm_vals, bins=50, color=info['color'], alpha=0.5,
                    edgecolor='black', lw=0.3, label='Null (permuted)')
            ax.axvline(obs_val, color=info['color'], lw=2.5,
                       label=f'Observed Δ_L = {obs_val:.3f}')
            ax.axvline(np.percentile(perm_vals, 95), color='gray', lw=0.7, ls='--',
                       alpha=0.7, label='Null 95th pct')

            loss_label = 'CCC alone' if loss_name == 'ccc_alone' else 'CCC + l_topk'
            ax.set_title(f"sub-{sid} ({info['cvd_type']}) — {loss_label}\n"
                         f"p_A(Δ_L) = {p_A:.4f}, p_B(argmin stable) = {p_B:.4f}",
                         color=info['color'], fontweight='bold', fontsize=9)
            ax.set_xlabel('Δ_L = L(β=0) − L(argmin)')
            ax.set_ylabel('Permutation count')
            ax.legend(loc='upper right', fontsize=7)
            ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {out_path.name} (+ pdf)')


def main():
    print(f'OUTDIR: {OUT}')
    print(f'n_perm = {N_PERM}, RNG seed = {RNG_SEED}')
    print(f'BEST argmins: {BEST}')

    all_results = {}
    for sid in ['08', '09']:
        results, vuln_obs = run_subject(sid)
        all_results[sid] = results
        all_results[sid]['_meta'] = {
            'cvd_type': BEST[sid]['cvd_type'],
            'vuln_obs': vuln_obs.tolist(),
        }

    # Save full results (large)
    full_path = OUT / 'permutation_test_full.json'
    with open(full_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nwrote {full_path.name}')

    # Save trimmed summary CSV
    csv_path = OUT / 'permutation_test_summary.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['subject', 'cvd_type', 'loss', 'argmin_bs', 'argmin_bc',
                    'observed_delta_L', 'observed_SNR',
                    'perm_delta_L_mean', 'perm_delta_L_95th',
                    'p_A_delta_L', 'p_B_argmin_stability', 'p_C_snr',
                    'verdict_A', 'verdict_B', 'verdict_C'])
        for sid in ['08', '09']:
            cvd = BEST[sid]['cvd_type']
            for loss_name in ['ccc_alone', 'ccc_ltopk']:
                r = all_results[sid][loss_name]
                p_A = r['perm']['p_A_delta_L']
                p_B = r['perm']['p_B_argmin_stability']
                p_C = r['perm']['p_C_snr']
                verdict_A = ('***' if p_A < 0.001 else '**' if p_A < 0.01
                             else '*' if p_A < 0.05 else 'n.s.')
                verdict_B = ('***' if p_B < 0.001 else '**' if p_B < 0.01
                             else '*' if p_B < 0.05 else 'n.s.')
                verdict_C = ('***' if p_C < 0.001 else '**' if p_C < 0.01
                             else '*' if p_C < 0.05 else 'n.s.')
                w.writerow([
                    f'sub-{sid}', cvd, loss_name,
                    r['observed']['argmin_bs'], r['observed']['argmin_bc'],
                    round(r['observed']['delta_L'], 4),
                    round(r['observed']['snr'], 3),
                    round(r['perm']['delta_L_mean'], 4),
                    round(r['perm']['delta_L_95th'], 4),
                    round(p_A, 4), round(p_B, 4), round(p_C, 4),
                    verdict_A, verdict_B, verdict_C,
                ])
    print(f'wrote {csv_path.name}')

    render_perm_distributions(all_results, OUT / 'permutation_test_distributions.png')

    print('\n=== FINAL SUMMARY ===')
    for sid in ['08', '09']:
        cvd = BEST[sid]['cvd_type']
        print(f'\nsub-{sid} ({cvd}):')
        for loss_name in ['ccc_alone', 'ccc_ltopk']:
            r = all_results[sid][loss_name]
            print(f'  {loss_name:12s}: argmin=({r["observed"]["argmin_bs"]:+.0f},{r["observed"]["argmin_bc"]:+.0f})  '
                  f'Δ_L={r["observed"]["delta_L"]:.3f}  SNR={r["observed"]["snr"]:.2f}  '
                  f'p_A={r["perm"]["p_A_delta_L"]:.3f}  '
                  f'p_B={r["perm"]["p_B_argmin_stability"]:.3f}  '
                  f'p_C={r["perm"]["p_C_snr"]:.3f}')


if __name__ == '__main__':
    main()
