#!/usr/bin/env python3
"""
pairwise_residual_heatmap.py — Exp A4: 28-Pair Pairwise Residual Heatmap.

Constructs predicted RDMs from LOCO predicted hues and compares HC vs CVD
pairwise angular distance patterns.

Key question: Which of the 28 color pairs show the largest HC-CVD difference?

Method:
  1. Per subject: mean pred_hue per held-out color → 8 predicted angles
  2. 28-pair predicted distances = circular_distance(pred_i, pred_j)
  3. HC mean predicted RDM vs CVD predicted RDMs → effect size heatmap

Input:  results/validation/sub-*_loco.json (ridge_gcv)
Output: results/pairwise_residual/

Usage:
    conda activate srm
    python scripts/pairwise_residual_heatmap.py \
        --validation_dir results/validation \
        --output_dir results/pairwise_residual
"""

import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from scipy import stats
from itertools import combinations

# ── Constants ──────────────────────────────────────────────────────────
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])
N_COLORS = 8
PAIR_INDICES = list(combinations(range(N_COLORS), 2))
N_PAIRS = 28

ENCODER = 'ridge_gcv'

# Pair categorization
LM_PAIRS = [(0, 3), (0, 1), (1, 3)]  # red-green, red-orange, orange-green
S_PAIRS = [(5, 6), (3, 5), (5, 2)]   # blue-purple, green-blue, blue-yellow
CROSS_PAIRS = [(0, 5), (1, 6)]        # red-blue, orange-purple

CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'deutan'}


def circular_abs_distance(a, b):
    """Absolute circular distance between two angles."""
    d = np.abs(a - b) % 360
    return np.minimum(d, 360 - d)


def load_validation_loco(validation_dir):
    """Load validation LOCO results."""
    results = {}
    for sub in ALL_SUBJECTS:
        path = Path(validation_dir) / f'sub-{sub}_loco.json'
        if path.exists():
            with open(path) as f:
                results[sub] = json.load(f)
    return results


def compute_predicted_rdms(results):
    """Compute predicted RDMs from LOCO pred_hues.

    Returns:
        rdms: dict[sub][roi] = (8, 8) symmetric distance matrix
        pred_hues: dict[sub][roi] = (8,) mean predicted hues
    """
    rdms = {}
    pred_hues_dict = {}

    for sub, data in results.items():
        rdms[sub] = {}
        pred_hues_dict[sub] = {}

        for roi in ROIS:
            if roi not in data or ENCODER not in data[roi]:
                continue

            folds = data[roi][ENCODER]['folds']
            mean_pred = np.full(N_COLORS, np.nan)

            for fold in folds:
                cidx = fold['test_color']
                preds = np.array(fold['pred_hues'])
                # Circular mean
                rad = np.deg2rad(preds)
                mean_angle = np.rad2deg(np.arctan2(np.mean(np.sin(rad)),
                                                    np.mean(np.cos(rad)))) % 360
                mean_pred[cidx] = mean_angle

            pred_hues_dict[sub][roi] = mean_pred

            # Build 8×8 RDM from predicted hues
            rdm = np.zeros((N_COLORS, N_COLORS))
            for i in range(N_COLORS):
                for j in range(N_COLORS):
                    if not np.isnan(mean_pred[i]) and not np.isnan(mean_pred[j]):
                        rdm[i, j] = circular_abs_distance(mean_pred[i], mean_pred[j])
            rdms[sub][roi] = rdm

    return rdms, pred_hues_dict


def compute_ideal_rdm():
    """Compute ideal RDM from true hue angles."""
    rdm = np.zeros((N_COLORS, N_COLORS))
    for i in range(N_COLORS):
        for j in range(N_COLORS):
            rdm[i, j] = circular_abs_distance(HUE_ANGLES[i], HUE_ANGLES[j])
    return rdm


def extract_pairs(rdm):
    """Extract 28 pairwise values from upper triangle."""
    return np.array([rdm[i, j] for i, j in PAIR_INDICES])


def pair_label(i, j):
    """Get pair label."""
    return f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}"


def crawford_howell(cvd_value, hc_values):
    """Crawford & Howell (1998) modified t-test."""
    n = len(hc_values)
    hc_mean = np.mean(hc_values)
    hc_std = np.std(hc_values, ddof=1)
    if hc_std == 0:
        return np.nan, np.nan
    t = (cvd_value - hc_mean) / (hc_std * np.sqrt((n + 1) / n))
    p = 2 * stats.t.sf(np.abs(t), df=n - 1)
    return t, p


