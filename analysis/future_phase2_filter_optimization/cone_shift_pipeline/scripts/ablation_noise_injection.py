#!/usr/bin/env python3
"""
ablation_noise_injection.py — Noise injection ablation for ΔRDM simulation pipeline.

Tests whether Phase C LOCO reproduction results survive realistic noise levels.
Answers: "Is synthetic LOCO superiority real representation or too-easy data?"

For each validated simulation result (from RESULTS_SIM.md), this script:
1. Loads the best_params (δ*) from Phase A
2. Generates synthetic data with varying noise levels
3. Runs LOCO on each noisy realization (Monte Carlo)
4. Reports how Phase C metrics degrade with noise

Noise model:
    Y_syn[r,c,v] = C(θ+δ*)[c] @ W_HC[v] + noise_scale * ε[r,c,v]
    where ε ~ N(0, σ²_residual) with per-voxel σ estimated from HC data.

    noise_scale=0: perfect (no noise in any run)
    noise_scale=1: noise at empirical HC residual level
    noise_scale>1: amplified noise (harder than real data)

Usage:
    conda activate srm
    python scripts/ablation_noise_injection.py [--n_mc 100] [--output_dir results/ablation]

Output:
    results/ablation/noise_injection.json  — Full results
    figures/noise_injection_ablation.png   — Diagnostic figure
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from itertools import permutations
import sys
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

# ============================================================================
# Path setup
# ============================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix

# ============================================================================
# Constants
# ============================================================================
_ANALYSIS_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Local data: phase1_procrustes_decoding (has amplitudes_procrustes.npy)
_LOCAL_BASELINE_1 = _ANALYSIS_DIR / 'phase1_procrustes_decoding' / 'results' / 'full_dataset_C010'
_LOCAL_BASELINE_2 = _ANALYSIS_DIR / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
_SERVER_BASELINE = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')
LOCAL_BASELINE = (
    _LOCAL_BASELINE_1 if _LOCAL_BASELINE_1.exists()
    else _LOCAL_BASELINE_2 if _LOCAL_BASELINE_2.exists()
    else _SERVER_BASELINE
)

FWD_RESULTS = _ANALYSIS_DIR / 'future_phase1_forward_model' / 'results'
SIM_DIR = _SCRIPT_DIR.parent / 'results' / 'sim'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

NOISE_SCALES = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

# Top results from RESULTS_SIM.md (cosine metric, Phase A significant)
TARGET_COMBOS = [
    # (sub, roi, model, metric) — ordered by Phase C strength
    ('09', 'V2', 'cone_1way', 'cosine'),    # ONLY fully significant (p=0.011)
    ('08', 'V2', 'fourier',   'cosine'),    # trending (p=0.058)
    ('08', 'V1', 'fourier',   'cosine'),    # trending (p=0.076)
    ('09', 'V2', 'cone_3way', 'cosine'),    # trending (p=0.086)
]

# V4 combos from step1_loco (shift_at_both method — canonical for V4 K=3)
V4_COMBOS = [
    ('09', 'V4', 'cone_1way', 'cosine'),    # sig (p=0.009) — strongest V4
    ('08', 'V4', 'cone_1way', 'cosine'),    # sig (p=0.036)
]

LOCO_V2_DIR = _SCRIPT_DIR.parent / 'results' / 'v2' / 'step1_loco'


# ============================================================================
# Data loading
# ============================================================================

def load_combo_result(sub, roi, model, metric):
    """Load Phase A result.json for a simulation combo."""
    dirname = f'sub-{sub}_{roi}_{model}_{metric}'
    path = SIM_DIR / dirname / 'result.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing: {path}')
    with open(path) as f:
        return json.load(f)


def load_v4_loco_result(sub, model):
    """Load step1_loco result for V4 (shift_at_both format).

    Adapts to the same interface as load_combo_result():
      result['phase_a']['best_params'] and
      result['phase_c']['loco_match']['spearman_rho'/'perm_p']
    """
    path = LOCO_V2_DIR / 'V4' / f'sub-{sub}_loco_v2.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing V4 LOCO: {path}')
    with open(path) as f:
        data = json.load(f)
    fit = data['fit_results'][model]
    return {
        'phase_a': {'best_params': fit['params']},
        'phase_c': {
            'loco_match': {
                'spearman_rho': fit['spearman_r'],
                'perm_p': fit['perm_p_spearman'],
            }
        },
    }


def load_cvd_loco_observed(sub_id, roi):
    """Load observed CVD LOCO vulnerability profile."""
    loco_path = FWD_RESULTS / 'validation' / f'sub-{sub_id}_loco.json'
    with open(loco_path) as f:
        data = json.load(f)
    folds = data[roi]['ridge_gcv']['folds']
    vuln = np.zeros(N_COLORS)
    for fold in folds:
        vuln[fold['test_color']] = fold['voxel_corr']
    return vuln


def precompute_hc_data(roi):
    """Load HC amplitudes and precompute W_HC for a given ROI.

    Returns:
        hc_amps_dict: {subj: (6, 8, V_s)}
        hc_W_dict: {subj: (K, V_s)}
        hc_residual_sd: {subj: (V_s,)} per-voxel residual SD
    """
    C_baseline = create_basis_matrix()
    C_pooled = np.tile(C_baseline, (N_RUNS, 1))

    hc_amps_dict = {}
    hc_W_dict = {}
    hc_residual_sd = {}

    for s in HC_SUBJECTS:
        try:
            amp = load_amplitudes(LOCAL_BASELINE, s, roi)
        except FileNotFoundError:
            continue

        hc_amps_dict[s] = amp
        V_s = amp.shape[2]

        # Precompute W
        X_all = amp.reshape(-1, V_s)
        alpha, _ = gcv_select_alpha(C_pooled, X_all)
        W = fit_W_ridge(C_pooled, X_all, alpha)
        hc_W_dict[s] = W

        # Compute per-voxel residual SD across runs and colors
        mean_patterns = amp.mean(axis=0)  # (8, V_s)
        residuals = amp - mean_patterns[np.newaxis, :, :]  # (6, 8, V_s)
        # SD across runs for each (color, voxel), then mean across colors
        sd_per_color = residuals.std(axis=0)  # (8, V_s)
        hc_residual_sd[s] = sd_per_color.mean(axis=0)  # (V_s,)

    return hc_amps_dict, hc_W_dict, hc_residual_sd


# ============================================================================
# Core: LOCO on noisy synthetic data
# ============================================================================

def loco_on_noisy_synthetic(Y_runs, C_shifted, alpha_fixed=None):
    """Run LOCO on one synthetic dataset (6 runs × 8 colors).

    Args:
        Y_runs: (6, 8, V_s)
        C_shifted: (8, K)
        alpha_fixed: if provided, skip GCV and use this alpha

    Returns:
        vuln: (8,) per-color LOCO vulnerability
    """
    V_s = Y_runs.shape[2]
    vuln = np.zeros(N_COLORS)

    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]

        X_train = Y_runs[:, train_colors].reshape(-1, V_s)  # (42, V_s)
        C_train = np.tile(C_shifted[train_colors], (N_RUNS, 1))  # (42, K)

        if alpha_fixed is not None:
            alpha = alpha_fixed
        else:
            alpha, _ = gcv_select_alpha(C_train, X_train)

        W_sim = fit_W_ridge(C_train, X_train, alpha)

        Y_pred = C_shifted[color:color + 1] @ W_sim  # (1, V_s)
        Y_actual = Y_runs[:, color].mean(axis=0, keepdims=True)  # (1, V_s)
        r = voxel_pattern_correlation(Y_pred, Y_actual)
        vuln[color] = r[0]

    return vuln


def weighted_spearman(x, y):
    """Weighted Spearman: emphasizes extreme ranks (worst/best colors)."""
    n = len(x)
    rx = np.argsort(np.argsort(x)).astype(float) + 1
    ry = np.argsort(np.argsort(y)).astype(float) + 1
    med = (n + 1) / 2.0
    w = np.abs(rx - med) + np.abs(ry - med)
    w = w / w.sum()

    mx = np.sum(w * rx)
    my = np.sum(w * ry)
    cov = np.sum(w * (rx - mx) * (ry - my))
    sx = np.sqrt(np.sum(w * (rx - mx) ** 2))
    sy = np.sqrt(np.sum(w * (ry - my) ** 2))

    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return cov / (sx * sy)


def perm_p_spearman(vuln_syn, vuln_obs):
    """Exact permutation p-value for Spearman ρ (8! = 40320)."""
    obs_rho, _ = spearmanr(vuln_syn, vuln_obs)
    obs_rho = float(obs_rho) if np.isfinite(obs_rho) else 0.0

    count = 0
    total = 0
    for perm in permutations(range(8)):
        r, _ = spearmanr(vuln_syn[list(perm)], vuln_obs)
        r = float(r) if np.isfinite(r) else 0.0
        if r >= obs_rho:
            count += 1
        total += 1

    return (count + 1) / (total + 1), obs_rho


def perm_p_weighted_spearman(vuln_syn, vuln_obs):
    """Exact permutation p-value for weighted Spearman."""
    obs_rho = weighted_spearman(vuln_syn, vuln_obs)

    count = 0
    total = 0
    for perm in permutations(range(8)):
        r = weighted_spearman(vuln_syn[list(perm)], vuln_obs)
        if r >= obs_rho:
            count += 1
        total += 1

    return (count + 1) / (total + 1), obs_rho


def lin_ccc(x, y):
    """Lin's Concordance Correlation Coefficient."""
    mx, my = np.mean(x), np.mean(y)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    r = np.corrcoef(x, y)[0, 1]
    return 2 * r * sx * sy / (sx**2 + sy**2 + (mx - my)**2)


