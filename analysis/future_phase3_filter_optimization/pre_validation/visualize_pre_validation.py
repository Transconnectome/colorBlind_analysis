#!/usr/bin/env python3
"""
Visualize Filter Pre-Validation Results

Generates publication-quality figures from filter_pre_validation_results.json:
  Fig 1: Per-pair z-score heatmaps (3 CVD × 4 ROIs) with bootstrap CIs
  Fig 2: Pair-level permutation p-values
  Fig 3: Split-half stability scatter plots
  Fig 4: Cross-subject consistency on color wheel

Usage:
  python visualize_pre_validation.py [--results PATH] [--output_dir PATH]
"""

import numpy as np
import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm

# ============================================================================
# CONFIG
# ============================================================================

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
N_COLORS = 8
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
CVD_TYPES = {'sub-08': 'Deutan', 'sub-09': 'Protan', 'sub-10': 'Deutan'}
ROIS_DISPLAY = ['V1', 'V2', 'V3', 'hV4']

# Color map for the 8 stimulus colors
STIMULUS_COLORS = {
    'red': '#FF0000', 'orange': '#FF8000', 'yellow': '#FFFF00', 'green': '#00FF00',
    'cyan': '#00FFFF', 'blue': '#0000FF', 'purple': '#8000FF', 'magenta': '#FF00FF',
}


def load_results(path):
    with open(path) as f:
        return json.load(f)


# ============================================================================
# FIGURE 1: Per-pair z-score heatmaps
# ============================================================================

def plot_zscore_heatmaps(results, output_dir):
    """3 CVD subjects × 4 ROIs heatmap of 28 pair z-scores with bootstrap CIs."""
    fig, axes = plt.subplots(3, 4, figsize=(20, 12))
    pair_labels = results['config']['pair_labels']
    n_pairs = len(pair_labels)

    for col, roi in enumerate(ROIS_DISPLAY):
        roi_data = results['results'][roi]
        b1 = roi_data['B1_permutation']
        b3 = roi_data['B3_bootstrap']

        for row, subj in enumerate(CVD_SUBJECTS):
            ax = axes[row, col]
            z_vals = np.array(b1['observed_individual_z'][subj])
            ci_lo = np.array(b3['per_subject'][subj]['ci_lower'])
            ci_hi = np.array(b3['per_subject'][subj]['ci_upper'])

            # Reshape to 8×8 matrix for visualization
            z_matrix = np.full((N_COLORS, N_COLORS), np.nan)
            pair_idx = 0
            for i in range(N_COLORS):
                for j in range(i + 1, N_COLORS):
                    z_matrix[i, j] = z_vals[pair_idx]
                    z_matrix[j, i] = z_vals[pair_idx]
                    pair_idx += 1

            # Plot heatmap
            vmax = max(abs(np.nanmin(z_matrix)), abs(np.nanmax(z_matrix)), 3.0)
            norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
            im = ax.imshow(z_matrix, cmap='RdBu_r', norm=norm, aspect='equal')

            # Mark significant pairs (CI excludes zero)
            pair_idx = 0
            for i in range(N_COLORS):
                for j in range(i + 1, N_COLORS):
                    if ci_lo[pair_idx] > 0 or ci_hi[pair_idx] < 0:
                        ax.plot(j, i, 'k*', markersize=6)
                        ax.plot(i, j, 'k*', markersize=6)
                    pair_idx += 1

            ax.set_xticks(range(N_COLORS))
            ax.set_yticks(range(N_COLORS))
            if row == 2:
                ax.set_xticklabels([c[:3] for c in COLOR_NAMES], rotation=45, ha='right', fontsize=8)
            else:
                ax.set_xticklabels([])
            if col == 0:
                ax.set_yticklabels([c[:3] for c in COLOR_NAMES], fontsize=8)
                ax.set_ylabel(f"{subj}\n({CVD_TYPES[subj]})", fontsize=10, fontweight='bold')
            else:
                ax.set_yticklabels([])

            if row == 0:
                ax.set_title(f"{roi} (k={roi_data['k']})", fontsize=12, fontweight='bold')

    # Colorbar
    fig.subplots_adjust(right=0.88)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    cb = fig.colorbar(im, cax=cbar_ax)
    cb.set_label('z-score (+ = over-separation, - = confusion)', fontsize=10)

    fig.suptitle('Per-Pair Z-Scores in HC-only SRM Space\n(* = bootstrap 95% CI excludes zero)',
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 0.88, 0.95])

    out_path = output_dir / 'fig1_zscore_heatmaps.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ============================================================================
