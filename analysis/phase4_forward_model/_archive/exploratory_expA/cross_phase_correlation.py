#!/usr/bin/env python3
"""
cross_phase_correlation.py — Exp A6: SRM ↔ FE Cross-Phase Correlation.

Correlates SRM crossnobis pairwise distances (Phase 2 pre-validation)
with FE LOCO predicted pairwise distances to verify convergence of
two independent analysis pipelines.

Key question: Do SRM and FE pipelines capture the same underlying structure?

Method:
  - SRM: 28 crossnobis pairwise distances per CVD subject per ROI
  - FE:  28 pairwise angular distances from LOCO pred_hues per subject per ROI
  - Spearman correlation between the two 28-element vectors

Input:
  - phase5_filter_optimization/pre_validation/results/crossnobis_pairs/
  - results/validation/sub-*_loco.json (FE LOCO pred_hues)
Output: results/cross_phase/

Note: SRM crossnobis data covers V1, V2, V3 only (not hV4).

Usage:
    conda activate srm
    python scripts/cross_phase_correlation.py \
        --crossnobis_path ../../phase5_filter_optimization/pre_validation/results/crossnobis_pairs/crossnobis_pair_analysis.json \
        --validation_dir results/validation \
        --output_dir results/cross_phase
"""

import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from itertools import combinations

# ── Constants ──────────────────────────────────────────────────────────
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS_SRM = ['V1', 'V2', 'V3']  # SRM crossnobis only covers these
ROIS_FE = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])
N_COLORS = 8
PAIR_INDICES = list(combinations(range(N_COLORS), 2))
N_PAIRS = 28

ENCODER = 'ridge_gcv'
CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'deutan'}


def circular_abs_distance(a, b):
    """Absolute circular distance."""
    d = np.abs(a - b) % 360
    return np.minimum(d, 360 - d)


def pair_label(i, j):
    return f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}"


def load_crossnobis(crossnobis_path):
    """Load SRM crossnobis pair analysis results.

    Returns:
        data: dict with structure:
            data[sub][roi] = {
                'hc_mean': array(28),
                'cvd_distances': array(28),
                'z_scores': array(28)
            }
    """
    with open(crossnobis_path) as f:
        raw = json.load(f)

    pair_labels = raw['config']['pair_labels']
    data = {}

    for sub_key in raw['by_subject_roi']:
        sub = sub_key.replace('sub-', '')
        data[sub] = {}
        for roi in raw['by_subject_roi'][sub_key]:
            entry = raw['by_subject_roi'][sub_key][roi]
            data[sub][roi] = {
                'hc_mean': np.array(entry['hc_mean']),
                'hc_std': np.array(entry['hc_std']),
                'cvd_distances': np.array(entry['cvd_distances']),
                'z_scores': np.array(entry['z_scores']),
                'p_values': np.array(entry['p_values'])
            }

    return data, pair_labels


def load_fe_loco(validation_dir):
    """Load FE LOCO predicted hues and compute pairwise distances.

    Returns:
        fe_pairs: dict[sub][roi] = array(28) of predicted pairwise angular distances
        fe_pred_hues: dict[sub][roi] = array(8) of mean predicted hues
    """
    fe_pairs = {}
    fe_pred_hues = {}

    for sub in ALL_SUBJECTS:
        path = Path(validation_dir) / f'sub-{sub}_loco.json'
        if not path.exists():
            continue

        with open(path) as f:
            data = json.load(f)

        fe_pairs[sub] = {}
        fe_pred_hues[sub] = {}

        for roi in ROIS_FE:
            if roi not in data or ENCODER not in data[roi]:
                continue

            folds = data[roi][ENCODER]['folds']
            mean_pred = np.full(N_COLORS, np.nan)

            for fold in folds:
                cidx = fold['test_color']
                preds = np.array(fold['pred_hues'])
                rad = np.deg2rad(preds)
                mean_angle = np.rad2deg(np.arctan2(np.mean(np.sin(rad)),
                                                    np.mean(np.cos(rad)))) % 360
                mean_pred[cidx] = mean_angle

            fe_pred_hues[sub][roi] = mean_pred

            # Compute 28 pairwise distances
            pairs = np.zeros(N_PAIRS)
            for idx, (i, j) in enumerate(PAIR_INDICES):
                if not np.isnan(mean_pred[i]) and not np.isnan(mean_pred[j]):
                    pairs[idx] = circular_abs_distance(mean_pred[i], mean_pred[j])
                else:
                    pairs[idx] = np.nan
            fe_pairs[sub][roi] = pairs

    return fe_pairs, fe_pred_hues