# ============================================================================
# Monte Carlo ablation
# ============================================================================

def run_noise_ablation_one_combo(sub, roi, model, metric,
                                 hc_amps_dict, hc_W_dict, hc_residual_sd,
                                 vuln_observed, n_mc=100, rng_seed=42,
                                 best_params=None):
    """Run noise injection ablation for one simulation combo.

    Returns:
        dict with results per noise level
    """
    # Load Phase A best_params
    if best_params is None:
        result = load_combo_result(sub, roi, model, metric)
        best_params = result['phase_a']['best_params']
    cvd_type = CVD_TYPE[sub]

    C_shifted = get_design_matrix(model, best_params, cvd_type=cvd_type)

    # Precompute clean synthetic signal per HC
    clean_signal = {}  # {subj: (8, V_s)}
    for s in sorted(hc_W_dict.keys()):
        if s not in hc_amps_dict:
            continue
        clean_signal[s] = C_shifted @ hc_W_dict[s]  # (8, V_s)

    # Precompute alpha from noise_scale=1 (median across subjects)
    # to avoid expensive GCV at every MC iteration
    alphas = []
    for s in sorted(clean_signal.keys()):
        amp = hc_amps_dict[s]
        mean_p = amp.mean(axis=0)
        residuals = amp - mean_p[np.newaxis, :, :]
        Y_noisy = clean_signal[s][np.newaxis, :, :] + residuals
        V_s = Y_noisy.shape[2]

        # Use 7-color training set (color 0 held out)
        X_train = Y_noisy[:, 1:].reshape(-1, V_s)
        C_train = np.tile(C_shifted[1:], (N_RUNS, 1))
        alpha, _ = gcv_select_alpha(C_train, X_train)
        alphas.append(alpha)

    alpha_fixed = float(np.median(alphas))

    rng = np.random.default_rng(rng_seed)

    results_per_level = {}
    for noise_scale in NOISE_SCALES:
        print(f'    noise_scale={noise_scale:.2f}: ', end='', flush=True)

        mc_rhos = []
        mc_wrhos = []
        mc_cccs = []
        mc_worst3_overlaps = []

        for mc_i in range(n_mc):
            # Generate noisy synthetic for each HC subject, then average LOCO
            vuln_list = []
            for s in sorted(clean_signal.keys()):
                V_s = hc_amps_dict[s].shape[2]
                sd = hc_residual_sd[s]  # (V_s,)

                # Generate 6 noisy runs
                noise = rng.normal(0, 1, size=(N_RUNS, N_COLORS, V_s))
                noise *= sd[np.newaxis, np.newaxis, :]  # scale by empirical SD
                noise *= noise_scale

                Y_runs = clean_signal[s][np.newaxis, :, :] + noise  # (6, 8, V_s)

                vuln = loco_on_noisy_synthetic(Y_runs, C_shifted,
                                                alpha_fixed=alpha_fixed)
                vuln_list.append(vuln)

            # Average vulnerability across HC subjects
            vuln_mean = np.mean(vuln_list, axis=0)

            # Metrics
            rho, _ = spearmanr(vuln_mean, vuln_observed)
            rho = float(rho) if np.isfinite(rho) else 0.0
            mc_rhos.append(rho)

            wrho = weighted_spearman(vuln_mean, vuln_observed)
            mc_wrhos.append(wrho)

            ccc = lin_ccc(vuln_mean, vuln_observed)
            mc_cccs.append(ccc)

            worst3_syn = set(np.argsort(vuln_mean)[:3])
            worst3_obs = set(np.argsort(vuln_observed)[:3])
            mc_worst3_overlaps.append(len(worst3_syn & worst3_obs))

        mc_rhos = np.array(mc_rhos)
        mc_wrhos = np.array(mc_wrhos)
        mc_cccs = np.array(mc_cccs)
        mc_worst3_overlaps = np.array(mc_worst3_overlaps)

        # Compute perm-p for median MC realization
        median_idx = np.argsort(mc_rhos)[len(mc_rhos) // 2]

        # For significance assessment: fraction of MC draws that achieve p<0.05
        # Use a fast approximate: compare against shuffled null per MC
        # Instead of full 8! for each MC, use the median rho for one exact test
        # Regenerate median-rho synthetic to get exact p
        rng_median = np.random.default_rng(rng_seed + median_idx)
        vuln_list_med = []
        for s in sorted(clean_signal.keys()):
            V_s = hc_amps_dict[s].shape[2]
            sd = hc_residual_sd[s]
            noise = rng_median.normal(0, 1, size=(N_RUNS, N_COLORS, V_s))
            noise *= sd[np.newaxis, np.newaxis, :] * noise_scale
            Y_runs = clean_signal[s][np.newaxis, :, :] + noise
            vuln = loco_on_noisy_synthetic(Y_runs, C_shifted,
                                            alpha_fixed=alpha_fixed)
            vuln_list_med.append(vuln)
        vuln_median = np.mean(vuln_list_med, axis=0)

        perm_p_rho, _ = perm_p_spearman(vuln_median, vuln_observed)
        perm_p_wrho, _ = perm_p_weighted_spearman(vuln_median, vuln_observed)

        print(f'ρ={mc_rhos.mean():.3f}±{mc_rhos.std():.3f}  '
              f'wρ={mc_wrhos.mean():.3f}±{mc_wrhos.std():.3f}  '
              f'CCC={mc_cccs.mean():.3f}  '
              f'w3={mc_worst3_overlaps.mean():.1f}/3  '
              f'perm_p={perm_p_rho:.4f}')

        results_per_level[str(noise_scale)] = {
            'noise_scale': noise_scale,
            'n_mc': n_mc,
            'spearman': {
                'mean': float(mc_rhos.mean()),
                'std': float(mc_rhos.std()),
                'median': float(np.median(mc_rhos)),
                'q25': float(np.percentile(mc_rhos, 25)),
                'q75': float(np.percentile(mc_rhos, 75)),
                'perm_p_median': perm_p_rho,
            },
            'weighted_spearman': {
                'mean': float(mc_wrhos.mean()),
                'std': float(mc_wrhos.std()),
                'median': float(np.median(mc_wrhos)),
                'perm_p_median': perm_p_wrho,
            },
            'ccc': {
                'mean': float(mc_cccs.mean()),
                'std': float(mc_cccs.std()),
            },
            'worst3_overlap': {
                'mean': float(mc_worst3_overlaps.mean()),
                'std': float(mc_worst3_overlaps.std()),
            },
            'vuln_synthetic_median': vuln_median.tolist(),
        }

    return results_per_level


# ============================================================================
# Visualization
# ============================================================================

def plot_ablation_results(all_results, output_path):
    """Generate noise ablation figure (adapts grid to number of combos)."""
    import matplotlib.pyplot as plt

    n_combos = len(all_results)
    ncols = min(n_combos, 3)
    nrows = (n_combos + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(7 * ncols, 5 * nrows))
    if n_combos == 1:
        axes = [axes]
    else:
        axes = np.array(axes).ravel()

    _base_colors = ['#D32F2F', '#1565C0', '#2E7D32', '#FF8F00', '#7B1FA2', '#00838F']
    _base_styles = ['-o', '-s', '-^', '-D', '-v', '-P']
    combo_colors = (_base_colors * ((n_combos // len(_base_colors)) + 1))[:n_combos]
    combo_styles = (_base_styles * ((n_combos // len(_base_styles)) + 1))[:n_combos]

    for idx, (combo_key, combo_data) in enumerate(all_results.items()):
        ax = axes[idx]
        meta = combo_data['meta']

        noise_levels = []
        rho_means = []
        rho_q25 = []
        rho_q75 = []
        wrho_means = []
        ccc_means = []
        w3_means = []
        perm_ps = []

        for ns_key in sorted(combo_data['levels'].keys(), key=float):
            level = combo_data['levels'][ns_key]
            noise_levels.append(level['noise_scale'])
            rho_means.append(level['spearman']['mean'])
            rho_q25.append(level['spearman']['q25'])
            rho_q75.append(level['spearman']['q75'])
            wrho_means.append(level['weighted_spearman']['mean'])
            ccc_means.append(level['ccc']['mean'])
            w3_means.append(level['worst3_overlap']['mean'])
            perm_ps.append(level['spearman']['perm_p_median'])

        noise_levels = np.array(noise_levels)
        rho_means = np.array(rho_means)
        rho_q25 = np.array(rho_q25)
        rho_q75 = np.array(rho_q75)

        # Spearman ρ with IQR band
        ax.fill_between(noise_levels, rho_q25, rho_q75,
                         alpha=0.15, color=combo_colors[idx])
        ax.plot(noise_levels, rho_means, combo_styles[idx],
                color=combo_colors[idx], label='Spearman ρ', linewidth=2,
                markersize=6)

        # Weighted Spearman
        ax.plot(noise_levels, wrho_means, '--',
                color=combo_colors[idx], alpha=0.7,
                label='Weighted ρ', linewidth=1.5)

        # Mark significance threshold
        ax.axhline(0, color='gray', linewidth=0.5, linestyle=':')

        # Mark perm_p < 0.05 with stars
        for i, pp in enumerate(perm_ps):
            if pp < 0.05:
                ax.plot(noise_levels[i], rho_means[i] + 0.05, '*',
                        color='gold', markersize=12, zorder=10)
            elif pp < 0.10:
                ax.plot(noise_levels[i], rho_means[i] + 0.05, '+',
                        color='orange', markersize=8, zorder=10)

        # Secondary y-axis for worst-3 overlap
        ax2 = ax.twinx()
        ax2.bar(noise_levels + 0.05, w3_means, width=0.08,
                alpha=0.2, color=combo_colors[idx], label='Worst-3 overlap')
        ax2.set_ylim(0, 3.5)
        ax2.set_ylabel('Worst-3 overlap', fontsize=8, color='gray')
        ax2.tick_params(axis='y', labelsize=7, colors='gray')

        # Labels
        sub, roi, model = meta['sub'], meta['roi'], meta['model']
        cvd = CVD_TYPE[sub]
        orig_p = meta['original_loco_p']
        orig_rho = meta['original_loco_rho']
        sig = '*' if orig_p < 0.05 else ('†' if orig_p < 0.10 else '')
        ax.set_title(f'sub-{sub} ({cvd}) {roi} {model}\n'
                      f'Original: ρ={orig_rho:.3f} p={orig_p:.4f}{sig}',
                      fontsize=10, fontweight='bold')
        ax.set_xlabel('Noise scale (× empirical σ)', fontsize=9)
        ax.set_ylabel('Spearman ρ (synthetic vs observed)', fontsize=9)
        ax.set_xlim(-0.1, max(NOISE_SCALES) + 0.2)
        ax.set_ylim(-0.8, 1.0)
        ax.legend(fontsize=7, loc='lower left')
        ax.grid(alpha=0.2)

        # Annotate noise_scale=1 (real data level)
        ax.axvline(1.0, color='red', linewidth=1, linestyle='--', alpha=0.4)
        ax.text(1.02, 0.95, 'real noise\nlevel',
                transform=ax.get_xaxis_transform(),
                fontsize=7, color='red', alpha=0.6, va='top')

    # Hide unused axes
    for i in range(n_combos, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle('Noise Injection Ablation: Phase C LOCO Robustness\n'
                  '★ perm p<.05  + perm p<.10  (IQR band from N MC draws)',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'\n  Saved figure: {output_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Noise injection ablation for ΔRDM simulation pipeline')
    parser.add_argument('--n_mc', type=int, default=100,
                        help='Number of Monte Carlo draws per noise level')
    parser.add_argument('--output_dir', default='results/ablation',
                        help='Output directory for JSON results')
    parser.add_argument('--figure_dir', default='figures',
                        help='Output directory for figures')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    parser.add_argument('--v4_only', action='store_true',
                        help='Run V4 combos only (append to existing JSON)')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = _SCRIPT_DIR.parent / args.figure_dir
    figure_dir.mkdir(parents=True, exist_ok=True)

    # Select which combos to run
    if args.v4_only:
        combos = V4_COMBOS
        combo_label = 'V4 ONLY'
    else:
        combos = TARGET_COMBOS
        combo_label = 'V1/V2'

    print('=' * 70)
    print(f'NOISE INJECTION ABLATION ({combo_label})')
    print(f'Monte Carlo draws: {args.n_mc}')
    print(f'Noise scales: {NOISE_SCALES}')
    print(f'Target combos: {len(combos)}')
    print('=' * 70)

    # Precompute HC data per ROI (avoid reloading)
    roi_data = {}
    rois_needed = sorted(set(roi for _, roi, _, _ in combos))
    for roi in rois_needed:
        print(f'\n[Precompute] Loading HC data for {roi}...')
        amps, W, sd = precompute_hc_data(roi)
        roi_data[roi] = (amps, W, sd)
        print(f'  HC subjects: {len(amps)}, '
              f'V_s range: {min(a.shape[2] for a in amps.values())}-'
              f'{max(a.shape[2] for a in amps.values())}')

    # If v4_only, load existing results and append
    json_path = output_dir / 'noise_injection.json'
    if args.v4_only and json_path.exists():
        with open(json_path) as f:
            all_results = json.load(f)
        print(f'\n  Loaded existing: {len(all_results)} combos from {json_path.name}')
    else:
        all_results = {}

    for combo_idx, (sub, roi, model, metric) in enumerate(combos):
        combo_key = f'sub-{sub}_{roi}_{model}_{metric}'
        print(f'\n{"=" * 50}')
        print(f'[{combo_idx+1}/{len(combos)}] {combo_key}')
        print(f'{"=" * 50}')

        hc_amps, hc_W, hc_sd = roi_data[roi]

        # Load observed CVD LOCO
        vuln_observed = load_cvd_loco_observed(sub, roi)
        print(f'  vuln_observed: {np.array2string(vuln_observed, precision=3)}')

        # Load original result (V4 uses step1_loco format)
        if roi == 'V4':
            orig = load_v4_loco_result(sub, model)
        else:
            orig = load_combo_result(sub, roi, model, metric)
        orig_loco_rho = orig['phase_c']['loco_match']['spearman_rho']
        orig_loco_p = orig['phase_c']['loco_match']['perm_p']
        orig_best_params = orig['phase_a']['best_params']
        print(f'  Original LOCO: ρ={orig_loco_rho:.3f}, p={orig_loco_p:.4f}')

        t0 = datetime.now()
        levels = run_noise_ablation_one_combo(
            sub, roi, model, metric,
            hc_amps, hc_W, hc_sd,
            vuln_observed,
            n_mc=args.n_mc,
            rng_seed=args.seed + combo_idx * 1000,
            best_params=orig_best_params,
        )
        elapsed = (datetime.now() - t0).total_seconds()
        print(f'  Elapsed: {elapsed:.1f}s')

        all_results[combo_key] = {
            'meta': {
                'sub': sub,
                'roi': roi,
                'model': model,
                'metric': metric,
                'cvd_type': CVD_TYPE[sub],
                'n_mc': args.n_mc,
                'seed': args.seed,
                'original_loco_rho': orig_loco_rho,
                'original_loco_p': orig_loco_p,
                'vuln_observed': vuln_observed.tolist(),
                'elapsed_sec': round(elapsed, 1),
            },
            'levels': levels,
        }

    # Save JSON
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\n[SAVED] {json_path}')

    # Generate figure (handles variable number of combos)
    fig_path = figure_dir / 'noise_injection_ablation.png'
    plot_ablation_results(all_results, fig_path)

    # Summary table
    print('\n' + '=' * 70)
    print('SUMMARY: Noise level at which result becomes NS (p≥0.05)')
    print('=' * 70)
    print(f'{"Combo":<40} {"Orig ρ":>8} {"Orig p":>8} '
          f'{"NS at σ×":>8} {"ρ@σ=1":>8} {"p@σ=1":>8}')
    print('-' * 80)

    for combo_key, combo_data in all_results.items():
        meta = combo_data['meta']
        levels = combo_data['levels']

        # Find first noise level where perm_p >= 0.05
        ns_threshold = '>3.0'
        for ns_key in sorted(levels.keys(), key=float):
            if levels[ns_key]['spearman']['perm_p_median'] >= 0.05:
                ns_threshold = f'{float(ns_key):.2f}'
                break

        # Get metrics at noise_scale=1.0
        level_1 = levels.get('1.0', {})
        rho_1 = level_1.get('spearman', {}).get('mean', np.nan)
        p_1 = level_1.get('spearman', {}).get('perm_p_median', np.nan)

        print(f'{combo_key:<40} {meta["original_loco_rho"]:>8.3f} '
              f'{meta["original_loco_p"]:>8.4f} '
              f'{ns_threshold:>8} {rho_1:>8.3f} {p_1:>8.4f}')

    print('\nDone.')


if __name__ == '__main__':
    main()
