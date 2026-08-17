#!/usr/bin/env python3
"""
analysis_srm_position_displacement.py — Per-color SRM position displacement.

For each color, compute the Euclidean displacement of CVD's projection
from the HC shared response in SRM space, and test whether it exceeds
HC inter-subject variability (Crawford-Howell).

Method:
  7-fold LOO SRM (each fold holds out 1 HC subject).
  For each fold f, for each color c:
    disp_HC(f,c) = ||Z_heldout[:,c] - S[:,c]||_2
    disp_CVD(f,c) = ||Z_cvd_08[:,c] - S[:,c]||_2

  Per-color Crawford-Howell:
    HC sample = {disp_HC(0,c), ..., disp_HC(6,c)}  (n=7)
    CVD value  = mean_f(disp_CVD(f,c))  (averaged across 7 folds)
    t = (CVD - HC_mean) / (HC_sd * sqrt(1 + 1/n))

Output:
  - results/srm_position_displacement/summary.json
  - figures/srm_position_displacement.png
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

# ── paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]  # future_phase3_behavioral_analysis/
PROJ = ROOT.parent.parent                    # colorBlind_analysis/
PRECOMP = PROJ / 'analysis' / 'future_phase2_filter_optimization' / 'cone_shift_pipeline' / 'results' / 'precomputed'
OUT_DIR = ROOT / 'results' / 'srm_position_displacement'
FIG_DIR = ROOT / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── constants ─────────────────────────────────────────────────────────
ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_K = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}
N_FOLDS = 7
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
N_COLORS = 8

# LOCO voxel_corr for sub-08 (ridge_gcv, from validation_lf4)
LOCO_SUB08 = {
    'V1': {'red': 0.123, 'orange': 0.017, 'yellow': 0.070, 'green': -0.080,
            'cyan': 0.150, 'blue': 0.202, 'purple': -0.582, 'magenta': -0.059},
    'V2': {'red': 0.361, 'orange': -0.459, 'yellow': 0.053, 'green': -0.427,
            'cyan': 0.053, 'blue': -0.419, 'purple': -0.729, 'magenta': -0.010},
}


def crawford_howell(case_val, control_vals):
    """Crawford-Howell t-test for single case vs control group."""
    n = len(control_vals)
    m = np.mean(control_vals)
    s = np.std(control_vals, ddof=1)
    if s < 1e-12:
        return np.nan, np.nan
    t = (case_val - m) / (s * np.sqrt(1 + 1/n))
    p = stats.t.sf(t, df=n-1)  # one-sided: CVD > HC
    return float(t), float(p)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    results = {}

    for roi in ROIS:
        roi_dir = PRECOMP / roi
        if not roi_dir.exists():
            print(f'  skip {roi} (no precomputed dir)')
            continue

        print(f'\n=== {roi} (K={ROI_K[roi]}) ===')

        # Collect per-fold displacements
        hc_disps = np.zeros((N_FOLDS, N_COLORS))   # displacement of held-out HC
        cvd_disps = np.zeros((N_FOLDS, N_COLORS))   # displacement of CVD sub-08

        # Also collect raw positions for visualization
        shared_responses = []
        z_heldouts = []
        z_cvds = []

        for f in range(N_FOLDS):
            fold_dir = roi_dir / f'fold_{f}'
            S = np.load(fold_dir / 'shared_response.npy')    # (K, 8)
            Z_hc = np.load(fold_dir / 'Z_heldout.npy')       # (K, 8)
            Z_cvd = np.load(fold_dir / 'Z_cvd_08.npy')       # (K, 8)

            shared_responses.append(S)
            z_heldouts.append(Z_hc)
            z_cvds.append(Z_cvd)

            for c in range(N_COLORS):
                hc_disps[f, c] = np.linalg.norm(Z_hc[:, c] - S[:, c])
                cvd_disps[f, c] = np.linalg.norm(Z_cvd[:, c] - S[:, c])

        # Per-color analysis
        results[roi] = {'colors': {}}

        print(f'  {"Color":<10} {"HC mean":>8} {"HC SD":>7} {"CVD mean":>9} '
              f'{"t":>7} {"p (1-s)":>8} {"Sig?":>5} {"LOCO r":>8}')
        print('  ' + '-' * 70)

        for c in range(N_COLORS):
            cname = COLOR_NAMES[c]

            # HC: each fold contributes one held-out HC displacement
            hc_vals = hc_disps[:, c]  # (7,)

            # CVD: average across folds (each fold is a slightly different SRM)
            cvd_mean = float(np.mean(cvd_disps[:, c]))
            cvd_sd = float(np.std(cvd_disps[:, c], ddof=1))

            # Crawford-Howell: is CVD displacement > HC displacement?
            t_val, p_val = crawford_howell(cvd_mean, hc_vals)
            sig = p_val < 0.05 if not np.isnan(p_val) else False

            loco_r = LOCO_SUB08.get(roi, {}).get(cname, np.nan)

            print(f'  {cname:<10} {np.mean(hc_vals):>8.3f} {np.std(hc_vals, ddof=1):>7.3f} '
                  f'{cvd_mean:>9.3f} {t_val:>7.2f} {p_val:>8.4f} '
                  f'{"*" if sig else "":>5} {loco_r:>8.3f}')

            results[roi]['colors'][cname] = {
                'hc_displacement_mean': float(np.mean(hc_vals)),
                'hc_displacement_sd': float(np.std(hc_vals, ddof=1)),
                'hc_displacement_values': hc_vals.tolist(),
                'cvd_displacement_mean': cvd_mean,
                'cvd_displacement_sd': cvd_sd,
                'cvd_displacement_values': cvd_disps[:, c].tolist(),
                'crawford_howell_t': t_val,
                'crawford_howell_p_onesided': p_val,
                'significant_005': bool(sig),
                'loco_voxel_corr': loco_r if not np.isnan(loco_r) else None,
            }

        # Correlation: CVD displacement vs LOCO
        if roi in LOCO_SUB08:
            cvd_disp_arr = np.array([results[roi]['colors'][cn]['cvd_displacement_mean']
                                     for cn in COLOR_NAMES])
            loco_arr = np.array([LOCO_SUB08[roi][cn] for cn in COLOR_NAMES])

            r_s, p_s = stats.spearmanr(cvd_disp_arr, loco_arr)
            r_p, p_p = stats.pearsonr(cvd_disp_arr, loco_arr)

            print(f'\n  Correlation (CVD displacement vs LOCO, n=8):')
            print(f'    Spearman r={r_s:.3f}, p={p_s:.3f}')
            print(f'    Pearson  r={r_p:.3f}, p={p_p:.3f}')

            results[roi]['correlation'] = {
                'spearman_r': float(r_s), 'spearman_p': float(p_s),
                'pearson_r': float(r_p), 'pearson_p': float(p_p),
                'note': 'Negative r = high displacement -> low LOCO (expected direction)',
            }

    # ── Save JSON ─────────────────────────────────────────────────────
    with open(OUT_DIR / 'summary.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: {OUT_DIR / "summary.json"}')

    # ── Figure: Per-color displacement comparison ─────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    color_hex = {
        'red': '#FF0000', 'orange': '#FF8000', 'yellow': '#CCCC00',
        'green': '#00CC00', 'cyan': '#00CCCC', 'blue': '#0000FF',
        'purple': '#8000FF', 'magenta': '#FF00FF',
    }

    for idx, roi in enumerate(ROIS):
        if roi not in results:
            continue
        ax = axes[idx]

        hc_means = []
        hc_sds = []
        cvd_means = []
        sig_flags = []

        for cn in COLOR_NAMES:
            d = results[roi]['colors'][cn]
            hc_means.append(d['hc_displacement_mean'])
            hc_sds.append(d['hc_displacement_sd'])
            cvd_means.append(d['cvd_displacement_mean'])
            sig_flags.append(d['significant_005'])

        x = np.arange(N_COLORS)
        width = 0.35

        bars_hc = ax.bar(x - width/2, hc_means, width, yerr=hc_sds,
                         color='steelblue', alpha=0.7, label='HC (held-out)', capsize=3)
        bars_cvd = ax.bar(x + width/2, cvd_means, width,
                          color='#d62728', alpha=0.7, label='CVD (sub-08)')

        # Mark significant colors
        for i, sig in enumerate(sig_flags):
            if sig:
                ax.text(x[i] + width/2, cvd_means[i] + 0.02, '*',
                        ha='center', va='bottom', fontsize=14, fontweight='bold')

        # Color-coded x-tick labels
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=8)
        for i, label in enumerate(ax.get_xticklabels()):
            label.set_color(color_hex[COLOR_NAMES[i]])
            label.set_fontweight('bold')

        ax.set_ylabel('Displacement from shared response')
        ax.set_title(f'{roi}')
        ax.legend(fontsize=8, loc='upper right')

        # Add correlation if available
        if 'correlation' in results[roi]:
            corr = results[roi]['correlation']
            ax.text(0.02, 0.95,
                    f"r_s={corr['spearman_r']:.2f}, p={corr['spearman_p']:.3f}",
                    transform=ax.transAxes, fontsize=7, va='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    fig.suptitle('SRM Per-Color Position Displacement: HC vs CVD (sub-08)\n'
                 'Crawford-Howell test (* = p < 0.05, one-sided)',
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'srm_position_displacement.png', dpi=150)
    plt.close(fig)
    print(f'Saved: {FIG_DIR / "srm_position_displacement.png"}')

    # ── Figure 2: Displacement vs LOCO scatter ────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    for idx, roi in enumerate(['V1', 'V2']):
        if roi not in results or 'correlation' not in results[roi]:
            continue
        ax = axes[idx]

        for cn in COLOR_NAMES:
            d = results[roi]['colors'][cn]
            marker = 's' if d['significant_005'] else 'o'
            edge = 'black' if d['significant_005'] else 'gray'
            ax.scatter(d['cvd_displacement_mean'], d['loco_voxel_corr'],
                       c=color_hex[cn], marker=marker, s=100,
                       edgecolors=edge, linewidths=1.5, zorder=3)
            ax.annotate(cn, (d['cvd_displacement_mean'], d['loco_voxel_corr']),
                        fontsize=8, ha='left', va='bottom',
                        xytext=(4, 4), textcoords='offset points')

        ax.axhline(0, color='gray', ls=':', alpha=0.5)

        corr = results[roi]['correlation']
        ax.set_xlabel('SRM Position Displacement (CVD)')
        ax.set_ylabel('LOCO voxel_corr (sub-08)')
        ax.set_title(f'{roi}: r_s={corr["spearman_r"]:.2f}, p={corr["spearman_p"]:.3f}')

    fig.suptitle('SRM Position Displacement vs LOCO Vulnerability', fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'srm_displacement_vs_loco.png', dpi=150)
    plt.close(fig)
    print(f'Saved: {FIG_DIR / "srm_displacement_vs_loco.png"}')


if __name__ == '__main__':
    main()