def compute_cross_correlations(srm_data, fe_pairs):
    """Compute Spearman correlations between SRM and FE pairwise distances.

    For each CVD subject × ROI:
      1. SRM vector: hc_mean - cvd_distances (28 values, HC-CVD difference)
      2. FE vector: hc_mean_fe - cvd_fe (28 values, HC-CVD predicted distance difference)
      3. Alternative: raw SRM cvd_distances vs raw FE cvd pairs
    """
    results = {}

    # Compute HC mean FE pairs per ROI
    hc_fe_mean = {}
    for roi in ROIS_SRM:
        hc_pairs = []
        for sub in HC_SUBJECTS:
            if sub in fe_pairs and roi in fe_pairs[sub]:
                hc_pairs.append(fe_pairs[sub][roi])
        if hc_pairs:
            hc_fe_mean[roi] = np.nanmean(hc_pairs, axis=0)

    for sub in CVD_SUBJECTS:
        results[sub] = {}
        for roi in ROIS_SRM:
            if sub not in srm_data or roi not in srm_data[sub]:
                continue
            if sub not in fe_pairs or roi not in fe_pairs[sub]:
                continue
            if roi not in hc_fe_mean:
                continue

            srm_entry = srm_data[sub][roi]

            # Method 1: Raw distances correlation
            # SRM: cvd crossnobis distances (absolute representation)
            # FE: cvd predicted angular distances
            srm_raw = srm_entry['cvd_distances']
            fe_raw = fe_pairs[sub][roi]
            valid = ~(np.isnan(srm_raw) | np.isnan(fe_raw))

            if valid.sum() < 5:
                continue

            r_raw, p_raw = stats.spearmanr(srm_raw[valid], fe_raw[valid])

            # Method 2: HC-CVD difference correlation
            # SRM: hc_mean - cvd_distances (deficit profile)
            # FE:  hc_mean_fe - cvd_fe (predicted deficit profile)
            srm_diff = srm_entry['hc_mean'] - srm_entry['cvd_distances']
            fe_diff = hc_fe_mean[roi] - fe_pairs[sub][roi]
            valid2 = ~(np.isnan(srm_diff) | np.isnan(fe_diff))

            if valid2.sum() >= 5:
                r_diff, p_diff = stats.spearmanr(srm_diff[valid2], fe_diff[valid2])
            else:
                r_diff, p_diff = np.nan, np.nan

            # Method 3: SRM z-scores vs FE difference
            srm_z = srm_entry['z_scores']
            valid3 = ~(np.isnan(srm_z) | np.isnan(fe_diff))
            if valid3.sum() >= 5:
                r_z, p_z = stats.spearmanr(srm_z[valid3], fe_diff[valid3])
            else:
                r_z, p_z = np.nan, np.nan

            results[sub][roi] = {
                'r_raw': float(r_raw), 'p_raw': float(p_raw),
                'r_diff': float(r_diff), 'p_diff': float(p_diff),
                'r_zscore': float(r_z), 'p_zscore': float(p_z),
                'n_valid_pairs': int(valid.sum()),
                'srm_raw': srm_raw.tolist(),
                'fe_raw': fe_raw.tolist(),
                'srm_diff': srm_diff.tolist(),
                'fe_diff': fe_diff.tolist()
            }

    return results


