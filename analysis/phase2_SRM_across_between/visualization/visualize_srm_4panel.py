#!/usr/bin/env python3
"""
Comprehensive 4-panel SRM figure showing:
  Panel A: Group-level HC-CVD disparity comparison (violin plot)
  Panel B: Individual CVD profiles (Crawford & Howell heatmap)
  Panel C: Convergent validity (SRM vs. Crossnobis scatter plots, 2×2 grid)
  Panel D: 3-way robustness summary (B2 temporal stability, B3 bootstrap, A4/A5 convergent validity)

Shows complete SRM analysis storyline: Results (A/B) + Validity & Robustness Evidence (C/D)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from pathlib import Path
import json
from scipy.stats import spearmanr

# Configuration
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = BASE_DIR / 'analysis' / 'phase2_SRM_across_between' / 'results' / 'loo_consistent' / '20260218_163819'
COLOR_PAIR_DIR = BASE_DIR / 'analysis' / 'phase2_SRM_across_between' / 'results' / 'color_pair_analysis'
VALIDATION_DIR = BASE_DIR / 'analysis'
OUTPUT_DIR = BASE_DIR / 'analysis' / 'phase2_SRM_across_between' / 'visualization'
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ROI configuration
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROIS_DISPLAY = ['V1', 'V2', 'V3', 'V4']  # For display
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 3}  # SRM k-values (7-fold LOSO, mean rank aggregation)

CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
CVD_TYPES = {'sub-08': 'Deutan', 'sub-09': 'Protan', 'sub-10': 'Deutan'}
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS


def create_panel_A(loo_results, ax):
    """
    Panel A: Group-level HC-CVD disparity comparison (violin plot)

    Shows HC LOO vs CVD LOO for V1 and V2 with significance markers
    """
    data = []
    labels = []
    positions = []
    pos = 0

    # Extract data for V1 and V2 (trending significance)
    for roi_idx, roi in enumerate(['V1', 'V2']):
        roi_data = loo_results[roi]

        # HC disparities (7 subjects)
        hc_disp = list(roi_data['hc_loo_disparities'].values())

        # CVD disparities (3 subjects)
        cvd_disp = [roi_data['individual_cvd'][cvd_id]['cvd_score']
                    for cvd_id in CVD_SUBJECTS]

        data.extend([hc_disp, cvd_disp])
        labels.extend([f'{ROIS_DISPLAY[roi_idx]}\nHC (n=7)',
                       f'{ROIS_DISPLAY[roi_idx]}\nCVD (n=3)'])
        positions.extend([pos, pos + 1])

        pos += 3  # Gap between ROIs

    # Create violin plot
    parts = ax.violinplot(data, positions=positions,
                          showmeans=True, showextrema=True, widths=0.8)

    # Color violins
    for i, pc in enumerate(parts['bodies']):
        color = 'steelblue' if i % 2 == 0 else '#FF6B6B'
        pc.set_facecolor(color)
        pc.set_alpha(0.6)
        pc.set_edgecolor('black')
        pc.set_linewidth(1.5)

    # Customize violin parts
    parts['cmeans'].set_edgecolor('black')
    parts['cmeans'].set_linewidth(2)
    parts['cbars'].set_edgecolor('black')
    parts['cbars'].set_linewidth(1.5)
    parts['cmaxes'].set_edgecolor('black')
    parts['cmaxes'].set_linewidth(1.5)
    parts['cmins'].set_edgecolor('black')
    parts['cmins'].set_linewidth(1.5)

    # Add individual points with jitter
    for i, d in enumerate(data):
        x = np.random.normal(positions[i], 0.04, size=len(d))
        color = 'steelblue' if i % 2 == 0 else '#FF6B6B'
        ax.scatter(x, d, alpha=0.7, s=60, c=color,
                   edgecolor='black', linewidth=1.2, zorder=3)

    # Add significance markers
    sig_info = [
        {'roi_idx': 0, 'p': 0.062, 'marker': '†'},  # V1
        {'roi_idx': 1, 'p': 0.075, 'marker': '†'},  # V2
    ]

    for info in sig_info:
        roi_idx = info['roi_idx']
        hc_pos = roi_idx * 3
        cvd_pos = roi_idx * 3 + 1

        # Get y position
        y_hc = max(data[roi_idx * 2])
        y_cvd = max(data[roi_idx * 2 + 1])
        y_pos = max(y_hc, y_cvd) * 1.05

        # Draw bracket
        ax.plot([hc_pos, cvd_pos], [y_pos, y_pos], 'k-', linewidth=2)
        ax.plot([hc_pos, hc_pos], [y_pos - 0.01, y_pos], 'k-', linewidth=2)
        ax.plot([cvd_pos, cvd_pos], [y_pos - 0.01, y_pos], 'k-', linewidth=2)

        # Add marker
        ax.text((hc_pos + cvd_pos) / 2, y_pos + 0.02, info['marker'],
                ha='center', va='bottom', fontsize=24, fontweight='bold')

        # Add p-value
        ax.text((hc_pos + cvd_pos) / 2, y_pos + 0.08, f"p={info['p']:.3f}",
                ha='center', va='bottom', fontsize=9, style='italic')

    # Formatting
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=10, fontweight='bold')
    ax.set_ylabel('Procrustes Disparity', fontsize=13, fontweight='bold')
    ax.set_title('A. Group-Level HC-CVD Comparison',
                 fontsize=15, fontweight='bold', pad=12)
    ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(axis='y', alpha=0.3, linestyle=':')

    # Set y-limits
    ax.set_ylim(-0.05, max([max(d) for d in data]) * 1.25)

    # Add legend
    legend_text = "† p < 0.10 (trending)\n* p < 0.05\n** p < 0.01"
    ax.text(0.98, 0.02, legend_text, transform=ax.transAxes,
            fontsize=10, va='bottom', ha='right', family='monospace',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='white',
                     alpha=0.95, edgecolor='black', linewidth=1.5))


def create_panel_B(loo_results, ax):
    """
    Panel B: Individual CVD profiles (Crawford & Howell heatmap)

    Shows t-statistics and p-values per CVD subject × ROI
    """
    # Extract t-statistics and p-values
    t_matrix = np.zeros((3, 4))
    p_matrix = np.zeros((3, 4))

    for i, cvd_id in enumerate(CVD_SUBJECTS):
        for j, roi in enumerate(ROIS):
            cvd_data = loo_results[roi]['individual_cvd'][cvd_id]
            t_matrix[i, j] = cvd_data['t_stat']
            p_matrix[i, j] = cvd_data['p_value']

    # Create color array based on p-values
    colors = np.ones((3, 4, 4))  # RGBA, start with white
    for i in range(3):
        for j in range(4):
            p = p_matrix[i, j]
            if p < 0.01:
                colors[i, j] = [0.7, 0, 0, 1]  # Dark red
            elif p < 0.05:
                colors[i, j] = [1, 0.2, 0.2, 1]  # Red
            elif p < 0.10:
                colors[i, j] = [1, 0.55, 0, 1]  # Orange
            else:
                colors[i, j] = [0.95, 0.95, 0.95, 1]  # Light gray

    # Display image
    im = ax.imshow(colors, aspect='auto', interpolation='nearest')

    # Add t-statistic values and p-values
    for i in range(3):
        for j in range(4):
            t_val = t_matrix[i, j]
            p_val = p_matrix[i, j]

            # Determine significance marker
            if p_val < 0.01:
                sig_marker = '**'
            elif p_val < 0.05:
                sig_marker = '*'
            elif p_val < 0.10:
                sig_marker = '†'
            else:
                sig_marker = ''

            # Format text
            text = f't={t_val:.1f}{sig_marker}\np={p_val:.3f}'

            # Text color (white for dark backgrounds)
            text_color = 'white' if p_val < 0.05 else 'black'

            ax.text(j, i, text, ha='center', va='center',
                   fontsize=10, fontweight='bold', color=text_color,
                   linespacing=1.2)

    # Formatting
    ax.set_xticks(range(4))
    ax.set_yticks(range(3))
    ax.set_xticklabels(ROIS_DISPLAY, fontsize=12, fontweight='bold')
    ax.set_yticklabels([f'{cvd_id}\n({CVD_TYPES[cvd_id]})'
                        for cvd_id in CVD_SUBJECTS],
                       fontsize=11)
    ax.set_title('B. Individual CVD Tests (Crawford & Howell)',
                 fontsize=15, fontweight='bold', pad=12)

    # Add border
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(2)



def create_panel_C(loo_results, validation_data, ax):
    """
    Panel C: Convergent Validity Scatter Plots (2×3 grid)

    Shows SRM disparity vs. 3 independent alignment methods for V1 and V2
    Demonstrates methodological robustness across different alignment approaches
    """
    # Create 2×3 subplots within ax
    ax.axis('off')

    # Create GridSpec for 2×3 layout (bottom_margin for legend/subtitle clearance)
    from matplotlib.gridspec import GridSpecFromSubplotSpec
    gs_inner = GridSpecFromSubplotSpec(2, 3, subplot_spec=ax.get_subplotspec(),
                                       hspace=0.45, wspace=0.35)

    # Title + subtitle with k-value info
    ax.text(0.5, 1.19, 'C. Convergent Validity: SRM vs. Alternative Alignment Methods',
            ha='center', va='top', fontsize=15, fontweight='bold',
            transform=ax.transAxes)
    ax.text(0.5, 1.13, 'PCA/PCA-CCA use identical k to SRM (V1/V2=4, V3/hV4=3)',
            ha='center', va='top', fontsize=9, style='italic', color='#555555',
            transform=ax.transAxes)

    # Extract validation data
    crossnobis_data = validation_data['crossnobis']
    pca_cca_data = validation_data['pca_cca']

    # Method names and data sources
    methods = ['Crossnobis\n(SRM-independent)', 'PCA-only\n(k matched to SRM)', 'PCA-CCA\n(k matched to SRM)']

    # Plot only V1 and V2
    for roi_idx, roi in enumerate(['V1', 'V2']):
        for method_idx, method_name in enumerate(methods):
            sub_ax = plt.subplot(gs_inner[roi_idx, method_idx])

            # Extract SRM disparity and alternative metric for all subjects
            srm_disparities = []
            alt_distances = []
            colors = []
            markers = []

            # Get alternative distance data based on method
            if method_idx == 0:  # Crossnobis
                alt_data_dict = crossnobis_data[roi]['distance_from_hc_mean']
            else:  # PCA-only or PCA-CCA
                # Use pre-computed subject_mean_dist_to_hc from PCA-CCA data
                method_key = 'pca_only' if method_idx == 1 else 'pca_cca'
                alt_data_dict = pca_cca_data[roi][method_key]

            # HC subjects
            for subj in HC_SUBJECTS:
                srm_disp = loo_results[roi]['hc_loo_disparities'][subj]
                alt_dist = alt_data_dict[subj]
                srm_disparities.append(srm_disp)
                alt_distances.append(alt_dist)
                colors.append('steelblue')
                markers.append('o')

            # CVD subjects
            for subj in CVD_SUBJECTS:
                srm_disp = loo_results[roi]['individual_cvd'][subj]['cvd_score']
                alt_dist = alt_data_dict[subj]
                srm_disparities.append(srm_disp)
                alt_distances.append(alt_dist)
                colors.append('#FF6B6B')
                markers.append('^')

            # Scatter plot
            for i, (x, y, c, m) in enumerate(zip(srm_disparities, alt_distances, colors, markers)):
                sub_ax.scatter(x, y, s=80, c=c, marker=m,
                              edgecolor='black', linewidth=1.5, zorder=3, alpha=0.8)

            # Regression line
            z = np.polyfit(srm_disparities, alt_distances, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(srm_disparities), max(srm_disparities), 100)
            sub_ax.plot(x_line, p(x_line), 'k--', linewidth=2, alpha=0.6, zorder=2)

            # Compute correlation
            r, p_val = spearmanr(srm_disparities, alt_distances)

            # Formatting
            sub_ax.set_xlabel('SRM Disparity', fontsize=9, fontweight='bold')
            roi_name = ['V1', 'V2'][roi_idx]
            k_val = K_VALUES[roi_name]
            if method_idx == 0:
                sub_ax.set_ylabel(f'{ROIS_DISPLAY[roi_idx]} (k={k_val})\nDistance', fontsize=9, fontweight='bold')
            else:
                sub_ax.set_ylabel('Distance', fontsize=9, fontweight='bold')

            # Column title only in top row
            if roi_idx == 0:
                sub_ax.set_title(method_name, fontsize=11, fontweight='bold', pad=8)

            sub_ax.grid(alpha=0.3, linestyle=':')

            # Add correlation annotation
            sig_marker = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else ''))
            sub_ax.text(0.05, 0.95, f'r={r:.3f}{sig_marker}\np={p_val:.3f}',
                       transform=sub_ax.transAxes, fontsize=8,
                       va='top', ha='left', family='monospace',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                alpha=0.9, edgecolor='gray', linewidth=1))




def create_panel_D(validation_data, ax):
    """
    Panel D: Temporal Stability (B2 Split-Half)

    Shows split-half reliability for all CVD subjects across all ROIs
    """
    ax.axis('off')

    # Title
    ax.text(0.5, 1.19, 'D. Temporal Stability (B2 Split-Half Correlation)',
            ha='center', va='top', fontsize=15, fontweight='bold',
            transform=ax.transAxes)

    # Create single subplot for heatmap
    from matplotlib.gridspec import GridSpecFromSubplotSpec
    gs_inner = GridSpecFromSubplotSpec(1, 1, subplot_spec=ax.get_subplotspec(),
                                       hspace=0.2, wspace=0.2)

    sub_ax = plt.subplot(gs_inner[0, 0])

    b2_data = validation_data['b2_b3']
    split_half_matrix = np.zeros((3, 4))  # 3 CVD × 4 ROIs
    p_values = np.zeros((3, 4))

    for i, cvd_id in enumerate(CVD_SUBJECTS):
        for j, roi in enumerate(ROIS):
            # B2/B3 data uses same ROI names as ROIS list
            corr_data = b2_data[roi]['B2_split_half']['first_last']['per_subject_correlation'][cvd_id]
            split_half_matrix[i, j] = corr_data['spearman_r']
            p_values[i, j] = corr_data['spearman_p']

    # Create heatmap
    im = sub_ax.imshow(split_half_matrix, cmap='Greens', aspect='auto',
                        vmin=0, vmax=1, interpolation='nearest')

    # Add text annotations
    for i in range(3):
        for j in range(4):
            r_val = split_half_matrix[i, j]
            p_val = p_values[i, j]
            sig_marker = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else ''))

            text_color = 'white' if r_val > 0.5 else 'black'
            sub_ax.text(j, i, f'{r_val:.2f}{sig_marker}',
                        ha='center', va='center', fontsize=14,
                        fontweight='bold', color=text_color)

    # Formatting
    sub_ax.set_xticks(range(4))
    sub_ax.set_yticks(range(3))
    sub_ax.set_xticklabels(ROIS_DISPLAY, fontsize=13, fontweight='bold')
    sub_ax.set_yticklabels([f'{cvd_id} ({CVD_TYPES[cvd_id]})'
                             for cvd_id in CVD_SUBJECTS], fontsize=12, fontweight='bold')

    # Add colorbar
    cbar = plt.colorbar(im, ax=sub_ax, fraction=0.046, pad=0.04)
    cbar.set_label('Spearman r (Split-Half)', fontsize=12, fontweight='bold')
    cbar.ax.tick_params(labelsize=11)

    for spine in sub_ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(2.5)

    # Add interpretation at bottom
    interpretation = ("Split-half reliability across 6 runs per ROI\n"
                     "Strong temporal stability in V1/V2/hV4 (r > 0.64), weaker in V3\n"
                     "→ RDM patterns are consistent across time, not random noise")

    ax.text(0.5, 0.08, interpretation, transform=ax.transAxes,
            fontsize=11, va='bottom', ha='center',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#E8F5E9',
                     alpha=0.95, edgecolor='#388E3C', linewidth=2.5),
            linespacing=1.5)


def load_validation_data():
    """Load all validation results for Panels C and D"""
    validation_dict = {}

    try:
        # Load crossnobis (A4) results
        crossnobis_path = VALIDATION_DIR / 'phase2_SRM_across_between' / 'validation' / 'results' / 'crossnobis_rdm' / 'crossnobis_results.json'
        print(f"  Loading crossnobis: {crossnobis_path}")
        with open(crossnobis_path, 'r') as f:
            crossnobis_full = json.load(f)
            validation_dict['crossnobis'] = crossnobis_full['results']
            validation_dict['crossnobis_pooled'] = crossnobis_full['convergent_validity']['pooled']

        # Load PCA-CCA (A5) results
        pca_cca_path = VALIDATION_DIR / 'phase2_SRM_across_between' / 'validation' / 'results' / 'pca_cca_replication' / 'pca_cca_results.json'
        print(f"  Loading PCA-CCA: {pca_cca_path}")
        with open(pca_cca_path, 'r') as f:
            pca_cca_full = json.load(f)
            # Extract subject_mean_dist_to_hc for both pca_only and pca_cca
            validation_dict['pca_cca'] = {}
            for roi in ROIS:
                validation_dict['pca_cca'][roi] = {
                    'pca_only': pca_cca_full['results'][roi]['pca_only']['subject_mean_dist_to_hc'],
                    'pca_cca': pca_cca_full['results'][roi]['pca_cca']['subject_mean_dist_to_hc']
                }

        # Load B2/B3 filter pre-validation results
        b2_b3_path = VALIDATION_DIR / 'future_phase2_filter_optimization' / 'pre_validation' / 'results' / 'filter_pre_validation_results.json'
        print(f"  Loading B2/B3: {b2_b3_path}")
        with open(b2_b3_path, 'r') as f:
            b2_b3_full = json.load(f)
            validation_dict['b2_b3'] = b2_b3_full['results']

        print("  ✓ Successfully loaded validation data")
        return validation_dict

    except Exception as e:
        print(f"  ✗ Error loading validation data: {e}")
        print("  Panels C and D will show error messages")
        return None


def main():
    """Main execution function"""

    print("=" * 80)
    print("Creating SRM 4-Panel Comprehensive Figure (With Validity/Robustness)")
    print("=" * 80)

    # Load SRM LOO-consistent results
    loo_file = SRM_DIR / 'loo_consistent_results.json'
    print(f"\nLoading SRM results: {loo_file}")

    with open(loo_file, 'r') as f:
        loo_data = json.load(f)

    loo_results = loo_data['results']

    # Load validation data for Panels C and D
    print(f"\nLoading validation data...")
    validation_data = load_validation_data()

    if validation_data is None:
        print("  ✗ Validation data loading failed. Creating figure with error messages in C/D.")

    # Create figure
    print("\nCreating 4-panel figure...")

    fig = plt.figure(figsize=(20, 14))
    gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.35,
                          left=0.08, right=0.92, top=0.92, bottom=0.08)

    ax_A = plt.subplot(gs[0, 0])
    ax_B = plt.subplot(gs[0, 1])
    ax_C = plt.subplot(gs[1, 0])
    ax_D = plt.subplot(gs[1, 1])

    # Create panels
    create_panel_A(loo_results, ax_A)
    create_panel_B(loo_results, ax_B)

    if validation_data:
        create_panel_C(loo_results, validation_data, ax_C)
        create_panel_D(validation_data, ax_D)
    else:
        # Show error message in panels C and D
        for ax, label in [(ax_C, 'C'), (ax_D, 'D')]:
            ax.axis('off')
            ax.text(0.5, 0.5, f'Panel {label}: Validation data not available\n(Check paths in load_validation_data())',
                   ha='center', va='center', fontsize=12, color='red',
                   transform=ax.transAxes,
                   bbox=dict(boxstyle='round,pad=1', facecolor='lightyellow',
                            edgecolor='red', linewidth=2))

    # Overall title
    fig.suptitle('SRM Analysis: HC-CVD Color Representation Differences\n' +
                 'Results (Panels A/B) + Validity & Robustness Evidence (Panels C/D)',
                 fontsize=17, fontweight='bold', y=0.98)

    # Save figure
    output_path = OUTPUT_DIR / 'srm_4panel_figure.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Figure saved: {output_path}")
    print("\n" + "=" * 80)
    print("✓ SRM 4-panel figure complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
