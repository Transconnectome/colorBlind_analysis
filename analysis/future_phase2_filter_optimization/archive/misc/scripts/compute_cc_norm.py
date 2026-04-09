#!/usr/bin/env python3
"""
compute_cc_norm.py — Noise Ceiling Normalization (CC_norm) for LOCO ablation.

Computes:
  1. r_ceiling: Split-half reliability of observed CVD LOCO vulnerability
     via C(6,3)=20 split-half pairs + Spearman-Brown correction
  2. CC_norm(σ) = mean_ρ(σ) / r_ceiling for each noise level
  3. σ*: Noise level where CC_norm = 1.0 (interpolated)

σ* interpretation:
  - σ* ≈ 1.0 → noise model well-calibrated, performance at data ceiling
  - σ* << 1.0 → synthetic advantage mostly from noise absence
  - σ* > 1.0 → HC averaging exceeds ceiling (legitimate advantage)

Reference: Schoppe et al. 2016 (CC_norm concept)

Usage:
    conda activate srm
    python scripts/compute_cc_norm.py

Output:
    results/ablation/cc_norm.json
    figures/cc_norm_ablation.png
"""

import json
import numpy as np
from pathlib import Path
from itertools import combinations
from scipy.stats import spearmanr
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
    N_COLORS,
    load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)

# ============================================================================
# Constants
# ============================================================================
_ANALYSIS_DIR = Path(__file__).resolve().parent.parent.parent.parent
_LOCAL_BASELINE_1 = _ANALYSIS_DIR / 'phase1_procrustes_decoding' / 'results' / 'full_dataset_C010'
_LOCAL_BASELINE_2 = _ANALYSIS_DIR / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
_SERVER_BASELINE = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')
LOCAL_BASELINE = (
    _LOCAL_BASELINE_1 if _LOCAL_BASELINE_1.exists()
    else _LOCAL_BASELINE_2 if _LOCAL_BASELINE_2.exists()
    else _SERVER_BASELINE
)

ABLATION_JSON = _SCRIPT_DIR.parent / 'results' / 'ablation' / 'noise_injection.json'

TARGET_COMBOS = [
    ('09', 'V2', 'cone_1way', 'cosine'),
    ('08', 'V2', 'fourier',   'cosine'),
    ('08', 'V1', 'fourier',   'cosine'),
    ('09', 'V2', 'cone_3way', 'cosine'),
    ('09', 'V4', 'cone_1way', 'cosine'),    # hV4 sig (p=0.009, shift_at_both)
    ('08', 'V4', 'cone_1way', 'cosine'),    # hV4 sig (p=0.036, shift_at_both)
]

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


# ============================================================================
# Split-half LOCO
# ============================================================================

def loco_variable_runs(Y_runs, C_basis, alpha_fixed):
    """LOCO vulnerability on data with variable number of runs.

    Unlike loco_on_noisy_synthetic() which hardcodes N_RUNS=6 in the
    C_train tiling, this infers run count from Y_runs.shape[0].

    Args:
        Y_runs: (n_runs, 8, V_s)
        C_basis: (8, K) baseline design matrix
        alpha_fixed: ridge alpha

    Returns:
        vuln: (8,) per-color LOCO vulnerability (voxel pattern correlation)
    """
    n_runs = Y_runs.shape[0]
    V_s = Y_runs.shape[2]
    vuln = np.zeros(N_COLORS)

    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]

        X_train = Y_runs[:, train_colors].reshape(-1, V_s)   # (n_runs*7, V_s)
        C_train = np.tile(C_basis[train_colors], (n_runs, 1))  # (n_runs*7, K)

        W = fit_W_ridge(C_train, X_train, alpha_fixed)

        Y_pred = C_basis[color:color + 1] @ W                 # (1, V_s)
        Y_actual = Y_runs[:, color].mean(axis=0, keepdims=True)  # (1, V_s)
        r = voxel_pattern_correlation(Y_pred, Y_actual)
        vuln[color] = r[0]

    return vuln


