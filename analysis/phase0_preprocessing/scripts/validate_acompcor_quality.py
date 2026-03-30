#!/usr/bin/env python3
"""
Comprehensive Quality Control for aCompCor Implementation

Validates aCompCor confounds across all subjects and runs:
1. Mask coverage statistics
2. Component variance explained
3. Component correlation analysis
4. Outlier detection
5. Summary visualizations

Usage:
    python validate_acompcor_quality.py --method method3_header_mi --output-dir qc_summary
"""

import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


def load_mask_statistics(base_dir, subjects, runs):
    """
    Load mask statistics from all subjects and runs

    Returns:
    --------
    stats_df : pd.DataFrame
        Columns: subject, run, n_brain_voxels, n_csf_voxels, n_wm_voxels,
                 csf_coverage, wm_coverage
    """
    records = []

    for subject in subjects:
        for run in runs:
            stats_file = base_dir / 'qc' / f'sub-{subject}' / f'sub-{subject}_run-{run}_mask_stats.json'

            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    stats['subject'] = subject
                    stats['run'] = run
                    records.append(stats)
            else:
                print(f"  ⚠️  Missing: sub-{subject} run-{run}")

    if len(records) == 0:
        raise ValueError("No mask statistics files found!")

    stats_df = pd.DataFrame(records)
    return stats_df


def load_confounds_variance(base_dir, subjects, runs):
    """
    Load aCompCor variance explained from confounds files

    Returns:
    --------
    variance_df : pd.DataFrame
        Columns: subject, run, comp_00_var, comp_01_var, ..., comp_09_var
    """
    records = []

    for subject in subjects:
        for run in runs:
            confounds_file = base_dir / f'sub-{subject}' / 'func' / \
                            f'sub-{subject}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv'

            if not confounds_file.exists():
                print(f"  ⚠️  Missing confounds: sub-{subject} run-{run}")
                continue

            # Load confounds
            confounds_df = pd.read_csv(confounds_file, sep='\t')

            # Extract aCompCor components
            acompcor_cols = [col for col in confounds_df.columns if col.startswith('a_comp_cor_')]

            if len(acompcor_cols) == 0:
                print(f"  ⚠️  No aCompCor columns: sub-{subject} run-{run}")
                continue

            # Compute variance explained for each component
            record = {'subject': subject, 'run': run}

            for col in acompcor_cols:
                component_data = confounds_df[col].values
                # Variance of component (already standardized in generation)
                record[f'{col}_var'] = np.var(component_data)

            records.append(record)

    variance_df = pd.DataFrame(records)
    return variance_df


def compute_component_correlations(base_dir, subjects, runs, n_components=10):
    """
    Compute inter-component correlations to check independence

    Returns:
    --------
    correlations : dict
        {subject: correlation_matrix for each run}
    """
    correlations = {}

    for subject in subjects:
        subject_corrs = []

        for run in runs:
            confounds_file = base_dir / f'sub-{subject}' / 'func' / \
                            f'sub-{subject}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv'

            if not confounds_file.exists():
                continue

            confounds_df = pd.read_csv(confounds_file, sep='\t')

            # Extract aCompCor components
            acompcor_cols = [f'a_comp_cor_{i:02d}' for i in range(n_components)]
            acompcor_cols = [col for col in acompcor_cols if col in confounds_df.columns]

            if len(acompcor_cols) < n_components:
                continue

            # Compute correlation matrix
            acompcor_data = confounds_df[acompcor_cols].values
            corr_matrix = np.corrcoef(acompcor_data.T)
            subject_corrs.append(corr_matrix)

        if len(subject_corrs) > 0:
            correlations[subject] = np.mean(subject_corrs, axis=0)

    return correlations


