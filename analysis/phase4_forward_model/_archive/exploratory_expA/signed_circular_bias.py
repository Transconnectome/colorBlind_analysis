#!/usr/bin/env python3
"""
signed_circular_bias.py — Exp A3: Signed Circular Bias Analysis.

Computes the direction and magnitude of LOCO prediction errors for each color.
Uses validation LOCO pred_hues (ridge_gcv, FE-6) to determine whether CVD errors
are random (symmetric) or systematically biased in a specific direction.

Key question: Is CVD LOCO error symmetric or directional?
- HC: mean signed error ≈ 0 per color (random scatter)
- CVD cool: systematic bias (e.g., blue → cyan direction)

Input:  results/validation/sub-*_loco.json (ridge_gcv encoder, FE-6)
Output: results/signed_bias/

Usage:
    conda activate srm
    python scripts/signed_circular_bias.py \
        --validation_dir results/validation \
        --output_dir results/signed_bias
"""

import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

# ── Constants ──────────────────────────────────────────────────────────
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])
N_COLORS = 8

ENCODER = 'ridge_gcv'

CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'deutan'}

# Color axis groupings
WARM_IDX = [0, 1, 2, 3]   # red, orange, yellow, green
COOL_IDX = [4, 5, 6, 7]   # cyan, blue, purple, magenta


def circular_distance(a, b):
    """Signed circular distance: a - b, wrapped to [-180, 180]."""
    d = (a - b) % 360
    return np.where(d > 180, d - 360, d)


def load_validation_loco(validation_dir):
    """Load validation LOCO results with pred_hues."""
    results = {}
    for sub in ALL_SUBJECTS:
        path = Path(validation_dir) / f'sub-{sub}_loco.json'
        if path.exists():
            with open(path) as f:
                results[sub] = json.load(f)
    return results


def compute_signed_bias(results):
    """Compute signed circular error for each subject × ROI × color.

    Returns:
        bias: dict[sub][roi] = array of shape (N_COLORS,) — mean signed error per color
        bias_per_run: dict[sub][roi] = array of shape (N_COLORS, 6) — per-run errors
    """
    bias = {}
    bias_per_run = {}

    for sub, data in results.items():
        bias[sub] = {}
        bias_per_run[sub] = {}
        for roi in ROIS:
            if roi not in data:
                continue
            if ENCODER not in data[roi]:
                continue
            folds = data[roi][ENCODER]['folds']
            per_color_mean = np.full(N_COLORS, np.nan)
            per_color_runs = np.full((N_COLORS, 6), np.nan)

            for fold in folds:
                cidx = fold['test_color']
                true_hue = fold['true_hue']
                pred_hues = np.array(fold['pred_hues'])
                signed_err = circular_distance(pred_hues, true_hue)
                per_color_mean[cidx] = np.mean(signed_err)
                per_color_runs[cidx, :len(signed_err)] = signed_err

            bias[sub][roi] = per_color_mean
            bias_per_run[sub][roi] = per_color_runs

    return bias, bias_per_run


def crawford_howell(cvd_value, hc_values):
    """Crawford & Howell (1998) modified t-test for single case."""
    n = len(hc_values)
    hc_mean = np.mean(hc_values)
    hc_std = np.std(hc_values, ddof=1)
    if hc_std == 0:
        return np.nan, np.nan
    t = (cvd_value - hc_mean) / (hc_std * np.sqrt((n + 1) / n))
    p = 2 * stats.t.sf(np.abs(t), df=n - 1)
    return t, p