def print_report(rdms, pred_hues_dict):
    """Print analysis report."""
    ideal_rdm = compute_ideal_rdm()
    ideal_pairs = extract_pairs(ideal_rdm)

    print("\n" + "=" * 110)
    print("EXP A4: 28-PAIR PAIRWISE RESIDUAL ANALYSIS")
    print("=" * 110)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        print(f"\n{'─' * 110}")
        print(f"  {name}")
        print(f"{'─' * 110}")

        # 1. Predicted hues summary
        print(f"\n  Mean predicted hues (°):")
        hdr = f"  {'Subject':>10} |"
        for cn in COLOR_NAMES:
            hdr += f" {cn:>7}"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))

        print(f"  {'TRUE':>10} |", end='')
        for h in HUE_ANGLES:
            print(f" {h:>7.0f}", end='')
        print()

        for sub in HC_SUBJECTS[:3] + ['...'] + CVD_SUBJECTS:
            if sub == '...':
                print(f"  {'...':>10} |")
                continue
            if sub not in pred_hues_dict or roi not in pred_hues_dict[sub]:
                continue
            ph = pred_hues_dict[sub][roi]
            group = 'HC' if sub in HC_SUBJECTS else CVD_TYPES.get(sub, 'CVD')
            print(f"  {'sub-'+sub:>10} |", end='')
            for h in ph:
                print(f" {h:>7.1f}", end='')
            print(f"  ({group})")

        # 2. Pairwise distance differences
        hc_pair_arr = []
        for sub in HC_SUBJECTS:
            if sub in rdms and roi in rdms[sub]:
                hc_pair_arr.append(extract_pairs(rdms[sub][roi]))
        if not hc_pair_arr:
            continue
        hc_pair_arr = np.array(hc_pair_arr)
        hc_pair_mean = np.mean(hc_pair_arr, axis=0)

        print(f"\n  Top-5 pairs with largest HC-CVD difference:")
        for sub in CVD_SUBJECTS:
            if sub not in rdms or roi not in rdms[sub]:
                continue
            cvd_pairs = extract_pairs(rdms[sub][roi])
            diff = hc_pair_mean - cvd_pairs  # positive = HC > CVD (CVD compressed)

            sorted_idx = np.argsort(np.abs(diff))[::-1]
            cvd_type = CVD_TYPES.get(sub, '?')
            print(f"    sub-{sub} ({cvd_type}):")
            for rank, idx in enumerate(sorted_idx[:5]):
                i, j = PAIR_INDICES[idx]
                pl = pair_label(i, j)
                d = diff[idx]
                direction = "HC>CVD" if d > 0 else "CVD>HC"
                print(f"      {rank+1}. {pl:>18}: diff={d:>+7.1f}° ({direction})")


def plot_heatmaps(rdms, output_dir):
    """Plot 8×8 pairwise distance heatmaps for HC mean vs each CVD."""
    ideal_rdm = compute_ideal_rdm()

    for roi in ROIS:
        name = ROI_DISPLAY[roi]

        # Compute HC mean RDM
        hc_rdm_list = []
        for sub in HC_SUBJECTS:
            if sub in rdms and roi in rdms[sub]:
                hc_rdm_list.append(rdms[sub][roi])
        if not hc_rdm_list:
            continue
        hc_mean_rdm = np.mean(hc_rdm_list, axis=0)

        # Plot: ideal, HC mean, and 3 CVD subjects
        ncols = 2 + len(CVD_SUBJECTS)
        fig, axes = plt.subplots(1, ncols, figsize=(4 * ncols, 4))

        # Ideal
        im = axes[0].imshow(ideal_rdm, cmap='viridis', vmin=0, vmax=180)
        axes[0].set_title('Ideal', fontweight='bold')
        axes[0].set_xticks(range(N_COLORS))
        axes[0].set_xticklabels(COLOR_NAMES, rotation=90, fontsize=7)
        axes[0].set_yticks(range(N_COLORS))
        axes[0].set_yticklabels(COLOR_NAMES, fontsize=7)

        # HC mean
        axes[1].imshow(hc_mean_rdm, cmap='viridis', vmin=0, vmax=180)
        axes[1].set_title('HC mean', fontweight='bold')
        axes[1].set_xticks(range(N_COLORS))
        axes[1].set_xticklabels(COLOR_NAMES, rotation=90, fontsize=7)
        axes[1].set_yticks(range(N_COLORS))
        axes[1].set_yticklabels(COLOR_NAMES, fontsize=7)

        # CVD subjects
        for j, sub in enumerate(CVD_SUBJECTS):
            if sub not in rdms or roi not in rdms[sub]:
                continue
            ax = axes[2 + j]
            ax.imshow(rdms[sub][roi], cmap='viridis', vmin=0, vmax=180)
            cvd_type = CVD_TYPES.get(sub, '?')
            ax.set_title(f'sub-{sub} ({cvd_type})', fontweight='bold')
            ax.set_xticks(range(N_COLORS))
            ax.set_xticklabels(COLOR_NAMES, rotation=90, fontsize=7)
            ax.set_yticks(range(N_COLORS))
            ax.set_yticklabels(COLOR_NAMES, fontsize=7)

        fig.colorbar(im, ax=axes, shrink=0.6, label='Angular distance (°)')
        plt.suptitle(f'{name}: Predicted Pairwise Distances (LOCO FE-6 ridge_gcv)',
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / f'rdm_heatmap_{roi}.png', dpi=150, bbox_inches='tight')
        plt.close()