def print_report(correlations):
    """Print cross-phase correlation report."""
    print("\n" + "=" * 100)
    print("EXP A6: SRM ↔ FE CROSS-PHASE CORRELATION (28-Pair)")
    print("=" * 100)
    print("SRM: crossnobis pairwise distances (Phase 2 pre-validation)")
    print("FE:  LOCO predicted angular distances (ridge_gcv, FE-6)")
    print("ROIs: V1, V2, V3 only (SRM crossnobis covers these)")

    print(f"\n{'Subject':>10} | {'ROI':>4} | {'r_raw':>7} {'p':>7} | "
          f"{'r_diff':>7} {'p':>7} | {'r_z':>7} {'p':>7}")
    print("-" * 80)

    for sub in CVD_SUBJECTS:
        if sub not in correlations:
            continue
        for roi in ROIS_SRM:
            if roi not in correlations[sub]:
                continue
            c = correlations[sub][roi]
            cvd_type = CVD_TYPES.get(sub, '?')
            name = ROI_DISPLAY[roi]

            star_raw = '*' if c['p_raw'] < 0.05 else ('+' if c['p_raw'] < 0.10 else '')
            star_diff = '*' if c['p_diff'] < 0.05 else ('+' if c['p_diff'] < 0.10 else '')
            star_z = '*' if c['p_zscore'] < 0.05 else ('+' if c['p_zscore'] < 0.10 else '')

            print(f"{'sub-'+sub:>10} | {name:>4} | "
                  f"{c['r_raw']:>+.3f}{star_raw:1} {c['p_raw']:>.3f} | "
                  f"{c['r_diff']:>+.3f}{star_diff:1} {c['p_diff']:>.3f} | "
                  f"{c['r_zscore']:>+.3f}{star_z:1} {c['p_zscore']:>.3f}")

    # Summary
    print(f"\n{'─' * 80}")
    print("  r_raw  = Spearman(SRM_cvd_distances, FE_cvd_pred_distances)")
    print("  r_diff = Spearman(SRM_hc-cvd_diff, FE_hc-cvd_diff)")
    print("  r_z    = Spearman(SRM_z-scores, FE_hc-cvd_diff)")
    print("  * p<0.05, + p<0.10")


def plot_scatter(correlations, output_dir):
    """Scatter plots of SRM vs FE pairwise distances."""
    for sub in CVD_SUBJECTS:
        if sub not in correlations:
            continue

        fig, axes = plt.subplots(1, len(ROIS_SRM), figsize=(5 * len(ROIS_SRM), 5))
        if len(ROIS_SRM) == 1:
            axes = [axes]

        for ax_i, roi in enumerate(ROIS_SRM):
            ax = axes[ax_i]
            if roi not in correlations[sub]:
                continue

            c = correlations[sub][roi]
            srm = np.array(c['srm_diff'])
            fe = np.array(c['fe_diff'])
            valid = ~(np.isnan(srm) | np.isnan(fe))

            ax.scatter(srm[valid], fe[valid], c='steelblue', alpha=0.6, s=40,
                       edgecolors='black', linewidth=0.3)

            # Fit line
            if valid.sum() > 2:
                slope, intercept = np.polyfit(srm[valid], fe[valid], 1)
                x_fit = np.linspace(srm[valid].min(), srm[valid].max(), 100)
                ax.plot(x_fit, slope * x_fit + intercept, 'r--', alpha=0.5)

            # Annotate extreme pairs
            if valid.sum() > 0:
                distances = np.sqrt(srm[valid]**2 + fe[valid]**2)
                top3 = np.argsort(distances)[-3:]
                valid_indices = np.where(valid)[0]
                for t in top3:
                    idx = valid_indices[t]
                    i, j = PAIR_INDICES[idx]
                    ax.annotate(f'{COLOR_NAMES[i][:3]}-{COLOR_NAMES[j][:3]}',
                                (srm[idx], fe[idx]), fontsize=7, alpha=0.7)

            name = ROI_DISPLAY[roi]
            r_val = c['r_diff']
            p_val = c['p_diff']
            ax.set_title(f'{name}: r={r_val:+.3f}, p={p_val:.3f}', fontweight='bold')
            ax.set_xlabel('SRM deficit (HC−CVD crossnobis)')
            ax.set_ylabel('FE deficit (HC−CVD pred distance)')
            ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
            ax.axvline(0, color='gray', linewidth=0.5, linestyle='--')

        cvd_type = CVD_TYPES.get(sub, '?')
        plt.suptitle(f'sub-{sub} ({cvd_type}): SRM ↔ FE Cross-Phase Correlation\n'
                     f'28-pair HC-CVD deficit profile',
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / f'scatter_cross_phase_sub-{sub}.png',
                    dpi=150, bbox_inches='tight')
        plt.close()