def plot_mask_coverage_summary(stats_df, output_path):
    """
    Plot mask coverage statistics across subjects
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. CSF coverage distribution
    ax = axes[0, 0]
    ax.hist(stats_df['csf_coverage'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axvline(stats_df['csf_coverage'].median(), color='red', linestyle='--',
               label=f'Median: {stats_df["csf_coverage"].median():.3f}%')
    ax.set_xlabel('CSF Coverage (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('CSF Mask Coverage Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. WM coverage distribution
    ax = axes[0, 1]
    ax.hist(stats_df['wm_coverage'], bins=20, color='coral', alpha=0.7, edgecolor='black')
    ax.axvline(stats_df['wm_coverage'].median(), color='red', linestyle='--',
               label=f'Median: {stats_df["wm_coverage"].median():.3f}%')
    ax.set_xlabel('WM Coverage (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('WM Mask Coverage Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. CSF voxel count by subject
    ax = axes[1, 0]
    subject_csf = stats_df.groupby('subject')['n_csf_voxels'].mean()
    ax.bar(range(len(subject_csf)), subject_csf.values, color='steelblue', alpha=0.7)
    ax.set_xlabel('Subject')
    ax.set_ylabel('CSF Voxels (mean across runs)')
    ax.set_title('CSF Voxel Count by Subject')
    ax.set_xticks(range(len(subject_csf)))
    ax.set_xticklabels([f'sub-{s}' for s in subject_csf.index], rotation=45)
    ax.grid(True, alpha=0.3, axis='y')

    # 4. WM voxel count by subject
    ax = axes[1, 1]
    subject_wm = stats_df.groupby('subject')['n_wm_voxels'].mean()
    ax.bar(range(len(subject_wm)), subject_wm.values, color='coral', alpha=0.7)
    ax.set_xlabel('Subject')
    ax.set_ylabel('WM Voxels (mean across runs)')
    ax.set_title('WM Voxel Count by Subject')
    ax.set_xticks(range(len(subject_wm)))
    ax.set_xticklabels([f'sub-{s}' for s in subject_wm.index], rotation=45)
    ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Tissue Mask Coverage Summary (Conservative: prob > 0.99, eroded)',
                 fontsize=14, y=0.995)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Mask coverage plot saved: {output_path}")


def plot_variance_summary(variance_df, output_path):
    """
    Plot variance explained by aCompCor components
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Extract component variances
    csf_var_cols = [f'a_comp_cor_{i:02d}_var' for i in range(5)]
    wm_var_cols = [f'a_comp_cor_{i:02d}_var' for i in range(5, 10)]

    csf_var_cols = [col for col in csf_var_cols if col in variance_df.columns]
    wm_var_cols = [col for col in wm_var_cols if col in variance_df.columns]

    # 1. CSF component variance
    ax = axes[0]
    csf_variances = variance_df[csf_var_cols].values
    positions = np.arange(len(csf_var_cols))

    # Box plot
    bp = ax.boxplot(csf_variances, positions=positions, widths=0.6,
                    patch_artist=True, showfliers=True)
    for patch in bp['boxes']:
        patch.set_facecolor('steelblue')
        patch.set_alpha(0.7)

    ax.set_xlabel('CSF Component')
    ax.set_ylabel('Variance')
    ax.set_title('CSF aCompCor Variance Distribution (comp 0-4)')
    ax.set_xticks(positions)
    ax.set_xticklabels([f'{i}' for i in range(len(csf_var_cols))])
    ax.grid(True, alpha=0.3, axis='y')

    # 2. WM component variance
    ax = axes[1]
    wm_variances = variance_df[wm_var_cols].values
    positions = np.arange(len(wm_var_cols))

    bp = ax.boxplot(wm_variances, positions=positions, widths=0.6,
                    patch_artist=True, showfliers=True)
    for patch in bp['boxes']:
        patch.set_facecolor('coral')
        patch.set_alpha(0.7)

    ax.set_xlabel('WM Component')
    ax.set_ylabel('Variance')
    ax.set_title('WM aCompCor Variance Distribution (comp 5-9)')
    ax.set_xticks(positions)
    ax.set_xticklabels([f'{i}' for i in range(5, 10)])
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Variance summary plot saved: {output_path}")


