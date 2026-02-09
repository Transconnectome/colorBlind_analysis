#!/usr/bin/env python3
"""
Analyze Procrustes Effects for C010 with Residuals - Validation Analysis

Analyzes decoding performance before and after Procrustes alignment
for the full_dataset_C010 directory.

Outputs:
  1. procrustes_effect_distributions.png (5-panel figure)
  2. procrustes_effect_by_roi.png (ROI comparison)
  3. procrustes_effect_hc_vs_cvd.png (Group comparison)
  4. c010_residuals_procrustes_analysis.json (Statistics)

Usage:
    python analyze_c010_procrustes_effects.py

Author: Adapted from analyze_procrustes_effects.py
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
import json
from scipy import stats
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import LeaveOneOut

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "full_dataset_C010_with_residuals"
OUTPUT_DIR = BASE_DIR / "validation_analysis_residuals"

# Subject groups
HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]   # sub-01 ~ sub-07
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]  # sub-08 ~ sub-10
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

# ROIs
ROIS = ['V1', 'V2', 'V3', 'V4']

# Colors
plt.style.use('seaborn-v0_8-whitegrid')

def compute_rdm(amplitudes):
    """
    Compute RDM from amplitudes using correlation distance

    Args:
        amplitudes: (n_conditions, n_voxels) array

    Returns:
        rdm: (n_conditions, n_conditions) distance matrix
    """
    from scipy.spatial.distance import pdist, squareform
    rdm = squareform(pdist(amplitudes, metric='correlation'))
    return rdm


def compute_rdm_reliability(rdms):
    """
    Compute RDM reliability using split-half correlation

    Args:
        rdms: list of RDMs, one per run

    Returns:
        reliability: Spearman correlation between split halves
    """
    n_runs = len(rdms)
    if n_runs < 2:
        return np.nan

    # Odd-even split
    odd_rdms = [rdms[i] for i in range(0, n_runs, 2)]
    even_rdms = [rdms[i] for i in range(1, n_runs, 2)]

    if len(odd_rdms) == 0 or len(even_rdms) == 0:
        return np.nan

    # Average within splits
    odd_avg = np.mean(odd_rdms, axis=0)
    even_avg = np.mean(even_rdms, axis=0)

    # Extract upper triangular
    mask = np.triu_indices_from(odd_avg, k=1)
    odd_vec = odd_avg[mask]
    even_vec = even_avg[mask]

    # Spearman correlation
    corr, _ = stats.spearmanr(odd_vec, even_vec)

    return corr


def loro_decoding(amplitudes, labels):
    """
    Leave-One-Run-Out cross-validated LDA decoding

    Args:
        amplitudes: (n_runs, n_conditions, n_voxels) array
        labels: (n_conditions,) array of color labels (0-7)

    Returns:
        accuracy: decoding accuracy (0-1)
    """
    n_runs, n_conditions, n_voxels = amplitudes.shape

    predictions = []
    true_labels = []

    # LORO cross-validation
    for test_run in range(n_runs):
        # Training data: all runs except test_run
        train_runs = [i for i in range(n_runs) if i != test_run]
        X_train = np.concatenate([amplitudes[r] for r in train_runs], axis=0)
        y_train = np.tile(labels, len(train_runs))

        # Test data: test_run
        X_test = amplitudes[test_run]
        y_test = labels

        # Train LDA
        lda = LinearDiscriminantAnalysis()
        lda.fit(X_train, y_train)

        # Predict
        y_pred = lda.predict(X_test)

        predictions.extend(y_pred)
        true_labels.extend(y_test)

    # Compute accuracy
    accuracy = np.mean(np.array(predictions) == np.array(true_labels))

    return accuracy


def load_subject_roi_data(subject, roi):
    """
    Load raw and Procrustes-aligned amplitudes for a subject-ROI pair

    Returns:
        data: dict with 'raw' and 'procrustes' amplitudes,
              'metrics' from existing JSON
    """
    subject_dir = DATA_DIR / f"sub-{subject}" / roi

    # Load amplitudes
    amp_raw = np.load(subject_dir / "amplitudes_raw.npy")
    amp_procrustes = np.load(subject_dir / "amplitudes_procrustes.npy")

    # Load existing metrics
    with open(subject_dir / "metrics.json") as f:
        metrics = json.load(f)

    return {
        'raw': amp_raw,
        'procrustes': amp_procrustes,
        'metrics': metrics
    }


def analyze_all_subjects():
    """
    Analyze all subject-ROI pairs and compile results

    Returns:
        df: DataFrame with all results
    """
    results = []

    labels = np.arange(8)  # 8 colors

    for subject in ALL_SUBJECTS:
        for roi in ROIS:
            print(f"  Processing sub-{subject} {roi}...")

            try:
                # Load data
                data = load_subject_roi_data(subject, roi)
                amp_raw = data['raw']
                amp_procrustes = data['procrustes']
                metrics = data['metrics']

                # Compute RDMs
                rdms_raw = [compute_rdm(amp_raw[r]) for r in range(len(amp_raw))]
                rdms_procrustes = [compute_rdm(amp_procrustes[r]) for r in range(len(amp_procrustes))]

                # Compute RDM reliability
                rdm_rel_raw = compute_rdm_reliability(rdms_raw)
                rdm_rel_procrustes = compute_rdm_reliability(rdms_procrustes)

                # Compute decoding accuracy
                decode_raw = loro_decoding(amp_raw, labels)
                decode_procrustes = loro_decoding(amp_procrustes, labels)

                # Compile results
                results.append({
                    'subject': subject,
                    'roi': roi,
                    'group': 'HC' if subject in HC_SUBJECTS else 'CVD',
                    # RDM reliability
                    'rdm_correlation_before': rdm_rel_raw,
                    'rdm_correlation_after': rdm_rel_procrustes,
                    'rdm_correlation_improvement': rdm_rel_procrustes - rdm_rel_raw,
                    # Use crossnobis from metrics (same as correlation for this analysis)
                    'rdm_crossnobis_before': metrics.get('raw_rdm_reliability', rdm_rel_raw),
                    'rdm_crossnobis_after': metrics.get('procrustes_rdm_reliability', rdm_rel_procrustes),
                    'rdm_crossnobis_improvement': metrics.get('procrustes_rdm_reliability', rdm_rel_procrustes) - metrics.get('raw_rdm_reliability', rdm_rel_raw),
                    # Decoding
                    'decoding_accuracy_before': decode_raw,
                    'decoding_accuracy_after': decode_procrustes,
                    'decoding_improvement': decode_procrustes - decode_raw,
                    # Procrustes disparity
                    'procrustes_disparity': metrics.get('procrustes_disparity', np.nan),
                })

            except Exception as e:
                print(f"    ⚠️  Error: {e}")
                continue

    df = pd.DataFrame(results)
    df.index = [f"sub-{row['subject']}_{row['roi']}" for _, row in df.iterrows()]

    return df


def filter_paired_data(data_before, data_after):
    """
    Filter out NaN values from paired data for statistical tests

    Returns:
        valid_before, valid_after (arrays without NaN in either)
    """
    mask = ~(np.isnan(data_before) | np.isnan(data_after))
    return data_before[mask], data_after[mask]


def plot_before_after_distributions(df, output_dir):
    """
    Figure 1: 5-panel Procrustes effect distributions

    Panels:
      A: RDM Correlation (Before vs After)
      B: RDM Crossnobis (Before vs After)
      C: Decoding Accuracy (Before vs After)
      D: Improvement Distributions
      E: Procrustes Disparity Distribution
    """

    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()

    # Panel A: RDM Correlation
    ax = axes[0]
    data_before = df['rdm_correlation_before'].values
    data_after = df['rdm_correlation_after'].values

    # Filter valid data for plotting
    valid_before, valid_after = filter_paired_data(data_before, data_after)

    if len(valid_before) > 0:
        parts = ax.violinplot([valid_before, valid_after],
                              positions=[0, 1],
                              widths=0.7,
                              showmeans=True,
                              showextrema=True)

        # Color
        parts['bodies'][0].set_facecolor('coral')
        parts['bodies'][0].set_alpha(0.7)
        parts['bodies'][1].set_facecolor('skyblue')
        parts['bodies'][1].set_alpha(0.7)

        # Paired lines (only for valid data)
        for idx in df.index:
            before_val = df.loc[idx, 'rdm_correlation_before']
            after_val = df.loc[idx, 'rdm_correlation_after']
            if not (np.isnan(before_val) or np.isnan(after_val)):
                ax.plot([0, 1], [before_val, after_val],
                        'gray', alpha=0.2, linewidth=0.5)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before\nProcrustes', 'After\nProcrustes'])
    ax.set_ylabel('RDM Correlation Reliability')
    ax.set_title(f'A. RDM Correlation (n={len(valid_before)})')
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # Wilcoxon test (only on valid pairs)
    if len(valid_before) > 0:
        stat, p = stats.wilcoxon(valid_before, valid_after, alternative='less')
        ax.text(0.5, ax.get_ylim()[1]*0.95, f'Wilcoxon p={p:.2e}',
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel B: RDM Crossnobis (same as correlation for this analysis)
    ax = axes[1]
    data_before = df['rdm_crossnobis_before'].values
    data_after = df['rdm_crossnobis_after'].values

    # Filter valid data
    valid_before, valid_after = filter_paired_data(data_before, data_after)

    if len(valid_before) > 0:
        parts = ax.violinplot([valid_before, valid_after],
                              positions=[0, 1],
                              widths=0.7,
                              showmeans=True,
                              showextrema=True)

        parts['bodies'][0].set_facecolor('coral')
        parts['bodies'][0].set_alpha(0.7)
        parts['bodies'][1].set_facecolor('skyblue')
        parts['bodies'][1].set_alpha(0.7)

        # Paired lines (only for valid data)
        for idx in df.index:
            before_val = df.loc[idx, 'rdm_crossnobis_before']
            after_val = df.loc[idx, 'rdm_crossnobis_after']
            if not (np.isnan(before_val) or np.isnan(after_val)):
                ax.plot([0, 1], [before_val, after_val],
                        'gray', alpha=0.2, linewidth=0.5)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before\nProcrustes', 'After\nProcrustes'])
    ax.set_ylabel('RDM Reliability')
    ax.set_title(f'B. RDM Reliability (n={len(valid_before)})')
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    if len(valid_before) > 0:
        stat, p = stats.wilcoxon(valid_before, valid_after, alternative='less')
        ax.text(0.5, ax.get_ylim()[1]*0.95, f'Wilcoxon p={p:.2e}',
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel C: Decoding Accuracy
    ax = axes[2]
    data_before = df['decoding_accuracy_before']
    data_after = df['decoding_accuracy_after']

    parts = ax.violinplot([data_before, data_after],
                          positions=[0, 1],
                          widths=0.7,
                          showmeans=True,
                          showextrema=True)

    parts['bodies'][0].set_facecolor('coral')
    parts['bodies'][0].set_alpha(0.7)
    parts['bodies'][1].set_facecolor('skyblue')
    parts['bodies'][1].set_alpha(0.7)

    for idx in df.index:
        ax.plot([0, 1],
                [df.loc[idx, 'decoding_accuracy_before'],
                 df.loc[idx, 'decoding_accuracy_after']],
                'gray', alpha=0.2, linewidth=0.5)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before\nProcrustes', 'After\nProcrustes'])
    ax.set_ylabel('Decoding Accuracy')
    ax.set_title('C. Decoding Accuracy (LORO, 8-class)')
    ax.axhline(0.125, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Chance (12.5%)')
    ax.legend(loc='lower right', fontsize=10)

    stat, p = stats.wilcoxon(data_before, data_after, alternative='less')
    ax.text(0.5, ax.get_ylim()[1]*0.95, f'Wilcoxon p={p:.2e}',
            ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel D: Improvement Distributions
    ax = axes[3]
    improvements = [
        ('RDM Corr', df['rdm_correlation_improvement'].dropna()),
        ('RDM Reliability', df['rdm_crossnobis_improvement'].dropna()),
        ('Decoding', df['decoding_improvement'].dropna())
    ]

    colors = ['steelblue', 'seagreen', 'mediumpurple']

    for i, (label, data) in enumerate(improvements):
        if len(data) > 0:
            ax.hist(data, bins=15, alpha=0.6, color=colors[i], label=label, edgecolor='black')

    ax.axvline(0, color='black', linestyle='--', linewidth=2, label='No improvement')
    ax.set_xlabel('Improvement (After - Before)')
    ax.set_ylabel('Count')
    ax.set_title('D. Improvement Distributions')
    ax.legend(loc='upper right', fontsize=10)

    # Annotate % positive
    y_pos = 0.98
    for label, data in improvements:
        if len(data) > 0:
            pct_positive = 100 * np.sum(data > 0) / len(data)
            mean_imp = np.mean(data)
            ax.text(0.02, y_pos,
                    f'{label}: {pct_positive:.1f}% positive (n={len(data)}, mean: {mean_imp:+.3f})',
                    transform=ax.transAxes, fontsize=9,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor=colors[improvements.index((label, data))], alpha=0.3))
            y_pos -= 0.08

    # Panel E: Procrustes Disparity
    ax = axes[4]
    disparities = df['procrustes_disparity'].dropna()

    ax.hist(disparities, bins=20, color='orange', alpha=0.7, edgecolor='black')
    ax.axvline(np.median(disparities), color='red', linestyle='--', linewidth=2,
               label=f'Median: {np.median(disparities):.4f}')
    ax.set_xlabel('Procrustes Disparity')
    ax.set_ylabel('Count')
    ax.set_title('E. Procrustes Disparity Distribution')
    ax.legend(loc='upper right')

    # Annotate statistics
    ax.text(0.98, 0.98,
            f'Mean: {np.mean(disparities):.4f}\n'
            f'Range: [{np.min(disparities):.4f}, {np.max(disparities):.4f}]',
            transform=ax.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Remove unused axis
    fig.delaxes(axes[5])

    plt.tight_layout()

    output_file = output_dir / 'procrustes_effect_distributions.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()


def plot_roi_comparison(df, output_dir):
    """
    Figure 2: ROI Comparison

    Boxplots: RDM reliability (before/after) per ROI
    """

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: Before Procrustes
    ax = axes[0]
    roi_order = ['V1', 'V2', 'V3', 'V4']
    data_before = [df[df['roi'] == roi]['rdm_correlation_before'].dropna().values for roi in roi_order]

    bp = ax.boxplot(data_before, labels=roi_order, patch_artist=True)

    for patch in bp['boxes']:
        patch.set_facecolor('coral')
        patch.set_alpha(0.7)

    ax.set_ylabel('RDM Correlation Reliability')
    ax.set_title('Before Procrustes')
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(axis='y', alpha=0.3)

    # Panel B: After Procrustes
    ax = axes[1]
    data_after = [df[df['roi'] == roi]['rdm_correlation_after'].dropna().values for roi in roi_order]

    bp = ax.boxplot(data_after, labels=roi_order, patch_artist=True)

    for patch in bp['boxes']:
        patch.set_facecolor('skyblue')
        patch.set_alpha(0.7)

    ax.set_ylabel('RDM Correlation Reliability')
    ax.set_title('After Procrustes')
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(axis='y', alpha=0.3)

    # ANOVA test
    from scipy.stats import f_oneway
    f_stat, p_anova = f_oneway(*data_after)

    ax.text(0.5, 0.02, f'ANOVA: F={f_stat:.2f}, p={p_anova:.3f}',
            transform=ax.transAxes, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat'))

    plt.tight_layout()

    output_file = output_dir / 'procrustes_effect_by_roi.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()


def plot_hc_vs_cvd(df, output_dir):
    """
    Figure 3: HC vs CVD Comparison

    3-panel comparison across groups
    """

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel A: RDM Reliability (after Procrustes)
    ax = axes[0]
    hc_data = df[df['group'] == 'HC']['rdm_correlation_after'].dropna()
    cvd_data = df[df['group'] == 'CVD']['rdm_correlation_after'].dropna()

    bp = ax.boxplot([hc_data, cvd_data],
                     labels=[f'HC (n={len(hc_data)})', f'CVD (n={len(cvd_data)})'],
                     patch_artist=True)

    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightcoral')

    ax.set_ylabel('RDM Correlation Reliability\n(after Procrustes)')
    ax.set_title('A. RDM Reliability by Group')
    ax.grid(axis='y', alpha=0.3)

    # Mann-Whitney U test
    if len(hc_data) > 0 and len(cvd_data) > 0:
        u_stat, p = stats.mannwhitneyu(hc_data, cvd_data, alternative='two-sided')
        ax.text(0.5, 0.98, f'Mann-Whitney U: p={p:.3f}',
                transform=ax.transAxes, ha='center', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel B: Decoding Accuracy (after Procrustes)
    ax = axes[1]
    hc_data = df[df['group'] == 'HC']['decoding_accuracy_after']
    cvd_data = df[df['group'] == 'CVD']['decoding_accuracy_after']

    bp = ax.boxplot([hc_data, cvd_data],
                     labels=[f'HC (n={len(hc_data)})', f'CVD (n={len(cvd_data)})'],
                     patch_artist=True)

    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightcoral')

    ax.set_ylabel('Decoding Accuracy\n(after Procrustes)')
    ax.set_title('B. Decoding Accuracy by Group')
    ax.axhline(0.125, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Chance')
    ax.legend(loc='lower right')
    ax.grid(axis='y', alpha=0.3)

    u_stat, p = stats.mannwhitneyu(hc_data, cvd_data, alternative='two-sided')
    ax.text(0.5, 0.98, f'Mann-Whitney U: p={p:.3f}',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel C: Procrustes Disparity
    ax = axes[2]
    hc_data = df[df['group'] == 'HC']['procrustes_disparity'].dropna()
    cvd_data = df[df['group'] == 'CVD']['procrustes_disparity'].dropna()

    bp = ax.boxplot([hc_data, cvd_data],
                     labels=[f'HC (n={len(hc_data)})', f'CVD (n={len(cvd_data)})'],
                     patch_artist=True)

    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightcoral')

    ax.set_ylabel('Procrustes Disparity')
    ax.set_title('C. Alignment Quality by Group')
    ax.grid(axis='y', alpha=0.3)

    u_stat, p = stats.mannwhitneyu(hc_data, cvd_data, alternative='two-sided')
    ax.text(0.5, 0.98, f'Mann-Whitney U: p={p:.3f}',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat'))

    plt.tight_layout()

    output_file = output_dir / 'procrustes_effect_hc_vs_cvd.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()


def compute_summary_statistics(df, output_dir):
    """Compute and save summary statistics"""

    # Count valid (non-NaN) measurements
    n_valid_rdm = df['rdm_correlation_after'].notna().sum()
    n_valid_rdm_improvement = df['rdm_correlation_improvement'].notna().sum()
    n_valid_decoding = df['decoding_accuracy_after'].notna().sum()

    summary = {
        'overall': {
            'n_total': len(df),
            'n_valid_rdm': int(n_valid_rdm),
            'n_valid_decoding': int(n_valid_decoding),
            'rdm_correlation_before': {
                'mean': float(df['rdm_correlation_before'].mean()),
                'std': float(df['rdm_correlation_before'].std()),
                'median': float(df['rdm_correlation_before'].median()),
                'range': [float(df['rdm_correlation_before'].min()),
                         float(df['rdm_correlation_before'].max())]
            },
            'rdm_correlation_after': {
                'mean': float(df['rdm_correlation_after'].mean()),
                'std': float(df['rdm_correlation_after'].std()),
                'median': float(df['rdm_correlation_after'].median()),
                'range': [float(df['rdm_correlation_after'].min()),
                         float(df['rdm_correlation_after'].max())]
            },
            'rdm_correlation_improvement': {
                'mean': float(df['rdm_correlation_improvement'].mean()),
                'std': float(df['rdm_correlation_improvement'].std()),
                'percent_positive': float(100 * (df['rdm_correlation_improvement'] > 0).sum() / n_valid_rdm_improvement) if n_valid_rdm_improvement > 0 else 0.0
            },
            'decoding_accuracy_before': {
                'mean': float(df['decoding_accuracy_before'].mean()),
                'std': float(df['decoding_accuracy_before'].std())
            },
            'decoding_accuracy_after': {
                'mean': float(df['decoding_accuracy_after'].mean()),
                'std': float(df['decoding_accuracy_after'].std())
            },
            'decoding_improvement': {
                'mean': float(df['decoding_improvement'].mean()),
                'std': float(df['decoding_improvement'].std()),
                'percent_positive': float(100 * (df['decoding_improvement'] > 0).sum() / n_valid_decoding) if n_valid_decoding > 0 else 0.0
            },
            'procrustes_disparity': {
                'mean': float(df['procrustes_disparity'].mean()),
                'median': float(df['procrustes_disparity'].median()),
                'range': [float(df['procrustes_disparity'].min()),
                         float(df['procrustes_disparity'].max())]
            }
        },
        'by_group': {},
        'by_roi': {}
    }

    # Group statistics
    for group in ['HC', 'CVD']:
        group_df = df[df['group'] == group]
        summary['by_group'][group] = {
            'n': len(group_df),
            'rdm_correlation_after': {
                'mean': float(group_df['rdm_correlation_after'].mean()),
                'std': float(group_df['rdm_correlation_after'].std())
            },
            'decoding_accuracy_after': {
                'mean': float(group_df['decoding_accuracy_after'].mean()),
                'std': float(group_df['decoding_accuracy_after'].std())
            }
        }

    # ROI statistics
    for roi in ROIS:
        roi_df = df[df['roi'] == roi]
        summary['by_roi'][roi] = {
            'n': len(roi_df),
            'rdm_correlation_after': {
                'mean': float(roi_df['rdm_correlation_after'].mean()),
                'std': float(roi_df['rdm_correlation_after'].std())
            },
            'decoding_accuracy_after': {
                'mean': float(roi_df['decoding_accuracy_after'].mean()),
                'std': float(roi_df['decoding_accuracy_after'].std())
            }
        }

    # Save
    output_file = output_dir / 'c010_residuals_procrustes_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Saved: {output_file}")

    # Also save detailed DataFrame
    df_output = output_dir / 'c010_residuals_procrustes_detailed.csv'
    df.to_csv(df_output)
    print(f"✓ Saved: {df_output}")

    return summary


def main():
    """Main analysis pipeline"""

    print("="*80)
    print("C010 with Residuals Procrustes Effect Analysis")
    print("="*80)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Analyze all subjects
    print("\nAnalyzing all subject-ROI pairs...")
    df = analyze_all_subjects()
    print(f"✓ Analyzed {len(df)} subject-ROI pairs")

    # Check groups
    n_hc = (df['group'] == 'HC').sum()
    n_cvd = (df['group'] == 'CVD').sum()
    print(f"  HC:  {n_hc} pairs (7 subjects × 4 ROIs)")
    print(f"  CVD: {n_cvd} pairs (3 subjects × 4 ROIs)")

    # Generate figures
    print("\nGenerating visualizations...")

    print("  Figure 1: Procrustes effect distributions (5-panel)...")
    plot_before_after_distributions(df, OUTPUT_DIR)

    print("  Figure 2: ROI comparison...")
    plot_roi_comparison(df, OUTPUT_DIR)

    print("  Figure 3: HC vs CVD comparison...")
    plot_hc_vs_cvd(df, OUTPUT_DIR)

    # Summary statistics
    print("\nComputing summary statistics...")
    summary = compute_summary_statistics(df, OUTPUT_DIR)

    # Print key findings
    print("\n" + "="*80)
    print("Key Findings")
    print("="*80)

    print(f"\nOverall Performance (n={len(df)})")
    print("  RDM Correlation:")
    print(f"    Before:      {summary['overall']['rdm_correlation_before']['mean']:.3f} ± "
          f"{summary['overall']['rdm_correlation_before']['std']:.3f}")
    print(f"    After:       {summary['overall']['rdm_correlation_after']['mean']:.3f} ± "
          f"{summary['overall']['rdm_correlation_after']['std']:.3f}")
    print(f"    Improvement: {summary['overall']['rdm_correlation_improvement']['mean']:+.3f} ± "
          f"{summary['overall']['rdm_correlation_improvement']['std']:.3f} "
          f"({summary['overall']['rdm_correlation_improvement']['percent_positive']:.1f}% positive)")

    print("  Decoding Accuracy:")
    print(f"    Before:      {summary['overall']['decoding_accuracy_before']['mean']:.3f} ± "
          f"{summary['overall']['decoding_accuracy_before']['std']:.3f}")
    print(f"    After:       {summary['overall']['decoding_accuracy_after']['mean']:.3f} ± "
          f"{summary['overall']['decoding_accuracy_after']['std']:.3f}")
    print(f"    Improvement: {summary['overall']['decoding_improvement']['mean']:+.3f} ± "
          f"{summary['overall']['decoding_improvement']['std']:.3f} "
          f"({summary['overall']['decoding_improvement']['percent_positive']:.1f}% positive)")

    print("\nGroup Comparison:")
    for group in ['HC', 'CVD']:
        stats_group = summary['by_group'][group]
        print(f"  {group} (n={stats_group['n']}):")
        print(f"    RDM (after):     {stats_group['rdm_correlation_after']['mean']:.3f} ± "
              f"{stats_group['rdm_correlation_after']['std']:.3f}")
        print(f"    Decoding (after): {stats_group['decoding_accuracy_after']['mean']:.3f} ± "
              f"{stats_group['decoding_accuracy_after']['std']:.3f}")

    print("\nROI Comparison:")
    for roi in ROIS:
        stats_roi = summary['by_roi'][roi]
        print(f"  {roi} (n={stats_roi['n']}):")
        print(f"    RDM (after):     {stats_roi['rdm_correlation_after']['mean']:.3f} ± "
              f"{stats_roi['rdm_correlation_after']['std']:.3f}")
        print(f"    Decoding (after): {stats_roi['decoding_accuracy_after']['mean']:.3f} ± "
              f"{stats_roi['decoding_accuracy_after']['std']:.3f}")

    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("")
    print("Generated files:")
    print(f"  - {OUTPUT_DIR}/procrustes_effect_distributions.png")
    print(f"  - {OUTPUT_DIR}/procrustes_effect_by_roi.png")
    print(f"  - {OUTPUT_DIR}/procrustes_effect_hc_vs_cvd.png")
    print(f"  - {OUTPUT_DIR}/c010_residuals_procrustes_analysis.json")
    print(f"  - {OUTPUT_DIR}/c010_residuals_procrustes_detailed.csv")
    print("="*80)


if __name__ == "__main__":
    main()