def plot_summary_bar(correlations, output_dir):
    """Summary bar plot of correlations across subjects and ROIs."""
    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(ROIS_SRM))
    width = 0.25
    cvd_colors = {'08': '#e74c3c', '09': '#3498db', '10': '#2ecc71'}

    for j, sub in enumerate(CVD_SUBJECTS):
        if sub not in correlations:
            continue
        r_vals = []
        for roi in ROIS_SRM:
            if roi in correlations[sub]:
                r_vals.append(correlations[sub][roi]['r_diff'])
            else:
                r_vals.append(0)
        cvd_type = CVD_TYPES.get(sub, '?')
        ax.bar(x + (j - 1) * width, r_vals, width,
               label=f'sub-{sub} ({cvd_type})', color=cvd_colors[sub], alpha=0.8)

        # Add p-value stars
        for i, roi in enumerate(ROIS_SRM):
            if roi in correlations[sub]:
                p = correlations[sub][roi]['p_diff']
                if p < 0.05:
                    ax.text(x[i] + (j - 1) * width, r_vals[i] + 0.02, '*', ha='center', fontsize=12)
                elif p < 0.10:
                    ax.text(x[i] + (j - 1) * width, r_vals[i] + 0.02, '+', ha='center', fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels([ROI_DISPLAY[r] for r in ROIS_SRM], fontsize=12)
    ax.set_ylabel('Spearman r (HC-CVD deficit)')
    ax.set_title('Cross-Phase Correlation: SRM ↔ FE', fontweight='bold')
    ax.axhline(0, color='black', linewidth=0.5)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / 'summary_cross_phase.png', dpi=150, bbox_inches='tight')
    plt.close()


def save_results(correlations, output_dir):
    """Save cross-phase correlation results."""
    out = {
        'description': 'SRM crossnobis vs FE LOCO pairwise distance correlation',
        'srm_source': 'crossnobis_pair_analysis.json',
        'fe_encoder': ENCODER,
        'fe_basis': 'FE-6',
        'rois': ROIS_SRM,
        'pair_labels': [pair_label(i, j) for i, j in PAIR_INDICES],
        'results': {}
    }

    for sub in CVD_SUBJECTS:
        if sub in correlations:
            out['results'][sub] = correlations[sub]

    with open(output_dir / 'cross_phase_results.json', 'w') as f:
        json.dump(out, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Exp A6: Cross-Phase Correlation')
    parser.add_argument('--crossnobis_path', type=str,
                        default='../../phase5_filter_optimization/pre_validation/results/crossnobis_pairs/crossnobis_pair_analysis.json')
    parser.add_argument('--validation_dir', type=str, default='results/validation')
    parser.add_argument('--output_dir', type=str, default='results/cross_phase')
    args = parser.parse_args()

    crossnobis_path = Path(args.crossnobis_path)
    validation_dir = Path(args.validation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading SRM crossnobis pair data...")
    srm_data, srm_pair_labels = load_crossnobis(crossnobis_path)
    print(f"  Loaded {len(srm_data)} CVD subjects, ROIs: {ROIS_SRM}")

    print("Loading FE LOCO predicted hues...")
    fe_pairs, fe_pred_hues = load_fe_loco(validation_dir)
    print(f"  Loaded {len(fe_pairs)} subjects")

    print("Computing cross-phase correlations...")
    correlations = compute_cross_correlations(srm_data, fe_pairs)

    print_report(correlations)

    print("\nGenerating plots...")
    plot_scatter(correlations, output_dir)
    plot_summary_bar(correlations, output_dir)

    print("Saving results...")
    save_results(correlations, output_dir)

    print(f"\nDone. Results saved to {output_dir}/")


if __name__ == '__main__':
    main()
