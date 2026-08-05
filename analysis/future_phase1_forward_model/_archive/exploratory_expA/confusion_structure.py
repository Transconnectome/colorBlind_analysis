#!/usr/bin/env python3
"""
confusion_structure.py — Exp A5: Neighboring-Color Confusion Structure.

Analyzes which colors are confused with which when LOCO prediction fails.
Classifies each predicted hue into its nearest color category to build
8×8 confusion matrices.

Key question: Do CVD errors show nearest-neighbor confusion (smooth distortion)
or non-adjacent confusion (axis compression)?

Input:  results/validation/sub-*_loco.json (ridge_gcv)
Output: results/confusion_structure/

Usage:
    conda activate srm
    python scripts/confusion_structure.py \
        --validation_dir results/validation \
        --output_dir results/confusion_structure
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


def classify_hue(pred_hue):
    """Classify a predicted hue to the nearest of 8 color categories."""
    dists = np.abs(pred_hue - HUE_ANGLES)
    dists = np.minimum(dists, 360 - dists)
    return np.argmin(dists)


def angular_step_distance(i, j):
    """Number of steps between two color indices on the hue circle (0-4)."""
    d = abs(i - j)
    return min(d, N_COLORS - d)


def load_validation_loco(validation_dir):
    """Load validation LOCO results."""
    results = {}
    for sub in ALL_SUBJECTS:
        path = Path(validation_dir) / f'sub-{sub}_loco.json'
        if path.exists():
            with open(path) as f:
                results[sub] = json.load(f)
    return results


def build_confusion_matrices(results):
    """Build confusion matrices from LOCO predictions.

    Returns:
        confusion: dict[sub][roi] = (8, 8) matrix
            Row = true color, Col = predicted (classified) color
            Values = proportion of runs classified as each color
        raw_counts: dict[sub][roi] = (8, 8) int matrix (counts)
    """
    confusion = {}
    raw_counts = {}

    for sub, data in results.items():
        confusion[sub] = {}
        raw_counts[sub] = {}

        for roi in ROIS:
            if roi not in data or ENCODER not in data[roi]:
                continue

            folds = data[roi][ENCODER]['folds']
            counts = np.zeros((N_COLORS, N_COLORS), dtype=int)

            for fold in folds:
                cidx = fold['test_color']
                pred_hues = fold['pred_hues']
                for ph in pred_hues:
                    classified = classify_hue(ph)
                    counts[cidx, classified] += 1

            # Normalize rows to proportions
            row_sums = counts.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1
            conf = counts / row_sums

            confusion[sub][roi] = conf
            raw_counts[sub][roi] = counts

    return confusion, raw_counts


def compute_confusion_metrics(confusion):
    """Compute summary metrics from confusion matrices.

    Returns per subject-roi:
        - accuracy: diagonal proportion (correct classification)
        - neighbor_error: proportion of errors going to ±1 adjacent colors
        - distant_error: proportion of errors going to ±2 or more
        - mean_step_distance: average step distance of errors
    """
    metrics = {}

    for sub in confusion:
        metrics[sub] = {}
        for roi in confusion[sub]:
            conf = confusion[sub][roi]
            diag = np.diag(conf)
            accuracy = np.mean(diag)

            # Off-diagonal analysis
            step_distances = []
            neighbor_err = 0
            distant_err = 0
            total_err = 0

            for true_c in range(N_COLORS):
                for pred_c in range(N_COLORS):
                    if true_c == pred_c:
                        continue
                    weight = conf[true_c, pred_c]
                    if weight > 0:
                        step = angular_step_distance(true_c, pred_c)
                        step_distances.append((step, weight))
                        if step == 1:
                            neighbor_err += weight
                        else:
                            distant_err += weight
                        total_err += weight

            if total_err > 0:
                neighbor_frac = neighbor_err / total_err
                distant_frac = distant_err / total_err
                mean_step = sum(s * w for s, w in step_distances) / sum(w for _, w in step_distances)
            else:
                neighbor_frac = distant_frac = mean_step = np.nan

            # Per-color accuracy (warm vs cool)
            warm_acc = np.mean(diag[:4])
            cool_acc = np.mean(diag[4:])

            metrics[sub][roi] = {
                'accuracy': float(accuracy),
                'warm_accuracy': float(warm_acc),
                'cool_accuracy': float(cool_acc),
                'neighbor_error_frac': float(neighbor_frac),
                'distant_error_frac': float(distant_frac),
                'mean_step_distance': float(mean_step),
                'per_color_accuracy': diag.tolist()
            }

    return metrics


def print_report(confusion, metrics):
    """Print confusion analysis report."""
    print("\n" + "=" * 100)
    print("EXP A5: NEIGHBORING-COLOR CONFUSION STRUCTURE")
    print("=" * 100)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        print(f"\n{'─' * 100}")
        print(f"  {name}")
        print(f"{'─' * 100}")

        # Summary metrics table
        print(f"\n  {'Subject':>10} | {'Group':>6} | {'Acc':>6} | {'Warm':>6} | {'Cool':>6} | "
              f"{'Nbr%':>6} | {'Dist%':>6} | {'MeanStep':>8}")
        print("  " + "-" * 80)

        for sub in HC_SUBJECTS + CVD_SUBJECTS:
            if sub not in metrics or roi not in metrics[sub]:
                continue
            m = metrics[sub][roi]
            group = 'HC' if sub in HC_SUBJECTS else CVD_TYPES.get(sub, 'CVD')
            print(f"  {'sub-'+sub:>10} | {group:>6} | {m['accuracy']:>.3f} | "
                  f"{m['warm_accuracy']:>.3f} | {m['cool_accuracy']:>.3f} | "
                  f"{m['neighbor_error_frac']:>.3f} | {m['distant_error_frac']:>.3f} | "
                  f"{m['mean_step_distance']:>8.2f}")

        # HC mean
        hc_accs = [metrics[s][roi]['accuracy'] for s in HC_SUBJECTS
                   if s in metrics and roi in metrics[s]]
        hc_warm = [metrics[s][roi]['warm_accuracy'] for s in HC_SUBJECTS
                   if s in metrics and roi in metrics[s]]
        hc_cool = [metrics[s][roi]['cool_accuracy'] for s in HC_SUBJECTS
                   if s in metrics and roi in metrics[s]]
        hc_step = [metrics[s][roi]['mean_step_distance'] for s in HC_SUBJECTS
                   if s in metrics and roi in metrics[s]]
        if hc_accs:
            print("  " + "-" * 80)
            print(f"  {'HC mean':>10} | {'':>6} | {np.mean(hc_accs):>.3f} | "
                  f"{np.mean(hc_warm):>.3f} | {np.mean(hc_cool):>.3f} | "
                  f"{'':>6} | {'':>6} | {np.mean(hc_step):>8.2f}")

        # Print hV4 confusion matrix for CVD subjects
        if roi == 'V4':
            for sub in CVD_SUBJECTS:
                if sub not in confusion or roi not in confusion[sub]:
                    continue
                conf = confusion[sub][roi]
                cvd_type = CVD_TYPES.get(sub, '?')
                print(f"\n  Confusion matrix — sub-{sub} ({cvd_type}):")
                label = 'True\\Pred'
                print(f"  {label:>10}", end='')
                for cn in COLOR_NAMES:
                    print(f" {cn[:4]:>6}", end='')
                print()
                for i in range(N_COLORS):
                    print(f"  {COLOR_NAMES[i]:>10}", end='')
                    for j in range(N_COLORS):
                        val = conf[i, j]
                        marker = '*' if i == j else (' ' if val < 0.15 else '!')
                        print(f" {val:>5.2f}{marker}", end='')
                    print()


def plot_confusion_matrices(confusion, output_dir):
    """Plot confusion matrices as heatmaps."""
    for roi in ROIS:
        name = ROI_DISPLAY[roi]

        # HC mean confusion
        hc_confs = []
        for sub in HC_SUBJECTS:
            if sub in confusion and roi in confusion[sub]:
                hc_confs.append(confusion[sub][roi])
        if not hc_confs:
            continue
        hc_mean_conf = np.mean(hc_confs, axis=0)

        ncols = 1 + len(CVD_SUBJECTS)
        fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4.5))
        if ncols == 1:
            axes = [axes]

        # HC mean
        ax = axes[0]
        im = ax.imshow(hc_mean_conf, cmap='Blues', vmin=0, vmax=0.6)
        ax.set_title('HC mean', fontweight='bold')
        ax.set_xticks(range(N_COLORS))
        ax.set_xticklabels(COLOR_NAMES, rotation=90, fontsize=8)
        ax.set_yticks(range(N_COLORS))
        ax.set_yticklabels(COLOR_NAMES, fontsize=8)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('True')

        # Annotate values
        for i in range(N_COLORS):
            for j in range(N_COLORS):
                val = hc_mean_conf[i, j]
                if val > 0.05:
                    color = 'white' if val > 0.3 else 'black'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                            fontsize=7, color=color)

        # CVD subjects
        for idx, sub in enumerate(CVD_SUBJECTS):
            if sub not in confusion or roi not in confusion[sub]:
                continue
            ax = axes[1 + idx]
            conf = confusion[sub][roi]
            ax.imshow(conf, cmap='Blues', vmin=0, vmax=0.6)
            cvd_type = CVD_TYPES.get(sub, '?')
            ax.set_title(f'sub-{sub} ({cvd_type})', fontweight='bold')
            ax.set_xticks(range(N_COLORS))
            ax.set_xticklabels(COLOR_NAMES, rotation=90, fontsize=8)
            ax.set_yticks(range(N_COLORS))
            ax.set_yticklabels(COLOR_NAMES, fontsize=8)
            ax.set_xlabel('Predicted')

            for i in range(N_COLORS):
                for j in range(N_COLORS):
                    val = conf[i, j]
                    if val > 0.05:
                        color = 'white' if val > 0.3 else 'black'
                        ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                                fontsize=7, color=color)

        fig.colorbar(im, ax=axes, shrink=0.7, label='Proportion')
        plt.suptitle(f'{name}: Color Confusion Matrices (LOCO FE-6 ridge_gcv)',
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / f'confusion_{roi}.png', dpi=150, bbox_inches='tight')
        plt.close()


def plot_step_distribution(confusion, output_dir):
    """Plot distribution of confusion step distances for hV4."""
    roi = 'V4'
    name = 'hV4'

    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)

    # HC mean
    hc_confs = [confusion[s][roi] for s in HC_SUBJECTS
                if s in confusion and roi in confusion[s]]
    if not hc_confs:
        plt.close()
        return
    hc_mean_conf = np.mean(hc_confs, axis=0)

    groups = [('HC mean', hc_mean_conf, 'gray')] + \
             [(f'sub-{s} ({CVD_TYPES.get(s, "?")})', confusion[s][roi],
               {'08': '#e74c3c', '09': '#3498db', '10': '#2ecc71'}[s])
              for s in CVD_SUBJECTS if s in confusion and roi in confusion[s]]

    max_step = 4  # on 8-color circle

    for ax_i, (label, conf, color) in enumerate(groups):
        ax = axes[ax_i]

        # Compute step distribution per color
        step_dist = np.zeros((N_COLORS, max_step + 1))  # color × step
        for true_c in range(N_COLORS):
            for pred_c in range(N_COLORS):
                step = angular_step_distance(true_c, pred_c)
                step_dist[true_c, step] += conf[true_c, pred_c]

        # Stacked bar: warm vs cool
        steps = np.arange(max_step + 1)
        warm_dist = np.mean(step_dist[:4], axis=0)
        cool_dist = np.mean(step_dist[4:], axis=0)

        width = 0.35
        ax.bar(steps - width/2, warm_dist, width, label='Warm colors', color='#e67e22', alpha=0.7)
        ax.bar(steps + width/2, cool_dist, width, label='Cool colors', color='#3498db', alpha=0.7)

        ax.set_xlabel('Step distance')
        ax.set_xticks(steps)
        ax.set_xticklabels(['0\n(correct)', '1\n(±45°)', '2\n(±90°)', '3\n(±135°)', '4\n(180°)'],
                           fontsize=8)
        ax.set_title(label, fontweight='bold', fontsize=10)
        if ax_i == 0:
            ax.set_ylabel('Proportion')
            ax.legend(fontsize=7)

    plt.suptitle(f'{name}: Step Distance Distribution (warm vs cool)',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'step_distribution_hv4.png', dpi=150, bbox_inches='tight')
    plt.close()


def save_results(confusion, raw_counts, metrics, output_dir):
    """Save results."""
    out = {'encoder': ENCODER, 'n_channels': 6}

    for roi in ROIS:
        roi_data = {'metrics': {}, 'confusion_matrices': {}}

        for sub in ALL_SUBJECTS:
            if sub in metrics and roi in metrics[sub]:
                roi_data['metrics'][sub] = metrics[sub][roi]
            if sub in confusion and roi in confusion[sub]:
                roi_data['confusion_matrices'][sub] = {
                    'proportions': confusion[sub][roi].tolist(),
                    'counts': raw_counts[sub][roi].tolist()
                }

        out[roi] = roi_data

    with open(output_dir / 'confusion_results.json', 'w') as f:
        json.dump(out, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Exp A5: Confusion Structure')
    parser.add_argument('--validation_dir', type=str, default='results/validation')
    parser.add_argument('--output_dir', type=str, default='results/confusion_structure')
    args = parser.parse_args()

    validation_dir = Path(args.validation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading validation LOCO results...")
    results = load_validation_loco(validation_dir)
    print(f"  Loaded {len(results)} subjects")

    print("Building confusion matrices...")
    confusion, raw_counts = build_confusion_matrices(results)

    print("Computing confusion metrics...")
    metrics = compute_confusion_metrics(confusion)

    print_report(confusion, metrics)

    print("\nGenerating plots...")
    plot_confusion_matrices(confusion, output_dir)
    plot_step_distribution(confusion, output_dir)

    print("Saving results...")
    save_results(confusion, raw_counts, metrics, output_dir)

    print(f"\nDone. Results saved to {output_dir}/")


if __name__ == '__main__':
    main()