def compute_split_half_ceiling(amp, C_basis):
    """Split-half LOCO noise ceiling for one subject-ROI.

    Procedure:
      1. Compute alpha_fixed from full 6-run data via GCV
      2. Enumerate all C(6,3)=20 half-splits
      3. Run LOCO on each half → vuln_h1, vuln_h2
      4. Spearman(vuln_h1, vuln_h2) → r_split
      5. Fisher z mean + Spearman-Brown → r_ceiling

    Args:
        amp: (6, 8, V_s)
        C_basis: (8, K)

    Returns:
        r_ceiling: float (Spearman-Brown corrected)
        r_splits: list of 20 split-half Spearman r values
        status: 'ok' or 'unreliable_loco'
    """
    n_runs = amp.shape[0]
    V_s = amp.shape[2]

    # Alpha from full data (same as observed LOCO)
    C_pooled = np.tile(C_basis, (n_runs, 1))  # (48, K)
    X_all = amp.reshape(-1, V_s)               # (48, V_s)
    alpha_fixed, _ = gcv_select_alpha(C_pooled, X_all)

    r_splits = []
    splits = list(combinations(range(n_runs), n_runs // 2))

    for split_i, half1_idx in enumerate(splits):
        half2_idx = tuple(r for r in range(n_runs) if r not in half1_idx)

        Y_h1 = amp[list(half1_idx)]  # (3, 8, V_s)
        Y_h2 = amp[list(half2_idx)]  # (3, 8, V_s)

        vuln_h1 = loco_variable_runs(Y_h1, C_basis, alpha_fixed)
        vuln_h2 = loco_variable_runs(Y_h2, C_basis, alpha_fixed)

        r, _ = spearmanr(vuln_h1, vuln_h2)
        r = float(r) if np.isfinite(r) else 0.0
        r_splits.append(r)

    r_splits_arr = np.array(r_splits)

    # All negative → unreliable
    if np.all(r_splits_arr < 0):
        return np.nan, r_splits, 'unreliable_loco'

    # Fisher z transform (clip ±0.999 to avoid arctanh divergence)
    r_clipped = np.clip(r_splits_arr, -0.999, 0.999)
    z_values = np.arctanh(r_clipped)
    z_mean = np.mean(z_values)
    r_mean = np.tanh(z_mean)

    # Spearman-Brown prophecy formula
    if r_mean <= 0:
        return 0.0, r_splits, 'unreliable_loco'

    r_ceiling = 2 * r_mean / (1 + r_mean)

    status = 'ok' if r_ceiling > 0 else 'unreliable_loco'
    return float(r_ceiling), r_splits, status


# ============================================================================
# CC_norm and σ* computation
# ============================================================================

def compute_cc_norm_curve(ablation_levels, r_ceiling):
    """Compute CC_norm(σ) = mean_ρ(σ) / r_ceiling + interpolate σ*.

    Args:
        ablation_levels: dict from noise_injection.json['combo']['levels']
        r_ceiling: split-half noise ceiling

    Returns:
        cc_norm_data: list of dicts per noise level
        sigma_star: noise level where CC_norm = 1.0
        sigma_star_status: 'ok', 'exceeds_range', 'below_zero', 'invalid_ceiling'
    """
    if np.isnan(r_ceiling) or r_ceiling <= 0:
        return [], np.nan, 'invalid_ceiling'

    cc_norm_data = []
    noise_levels = []
    cc_norms = []

    for ns_key in sorted(ablation_levels.keys(), key=float):
        level = ablation_levels[ns_key]
        sigma = level['noise_scale']
        mean_rho = level['spearman']['mean']
        std_rho = level['spearman']['std']

        ccn = mean_rho / r_ceiling
        ci_lo = (mean_rho - 1.96 * std_rho) / r_ceiling
        ci_hi = (mean_rho + 1.96 * std_rho) / r_ceiling

        noise_levels.append(sigma)
        cc_norms.append(ccn)

        cc_norm_data.append({
            'noise_scale': sigma,
            'cc_norm': float(ccn),
            'ci_95_lo': float(ci_lo),
            'ci_95_hi': float(ci_hi),
            'mean_rho': float(mean_rho),
            'std_rho': float(std_rho),
        })

    noise_levels = np.array(noise_levels)
    cc_norms = np.array(cc_norms)

    sigma_star, status = _interpolate_sigma_star(noise_levels, cc_norms)
    return cc_norm_data, sigma_star, status


def _interpolate_sigma_star(noise_levels, cc_norms):
    """Find σ* where CC_norm crosses 1.0 via linear interpolation."""
    # CC_norm(σ=0) ≤ 1.0 → σ* = 0
    if cc_norms[0] <= 1.0:
        return 0.0, 'below_zero'

    # Find first downward crossing of 1.0
    for i in range(len(cc_norms) - 1):
        if cc_norms[i] >= 1.0 and cc_norms[i + 1] < 1.0:
            sigma_star = noise_levels[i] + (1.0 - cc_norms[i]) * (
                noise_levels[i + 1] - noise_levels[i]
            ) / (cc_norms[i + 1] - cc_norms[i])
            return float(sigma_star), 'ok'

    # All > 1.0 → exceeds range
    if np.all(cc_norms > 1.0):
        return float(noise_levels[-1]), 'exceeds_range'

    # Non-monotonic: find first point below 1.0
    for i in range(len(cc_norms)):
        if cc_norms[i] < 1.0:
            if i == 0:
                return 0.0, 'below_zero'
            sigma_star = noise_levels[i - 1] + (1.0 - cc_norms[i - 1]) * (
                noise_levels[i] - noise_levels[i - 1]
            ) / (cc_norms[i] - cc_norms[i - 1])
            return float(sigma_star), 'ok'

    return np.nan, 'unknown'


# ============================================================================
# Visualization
# ============================================================================

def plot_cc_norm(all_results, output_path):
    """Generate 2x2 CC_norm figure."""
    import matplotlib
    matplotlib.use('Agg')
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
    combo_colors = (_base_colors * ((n_combos // len(_base_colors)) + 1))[:n_combos]

    for idx, (combo_key, data) in enumerate(all_results.items()):
        ax = axes[idx]

        cc_data = data['cc_norm_curve']
        r_ceil = data['r_ceiling']
        sigma_star = data['sigma_star']
        sigma_status = data['sigma_star_status']
        sub = data['sub']
        roi = data['roi']
        model = data['model']

        if not cc_data or r_ceil is None or r_ceil <= 0:
            ax.text(0.5, 0.5, 'Unreliable LOCO\n(r_ceiling invalid)',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=12, color='red')
            ax.set_title(f'{combo_key}', fontsize=10)
            continue

        sigmas = [d['noise_scale'] for d in cc_data]
        ccn = [d['cc_norm'] for d in cc_data]
        ci_lo = [d['ci_95_lo'] for d in cc_data]
        ci_hi = [d['ci_95_hi'] for d in cc_data]

        # CC_norm curve + 95% CI band
        ax.fill_between(sigmas, ci_lo, ci_hi,
                        alpha=0.15, color=combo_colors[idx])
        ax.plot(sigmas, ccn, '-o', color=combo_colors[idx],
                linewidth=2, markersize=6, label='CC_norm')

        # Ceiling line (CC_norm = 1.0)
        ax.axhline(1.0, color='black', linewidth=1.5, linestyle='-',
                   alpha=0.6, label='Ceiling (CC_norm=1)')

        # σ=1.0 vertical line (empirical noise level)
        ax.axvline(1.0, color='red', linewidth=1, linestyle='--', alpha=0.5)
        ax.text(1.02, 0.02, 'real noise\n(σ=1)',
                transform=ax.get_xaxis_transform(),
                fontsize=7, color='red', alpha=0.6, va='bottom')

        # σ* vertical line
        if sigma_status == 'ok' and sigma_star is not None:
            ax.axvline(sigma_star, color='green', linewidth=2,
                       linestyle='-.', alpha=0.7)
            ax.text(sigma_star + 0.05, 0.95, f'σ*={sigma_star:.2f}',
                    transform=ax.get_xaxis_transform(),
                    fontsize=9, color='green', fontweight='bold', va='top')

        # CC_norm at σ=1.0
        ccn_at_1 = data.get('cc_norm_at_sigma1')

        # Title with key metrics
        cvd = CVD_TYPE.get(sub, '?')
        if sigma_status == 'ok' and sigma_star is not None:
            status_str = f'σ*={sigma_star:.2f}'
        else:
            status_str = sigma_status

        title = (f'sub-{sub} ({cvd}) {roi} {model}\n'
                 f'r_ceiling={r_ceil:.3f}  {status_str}')
        if ccn_at_1 is not None:
            title += f'  CC_norm@σ=1={ccn_at_1:.3f}'

        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xlabel('Noise scale (x empirical σ)', fontsize=9)
        ax.set_ylabel('CC_norm = ρ / r_ceiling', fontsize=9)
        ax.set_xlim(-0.1, 3.2)
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(alpha=0.2)

    # Hide unused axes
    for i in range(n_combos, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle('CC_norm Noise Ceiling Normalization\n'
                 'How much synthetic advantage is due to noise absence?',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'\n  Saved figure: {output_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    print('=' * 70)
    print('CC_norm NOISE CEILING NORMALIZATION')
    print('=' * 70)

    # Load ablation results
    with open(ABLATION_JSON) as f:
        ablation = json.load(f)
    print(f'Loaded ablation: {len(ablation)} combos from {ABLATION_JSON.name}')

    C_baseline = create_basis_matrix()
    print(f'C_baseline: {C_baseline.shape}')

    # --- Step 1: Split-half noise ceiling for unique (sub, ROI) pairs ---
    unique_pairs = set()
    for sub, roi, _, _ in TARGET_COMBOS:
        unique_pairs.add((sub, roi))

    ceilings = {}
    for sub, roi in sorted(unique_pairs):
        print(f'\n--- Split-half ceiling: sub-{sub} {roi} ---')
        amp = load_amplitudes(LOCAL_BASELINE, sub, roi)
        print(f'  Amplitudes: {amp.shape}  (alpha via GCV on full data)')

        r_ceiling, r_splits, status = compute_split_half_ceiling(amp, C_baseline)

        r_arr = np.array(r_splits)
        print(f'  Split-half r: mean={r_arr.mean():.3f}, '
              f'median={np.median(r_arr):.3f}, '
              f'range=[{r_arr.min():.3f}, {r_arr.max():.3f}]')
        print(f'  r_ceiling (Spearman-Brown): {r_ceiling:.3f}  [{status}]')

        ceilings[(sub, roi)] = {
            'r_ceiling': float(r_ceiling) if np.isfinite(r_ceiling) else None,
            'r_splits': [float(r) for r in r_splits],
            'r_splits_mean': float(r_arr.mean()),
            'r_splits_std': float(r_arr.std()),
            'n_splits': len(r_splits),
            'status': status,
        }

    # --- Step 2-3: CC_norm + σ* for each combo ---
    all_results = {}

    for sub, roi, model, metric in TARGET_COMBOS:
        combo_key = f'sub-{sub}_{roi}_{model}_{metric}'
        print(f'\n--- CC_norm: {combo_key} ---')

        ceil_data = ceilings[(sub, roi)]
        r_ceiling = ceil_data['r_ceiling']

        if r_ceiling is None or r_ceiling <= 0:
            print(f'  SKIP: invalid r_ceiling')
            all_results[combo_key] = {
                'sub': sub, 'roi': roi, 'model': model, 'metric': metric,
                'r_ceiling': None,
                'r_ceiling_splits': ceil_data,
                'cc_norm_curve': [],
                'sigma_star': None,
                'sigma_star_status': 'invalid_ceiling',
                'cc_norm_at_sigma1': None,
            }
            continue

        ablation_levels = ablation[combo_key]['levels']
        cc_norm_data, sigma_star, sigma_status = compute_cc_norm_curve(
            ablation_levels, r_ceiling)

        # CC_norm at σ=1.0
        ccn_at_1 = None
        for d in cc_norm_data:
            if d['noise_scale'] == 1.0:
                ccn_at_1 = d['cc_norm']

        print(f'  r_ceiling = {r_ceiling:.3f}')
        print(f'  CC_norm@σ=0 = {cc_norm_data[0]["cc_norm"]:.3f}')
        if ccn_at_1 is not None:
            print(f'  CC_norm@σ=1 = {ccn_at_1:.3f}')
        if sigma_star is not None and np.isfinite(sigma_star):
            print(f'  σ* = {sigma_star:.3f} [{sigma_status}]')
        else:
            print(f'  σ* = N/A [{sigma_status}]')

        all_results[combo_key] = {
            'sub': sub,
            'roi': roi,
            'model': model,
            'metric': metric,
            'r_ceiling': float(r_ceiling),
            'r_ceiling_splits': ceil_data,
            'cc_norm_curve': cc_norm_data,
            'sigma_star': float(sigma_star) if (sigma_star is not None and np.isfinite(sigma_star)) else None,
            'sigma_star_status': sigma_status,
            'cc_norm_at_sigma1': float(ccn_at_1) if ccn_at_1 is not None else None,
        }

    # --- Save JSON ---
    output_dir = _SCRIPT_DIR.parent / 'results' / 'ablation'
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'cc_norm.json'
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\n[SAVED] {json_path}')

    # --- Figure ---
    figure_dir = _SCRIPT_DIR.parent / 'figures'
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig_path = figure_dir / 'cc_norm_ablation.png'
    plot_cc_norm(all_results, fig_path)

    # --- Summary Table ---
    print('\n' + '=' * 70)
    print('SUMMARY: CC_norm Noise Ceiling Normalization')
    print('=' * 70)
    print(f'{"Combo":<40} {"r_ceil":>8} {"σ*":>8} '
          f'{"CC@σ=0":>8} {"CC@σ=1":>8} {"Status":>14}')
    print('-' * 86)

    for combo_key, data in all_results.items():
        r_c = data['r_ceiling']
        ss = data['sigma_star']
        ccn0 = data['cc_norm_curve'][0]['cc_norm'] if data['cc_norm_curve'] else np.nan
        ccn1 = data.get('cc_norm_at_sigma1')

        r_str = f'{r_c:.3f}' if r_c is not None else 'N/A'
        ss_str = f'{ss:.3f}' if ss is not None else 'N/A'
        ccn0_str = f'{ccn0:.3f}' if np.isfinite(ccn0) else 'N/A'
        ccn1_str = f'{ccn1:.3f}' if ccn1 is not None else 'N/A'
        status = data['sigma_star_status']

        print(f'{combo_key:<40} {r_str:>8} {ss_str:>8} '
              f'{ccn0_str:>8} {ccn1_str:>8} {status:>14}')

    # --- Validation ---
    print('\n' + '=' * 70)
    print('VALIDATION')
    print('=' * 70)

    for combo_key, data in all_results.items():
        checks = []
        r_c = data['r_ceiling']

        if r_c is not None:
            if 0.1 < r_c < 0.9:
                checks.append(f'  [ok] r_ceiling={r_c:.3f} in reasonable range [0.1, 0.9]')
            else:
                checks.append(f'  [!]  r_ceiling={r_c:.3f} outside typical range')

        if data['cc_norm_curve']:
            ccn0 = data['cc_norm_curve'][0]['cc_norm']
            if ccn0 > 1.0:
                checks.append(f'  [ok] CC_norm(σ=0)={ccn0:.3f} > 1.0 (noise-free exceeds ceiling)')
            else:
                checks.append(f'  [!]  CC_norm(σ=0)={ccn0:.3f} <= 1.0 (noise-free below ceiling)')

        ss = data['sigma_star']
        if ss is not None and 0 < ss < 3:
            checks.append(f'  [ok] σ*={ss:.3f} in physical range (0, 3)')
        elif ss is not None:
            checks.append(f'  [!]  σ*={ss:.3f} outside expected range')

        if checks:
            print(f'\n{combo_key}:')
            for c in checks:
                print(c)

    # Cross-combo validation: sub-09 V2 cone_1way should have highest CC_norm@σ=1
    print('\n--- Cross-combo: CC_norm@σ=1 ranking ---')
    ccn1_vals = {}
    for combo_key, data in all_results.items():
        v = data.get('cc_norm_at_sigma1')
        if v is not None:
            ccn1_vals[combo_key] = v
    if ccn1_vals:
        ranked = sorted(ccn1_vals.items(), key=lambda x: x[1], reverse=True)
        for rank, (k, v) in enumerate(ranked, 1):
            marker = ' <-- strongest' if rank == 1 else ''
            print(f'  {rank}. {k}: {v:.3f}{marker}')

    print('\nDone.')


if __name__ == '__main__':
    main()