# FIGURE 2: Permutation p-values per pair
# ============================================================================

def plot_permutation_pvalues(results, output_dir):
    """Bar plot of permutation p-values per pair per ROI."""
    fig, axes = plt.subplots(4, 1, figsize=(16, 16))
    pair_labels = results['config']['pair_labels']
    pair_steps = results['config']['pair_steps']
    n_pairs = len(pair_labels)

    # Color bars by hue step
    step_colors = {1: '#e74c3c', 2: '#f39c12', 3: '#27ae60', 4: '#2980b9'}

    for ax_i, roi in enumerate(ROIS_DISPLAY):
        ax = axes[ax_i]
        roi_data = results['results'][roi]
        p_vals = np.array(roi_data['B1_permutation']['p_two_sided'])
        mean_z = np.array(roi_data['B1_permutation']['observed_group_mean_z'])

        x = np.arange(n_pairs)
        colors = [step_colors.get(s, '#95a5a6') for s in pair_steps]

        # Transform p-values to -log10 for visualization
        neg_log_p = -np.log10(np.clip(p_vals, 1e-10, 1.0))

        # Sign the bars by direction of z-score
        signed_neg_log_p = neg_log_p * np.sign(mean_z)

        bars = ax.bar(x, signed_neg_log_p, color=colors, alpha=0.8, edgecolor='gray', linewidth=0.5)

        # Significance threshold
        thresh = -np.log10(0.05)
        ax.axhline(thresh, color='red', linestyle='--', linewidth=0.8, alpha=0.5, label='p=0.05')
        ax.axhline(-thresh, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(0, color='black', linewidth=0.5)

        ax.set_xticks(x)
        if ax_i == 3:
            ax.set_xticklabels([p.replace('-', '\n') for p in pair_labels],
                               fontsize=6, rotation=0, ha='center')
        else:
            ax.set_xticklabels([])
        ax.set_ylabel('-log10(p) × sign(z)', fontsize=9)
        ax.set_title(f"{roi} (k={roi_data['k']})", fontsize=11, fontweight='bold')
        ax.set_xlim(-0.5, n_pairs - 0.5)

        # Mark significant pairs
        for i in range(n_pairs):
            if p_vals[i] < 0.05:
                y_pos = signed_neg_log_p[i]
                ax.text(i, y_pos + np.sign(y_pos) * 0.1, '*', ha='center', fontsize=10,
                        fontweight='bold', color='red')

    # Legend for step colors
    legend_patches = [mpatches.Patch(color=step_colors[s], label=f'step={s}') for s in sorted(step_colors)]
    axes[0].legend(handles=legend_patches, loc='upper right', fontsize=8)

    fig.suptitle('B1: Pair-Level Permutation Test (Exhaustive, n=120)\n'
                 'Positive = CVD over-separation, Negative = CVD confusion',
                 fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out_path = output_dir / 'fig2_permutation_pvalues.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ============================================================================
# FIGURE 3: Split-half stability
# ============================================================================

def plot_split_half(results, output_dir):
    """Scatter plot: half1 z-scores vs half2 z-scores per CVD subject."""
    fig, axes = plt.subplots(3, 4, figsize=(16, 12))
    pair_steps = results['config']['pair_steps']
    step_colors = {1: '#e74c3c', 2: '#f39c12', 3: '#27ae60', 4: '#2980b9'}

    for col, roi in enumerate(ROIS_DISPLAY):
        roi_data = results['results'][roi]
        # Use first_last split
        split_data = roi_data['B2_split_half']['first_last']

        for row, subj in enumerate(CVD_SUBJECTS):
            ax = axes[row, col]
            z1 = np.array(split_data['half1_zscores'][subj])
            z2 = np.array(split_data['half2_zscores'][subj])
            colors = [step_colors.get(s, '#95a5a6') for s in pair_steps]

            ax.scatter(z1, z2, c=colors, s=30, alpha=0.7, edgecolors='gray', linewidth=0.5)

            # Identity line
            lims = [min(z1.min(), z2.min()) - 0.5, max(z1.max(), z2.max()) + 0.5]
            ax.plot(lims, lims, 'k--', linewidth=0.5, alpha=0.3)
            ax.axhline(0, color='gray', linewidth=0.3)
            ax.axvline(0, color='gray', linewidth=0.3)

            # Correlation
            corr_data = split_data['per_subject_correlation'][subj]
            r_val = corr_data['spearman_r']
            p_val = corr_data['spearman_p']
            r_str = f"r={r_val:.2f}" if r_val is not None else "r=N/A"
            p_str = f"p={p_val:.3f}" if p_val is not None else ""
            sig_str = "*" if p_val is not None and p_val < 0.05 else ""
            ax.text(0.05, 0.95, f"{r_str} {sig_str}\n{p_str}",
                    transform=ax.transAxes, fontsize=8, va='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            if row == 2:
                ax.set_xlabel('Half 1 z-score (runs 1-3)', fontsize=8)
            if col == 0:
                ax.set_ylabel(f"{subj}\nHalf 2 z-score (runs 4-6)", fontsize=9, fontweight='bold')
            if row == 0:
                ax.set_title(f"{roi}", fontsize=11, fontweight='bold')

    fig.suptitle('B2: Split-Half Stability of Per-Pair Z-Scores\n(each dot = one color pair)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out_path = output_dir / 'fig3_split_half_stability.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ============================================================================
# FIGURE 4: Bootstrap CIs for key pairs
# ============================================================================

def plot_bootstrap_cis(results, output_dir):
    """Forest plot of bootstrap CIs for adjacent pairs (step=1) per CVD subject."""
    pair_labels = results['config']['pair_labels']
    pair_steps = results['config']['pair_steps']
    adj_indices = [i for i, s in enumerate(pair_steps) if s == 1]
    adj_labels = [pair_labels[i] for i in adj_indices]
    n_adj = len(adj_indices)

    fig, axes = plt.subplots(1, 4, figsize=(20, 6), sharey=True)
    cvd_colors = {'sub-08': '#e74c3c', 'sub-09': '#2980b9', 'sub-10': '#27ae60'}

    for col, roi in enumerate(ROIS_DISPLAY):
        ax = axes[col]
        roi_data = results['results'][roi]
        b3 = roi_data['B3_bootstrap']
        b1 = roi_data['B1_permutation']

        for j, subj in enumerate(CVD_SUBJECTS):
            z_vals = np.array(b1['observed_individual_z'][subj])
            ci_lo = np.array(b3['per_subject'][subj]['ci_lower'])
            ci_hi = np.array(b3['per_subject'][subj]['ci_upper'])

            y_positions = np.arange(n_adj) * 3.5 + j * 1.0  # Offset per subject

            for i, pi in enumerate(adj_indices):
                y = y_positions[i]
                ax.plot([ci_lo[pi], ci_hi[pi]], [y, y], color=cvd_colors[subj],
                        linewidth=2, alpha=0.7)
                ax.plot(z_vals[pi], y, 'o', color=cvd_colors[subj], markersize=5)

                # Mark if CI excludes zero
                if ci_lo[pi] > 0 or ci_hi[pi] < 0:
                    ax.plot(z_vals[pi], y, 'o', color=cvd_colors[subj],
                            markersize=7, markeredgecolor='black', markeredgewidth=1.5)

        ax.axvline(0, color='gray', linewidth=1, linestyle='-')
        ax.set_yticks(np.arange(n_adj) * 3.5 + 1.0)
        ax.set_yticklabels(adj_labels, fontsize=9)
        ax.set_xlabel('z-score', fontsize=10)
        ax.set_title(f"{roi}", fontsize=11, fontweight='bold')
        ax.invert_yaxis()

    # Legend
    legend_patches = [mpatches.Patch(color=cvd_colors[s], label=f"{s} ({CVD_TYPES[s]})")
                      for s in CVD_SUBJECTS]
    axes[-1].legend(handles=legend_patches, loc='lower right', fontsize=8)

    fig.suptitle('B3: Bootstrap 95% CIs for Adjacent Pair Z-Scores\n'
                 '(bold circle = CI excludes zero)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.92])

    out_path = output_dir / 'fig4_bootstrap_cis.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ============================================================================
# SUMMARY TABLE
# ============================================================================

def print_summary_table(results):
    """Print concise summary to terminal."""
    print("\n" + "=" * 80)
    print("FILTER PRE-VALIDATION SUMMARY")
    print("=" * 80)

    for roi in ROIS_DISPLAY:
        roi_data = results['results'][roi]
        b1 = roi_data['B1_permutation']
        b2 = roi_data['B2_split_half']
        b3 = roi_data['B3_bootstrap']

        print(f"\n--- {roi} (k={roi_data['k']}) ---")

        # B1: Significant permutation pairs
        sig_raw = b1['significant_raw']
        if sig_raw:
            print(f"  B1 Permutation (p<0.05): {', '.join(sig_raw)}")
        else:
            print(f"  B1 Permutation: no pairs significant at p<0.05")

        # B2: Split-half stability
        for split_name, split_data in b2.items():
            print(f"  B2 {split_name}:")
            for subj in CVD_SUBJECTS:
                corr = split_data['per_subject_correlation'][subj]
                r = corr['spearman_r']
                p = corr['spearman_p']
                if r is not None:
                    sig = "*" if p < 0.05 else ""
                    print(f"    {subj}: r={r:.3f} (p={p:.3f}) {sig}")

        # B3: Bootstrap significant pairs per subject
        print(f"  B3 Bootstrap (CI excl. zero):")
        for subj in CVD_SUBJECTS:
            subj_data = b3['per_subject'][subj]
            n_sig = subj_data['n_significant']
            sig_pairs = subj_data['significant_pairs']
            adj_sig = [p for p in sig_pairs if p in [
                'red-orange', 'orange-yellow', 'yellow-green', 'green-cyan',
                'cyan-blue', 'blue-purple', 'purple-magenta', 'red-magenta'
            ]]
            print(f"    {subj}: {n_sig}/28 total, adj: {', '.join(adj_sig) if adj_sig else 'none'}")

    # Cross-subject consistency
    print(f"\n--- Cross-Subject Consistency ---")
    for roi in ROIS_DISPLAY:
        consistency = results['results'][roi]['cross_subject_consistency']
        n_def = len(consistency['all_3_deficit'])
        n_elev = len(consistency['all_3_elevation'])
        print(f"  {roi}: {n_def} all-3-deficit, {n_elev} all-3-elevation pairs")
        for entry in consistency['all_3_deficit']:
            print(f"    DEFICIT: {entry['pair']} (step={entry['step']}) "
                  f"z=[{entry['z_sub08']}, {entry['z_sub09']}, {entry['z_sub10']}]")
        for entry in consistency['all_3_elevation']:
            print(f"    ELEVATION: {entry['pair']} (step={entry['step']}) "
                  f"z=[{entry['z_sub08']}, {entry['z_sub09']}, {entry['z_sub10']}]")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Visualize Filter Pre-Validation Results')
    parser.add_argument('--results', type=str, default=None,
                        help='Path to results JSON')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory for figures')
    args = parser.parse_args()

    # Find results file
    if args.results:
        results_path = Path(args.results)
    else:
        results_path = Path(__file__).resolve().parent / "results" / "filter_pre_validation_results.json"

    if not results_path.exists():
        print(f"ERROR: Results file not found: {results_path}")
        print("Run filter_pre_validation.py first.")
        sys.exit(1)

    results = load_results(results_path)
    print(f"Loaded results from: {results_path}")
    print(f"  Timestamp: {results['config']['timestamp']}")
    print(f"  SRM backend: {results['config']['srm_backend']}")

    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = results_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Print summary
    print_summary_table(results)

    # Generate figures
    print(f"\nGenerating figures...")
    plot_zscore_heatmaps(results, output_dir)
    plot_permutation_pvalues(results, output_dir)
    plot_split_half(results, output_dir)
    plot_bootstrap_cis(results, output_dir)

    print(f"\nAll figures saved to: {output_dir}")


if __name__ == '__main__':
    import sys
    main()