def plot_difference_heatmaps(rdms, output_dir):
    """Plot HC-CVD difference heatmaps with axis annotations."""
    for roi in ROIS:
        name = ROI_DISPLAY[roi]

        hc_rdm_list = []
        for sub in HC_SUBJECTS:
            if sub in rdms and roi in rdms[sub]:
                hc_rdm_list.append(rdms[sub][roi])
        if not hc_rdm_list:
            continue
        hc_mean_rdm = np.mean(hc_rdm_list, axis=0)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        for j, sub in enumerate(CVD_SUBJECTS):
            if sub not in rdms or roi not in rdms[sub]:
                continue
            ax = axes[j]
            diff = hc_mean_rdm - rdms[sub][roi]  # positive = HC larger (CVD compressed)

            vmax = max(abs(np.nanmin(diff)), abs(np.nanmax(diff)), 1)
            norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
            im = ax.imshow(diff, cmap='RdBu_r', norm=norm)

            # Annotate key pairs
            for i_pair, j_pair in LM_PAIRS:
                ax.plot(j_pair, i_pair, 's', color='lime', markersize=8, markerfacecolor='none',
                        markeredgewidth=2)
            for i_pair, j_pair in S_PAIRS:
                ax.plot(j_pair, i_pair, 'o', color='cyan', markersize=8, markerfacecolor='none',
                        markeredgewidth=2)

            cvd_type = CVD_TYPES.get(sub, '?')
            ax.set_title(f'sub-{sub} ({cvd_type})', fontweight='bold')
            ax.set_xticks(range(N_COLORS))
            ax.set_xticklabels(COLOR_NAMES, rotation=90, fontsize=8)
            ax.set_yticks(range(N_COLORS))
            ax.set_yticklabels(COLOR_NAMES, fontsize=8)
            fig.colorbar(im, ax=ax, shrink=0.7)

        plt.suptitle(f'{name}: HC−CVD Pairwise Distance Difference\n'
                     f'Red=HC>CVD (CVD compressed), Blue=CVD>HC\n'
                     f'□=L-M pairs, ○=S-axis pairs',
                     fontsize=11, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / f'diff_heatmap_{roi}.png', dpi=150, bbox_inches='tight')
        plt.close()


