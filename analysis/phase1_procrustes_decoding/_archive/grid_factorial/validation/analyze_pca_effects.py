#!/usr/bin/env python3
"""
PCA Effect Analysis on Raw fMRI Data

Tests whether PCA dimensionality reduction on raw (non-Procrustes) data
can improve RDM reliability and decoding performance.

Compares:
  1. Raw (no processing)
  2. Raw + PCA (various n_components)
  3. Procrustes (reference)
  4. Procrustes + PCA (optional)

Outputs:
  - PCA effect plots (RDM, decoding, variance explained)
  - Optimal n_components per subject-ROI
  - Summary statistics and recommendations

Author: Claude Code
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from scipy.spatial.distance import pdist, squareform

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "full_dataset_C010"
OUTPUT_DIR = BASE_DIR / "pca_analysis"

# Subject groups
HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

# ROIs
ROIS = ['V1', 'V2', 'V3', 'V4']

# PCA configurations to test
PCA_CONFIGS = {
    'variance_95': 0.95,  # Keep 95% variance
    'variance_90': 0.90,  # Keep 90% variance
    'variance_85': 0.85,  # Keep 85% variance
    'variance_80': 0.80,  # Keep 80% variance
    'n_50': 50,           # Fixed 50 components
    'n_100': 100,         # Fixed 100 components
    'n_150': 150,         # Fixed 150 components
}


def apply_pca(amplitudes, n_components_or_variance):
    """
    Apply PCA to amplitudes

    Args:
        amplitudes: (n_runs, n_conditions, n_voxels) array
        n_components_or_variance: int (n_components) or float (variance ratio)

    Returns:
        amplitudes_pca: (n_runs, n_conditions, n_components) array
        pca: fitted PCA object
        variance_explained: cumulative variance explained
    """
    n_runs, n_conditions, n_voxels = amplitudes.shape

    # Reshape for PCA: (n_samples, n_features)
    # Treat each run-condition as a sample
    X = amplitudes.reshape(-1, n_voxels)

    # Fit PCA
    if isinstance(n_components_or_variance, float):
        # Variance threshold
        pca = PCA(n_components=n_components_or_variance, svd_solver='full')
    else:
        # Fixed number of components
        pca = PCA(n_components=min(n_components_or_variance, n_voxels, X.shape[0]))

    X_pca = pca.fit_transform(X)

    # Reshape back
    amplitudes_pca = X_pca.reshape(n_runs, n_conditions, -1)

    variance_explained = np.cumsum(pca.explained_variance_ratio_)

    return amplitudes_pca, pca, variance_explained


def compute_rdm(amplitudes):
    """Compute RDM using correlation distance"""
    rdm = squareform(pdist(amplitudes, metric='correlation'))
    return rdm


def compute_rdm_reliability(rdms):
    """Compute split-half correlation"""
    n_runs = len(rdms)
    if n_runs < 2:
        return np.nan

    odd_rdms = [rdms[i] for i in range(0, n_runs, 2)]
    even_rdms = [rdms[i] for i in range(1, n_runs, 2)]

    if len(odd_rdms) == 0 or len(even_rdms) == 0:
        return np.nan

    odd_avg = np.mean(odd_rdms, axis=0)
    even_avg = np.mean(even_rdms, axis=0)

    mask = np.triu_indices_from(odd_avg, k=1)
    odd_vec = odd_avg[mask]
    even_vec = even_avg[mask]

    corr, _ = stats.spearmanr(odd_vec, even_vec)
    return corr


def loro_decoding(amplitudes, labels):
    """Leave-One-Run-Out cross-validated LDA decoding"""
    n_runs, n_conditions, n_features = amplitudes.shape

    predictions = []
    true_labels = []

    for test_run in range(n_runs):
        train_runs = [i for i in range(n_runs) if i != test_run]
        X_train = np.concatenate([amplitudes[r] for r in train_runs], axis=0)
        y_train = np.tile(labels, len(train_runs))

        X_test = amplitudes[test_run]
        y_test = labels

        lda = LinearDiscriminantAnalysis()
        lda.fit(X_train, y_train)

        y_pred = lda.predict(X_test)

        predictions.extend(y_pred)
        true_labels.extend(y_test)

    accuracy = np.mean(np.array(predictions) == np.array(true_labels))
    return accuracy


def analyze_subject_roi_pca(subject, roi):
    """
    Analyze PCA effects for one subject-ROI pair

    Returns:
        results: dict with performance metrics for each configuration
    """
    subject_dir = DATA_DIR / f"sub-{subject}" / roi

    # Load data
    amp_raw = np.load(subject_dir / "amplitudes_raw.npy")
    amp_procrustes = np.load(subject_dir / "amplitudes_procrustes.npy")

    labels = np.arange(8)

    results = {
        'subject': subject,
        'roi': roi,
        'group': 'HC' if subject in HC_SUBJECTS else 'CVD',
    }

    # 1. Baseline: Raw (no PCA)
    rdms_raw = [compute_rdm(amp_raw[r]) for r in range(len(amp_raw))]
    results['raw_rdm_reliability'] = compute_rdm_reliability(rdms_raw)
    results['raw_decoding'] = loro_decoding(amp_raw, labels)
    results['raw_n_voxels'] = amp_raw.shape[2]

    # 2. Baseline: Procrustes (no PCA)
    rdms_proc = [compute_rdm(amp_procrustes[r]) for r in range(len(amp_procrustes))]
    results['procrustes_rdm_reliability'] = compute_rdm_reliability(rdms_proc)
    results['procrustes_decoding'] = loro_decoding(amp_procrustes, labels)

    # 3. Test various PCA configurations on raw
    for config_name, config_value in PCA_CONFIGS.items():
        try:
            amp_pca, pca, var_explained = apply_pca(amp_raw, config_value)
            n_components = amp_pca.shape[2]

            # RDM reliability
            rdms_pca = [compute_rdm(amp_pca[r]) for r in range(len(amp_pca))]
            rdm_rel = compute_rdm_reliability(rdms_pca)

            # Decoding
            decoding = loro_decoding(amp_pca, labels)

            # Store results
            results[f'{config_name}_rdm_reliability'] = rdm_rel
            results[f'{config_name}_decoding'] = decoding
            results[f'{config_name}_n_components'] = n_components
            results[f'{config_name}_variance_explained'] = float(var_explained[-1])

        except Exception as e:
            print(f"    ⚠️  Error with {config_name}: {e}")
            results[f'{config_name}_rdm_reliability'] = np.nan
            results[f'{config_name}_decoding'] = np.nan
            results[f'{config_name}_n_components'] = np.nan
            results[f'{config_name}_variance_explained'] = np.nan

    # 4. Test PCA on Procrustes (optional)
    try:
        amp_proc_pca, pca_proc, var_proc = apply_pca(amp_procrustes, 0.95)
        rdms_proc_pca = [compute_rdm(amp_proc_pca[r]) for r in range(len(amp_proc_pca))]
        results['procrustes_pca95_rdm_reliability'] = compute_rdm_reliability(rdms_proc_pca)
        results['procrustes_pca95_decoding'] = loro_decoding(amp_proc_pca, labels)
        results['procrustes_pca95_n_components'] = amp_proc_pca.shape[2]
    except:
        results['procrustes_pca95_rdm_reliability'] = np.nan
        results['procrustes_pca95_decoding'] = np.nan
        results['procrustes_pca95_n_components'] = np.nan

    return results


def analyze_all_subjects():
    """Analyze all subject-ROI pairs"""
    results = []

    for subject in ALL_SUBJECTS:
        for roi in ROIS:
            print(f"  Processing sub-{subject} {roi}...")
            try:
                result = analyze_subject_roi_pca(subject, roi)
                results.append(result)
            except Exception as e:
                print(f"    ⚠️  Error: {e}")
                continue

    df = pd.DataFrame(results)
    return df


def plot_pca_effects(df, output_dir):
    """
    Plot PCA effects on RDM and decoding
    """
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()

    # Config names for plotting
    configs = ['raw', 'variance_95', 'variance_90', 'variance_85',
               'variance_80', 'n_50', 'n_100', 'n_150', 'procrustes']
    config_labels = ['Raw', 'PCA95%', 'PCA90%', 'PCA85%',
                     'PCA80%', 'PCA50', 'PCA100', 'PCA150', 'Procrustes']

    # Panel A: RDM Reliability comparison
    ax = axes[0]
    rdm_means = []
    rdm_stds = []

    for config in configs:
        col = f'{config}_rdm_reliability'
        if col in df.columns:
            rdm_means.append(df[col].mean())
            rdm_stds.append(df[col].std())
        else:
            rdm_means.append(np.nan)
            rdm_stds.append(np.nan)

    x = np.arange(len(configs))
    ax.bar(x, rdm_means, yerr=rdm_stds, capsize=5, alpha=0.7,
           color=['coral' if c == 'raw' else 'skyblue' if c == 'procrustes' else 'lightgreen'
                  for c in configs])
    ax.set_xticks(x)
    ax.set_xticklabels(config_labels, rotation=45, ha='right')
    ax.set_ylabel('RDM Reliability')
    ax.set_title('A. RDM Reliability by Configuration')
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(axis='y', alpha=0.3)

    # Panel B: Decoding Accuracy comparison
    ax = axes[1]
    dec_means = []
    dec_stds = []

    for config in configs:
        col = f'{config}_decoding'
        if col in df.columns:
            dec_means.append(df[col].mean())
            dec_stds.append(df[col].std())
        else:
            dec_means.append(np.nan)
            dec_stds.append(np.nan)

    ax.bar(x, dec_means, yerr=dec_stds, capsize=5, alpha=0.7,
           color=['coral' if c == 'raw' else 'skyblue' if c == 'procrustes' else 'lightgreen'
                  for c in configs])
    ax.set_xticks(x)
    ax.set_xticklabels(config_labels, rotation=45, ha='right')
    ax.set_ylabel('Decoding Accuracy')
    ax.set_title('B. Decoding Accuracy by Configuration')
    ax.axhline(0.125, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Chance')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Panel C: N_components vs RDM reliability
    ax = axes[2]
    variance_configs = ['variance_95', 'variance_90', 'variance_85', 'variance_80']
    for config in variance_configs:
        n_comp = df[f'{config}_n_components']
        rdm_rel = df[f'{config}_rdm_reliability']
        ax.scatter(n_comp, rdm_rel, alpha=0.5, label=config.replace('_', ' '))

    ax.set_xlabel('Number of Components')
    ax.set_ylabel('RDM Reliability')
    ax.set_title('C. RDM Reliability vs N_Components')
    ax.legend()
    ax.grid(alpha=0.3)

    # Panel D: Improvement over raw
    ax = axes[3]
    pca_configs = ['variance_95', 'variance_90', 'variance_85', 'variance_80']
    improvements = []
    labels_imp = []

    for config in pca_configs:
        imp = df[f'{config}_rdm_reliability'] - df['raw_rdm_reliability']
        improvements.append(imp.dropna())
        labels_imp.append(config.replace('variance_', ''))

    bp = ax.boxplot(improvements, labels=labels_imp, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightgreen')
        patch.set_alpha(0.7)

    ax.axhline(0, color='black', linestyle='--', linewidth=2, label='No improvement')
    ax.set_ylabel('RDM Improvement (PCA - Raw)')
    ax.set_xlabel('Variance Threshold')
    ax.set_title('D. RDM Improvement Distribution')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Panel E: Decoding improvement over raw
    ax = axes[4]
    improvements_dec = []

    for config in pca_configs:
        imp = df[f'{config}_decoding'] - df['raw_decoding']
        improvements_dec.append(imp.dropna())

    bp = ax.boxplot(improvements_dec, labels=labels_imp, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightgreen')
        patch.set_alpha(0.7)

    ax.axhline(0, color='black', linestyle='--', linewidth=2, label='No improvement')
    ax.set_ylabel('Decoding Improvement (PCA - Raw)')
    ax.set_xlabel('Variance Threshold')
    ax.set_title('E. Decoding Improvement Distribution')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Panel F: Variance explained distribution
    ax = axes[5]
    for config in variance_configs:
        var_exp = df[f'{config}_variance_explained'].dropna()
        n_comp = df[f'{config}_n_components'].dropna()
        ax.scatter(n_comp, var_exp, alpha=0.5, label=config.replace('_', ' '))

    ax.set_xlabel('Number of Components')
    ax.set_ylabel('Variance Explained')
    ax.set_title('F. Variance Explained vs N_Components')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()

    output_file = output_dir / 'pca_effects_summary.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_pca_vs_procrustes(df, output_dir):
    """
    Compare best PCA result vs Procrustes
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Find best PCA config per subject-ROI
    pca_configs = ['variance_95', 'variance_90', 'variance_85', 'variance_80']

    best_rdm_pca = []
    best_dec_pca = []

    for idx, row in df.iterrows():
        rdm_values = [row[f'{c}_rdm_reliability'] for c in pca_configs]
        dec_values = [row[f'{c}_decoding'] for c in pca_configs]

        best_rdm_pca.append(np.nanmax(rdm_values))
        best_dec_pca.append(np.nanmax(dec_values))

    df['best_pca_rdm'] = best_rdm_pca
    df['best_pca_decoding'] = best_dec_pca

    # Panel A: RDM - Raw vs Best PCA vs Procrustes
    ax = axes[0]
    data = [df['raw_rdm_reliability'], df['best_pca_rdm'], df['procrustes_rdm_reliability']]
    bp = ax.boxplot(data, labels=['Raw', 'Best PCA', 'Procrustes'], patch_artist=True)

    colors = ['coral', 'lightgreen', 'skyblue']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('RDM Reliability')
    ax.set_title('A. RDM Reliability Comparison')
    ax.grid(axis='y', alpha=0.3)

    # Statistical tests
    _, p_pca_vs_raw = stats.wilcoxon(df['best_pca_rdm'], df['raw_rdm_reliability'], alternative='greater')
    _, p_proc_vs_pca = stats.wilcoxon(df['procrustes_rdm_reliability'], df['best_pca_rdm'], alternative='greater')

    ax.text(0.5, 0.98, f'PCA vs Raw: p={p_pca_vs_raw:.2e}\nProc vs PCA: p={p_proc_vs_pca:.2e}',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel B: Decoding - Raw vs Best PCA vs Procrustes
    ax = axes[1]
    data = [df['raw_decoding'], df['best_pca_decoding'], df['procrustes_decoding']]
    bp = ax.boxplot(data, labels=['Raw', 'Best PCA', 'Procrustes'], patch_artist=True)

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('Decoding Accuracy')
    ax.set_title('B. Decoding Accuracy Comparison')
    ax.axhline(0.125, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Chance')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    _, p_pca_vs_raw_dec = stats.wilcoxon(df['best_pca_decoding'], df['raw_decoding'], alternative='greater')
    _, p_proc_vs_pca_dec = stats.wilcoxon(df['procrustes_decoding'], df['best_pca_decoding'], alternative='greater')

    ax.text(0.5, 0.98, f'PCA vs Raw: p={p_pca_vs_raw_dec:.2e}\nProc vs PCA: p={p_proc_vs_pca_dec:.2e}',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat'))

    # Panel C: Scatter - PCA vs Procrustes
    ax = axes[2]
    ax.scatter(df['best_pca_decoding'], df['procrustes_decoding'], alpha=0.6, s=100)

    # Add diagonal line
    lim = [0, max(df['procrustes_decoding'].max(), df['best_pca_decoding'].max()) * 1.1]
    ax.plot(lim, lim, 'k--', alpha=0.5, linewidth=2, label='Equal performance')

    ax.set_xlabel('Best PCA Decoding')
    ax.set_ylabel('Procrustes Decoding')
    ax.set_title('C. PCA vs Procrustes (per subject-ROI)')
    ax.legend()
    ax.grid(alpha=0.3)

    # Count wins
    pca_wins = (df['best_pca_decoding'] > df['procrustes_decoding']).sum()
    proc_wins = (df['procrustes_decoding'] > df['best_pca_decoding']).sum()

    ax.text(0.05, 0.95, f'PCA wins: {pca_wins}\nProc wins: {proc_wins}',
            transform=ax.transAxes, va='top',
            bbox=dict(boxstyle='round', facecolor='wheat'))

    plt.tight_layout()

    output_file = output_dir / 'pca_vs_procrustes.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def compute_summary_statistics(df, output_dir):
    """Compute and save summary statistics"""

    # Best PCA per subject
    pca_configs = ['variance_95', 'variance_90', 'variance_85', 'variance_80']

    summary = {
        'overall': {
            'n_total': len(df),
            'raw': {
                'rdm_mean': float(df['raw_rdm_reliability'].mean()),
                'rdm_std': float(df['raw_rdm_reliability'].std()),
                'decoding_mean': float(df['raw_decoding'].mean()),
                'decoding_std': float(df['raw_decoding'].std()),
            },
            'procrustes': {
                'rdm_mean': float(df['procrustes_rdm_reliability'].mean()),
                'rdm_std': float(df['procrustes_rdm_reliability'].std()),
                'decoding_mean': float(df['procrustes_decoding'].mean()),
                'decoding_std': float(df['procrustes_decoding'].std()),
            },
            'pca_configs': {}
        }
    }

    # PCA config statistics
    for config in pca_configs:
        summary['overall']['pca_configs'][config] = {
            'rdm_mean': float(df[f'{config}_rdm_reliability'].mean()),
            'rdm_std': float(df[f'{config}_rdm_reliability'].std()),
            'decoding_mean': float(df[f'{config}_decoding'].mean()),
            'decoding_std': float(df[f'{config}_decoding'].std()),
            'n_components_mean': float(df[f'{config}_n_components'].mean()),
            'n_components_std': float(df[f'{config}_n_components'].std()),
            'variance_explained_mean': float(df[f'{config}_variance_explained'].mean()),
        }

    # Best PCA statistics
    best_rdm = df[[f'{c}_rdm_reliability' for c in pca_configs]].max(axis=1)
    best_dec = df[[f'{c}_decoding' for c in pca_configs]].max(axis=1)

    summary['overall']['best_pca'] = {
        'rdm_mean': float(best_rdm.mean()),
        'rdm_std': float(best_rdm.std()),
        'decoding_mean': float(best_dec.mean()),
        'decoding_std': float(best_dec.std()),
    }

    # Improvement statistics
    rdm_imp_pca = best_rdm - df['raw_rdm_reliability']
    rdm_imp_proc = df['procrustes_rdm_reliability'] - df['raw_rdm_reliability']
    dec_imp_pca = best_dec - df['raw_decoding']
    dec_imp_proc = df['procrustes_decoding'] - df['raw_decoding']

    summary['improvements'] = {
        'pca_vs_raw': {
            'rdm_mean': float(rdm_imp_pca.mean()),
            'rdm_pct_positive': float(100 * (rdm_imp_pca > 0).sum() / len(rdm_imp_pca)),
            'decoding_mean': float(dec_imp_pca.mean()),
            'decoding_pct_positive': float(100 * (dec_imp_pca > 0).sum() / len(dec_imp_pca)),
        },
        'procrustes_vs_raw': {
            'rdm_mean': float(rdm_imp_proc.mean()),
            'rdm_pct_positive': float(100 * (rdm_imp_proc > 0).sum() / len(rdm_imp_proc)),
            'decoding_mean': float(dec_imp_proc.mean()),
            'decoding_pct_positive': float(100 * (dec_imp_proc > 0).sum() / len(dec_imp_proc)),
        },
        'procrustes_vs_pca': {
            'rdm_mean': float((df['procrustes_rdm_reliability'] - best_rdm).mean()),
            'rdm_pct_positive': float(100 * (df['procrustes_rdm_reliability'] > best_rdm).sum() / len(best_rdm)),
            'decoding_mean': float((df['procrustes_decoding'] - best_dec).mean()),
            'decoding_pct_positive': float(100 * (df['procrustes_decoding'] > best_dec).sum() / len(best_dec)),
        }
    }

    # Save
    output_file = output_dir / 'pca_analysis_summary.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved: {output_file}")

    # Save detailed DataFrame
    df_output = output_dir / 'pca_analysis_detailed.csv'
    df.to_csv(df_output, index=False)
    print(f"✓ Saved: {df_output}")

    return summary


def main():
    """Main analysis pipeline"""

    print("="*80)
    print("PCA Effect Analysis on Raw fMRI Data")
    print("="*80)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Analyze all subjects
    print("\nAnalyzing PCA effects on all subject-ROI pairs...")
    df = analyze_all_subjects()
    print(f"✓ Analyzed {len(df)} subject-ROI pairs")

    # Generate figures
    print("\nGenerating visualizations...")

    print("  Figure 1: PCA effects summary (6-panel)...")
    plot_pca_effects(df, OUTPUT_DIR)

    print("  Figure 2: PCA vs Procrustes comparison...")
    plot_pca_vs_procrustes(df, OUTPUT_DIR)

    # Summary statistics
    print("\nComputing summary statistics...")
    summary = compute_summary_statistics(df, OUTPUT_DIR)

    # Print key findings
    print("\n" + "="*80)
    print("Key Findings")
    print("="*80)

    print(f"\nOverall Performance (n={len(df)})")
    print("  Raw (no processing):")
    print(f"    RDM:      {summary['overall']['raw']['rdm_mean']:.3f} ± {summary['overall']['raw']['rdm_std']:.3f}")
    print(f"    Decoding: {summary['overall']['raw']['decoding_mean']:.3f} ± {summary['overall']['raw']['decoding_std']:.3f}")

    print("\n  Best PCA (optimal per subject):")
    print(f"    RDM:      {summary['overall']['best_pca']['rdm_mean']:.3f} ± {summary['overall']['best_pca']['rdm_std']:.3f}")
    print(f"    Decoding: {summary['overall']['best_pca']['decoding_mean']:.3f} ± {summary['overall']['best_pca']['decoding_std']:.3f}")

    print("\n  Procrustes (reference):")
    print(f"    RDM:      {summary['overall']['procrustes']['rdm_mean']:.3f} ± {summary['overall']['procrustes']['rdm_std']:.3f}")
    print(f"    Decoding: {summary['overall']['procrustes']['decoding_mean']:.3f} ± {summary['overall']['procrustes']['decoding_std']:.3f}")

    print("\nImprovements:")
    print("  PCA vs Raw:")
    print(f"    RDM:      {summary['improvements']['pca_vs_raw']['rdm_mean']:+.3f} "
          f"({summary['improvements']['pca_vs_raw']['rdm_pct_positive']:.1f}% positive)")
    print(f"    Decoding: {summary['improvements']['pca_vs_raw']['decoding_mean']:+.3f} "
          f"({summary['improvements']['pca_vs_raw']['decoding_pct_positive']:.1f}% positive)")

    print("\n  Procrustes vs PCA:")
    print(f"    RDM:      {summary['improvements']['procrustes_vs_pca']['rdm_mean']:+.3f} "
          f"({summary['improvements']['procrustes_vs_pca']['rdm_pct_positive']:.1f}% positive)")
    print(f"    Decoding: {summary['improvements']['procrustes_vs_pca']['decoding_mean']:+.3f} "
          f"({summary['improvements']['procrustes_vs_pca']['decoding_pct_positive']:.1f}% positive)")

    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("")
    print("Generated files:")
    print(f"  - {OUTPUT_DIR}/pca_effects_summary.png")
    print(f"  - {OUTPUT_DIR}/pca_vs_procrustes.png")
    print(f"  - {OUTPUT_DIR}/pca_analysis_summary.json")
    print(f"  - {OUTPUT_DIR}/pca_analysis_detailed.csv")
    print("="*80)


if __name__ == "__main__":
    main()