def plot_correlation_heatmap(correlations, output_path):
    """
    Plot average inter-component correlation heatmap
    """
    # Average across subjects
    all_corr_matrices = list(correlations.values())
    if len(all_corr_matrices) == 0:
        print("  ⚠️  No correlation data available")
        return

    avg_corr = np.mean(all_corr_matrices, axis=0)

    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(avg_corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

    # Labels
    n_comp = avg_corr.shape[0]
    ax.set_xticks(range(n_comp))
    ax.set_yticks(range(n_comp))
    ax.set_xticklabels([f'{i}' for i in range(n_comp)])
    ax.set_yticklabels([f'{i}' for i in range(n_comp)])

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Correlation', rotation=270, labelpad=20)

    # Add dividing line between CSF (0-4) and WM (5-9)
    ax.axhline(y=4.5, color='black', linewidth=2)
    ax.axvline(x=4.5, color='black', linewidth=2)

    # Labels
    ax.text(2, -1.5, 'CSF', ha='center', fontsize=12, fontweight='bold')
    ax.text(7, -1.5, 'WM', ha='center', fontsize=12, fontweight='bold')

    ax.set_xlabel('Component Index')
    ax.set_ylabel('Component Index')
    ax.set_title('Average Inter-Component Correlation\n(Lower off-diagonal = better independence)',
                 fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Correlation heatmap saved: {output_path}")


def generate_summary_report(stats_df, variance_df, correlations, output_path):
    """
    Generate text summary report
    """
    report = []
    report.append("=" * 80)
    report.append("aCompCor Quality Control Report")
    report.append("=" * 80)
    report.append("")

    # 1. Data coverage
    report.append("1. Data Coverage")
    report.append("-" * 80)
    n_subjects = stats_df['subject'].nunique()
    n_runs_per_subject = stats_df.groupby('subject').size()
    report.append(f"  Subjects: {n_subjects}")
    report.append(f"  Runs per subject: {n_runs_per_subject.mean():.1f} (expected: 6)")
    report.append(f"  Total runs: {len(stats_df)}")
    report.append("")

    # 2. Mask coverage statistics
    report.append("2. Tissue Mask Coverage")
    report.append("-" * 80)
    report.append(f"  CSF Coverage:")
    report.append(f"    Mean:   {stats_df['csf_coverage'].mean():.4f}%")
    report.append(f"    Median: {stats_df['csf_coverage'].median():.4f}%")
    report.append(f"    Range:  [{stats_df['csf_coverage'].min():.4f}, {stats_df['csf_coverage'].max():.4f}]%")
    report.append("")
    report.append(f"  WM Coverage:")
    report.append(f"    Mean:   {stats_df['wm_coverage'].mean():.4f}%")
    report.append(f"    Median: {stats_df['wm_coverage'].median():.4f}%")
    report.append(f"    Range:  [{stats_df['wm_coverage'].min():.4f}, {stats_df['wm_coverage'].max():.4f}]%")
    report.append("")
    report.append(f"  CSF Voxel Count:")
    report.append(f"    Mean:   {stats_df['n_csf_voxels'].mean():.1f}")
    report.append(f"    Median: {stats_df['n_csf_voxels'].median():.1f}")
    report.append("")
    report.append(f"  WM Voxel Count:")
    report.append(f"    Mean:   {stats_df['n_wm_voxels'].mean():.1f}")
    report.append(f"    Median: {stats_df['n_wm_voxels'].median():.1f}")
    report.append("")

    # Check for problematic cases
    low_csf = stats_df[stats_df['n_csf_voxels'] < 10]
    low_wm = stats_df[stats_df['n_wm_voxels'] < 100]

    if len(low_csf) > 0:
        report.append(f"  ⚠️  WARNING: {len(low_csf)} runs have <10 CSF voxels (partial FOV expected)")
    if len(low_wm) > 0:
        report.append(f"  ⚠️  WARNING: {len(low_wm)} runs have <100 WM voxels (very conservative)")
    report.append("")

    # 3. Variance statistics
    if len(variance_df) > 0:
        report.append("3. aCompCor Component Variance")
        report.append("-" * 80)

        csf_var_cols = [f'a_comp_cor_{i:02d}_var' for i in range(5)]
        wm_var_cols = [f'a_comp_cor_{i:02d}_var' for i in range(5, 10)]

        csf_var_cols = [col for col in csf_var_cols if col in variance_df.columns]
        wm_var_cols = [col for col in wm_var_cols if col in variance_df.columns]

        if len(csf_var_cols) > 0:
            csf_var_mean = variance_df[csf_var_cols].mean().values
            report.append(f"  CSF Components (0-4):")
            for i, var in enumerate(csf_var_mean):
                report.append(f"    Comp {i}: {var:.4f}")

        if len(wm_var_cols) > 0:
            wm_var_mean = variance_df[wm_var_cols].mean().values
            report.append(f"  WM Components (5-9):")
            for i, var in enumerate(wm_var_mean):
                report.append(f"    Comp {i+5}: {var:.4f}")
        report.append("")

    # 4. Component independence
    if len(correlations) > 0:
        report.append("4. Component Independence (Correlation Check)")
        report.append("-" * 80)

        avg_corr = np.mean(list(correlations.values()), axis=0)

        # Off-diagonal correlations (should be low)
        off_diag = avg_corr[np.triu_indices_from(avg_corr, k=1)]

        report.append(f"  Off-diagonal correlations:")
        report.append(f"    Mean:   {off_diag.mean():.4f} (should be ~0)")
        report.append(f"    Median: {np.median(off_diag):.4f}")
        report.append(f"    Max:    {off_diag.max():.4f} (should be <0.5)")

        if off_diag.max() > 0.5:
            report.append(f"  ⚠️  WARNING: High inter-component correlation detected!")
            report.append(f"     Components may not be independent.")
        else:
            report.append(f"  ✅ Good component independence (low correlations)")
        report.append("")

    # 5. Recommendations
    report.append("5. Quality Assessment & Recommendations")
    report.append("-" * 80)

    # Check 1: CSF coverage
    csf_median = stats_df['csf_coverage'].median()
    if csf_median < 0.01:
        report.append("  ⚠️  Very low CSF coverage (<0.01%)")
        report.append("     → Expected for partial FOV (occipital cortex)")
        report.append("     → CSF aCompCor may have limited effectiveness")
        report.append("     → WM aCompCor is still valid and useful")
        report.append("")

    # Check 2: WM coverage
    wm_median = stats_df['wm_coverage'].median()
    if wm_median < 0.1:
        report.append("  ℹ️  Low WM coverage (<0.1%)")
        report.append("     → Very conservative masking (prob > 0.99 + erosion)")
        report.append("     → Minimizes GM contamination risk")
        report.append("     → Trade-off: fewer voxels but higher purity")
        report.append("")

    # Check 3: Sufficient voxels for PCA
    min_wm = stats_df['n_wm_voxels'].min()
    if min_wm < 5:
        report.append("  ⚠️  Some runs have <5 WM voxels")
        report.append("     → Insufficient for 5 PCA components")
        report.append("     → Check QC visualizations for these runs")
        report.append("")

    # Overall recommendation
    report.append("  Overall Recommendation:")
    if csf_median < 0.01 and wm_median > 0.1:
        report.append("    ✅ Use WM aCompCor (a_comp_cor_05 ~ 09)")
        report.append("    ⚠️  Skip CSF aCompCor (insufficient coverage)")
        report.append("    → Recommended: compcor_n=5 (but use WM components)")
    elif wm_median > 0.1:
        report.append("    ✅ Use both CSF and WM aCompCor")
        report.append("    → Recommended: compcor_n=10")
    else:
        report.append("    ⚠️  Both CSF and WM coverage very low")
        report.append("    → Consider lowering threshold (e.g., prob > 0.95)")
        report.append("    → Or use mean tissue signals only")

    report.append("")
    report.append("=" * 80)

    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))

    print(f"  ✅ Summary report saved: {output_path}")

    # Also print to console
    print("\n" + '\n'.join(report))