def plot_pair_barplot(rdms, output_dir):
    """28-pair bar plot for hV4 showing HC-CVD differences."""
    roi = 'V4'
    name = 'hV4'

    hc_pair_arr = []
    for sub in HC_SUBJECTS:
        if sub in rdms and roi in rdms[sub]:
            hc_pair_arr.append(extract_pairs(rdms[sub][roi]))
    if not hc_pair_arr:
        return
    hc_pair_arr = np.array(hc_pair_arr)
    hc_pair_mean = np.mean(hc_pair_arr, axis=0)

    fig, axes = plt.subplots(3, 1, figsize=(18, 12), sharex=True)

    pair_labels = [pair_label(i, j) for i, j in PAIR_INDICES]
    x = np.arange(N_PAIRS)

    for ax_i, sub in enumerate(CVD_SUBJECTS):
        ax = axes[ax_i]
        if sub not in rdms or roi not in rdms[sub]:
            continue
        cvd_pairs = extract_pairs(rdms[sub][roi])
        diff = hc_pair_mean - cvd_pairs

        colors = []
        for idx, (i, j) in enumerate(PAIR_INDICES):
            if (i, j) in LM_PAIRS or (j, i) in LM_PAIRS:
                colors.append('#2ecc71')  # green for L-M
            elif (i, j) in S_PAIRS or (j, i) in S_PAIRS:
                colors.append('#3498db')  # blue for S-axis
            elif (i, j) in CROSS_PAIRS or (j, i) in CROSS_PAIRS:
                colors.append('#9b59b6')  # purple for cross
            else:
                colors.append('#95a5a6')  # gray for other

        ax.bar(x, diff, color=colors, alpha=0.8, edgecolor='black', linewidth=0.3)
        ax.axhline(0, color='black', linewidth=0.5)
        cvd_type = CVD_TYPES.get(sub, '?')
        ax.set_ylabel('HC − CVD distance (°)')
        ax.set_title(f'sub-{sub} ({cvd_type})', fontweight='bold')

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(pair_labels, rotation=90, fontsize=7)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', label='L-M pairs'),
        Patch(facecolor='#3498db', label='S-axis pairs'),
        Patch(facecolor='#9b59b6', label='Cross-axis pairs'),
        Patch(facecolor='#95a5a6', label='Other')
    ]
    axes[0].legend(handles=legend_elements, loc='upper right', fontsize=8)

    plt.suptitle(f'{name}: 28-Pair HC−CVD Distance Difference\n'
                 f'Positive = CVD compression, Negative = CVD expansion',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'pair_barplot_hv4.png', dpi=150, bbox_inches='tight')
    plt.close()


def save_results(rdms, pred_hues_dict, output_dir):
    """Save results as JSON."""
    ideal_rdm = compute_ideal_rdm()
    ideal_pairs = extract_pairs(ideal_rdm)

    out = {'encoder': ENCODER, 'n_channels': 6,
           'pair_labels': [pair_label(i, j) for i, j in PAIR_INDICES],
           'ideal_pairs': ideal_pairs.tolist()}

    for roi in ROIS:
        roi_data = {}

        # HC mean pairs
        hc_pair_arr = []
        for sub in HC_SUBJECTS:
            if sub in rdms and roi in rdms[sub]:
                hc_pair_arr.append(extract_pairs(rdms[sub][roi]))
        if not hc_pair_arr:
            continue
        hc_pair_arr = np.array(hc_pair_arr)
        roi_data['hc_mean_pairs'] = np.mean(hc_pair_arr, axis=0).tolist()
        roi_data['hc_std_pairs'] = np.std(hc_pair_arr, axis=0, ddof=1).tolist()

        # CVD pairs + Crawford-Howell
        roi_data['cvd'] = {}
        for sub in CVD_SUBJECTS:
            if sub not in rdms or roi not in rdms[sub]:
                continue
            cvd_pairs = extract_pairs(rdms[sub][roi])
            diff = np.mean(hc_pair_arr, axis=0) - cvd_pairs

            ch_results = []
            for p_idx in range(N_PAIRS):
                t, p = crawford_howell(cvd_pairs[p_idx], hc_pair_arr[:, p_idx])
                ch_results.append({'t': float(t), 'p': float(p)})

            roi_data['cvd'][sub] = {
                'pairs': cvd_pairs.tolist(),
                'diff_from_hc': diff.tolist(),
                'crawford_howell': ch_results,
                'type': CVD_TYPES.get(sub, 'unknown')
            }

        # Predicted hues
        roi_data['predicted_hues'] = {}
        for sub in ALL_SUBJECTS:
            if sub in pred_hues_dict and roi in pred_hues_dict[sub]:
                roi_data['predicted_hues'][sub] = pred_hues_dict[sub][roi].tolist()

        out[roi] = roi_data

    with open(output_dir / 'pairwise_residual_results.json', 'w') as f:
        json.dump(out, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Exp A4: 28-Pair Pairwise Residual')
    parser.add_argument('--validation_dir', type=str, default='results/validation')
    parser.add_argument('--output_dir', type=str, default='results/pairwise_residual')
    args = parser.parse_args()

    validation_dir = Path(args.validation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading validation LOCO results...")
    results = load_validation_loco(validation_dir)
    print(f"  Loaded {len(results)} subjects")

    print("Computing predicted RDMs...")
    rdms, pred_hues_dict = compute_predicted_rdms(results)

    print_report(rdms, pred_hues_dict)

    print("\nGenerating plots...")
    plot_heatmaps(rdms, output_dir)
    plot_difference_heatmaps(rdms, output_dir)
    plot_pair_barplot(rdms, output_dir)

    print("Saving results...")
    save_results(rdms, pred_hues_dict, output_dir)

    print(f"\nDone. Results saved to {output_dir}/")


if __name__ == '__main__':
    main()