def print_report(bias):
    """Print formatted report of signed bias per color."""
    print("\n" + "=" * 100)
    print("EXP A3: SIGNED CIRCULAR BIAS ANALYSIS")
    print("=" * 100)
    print("Positive = clockwise bias, Negative = counter-clockwise bias")
    print(f"Encoder: {ENCODER} (FE-6)")

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        print(f"\n{'─' * 100}")
        print(f"  {name}")
        print(f"{'─' * 100}")

        # Header
        hdr = f"{'Subject':>10} | {'Group':>6} |"
        for cn in COLOR_NAMES:
            hdr += f" {cn:>8}"
        hdr += f" | {'Warm M':>8} | {'Cool M':>8}"
        print(hdr)
        print("-" * len(hdr))

        # Collect HC values per color for Crawford-Howell
        hc_vals = {c: [] for c in range(N_COLORS)}

        for sub in HC_SUBJECTS:
            if sub not in bias or roi not in bias[sub]:
                continue
            b = bias[sub][roi]
            warm_m = np.nanmean(b[WARM_IDX])
            cool_m = np.nanmean(b[COOL_IDX])
            line = f"{'sub-' + sub:>10} | {'HC':>6} |"
            for i in range(N_COLORS):
                line += f" {b[i]:>8.1f}"
                hc_vals[i].append(b[i])
            line += f" | {warm_m:>8.1f} | {cool_m:>8.1f}"
            print(line)

        # HC mean
        hc_mean_vals = np.array([np.mean(hc_vals[c]) for c in range(N_COLORS)])
        warm_hc = np.mean(hc_mean_vals[WARM_IDX])
        cool_hc = np.mean(hc_mean_vals[COOL_IDX])
        line = f"{'HC mean':>10} | {'':>6} |"
        for i in range(N_COLORS):
            line += f" {hc_mean_vals[i]:>8.1f}"
        line += f" | {warm_hc:>8.1f} | {cool_hc:>8.1f}"
        print(line)
        print("-" * len(hdr))

        # CVD subjects
        for sub in CVD_SUBJECTS:
            if sub not in bias or roi not in bias[sub]:
                continue
            b = bias[sub][roi]
            warm_m = np.nanmean(b[WARM_IDX])
            cool_m = np.nanmean(b[COOL_IDX])
            cvd_type = CVD_TYPES.get(sub, '?')
            line = f"{'sub-' + sub:>10} | {cvd_type:>6} |"
            for i in range(N_COLORS):
                # Crawford-Howell test
                if len(hc_vals[i]) > 1:
                    _, p = crawford_howell(b[i], hc_vals[i])
                    star = '*' if p < 0.05 else ('+' if p < 0.10 else '')
                else:
                    star = ''
                line += f" {b[i]:>7.1f}{star}"
            line += f" | {warm_m:>8.1f} | {cool_m:>8.1f}"
            print(line)

        # Summary: HC mean |signed bias| per axis
        print(f"\n  HC mean |signed error|: warm={np.mean(np.abs(hc_mean_vals[WARM_IDX])):.1f}°, "
              f"cool={np.mean(np.abs(hc_mean_vals[COOL_IDX])):.1f}°")


