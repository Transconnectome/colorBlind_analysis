"""phase3_wfixed_diagnostic.py — A1 diagnostic: W-fixed LOCO vs shift_at_both.

Implements an alternative cone-shift simulator with LOCO-style hold-out but
training W on the **unshifted** design matrix C_orig (only the 7 non-k colors),
then applying the same W_k to the shifted design C_shifted(θ_k + δθ_k) for the
held-out prediction. This isolates the contribution of "shifting C during W
training" (shift_at_both) vs only "shifting C at test time" (shift_at_test_only).

Pipeline per (subject, ROI=V4):
  1. Load CVD vuln target + HC amplitudes (n=7, same pool as 4-term cache).
  2. Precompute W_k for each (HC, held-out color k) on the 7 non-k colors
     with C_orig — INDEPENDENT of the (β_s, β_c) grid (no leak).
  3. Precompute single-W per HC trained on all 8 colors with C_orig
     (used by L_rdm only, identical to existing 4-term).
  4. Precompute ΔRDM_obs (same as 4-term).
  5. Grid sweep (26 × 51 = 1326): for each (β_s, β_c) →
       vuln_sim from W_k · C_shifted (LOCO),
       ΔRDM_sim from single-W (held FIXED, identical to 4-term),
       compute 4-term loss with identical NORM/WEIGHTS.
  6. Also runs / loads shift_at_both (wretrained) reference landscapes.
  7. Emit landscape JSONs, comparison CSV, verdict markdown, comparison PDF.

Pool note: HC_SUBJECTS (n=7) used to match existing 4-term landscape cache.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.gridspec import GridSpec
from scipy.stats import spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

# Make forward-model utils visible (mirrors phase3_old_formula_4term.py).
_PHASE2 = _THIS_DIR.parent
for _base in [_PHASE2.parent, _PHASE2.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    create_basis_full, load_amplitudes,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from old_formula_refit import (  # noqa: E402
    LOCAL_DATA, SERVER_DATA, get_shifted_design_old,
)
from step1_fit_loco_v2 import (  # noqa: E402
    simulate_mean_hc_loco_legacy, precompute_hc_W, load_cvd_loco_target,
)
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_obs, compute_delta_rdm_sim,
)

OUTDIR = _PHASE2 / 'results' / 'old_formula'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Loss normalisers/weights — IDENTICAL to phase3_old_formula_4term.py.
NORM = {'vuln': 4.0, 'rank': 2.0, 'rdm': 2.0, 'smooth': 32400.0}
WEIGHTS = {'alpha': 1.0, 'beta': 0.5, 'delta': 0.2, 'epsilon': 0.1}

SUBJECTS = ['08', '09', '10']
ROI = 'V4'


# ---------------------------------------------------------------------------
# Pre-compute W_k for LOCO with UNSHIFTED training
# ---------------------------------------------------------------------------
def precompute_hc_W_loco_unshifted(hc_amps_dict, C_baseline):
    """For each HC, precompute W_k trained on the 7 non-k colors of C_baseline.

    W_k depends only on (subject, held-out color) — NOT on (β_s, β_c).
    Once precomputed, all 1326 grid cells reuse the same {W_k}.

    Args:
        hc_amps_dict: {subj: (N_RUNS=6, N_COLORS=8, V_s)}
        C_baseline: (8, K) unshifted design.

    Returns:
        W_loco[subj] -> list of length 8, each entry shape (K, V_s)
        alpha_loco[subj] -> list of length 8 of float alphas
    """
    W_loco = {}
    alpha_loco = {}
    for subj, amp in hc_amps_dict.items():
        V_s = amp.shape[2]
        Wks = []
        alphas = []
        for k in range(N_COLORS):
            train_colors = [c for c in range(N_COLORS) if c != k]
            X_train = amp[:, train_colors].reshape(-1, V_s)             # (42, V_s)
            C_train = np.tile(C_baseline[train_colors], (N_RUNS, 1))    # (42, K)
            alpha, _ = gcv_select_alpha(C_train, X_train)
            W = fit_W_ridge(C_train, X_train, alpha)                    # (K, V_s)
            Wks.append(W)
            alphas.append(float(alpha))
        W_loco[subj] = Wks
        alpha_loco[subj] = alphas
    return W_loco, alpha_loco


def simulate_single_hc_loco_wfixed(W_loco_subj, amp_hc, C_shifted):
    """LOCO prediction for one HC with W_k trained on UNSHIFTED design."""
    vuln = np.zeros(N_COLORS)
    for k in range(N_COLORS):
        W_k = W_loco_subj[k]                                            # (K, V_s)
        Y_pred = C_shifted[k:k+1] @ W_k                                 # (1, V_s)
        Y_actual = amp_hc[:, k].mean(axis=0, keepdims=True)             # (1, V_s)
        r = voxel_pattern_correlation(Y_pred, Y_actual)
        vuln[k] = r[0]
    return vuln


def simulate_mean_hc_loco_wfixed(W_loco, hc_amps_dict, C_shifted):
    """Mean-HC LOCO-with-unshifted-training vulnerability."""
    per_hc = {}
    for subj in W_loco:
        per_hc[subj] = simulate_single_hc_loco_wfixed(
            W_loco[subj], hc_amps_dict[subj], C_shifted)
    mean_vuln = np.array(list(per_hc.values())).mean(axis=0)
    return mean_vuln, per_hc


# ---------------------------------------------------------------------------
# Loss (matches phase3_old_formula_4term.compute_L_fit_4term)
# ---------------------------------------------------------------------------
def cosine_sim(a, b):
    a = np.asarray(a).ravel(); b = np.asarray(b).ravel()
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return float(a @ b / (na * nb))


def compute_L_fit_4term(vuln_sim, vuln_cvd, dt, delta_rdm_sim, delta_rdm_obs):
    L_vuln = float(np.mean((vuln_sim - vuln_cvd) ** 2)) / NORM['vuln']
    rho, _ = spearmanr(vuln_sim, vuln_cvd)
    rho = float(rho) if np.isfinite(rho) else 0.0
    L_rank = (1.0 - rho) / NORM['rank']
    cos_sim = cosine_sim(delta_rdm_sim, delta_rdm_obs)
    L_rdm = (1.0 - cos_sim) / NORM['rdm']
    dt_arr = np.asarray(dt)
    diffs = np.diff(dt_arr, append=dt_arr[0])
    diffs = (diffs + 180.0) % 360.0 - 180.0
    L_smooth = float(np.mean(diffs ** 2)) / NORM['smooth']
    L_fit = (WEIGHTS['alpha'] * L_vuln + WEIGHTS['beta'] * L_rank
             + WEIGHTS['delta'] * L_rdm + WEIGHTS['epsilon'] * L_smooth)
    return {
        'l_fit': L_fit, 'l_vuln': L_vuln, 'l_rank': L_rank,
        'l_rdm': L_rdm, 'l_smooth': L_smooth,
        'spearman_r': rho, 'rdm_cosine': cos_sim,
    }


# ---------------------------------------------------------------------------
# Driver: produce wfixed landscape for one subject
# ---------------------------------------------------------------------------
def fit_wfixed_for_subject(subj_id: str, roi: str, hc_amps, vuln_cvd,
                           hc_W_single, delta_rdm_obs, C_baseline):
    print(f'\n=== sub-{subj_id} {roi} A1 (wfixed = LOCO + unshifted training) ===')
    # Precompute W_k (LOCO with unshifted training).
    print('  Precomputing W_k {subj × 8 colors} on C_orig...')
    t0 = time.time()
    W_loco, alpha_loco = precompute_hc_W_loco_unshifted(hc_amps, C_baseline)
    print(f'  ...done in {time.time()-t0:.1f}s')

    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    n_cells = len(bs_range) * len(bc_range)
    print(f'  Grid: {len(bs_range)} × {len(bc_range)} = {n_cells} cells')

    landscape = []
    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design_old(bs, bc)
            vuln_sim, _ = simulate_mean_hc_loco_wfixed(W_loco, hc_amps, C_shifted)
            delta_rdm_sim, _ = compute_delta_rdm_sim(
                hc_W_single, C_shifted, C_baseline, distance='correlation')
            loss = compute_L_fit_4term(vuln_sim, vuln_cvd, dt,
                                       delta_rdm_sim, delta_rdm_obs)
            entry = {
                'bs': float(bs), 'bc': float(bc),
                'delta_theta': dt.tolist(),
                'vuln_sim': vuln_sim.tolist(),
                **loss,
            }
            landscape.append(entry)
        if (i + 1) % max(1, len(bs_range) // 5) == 0:
            best_so_far = min(landscape, key=lambda r: r['l_fit'])
            print(f'    [{i+1}/{len(bs_range)} β_s rows] best L_fit={best_so_far["l_fit"]:.4f} '
                  f'@ β=({best_so_far["bs"]:.0f}, {best_so_far["bc"]:+.0f}) '
                  f'ρ={best_so_far["spearman_r"]:.3f}')
    elapsed = time.time() - t0
    print(f'  Grid sweep done in {elapsed:.0f}s')

    by_lfit = sorted(landscape, key=lambda r: r['l_fit'])
    by_rho = sorted(landscape, key=lambda r: -r['spearman_r'])
    out = {
        'subject': subj_id, 'roi': roi,
        'simulator': 'wfixed_loco_unshifted',
        'description': ('LOCO with W_k trained on 7 non-k colors using '
                        'UNSHIFTED C_orig; only C_shifted at test.'),
        'formula': 'OLD CIELab-direct + 4-term L_fit',
        'weights': WEIGHTS, 'norm': NORM,
        'grid_bounds': {'bs': [0, 50, 2], 'bc': [-50, 50, 2]},
        'n_cells': n_cells,
        'elapsed_s': elapsed,
        'vuln_cvd': vuln_cvd.tolist(),
        'delta_rdm_obs': delta_rdm_obs.tolist(),
        'hc_subjects': list(hc_amps.keys()),
        'alpha_loco': alpha_loco,
        'best_by_l_fit': by_lfit[0],
        'best_by_rho': by_rho[0],
        'top_10_by_l_fit': by_lfit[:10],
        'top_10_by_rho': by_rho[:10],
    }
    fn = f'sub-{subj_id}_{roi}_wfixed'
    with open(OUTDIR / f'{fn}_summary.json', 'w') as f:
        json.dump(out, f, indent=2)
    with open(OUTDIR / f'{fn}_landscape.json', 'w') as f:
        json.dump(landscape, f, indent=2)
    print(f'  Wrote {fn}_landscape.json + _summary.json')
    return landscape, out


# ---------------------------------------------------------------------------
# Driver: produce wretrained (shift_at_both) reference landscape for sub-10
# (sub-08, sub-09 already cached as sub-XX_V4_4term_landscape.json)
# ---------------------------------------------------------------------------
def fit_wretrained_for_subject(subj_id: str, roi: str, hc_amps, vuln_cvd,
                                hc_W_single, delta_rdm_obs, C_baseline,
                                save_tag='4term'):
    print(f'\n=== sub-{subj_id} {roi} shift_at_both (wretrained) reference ===')
    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    n_cells = len(bs_range) * len(bc_range)
    print(f'  Grid: {len(bs_range)} × {len(bc_range)} = {n_cells} cells (≈12 min)')

    landscape = []
    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design_old(bs, bc)
            # shift_at_both — W retrained at each (β_s, β_c)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
            delta_rdm_sim, _ = compute_delta_rdm_sim(
                hc_W_single, C_shifted, C_baseline, distance='correlation')
            loss = compute_L_fit_4term(vuln_sim, vuln_cvd, dt,
                                       delta_rdm_sim, delta_rdm_obs)
            entry = {
                'bs': float(bs), 'bc': float(bc),
                'delta_theta': dt.tolist(),
                'vuln_sim': vuln_sim.tolist(),
                **loss,
            }
            landscape.append(entry)
        if (i + 1) % max(1, len(bs_range) // 5) == 0:
            best_so_far = min(landscape, key=lambda r: r['l_fit'])
            print(f'    [{i+1}/{len(bs_range)} β_s rows] best L_fit={best_so_far["l_fit"]:.4f} '
                  f'@ β=({best_so_far["bs"]:.0f}, {best_so_far["bc"]:+.0f}) '
                  f'ρ={best_so_far["spearman_r"]:.3f}')
    elapsed = time.time() - t0
    print(f'  Grid sweep done in {elapsed:.0f}s')

    by_lfit = sorted(landscape, key=lambda r: r['l_fit'])
    by_rho = sorted(landscape, key=lambda r: -r['spearman_r'])
    out = {
        'subject': subj_id, 'roi': roi,
        'simulator': 'shift_at_both_wretrained',
        'description': ('shift_at_both: W retrained at every (β_s, β_c) with '
                        'shifted C(θ+δθ); prediction also uses shifted C.'),
        'formula': 'OLD CIELab-direct + 4-term L_fit',
        'weights': WEIGHTS, 'norm': NORM,
        'grid_bounds': {'bs': [0, 50, 2], 'bc': [-50, 50, 2]},
        'n_cells': n_cells,
        'elapsed_s': elapsed,
        'vuln_cvd': vuln_cvd.tolist(),
        'delta_rdm_obs': delta_rdm_obs.tolist(),
        'hc_subjects': list(hc_amps.keys()),
        'best_by_l_fit': by_lfit[0],
        'best_by_rho': by_rho[0],
        'top_10_by_l_fit': by_lfit[:10],
        'top_10_by_rho': by_rho[:10],
    }
    fn = f'sub-{subj_id}_{roi}_{save_tag}'
    with open(OUTDIR / f'{fn}_summary.json', 'w') as f:
        json.dump(out, f, indent=2)
    with open(OUTDIR / f'{fn}_landscape.json', 'w') as f:
        json.dump(landscape, f, indent=2)
    print(f'  Wrote {fn}_landscape.json + _summary.json')
    return landscape, out


# ---------------------------------------------------------------------------
# Comparison: CSV + verdict + figure
# ---------------------------------------------------------------------------
def landscape_to_grid(landscape):
    bs_vals = sorted({c['bs'] for c in landscape})
    bc_vals = sorted({c['bc'] for c in landscape})
    bs_idx = {v: i for i, v in enumerate(bs_vals)}
    bc_idx = {v: i for i, v in enumerate(bc_vals)}
    rho = np.full((len(bs_vals), len(bc_vals)), np.nan)
    lfit = np.full_like(rho, np.nan)
    vuln_max = np.full_like(rho, np.nan)
    for c in landscape:
        i = bs_idx[c['bs']]; j = bc_idx[c['bc']]
        rho[i, j] = c['spearman_r']
        lfit[i, j] = c['l_fit']
        vuln_max[i, j] = max(c['vuln_sim'])
    return np.array(bs_vals), np.array(bc_vals), rho, lfit, vuln_max


def find_baseline_rho(landscape):
    """Find the cell with β_s=0, β_c=0 and return its Spearman ρ."""
    for c in landscape:
        if c['bs'] == 0 and c['bc'] == 0:
            return float(c['spearman_r'])
    return float('nan')


def write_csv(rows, path):
    fieldnames = ['subject', 'simulator',
                  'argmin_bs', 'argmin_bc', 'argmin_norm',
                  'best_spearman_r', 'best_l_fit',
                  'max_sigma_sim', 'sigma_obs',
                  'baseline_rho_at_beta0']
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})
    print(f'Wrote {path}')


def make_verdict(per_subject, path):
    lines = [
        '# A1 Diagnostic Verdict — W-fixed (LOCO + unshifted training)',
        '',
        ('This file compares two LOCO simulators that differ ONLY in how the '
         'cone shift δθ enters the ridge weights W during training:'),
        '',
        '- `wretrained` (shift_at_both): W is retrained at every (β_s, β_c) '
         'using the SHIFTED design C(θ+δθ) on 7 non-k colors; held-out '
         'prediction also uses the shifted design.',
        '- `wfixed` (shift_at_test_only / A1): W_k is trained ONCE per '
         '(subject × held-out color) on the UNSHIFTED design C_orig of the '
         '7 non-k colors; only the held-out test design C_shifted(θ_k+δθ_k) '
         'is shifted at every (β_s, β_c).',
        '',
        'Loss family is held FIXED across simulators: same 4-term L_fit '
        '(`1·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth`), same NORM, '
        'same ΔRDM reference (single-W trained on all 8 colors with C_orig). '
        'The only thing that changes between landscapes is the vuln_sim '
        'computation that feeds L_vuln and L_rank.',
        '',
        'HC pool used: **sub-01..07 (n=7)** — same as the existing 4-term '
        'cache to enable like-for-like comparison. The task brief mentioned '
        'sub-01..06 but this would have differed from the cached wretrained '
        'reference and confounded simulator-vs-pool differences.',
        '',
        '## Per-subject verdicts',
        '',
    ]

    def classify(dbs, dbc, dnorm):
        d_arg = max(abs(dbs), abs(dbc))
        if abs(dnorm) < 5 and d_arg <= 10:
            return 'robust', ('|Δnorm|<5 AND argmin shift within ±10° → '
                              'current shift_at_both result NOT an absorption artifact.')
        if abs(dnorm) >= 15 or d_arg > 30:
            return 'absorption_confound', ('|Δnorm|≥15 OR argmin shift >30° in '
                                           'one axis → current shift_at_both result is biased.')
        return 'moderate_sensitivity', ('Intermediate → result is sensitive to '
                                        'the simulator choice; report as caveat.')

    for ps in per_subject:
        wr = ps['wretrained']; wf = ps['wfixed']
        d_bs = wf['argmin_bs'] - wr['argmin_bs']
        d_bc = wf['argmin_bc'] - wr['argmin_bc']
        d_norm = wf['argmin_norm'] - wr['argmin_norm']
        d_sigma = wf['max_sigma_sim'] - wr['max_sigma_sim']
        verdict, expl = classify(d_bs, d_bc, d_norm)
        lines += [
            f'### sub-{ps["subject"]} ({ROI})',
            '',
            f'- wretrained argmin: (β_s={wr["argmin_bs"]:.0f}, β_c={wr["argmin_bc"]:+.0f}), '
            f'norm={wr["argmin_norm"]:.1f}°, ρ={wr["best_spearman_r"]:.3f}, '
            f'L_fit={wr["best_l_fit"]:.4f}',
            f'- wfixed     argmin: (β_s={wf["argmin_bs"]:.0f}, β_c={wf["argmin_bc"]:+.0f}), '
            f'norm={wf["argmin_norm"]:.1f}°, ρ={wf["best_spearman_r"]:.3f}, '
            f'L_fit={wf["best_l_fit"]:.4f}',
            f'- Δ(β_s, β_c) = ({d_bs:+.0f}°, {d_bc:+.0f}°), '
            f'Δnorm = {d_norm:+.1f}°',
            f'- Max σ(vuln_sim): wretrained={wr["max_sigma_sim"]:.3f}, '
            f'wfixed={wf["max_sigma_sim"]:.3f}, Δ={d_sigma:+.3f}',
            f'- Baseline ρ(β=0): wretrained={wr["baseline_rho_at_beta0"]:.3f}, '
            f'wfixed={wf["baseline_rho_at_beta0"]:.3f}',
            f'- **Verdict: {verdict}** — {expl}',
            '',
        ]

    lines += [
        '## Framing',
        '',
        'This diagnostic test asks whether the canonical Phase 2 (β_s, β_c) '
        'point estimate is sensitive to the choice of LOCO simulator family. '
        'It does NOT introduce a new selection rule, specificity test, or '
        'filter criterion. Verdicts above are descriptive: they characterise '
        'how the same (loss, grid, HC pool, ΔRDM reference) responds when '
        'only the vuln_sim simulator changes.',
        '',
    ]

    mode = 'a' if path.exists() else 'w'
    with open(path, mode) as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote/appended verdict → {path}')


def make_figure(per_subject_landscapes, path):
    """3 rows × 2 cols heatmap: ρ landscape with argmin marked."""
    fig = plt.figure(figsize=(12, 13))
    gs = GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.30)

    # Shared color scale spanning all panels for fair comparison.
    all_rho = []
    for ps in per_subject_landscapes:
        _, _, rho_wr, _, _ = landscape_to_grid(ps['wretrained_landscape'])
        _, _, rho_wf, _, _ = landscape_to_grid(ps['wfixed_landscape'])
        all_rho.append(rho_wr); all_rho.append(rho_wf)
    rho_min = float(np.nanmin([r.min() for r in all_rho]))
    rho_max = float(np.nanmax([r.max() for r in all_rho]))
    rho_max = max(rho_max, 1e-6)
    rho_min = min(rho_min, -1e-6)
    norm = TwoSlopeNorm(vmin=rho_min, vcenter=0.0, vmax=rho_max)

    for i, ps in enumerate(per_subject_landscapes):
        subj = ps['subject']
        for j, simulator in enumerate(['wretrained', 'wfixed']):
            ax = fig.add_subplot(gs[i, j])
            land = ps[f'{simulator}_landscape']
            bs_vals, bc_vals, rho_grid, lfit_grid, vuln_max = landscape_to_grid(land)
            im = ax.imshow(rho_grid, aspect='auto', origin='lower',
                           cmap='RdBu_r', norm=norm,
                           extent=[bc_vals[0], bc_vals[-1],
                                   bs_vals[0], bs_vals[-1]])
            # Mark argmin by L_fit (canonical cell)
            best_idx = np.nanargmin(lfit_grid)
            bi, bj = np.unravel_index(best_idx, lfit_grid.shape)
            ax.plot(bc_vals[bj], bs_vals[bi], marker='*',
                    color='black', markersize=18,
                    markeredgecolor='white', markeredgewidth=1.5,
                    linestyle='None', zorder=5)
            label = ('shift_at_both (wretrained)' if simulator == 'wretrained'
                     else 'shift_at_test_only (wfixed)')
            argmin_bs = bs_vals[bi]; argmin_bc = bc_vals[bj]
            rho_at_argmin = rho_grid[bi, bj]
            sigma_max = float(np.nanmax(vuln_max))
            ax.set_title(
                f'sub-{subj} V4 — {label}\n'
                f'argmin (β_s, β_c)=({argmin_bs:.0f}, {argmin_bc:+.0f}), '
                f'norm={np.hypot(argmin_bs, argmin_bc):.1f}°  '
                f'ρ*={rho_at_argmin:.3f}  σ_sim_max={sigma_max:.3f}',
                fontsize=10)
            ax.set_xlabel('β_c (deg)')
            ax.set_ylabel('β_s (deg)')
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04,
                         label='Spearman ρ(vuln_sim, vuln_cvd)')
    fig.suptitle('A1 diagnostic — landscapes under shift_at_both vs shift_at_test_only',
                 fontsize=13)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    print(f'Wrote {path}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'Data dir: {data_dir}')
    print(f'HC pool (n={len(HC_SUBJECTS)}): {HC_SUBJECTS}')
    hc_amps = {s: load_amplitudes(data_dir, s, ROI) for s in HC_SUBJECTS}
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]                                # (8, K)

    print('Precomputing single-W per HC on all 8 colors (for ΔRDM_sim only)...')
    hc_W_single, _ = precompute_hc_W(hc_amps, C_baseline)

    per_subject_rows = []
    per_subject_landscapes = []

    for subj in SUBJECTS:
        vuln_cvd = load_cvd_loco_target(subj, ROI)
        print(f'\n--- sub-{subj} ---  CVD vuln = {np.round(vuln_cvd, 3).tolist()}')
        sigma_obs = float(np.std(vuln_cvd, ddof=1))

        # ΔRDM_obs is per-subject (depends on amp_cvd).
        amp_cvd = load_amplitudes(data_dir, subj, ROI)
        delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
            amp_cvd, hc_amps, distance='correlation')

        # --- wfixed (A1) ---
        wf_landscape, wf_summary = fit_wfixed_for_subject(
            subj, ROI, hc_amps, vuln_cvd, hc_W_single,
            delta_rdm_obs, C_baseline)

        # --- wretrained reference ---
        cached_path = OUTDIR / f'sub-{subj}_{ROI}_4term_landscape.json'
        if cached_path.exists():
            print(f'\n=== sub-{subj} {ROI} loading cached 4term landscape ===')
            with open(cached_path) as f:
                wr_landscape = json.load(f)
            # Cached entries DON'T include vuln_sim. Recompute σ_sim_max
            # by reading the cached sub-XX_V4_4term_summary.json or by
            # re-running cells — we recompute on the fly to keep numbers
            # exactly comparable.
            need_vuln = any('vuln_sim' not in c for c in wr_landscape)
            if need_vuln:
                print('  cached landscape has no vuln_sim — recomputing for σ_sim...')
                for c in wr_landscape:
                    C_shift, _ = get_shifted_design_old(c['bs'], c['bc'])
                    v, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shift)
                    c['vuln_sim'] = v.tolist()
        else:
            wr_landscape, wr_summary = fit_wretrained_for_subject(
                subj, ROI, hc_amps, vuln_cvd, hc_W_single,
                delta_rdm_obs, C_baseline, save_tag='4term')

        # --- Build per-simulator rows ---
        def summarise(landscape, tag):
            best = min(landscape, key=lambda r: r['l_fit'])
            sigma_max = max(max(c['vuln_sim']) for c in landscape if 'vuln_sim' in c)
            # use proper std-style σ — vuln_sim is per-cell 8-vector,
            # so report max over cells of std(vuln_sim).
            sigma_max_std = max(
                float(np.std(np.asarray(c['vuln_sim']), ddof=1))
                for c in landscape if 'vuln_sim' in c
            )
            row = {
                'subject': subj,
                'simulator': tag,
                'argmin_bs': best['bs'],
                'argmin_bc': best['bc'],
                'argmin_norm': float(np.hypot(best['bs'], best['bc'])),
                'best_spearman_r': best['spearman_r'],
                'best_l_fit': best['l_fit'],
                'max_sigma_sim': sigma_max_std,
                'sigma_obs': sigma_obs,
                'baseline_rho_at_beta0': find_baseline_rho(landscape),
            }
            return row

        wr_row = summarise(wr_landscape, 'wretrained')
        wf_row = summarise(wf_landscape, 'wfixed')
        per_subject_rows += [wr_row, wf_row]
        per_subject_landscapes.append({
            'subject': subj,
            'wretrained_landscape': wr_landscape,
            'wfixed_landscape': wf_landscape,
        })

    # CSV
    csv_path = OUTDIR / 'wfixed_vs_wretrained_v4.csv'
    write_csv(per_subject_rows, csv_path)

    # Verdict markdown
    verdict_rows = []
    for subj in SUBJECTS:
        wr = next(r for r in per_subject_rows
                  if r['subject'] == subj and r['simulator'] == 'wretrained')
        wf = next(r for r in per_subject_rows
                  if r['subject'] == subj and r['simulator'] == 'wfixed')
        verdict_rows.append({'subject': subj, 'wretrained': wr, 'wfixed': wf})
    verdict_path = OUTDIR / 'wfixed_verdict.md'
    make_verdict(verdict_rows, verdict_path)

    # PDF figure
    pdf_path = OUTDIR / 'wfixed_vs_wretrained_landscapes.pdf'
    make_figure(per_subject_landscapes, pdf_path)

    print('\n[Done]')
    print(f'  Landscape JSONs: results/old_formula/sub-{{08,09,10}}_V4_wfixed_landscape.json')
    print(f'  CSV:              {csv_path}')
    print(f'  Verdict:          {verdict_path}')
    print(f'  Figure:           {pdf_path}')


if __name__ == '__main__':
    main()
