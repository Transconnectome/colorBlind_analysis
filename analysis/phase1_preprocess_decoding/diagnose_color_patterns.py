#!/usr/bin/env python3
"""
Color Pattern Diagnosis

Purpose: Understand why RDM reliability is so low (0.001) despite high run correlation (0.80)

Visualizations:
1. Voxel × Color heatmap (sorted by color preference)
2. Color pattern similarity matrix
3. Run-pair amplitude correlation
4. ANOVA F-statistics
5. Classification performance (quick LDA test)
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import f_oneway, spearmanr
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import LeaveOneOut
import sys

plt.rcParams['figure.dpi'] = 150


def load_amplitudes(subject, roi, use_raw=False):
    """Load amplitudes from no-drift results"""
    results_dir = Path(f"analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/nzNone_moNo/sub-{subject}/{roi}")

    if use_raw:
        amp_file = results_dir / "amplitude.npy"
    else:
        amp_file = results_dir / "amplitudes_z.npy"

    if not amp_file.exists():
        raise FileNotFoundError(f"Not found: {amp_file}")

    return np.load(amp_file)


def compute_anova_f(amplitudes_z):
    """Compute ANOVA F-statistic per voxel"""
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Reshape: (n_runs*n_colors, n_voxels)
    X = amplitudes_z.reshape(-1, n_voxels)
    y = np.tile(np.arange(n_colors), n_runs)

    f_values = []
    for voxel_idx in range(n_voxels):
        # Group data by color
        groups = [X[y == c, voxel_idx] for c in range(n_colors)]
        f_stat, p_val = f_oneway(*groups)
        f_values.append(f_stat)

    return np.array(f_values)


def quick_lda_test(amplitudes_z):
    """Quick LDA classification test"""
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    accuracies = []

    for test_run in range(n_runs):
        # Train/test split
        train_runs = [r for r in range(n_runs) if r != test_run]

        X_train = amplitudes_z[train_runs].reshape(-1, n_voxels)
        y_train = np.tile(np.arange(n_colors), len(train_runs))

        X_test = amplitudes_z[test_run]  # (n_colors, n_voxels)
        y_test = np.arange(n_colors)

        # LDA
        clf = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
        clf.fit(X_train, y_train)
        acc = clf.score(X_test, y_test)
        accuracies.append(acc)

    return np.array(accuracies)


def compute_rdm_proper(amplitudes):
    """
    Compute RDM properly

    Args:
        amplitudes: (n_colors, n_voxels)

    Returns:
        rdm: (n_colors, n_colors)
    """
    # Pearson correlation between color patterns
    corr_matrix = np.corrcoef(amplitudes)  # Each row is a color pattern
    rdm = 1 - corr_matrix
    return rdm


def main():
    if len(sys.argv) < 3:
        print("Usage: python diagnose_color_patterns.py <subject> <roi>")
        print("Example: python diagnose_color_patterns.py 01 V1")
        sys.exit(1)

    subject = sys.argv[1]
    roi = sys.argv[2]

    output_dir = Path("analysis/phase1_preprocess_decoding/color_pattern_diagnosis")
    output_dir.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print(f"Color Pattern Diagnosis: sub-{subject} {roi}")
    print("=" * 80)

    # Load data
    print("\n[1/6] Loading data...")
    try:
        amplitudes_z = load_amplitudes(subject, roi, use_raw=False)
        print(f"  ✓ Loaded z-scored amplitudes: {amplitudes_z.shape}")
    except FileNotFoundError:
        print("  ✗ Z-scored amplitudes not found, trying raw...")
        amplitudes_raw = load_amplitudes(subject, roi, use_raw=True)
        print(f"  ✓ Loaded raw amplitudes: {amplitudes_raw.shape}")

        # Manual z-score
        n_runs, n_colors, n_voxels = amplitudes_raw.shape
        amplitudes_z = np.zeros_like(amplitudes_raw)

        for run_idx in range(n_runs):
            for voxel_idx in range(n_voxels):
                voxel_amps = amplitudes_raw[run_idx, :, voxel_idx]
                if np.std(voxel_amps) > 1e-10:
                    amplitudes_z[run_idx, :, voxel_idx] = (voxel_amps - np.mean(voxel_amps)) / np.std(voxel_amps)

        print(f"  ✓ Manually z-scored")

    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # ANOVA F-statistics
    print("\n[2/6] Computing ANOVA F-statistics...")
    f_values = compute_anova_f(amplitudes_z)
    n_significant = np.sum(~np.isnan(f_values))
    print(f"  F-value range: [{np.nanmin(f_values):.2f}, {np.nanmax(f_values):.2f}]")
    print(f"  F-value mean: {np.nanmean(f_values):.2f}")
    print(f"  Valid voxels: {n_significant}/{n_voxels}")

    # Quick LDA test
    print("\n[3/6] Running quick LDA classification...")
    accuracies = quick_lda_test(amplitudes_z)
    print(f"  Accuracies per fold: {accuracies}")
    print(f"  Mean accuracy: {np.mean(accuracies):.1%}")
    print(f"  Chance level: {100/n_colors:.1%}")

    # Run correlation
    print("\n[4/6] Computing run-pair correlations...")
    run_correlations = []
    for run_i in range(n_runs):
        for run_j in range(run_i+1, n_runs):
            # Flatten all color×voxel patterns
            pattern_i = amplitudes_z[run_i].flatten()
            pattern_j = amplitudes_z[run_j].flatten()
            r = np.corrcoef(pattern_i, pattern_j)[0, 1]
            run_correlations.append(r)

    print(f"  Run-pair correlations: {run_correlations}")
    print(f"  Mean: {np.mean(run_correlations):.4f}")

    # RDM analysis
    print("\n[5/6] Computing RDM reliability...")
    rdms = []
    for run_idx in range(n_runs):
        rdm = compute_rdm_proper(amplitudes_z[run_idx])
        rdms.append(rdm)

    # RDM run-pair correlation
    rdm_correlations = []
    for run_i in range(n_runs):
        for run_j in range(run_i+1, n_runs):
            rdm_i = rdms[run_i]
            rdm_j = rdms[run_j]

            # Upper triangle
            triu_idx = np.triu_indices(n_colors, k=1)
            vec_i = rdm_i[triu_idx]
            vec_j = rdm_j[triu_idx]

            r, _ = spearmanr(vec_i, vec_j)
            rdm_correlations.append(r)

    print(f"  RDM correlations: {rdm_correlations}")
    print(f"  Mean: {np.mean(rdm_correlations):.4f}")

    # Visualizations
    print("\n[6/6] Creating visualizations...")

    color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']

    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # === Plot 1: Voxel × Color heatmap (run 1, sorted by best F-value voxels) ===
    ax = fig.add_subplot(gs[0, :2])

    # Select top 50 voxels by F-value
    valid_f_idx = ~np.isnan(f_values)
    valid_f_values = f_values[valid_f_idx]
    valid_voxel_idx = np.where(valid_f_idx)[0]

    if len(valid_f_values) > 0:
        top_k = min(50, len(valid_f_values))
        top_voxel_idx = valid_voxel_idx[np.argsort(valid_f_values)[-top_k:]]

        # Get amplitudes for these voxels (run 1)
        data = amplitudes_z[0, :, top_voxel_idx].T  # (voxels, colors)

        # Sort voxels by their preferred color
        preferred_color = np.argmax(data, axis=1)
        sort_idx = np.argsort(preferred_color)
        data_sorted = data[sort_idx, :]

        im = ax.imshow(data_sorted, aspect='auto', cmap='RdBu_r', vmin=-2, vmax=2)
        ax.set_xlabel('Color', fontsize=12)
        ax.set_ylabel(f'Voxel (top {top_k} by F-value, sorted by preference)', fontsize=12)
        ax.set_title('Voxel × Color Pattern (Run 1)', fontsize=14, fontweight='bold')
        ax.set_xticks(range(n_colors))
        ax.set_xticklabels(color_names, rotation=45, ha='right')
        plt.colorbar(im, ax=ax, label='Z-scored amplitude')

    # === Plot 2: F-value distribution ===
    ax = fig.add_subplot(gs[0, 2])
    ax.hist(f_values[valid_f_idx], bins=30, edgecolor='black', alpha=0.7)
    ax.set_xlabel('F-value', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title(f'F-value Distribution\n(Valid: {n_significant}/{n_voxels})', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)

    # === Plot 3: Color similarity matrix (run 1) ===
    ax = fig.add_subplot(gs[1, 0])
    corr_matrix = np.corrcoef(amplitudes_z[0])  # Color × Color
    im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(n_colors))
    ax.set_yticks(range(n_colors))
    ax.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(color_names, fontsize=9)
    ax.set_title('Color Pattern Correlation\n(Run 1)', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax)

    # === Plot 4: RDM (run 1) ===
    ax = fig.add_subplot(gs[1, 1])
    rdm = rdms[0]
    im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2)
    ax.set_xticks(range(n_colors))
    ax.set_yticks(range(n_colors))
    ax.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(color_names, fontsize=9)
    ax.set_title('RDM (1 - correlation)\n(Run 1)', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax)

    # === Plot 5: Run-pair RDM correlations ===
    ax = fig.add_subplot(gs[1, 2])
    ax.bar(range(len(rdm_correlations)), rdm_correlations, edgecolor='black')
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_xlabel('Run Pair', fontsize=12)
    ax.set_ylabel('Spearman r', fontsize=12)
    ax.set_title(f'RDM Reliability\n(Mean: {np.mean(rdm_correlations):.3f})', fontsize=12, fontweight='bold')
    ax.set_ylim([-1, 1])
    ax.grid(alpha=0.3, axis='y')

    # === Plot 6: Classification accuracy ===
    ax = fig.add_subplot(gs[2, 0])
    ax.bar(range(1, n_runs+1), accuracies * 100, edgecolor='black', alpha=0.7)
    ax.axhline(100/n_colors, color='red', linestyle='--', linewidth=2, label='Chance')
    ax.set_xlabel('Test Run', fontsize=12)
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title(f'LDA Classification\n(Mean: {np.mean(accuracies):.1%})', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3, axis='y')

    # === Plot 7: Run-pair amplitude correlation ===
    ax = fig.add_subplot(gs[2, 1])
    ax.bar(range(len(run_correlations)), run_correlations, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Run Pair', fontsize=12)
    ax.set_ylabel('Pearson r', fontsize=12)
    ax.set_title(f'Run-pair Amplitude Correlation\n(Mean: {np.mean(run_correlations):.3f})', fontsize=12, fontweight='bold')
    ax.set_ylim([0, 1])
    ax.grid(alpha=0.3, axis='y')

    # === Plot 8: Per-color mean amplitude (across runs) ===
    ax = fig.add_subplot(gs[2, 2])

    # Average across runs and voxels
    color_means = np.mean(amplitudes_z, axis=(0, 2))  # (n_colors,)
    color_stds = np.std(amplitudes_z, axis=(0, 2))

    ax.bar(range(n_colors), color_means, yerr=color_stds, capsize=5, edgecolor='black', alpha=0.7)
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_xticks(range(n_colors))
    ax.set_xticklabels(color_names, rotation=45, ha='right')
    ax.set_ylabel('Mean Z-scored Amplitude', fontsize=12)
    ax.set_title('Mean Amplitude per Color\n(across runs & voxels)', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3, axis='y')

    plt.suptitle(f'Color Pattern Diagnosis: sub-{subject} {roi}', fontsize=16, fontweight='bold', y=0.995)

    fig_path = output_dir / f"color_pattern_diagnosis_sub-{subject}_{roi}.png"
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: {fig_path}")
    plt.close()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Valid voxels (F-statistic): {n_significant}/{n_voxels}")
    print(f"Mean F-value: {np.nanmean(f_values):.2f}")
    print(f"Classification accuracy: {np.mean(accuracies):.1%} (chance: {100/n_colors:.1%})")
    print(f"Run-pair amplitude correlation: {np.mean(run_correlations):.4f}")
    print(f"RDM reliability (run-pair RDM correlation): {np.mean(rdm_correlations):.4f}")

    if np.mean(rdm_correlations) < 0.1:
        print("\n🚨 CRITICAL: RDM reliability is extremely low!")
        print("   Possible reasons:")
        print("   1. Too few voxels with reliable color tuning")
        print("   2. High inter-voxel noise")
        print("   3. RDM calculation issue")
        print("   → Recommendation: Use ANOVA feature selection to select color-selective voxels")

    if np.mean(accuracies) > 1/n_colors * 1.5:
        print("\n✅ Classification shows above-chance performance")
        print("   → Color information exists, but RDM may be too sensitive to noise")

    print("=" * 80)


if __name__ == "__main__":
    main()