def main():
    parser = argparse.ArgumentParser(description='Validate aCompCor quality')
    parser.add_argument('--method', type=str, default='method3_header_mi',
                        help='Preprocessing method')
    parser.add_argument('--subjects', type=str, default='01,02,03,04,05,06,07,08,09,10',
                        help='Comma-separated subject IDs')
    parser.add_argument('--runs', type=str, default='1,2,3,4,5,6',
                        help='Comma-separated run numbers')
    parser.add_argument('--output-dir', type=str, default='qc_summary',
                        help='Output directory for summary plots')

    args = parser.parse_args()

    # Parse subjects and runs
    subjects = args.subjects.split(',')
    runs = [int(r) for r in args.runs.split(',')]

    # Base directory
    base_dir = Path(f'/storage/connectome/haba6030/fmriprep_out_{args.method}')

    # Output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("aCompCor Quality Control Validation")
    print("=" * 80)
    print(f"Method: {args.method}")
    print(f"Subjects: {len(subjects)}")
    print(f"Runs per subject: {len(runs)}")
    print(f"Output: {output_dir}/")
    print()

    # 1. Load mask statistics
    print("[1/5] Loading mask statistics...")
    stats_df = load_mask_statistics(base_dir, subjects, runs)
    print(f"  ✅ Loaded {len(stats_df)} runs")
    print()

    # 2. Load variance data
    print("[2/5] Loading component variance data...")
    variance_df = load_confounds_variance(base_dir, subjects, runs)
    print(f"  ✅ Loaded {len(variance_df)} runs")
    print()

    # 3. Compute correlations
    print("[3/5] Computing inter-component correlations...")
    correlations = compute_component_correlations(base_dir, subjects, runs)
    print(f"  ✅ Computed for {len(correlations)} subjects")
    print()

    # 4. Generate plots
    print("[4/5] Generating summary plots...")
    plot_mask_coverage_summary(stats_df, output_dir / 'mask_coverage_summary.png')
    plot_variance_summary(variance_df, output_dir / 'variance_summary.png')
    plot_correlation_heatmap(correlations, output_dir / 'correlation_heatmap.png')
    print()

    # 5. Generate report
    print("[5/5] Generating summary report...")
    generate_summary_report(stats_df, variance_df, correlations,
                           output_dir / 'acompcor_qc_report.txt')
    print()

    print("=" * 80)
    print("Quality Control Complete")
    print("=" * 80)
    print(f"Outputs saved to: {output_dir}/")
    print("  - mask_coverage_summary.png")
    print("  - variance_summary.png")
    print("  - correlation_heatmap.png")
    print("  - acompcor_qc_report.txt")
    print()


if __name__ == '__main__':
    main()