def plot_polar_bias(bias, output_dir):
    """Create polar plots of signed bias per color for HC mean vs CVD."""
    fig, axes = plt.subplots(1, 4, figsize=(20, 5),
                              subplot_kw={'projection': 'polar'})

    for ax_i, roi in enumerate(ROIS):
        ax = axes[ax_i]
        name = ROI_DISPLAY[roi]

        # HC mean signed bias
        hc_biases = []
        for sub in HC_SUBJECTS:
            if sub in bias and roi in bias[sub]:
                hc_biases.append(bias[sub][roi])
        if not hc_biases:
            ax.set_title(name)
            continue
        hc_mean = np.nanmean(hc_biases, axis=0)
        hc_sem = np.nanstd(hc_biases, axis=0) / np.sqrt(len(hc_biases))

        # Plot true hue positions (reference circle)
        theta = np.deg2rad(HUE_ANGLES)

        # HC: arrows from true position with bias magnitude/direction
        for i in range(N_COLORS):
            bias_rad = np.deg2rad(hc_mean[i])
            r_base = 1.0
            ax.annotate('', xy=(theta[i] + bias_rad * 0.01, r_base + abs(hc_mean[i]) * 0.005),
                        xytext=(theta[i], r_base),
                        arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

        # CVD subjects
        cvd_colors = {'08': 'red', '09': 'blue', '10': 'green'}
        for sub in CVD_SUBJECTS:
            if sub not in bias or roi not in bias[sub]:
                continue
            b = bias[sub][roi]
            # Plot as arrows from true position
            for i in range(N_COLORS):
                bias_rad = np.deg2rad(b[i])
                ax.annotate('', xy=(theta[i] + bias_rad * 0.01, 1.0 + abs(b[i]) * 0.005),
                            xytext=(theta[i], 1.0),
                            arrowprops=dict(arrowstyle='->', color=cvd_colors[sub], lw=1.5, alpha=0.7))

        # Mark color positions
        color_hex = ['#FF0000', '#FF8000', '#FFFF00', '#00FF00',
                     '#00FFFF', '#0000FF', '#8000FF', '#FF00FF']
        for i in range(N_COLORS):
            ax.scatter(theta[i], 1.0, c=color_hex[i], s=80, zorder=5, edgecolors='black', linewidth=0.5)

        ax.set_title(name, fontsize=14, fontweight='bold')
        ax.set_ylim(0, 2.0)
        ax.set_rticks([])
        ax.set_thetagrids(HUE_ANGLES, COLOR_NAMES, fontsize=7)

    plt.suptitle('Signed Circular Bias: Arrows = bias direction & magnitude\n'
                 'Gray=HC mean, Red=sub-08(D), Blue=sub-09(P), Green=sub-10(D)',
                 fontsize=11)
    plt.tight_layout()
    plt.savefig(output_dir / 'polar_signed_bias.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_bar_bias(bias, output_dir):
    """Bar chart of signed bias per color, HC mean vs CVD individuals."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    for ax_i, roi in enumerate(ROIS):
        ax = axes[ax_i // 2, ax_i % 2]
        name = ROI_DISPLAY[roi]

        # Collect HC biases
        hc_biases = []
        for sub in HC_SUBJECTS:
            if sub in bias and roi in bias[sub]:
                hc_biases.append(bias[sub][roi])
        if not hc_biases:
            ax.set_title(name)
            continue

        hc_mean = np.nanmean(hc_biases, axis=0)
        hc_sem = np.nanstd(hc_biases, axis=0) / np.sqrt(len(hc_biases))

        x = np.arange(N_COLORS)
        width = 0.2

        # HC mean
        ax.bar(x - 1.5 * width, hc_mean, width, yerr=hc_sem,
               label='HC mean', color='gray', alpha=0.7, capsize=3)

        # CVD subjects
        cvd_colors = {'08': '#e74c3c', '09': '#3498db', '10': '#2ecc71'}
        cvd_labels = {'08': 'sub-08 (D)', '09': 'sub-09 (P)', '10': 'sub-10 (D)'}
        for j, sub in enumerate(CVD_SUBJECTS):
            if sub not in bias or roi not in bias[sub]:
                continue
            b = bias[sub][roi]
            ax.bar(x + (j - 0.5) * width, b, width,
                   label=cvd_labels[sub], color=cvd_colors[sub], alpha=0.7)

        ax.axhline(0, color='black', linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
        ax.set_ylabel('Signed circular error (°)')
        ax.set_title(f'{name} — Signed Circular Bias', fontweight='bold')

        # Shade cool region
        ax.axvspan(3.5, 7.5, alpha=0.08, color='blue', label='Cool axis')

        if ax_i == 0:
            ax.legend(fontsize=8, loc='upper right')

    plt.suptitle('Exp A3: Signed Circular Bias (positive = CW, negative = CCW)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'bar_signed_bias.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_per_run_scatter(bias_per_run, output_dir):
    """Scatter plot of per-run errors for hV4, showing dispersion."""
    roi = 'V4'
    fig, axes = plt.subplots(1, N_COLORS, figsize=(24, 4), sharey=True)

    for cidx in range(N_COLORS):
        ax = axes[cidx]

        # HC runs
        hc_all_runs = []
        for sub in HC_SUBJECTS:
            if sub in bias_per_run and roi in bias_per_run[sub]:
                runs = bias_per_run[sub][roi][cidx]
                valid = runs[~np.isnan(runs)]
                hc_all_runs.extend(valid)
                ax.scatter(np.random.normal(0, 0.1, len(valid)), valid,
                           c='gray', alpha=0.3, s=15)

        # CVD runs
        cvd_colors = {'08': '#e74c3c', '09': '#3498db', '10': '#2ecc71'}
        for sub in CVD_SUBJECTS:
            if sub in bias_per_run and roi in bias_per_run[sub]:
                runs = bias_per_run[sub][roi][cidx]
                valid = runs[~np.isnan(runs)]
                offset = 0.5 + CVD_SUBJECTS.index(sub) * 0.5
                ax.scatter(np.random.normal(offset, 0.08, len(valid)), valid,
                           c=cvd_colors[sub], alpha=0.5, s=25, edgecolors='black', linewidth=0.3)

        ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
        ax.set_title(COLOR_NAMES[cidx], fontsize=10)
        ax.set_xticks([0, 0.5, 1.0, 1.5])
        ax.set_xticklabels(['HC', '08', '09', '10'], fontsize=7)

        if cidx == 0:
            ax.set_ylabel('Signed error (°)')

    plt.suptitle('hV4: Per-run signed errors (HC=gray, CVD=colored)', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'scatter_per_run_hv4.png', dpi=150, bbox_inches='tight')
    plt.close()


def save_results(bias, output_dir):
    """Save results as JSON."""
    out = {'encoder': ENCODER, 'n_channels': 6}

    for roi in ROIS:
        roi_data = {'hc': {}, 'cvd': {}}

        for sub in HC_SUBJECTS:
            if sub in bias and roi in bias[sub]:
                b = bias[sub][roi]
                roi_data['hc'][sub] = {
                    'per_color': b.tolist(),
                    'warm_mean': float(np.nanmean(b[WARM_IDX])),
                    'cool_mean': float(np.nanmean(b[COOL_IDX]))
                }

        for sub in CVD_SUBJECTS:
            if sub in bias and roi in bias[sub]:
                b = bias[sub][roi]
                roi_data['cvd'][sub] = {
                    'per_color': b.tolist(),
                    'warm_mean': float(np.nanmean(b[WARM_IDX])),
                    'cool_mean': float(np.nanmean(b[COOL_IDX])),
                    'type': CVD_TYPES.get(sub, 'unknown')
                }

        # Compute HC mean for Crawford-Howell
        hc_arr = np.array([bias[s][roi] for s in HC_SUBJECTS
                           if s in bias and roi in bias[s]])
        if len(hc_arr) > 0:
            hc_mean = np.nanmean(hc_arr, axis=0)
            roi_data['hc_mean'] = hc_mean.tolist()
            roi_data['hc_std'] = np.nanstd(hc_arr, axis=0, ddof=1).tolist()

            # Crawford-Howell per CVD per color
            for sub in CVD_SUBJECTS:
                if sub in bias and roi in bias[sub]:
                    ch_results = []
                    for c in range(N_COLORS):
                        hc_vals = hc_arr[:, c]
                        hc_vals_clean = hc_vals[~np.isnan(hc_vals)]
                        if len(hc_vals_clean) > 1:
                            t, p = crawford_howell(bias[sub][roi][c], hc_vals_clean)
                            ch_results.append({'color': COLOR_NAMES[c], 't': float(t), 'p': float(p)})
                    roi_data['cvd'][sub]['crawford_howell'] = ch_results

        out[roi] = roi_data

    with open(output_dir / 'signed_bias_results.json', 'w') as f:
        json.dump(out, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Exp A3: Signed Circular Bias')
    parser.add_argument('--validation_dir', type=str, default='results/validation')
    parser.add_argument('--output_dir', type=str, default='results/signed_bias')
    args = parser.parse_args()

    validation_dir = Path(args.validation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading validation LOCO results...")
    results = load_validation_loco(validation_dir)
    print(f"  Loaded {len(results)} subjects")

    print("Computing signed circular bias...")
    bias, bias_per_run = compute_signed_bias(results)

    print_report(bias)

    print("\nGenerating plots...")
    plot_bar_bias(bias, output_dir)
    plot_per_run_scatter(bias_per_run, output_dir)
    plot_polar_bias(bias, output_dir)

    print("Saving results...")
    save_results(bias, output_dir)

    print(f"\nDone. Results saved to {output_dir}/")


if __name__ == '__main__':
    main()
