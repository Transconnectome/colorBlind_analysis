#!/usr/bin/env python3
"""
Deep analysis of ROI pipeline results
Compare all parameter combinations and identify optimal settings
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 150


class ROIResultsAnalyzer:
    """Analyze and compare ROI pipeline results"""

    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.results_csv = self.results_dir / 'results_summary.csv'
        self.results_json = self.results_dir / 'results_full.json'

        # Load results
        self.df = pd.read_csv(self.results_csv)
        with open(self.results_json, 'r') as f:
            self.results_full = json.load(f)

        print(f"Loaded {len(self.df)} results from {results_dir}")

        # Create analysis output directory
        self.analysis_dir = self.results_dir / 'detailed_analysis'
        self.analysis_dir.mkdir(exist_ok=True)

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*70)
        print("ROI PIPELINE RESULTS SUMMARY")
        print("="*70)

        print(f"\nTotal configurations tested: {len(self.df)}")
        print(f"ROIs analyzed: {self.df['roi_name'].unique().tolist()}")
        print(f"Thresholds tested: {sorted(self.df['threshold'].unique())}")
        print(f"Interpolation methods: {self.df['interpolation'].unique().tolist()}")
        print(f"Binarize options: {self.df['binarize_after_resample'].unique().tolist()}")

        print("\n" + "-"*70)
        print("VOXEL COUNT STATISTICS BY ROI")
        print("-"*70)

        for roi_name in self.df['roi_name'].unique():
            roi_df = self.df[self.df['roi_name'] == roi_name]
            print(f"\n{roi_name}:")
            print(f"  Min voxels:  {roi_df['n_voxels'].min():6d}")
            print(f"  Max voxels:  {roi_df['n_voxels'].max():6d}")
            print(f"  Mean voxels: {roi_df['n_voxels'].mean():6.1f}")
            print(f"  Std voxels:  {roi_df['n_voxels'].std():6.1f}")

    def plot_voxel_heatmaps(self):
        """Create heatmaps of voxel counts for each parameter combination"""
        rois = self.df['roi_name'].unique()
        n_rois = len(rois)

        fig, axes = plt.subplots(2, 2, figsize=(16, 14))
        axes = axes.flatten()

        for idx, roi_name in enumerate(rois):
            ax = axes[idx]
            roi_df = self.df[self.df['roi_name'] == roi_name]

            # Create pivot table for heatmap
            for binarize in [True, False]:
                for interp in ['nearest', 'linear']:
                    subset = roi_df[
                        (roi_df['binarize_after_resample'] == binarize) &
                        (roi_df['interpolation'] == interp)
                    ]

                    if len(subset) > 0:
                        label = f"{interp}, bin={binarize}"
                        thresholds = subset['threshold'].values
                        voxels = subset['n_voxels'].values

                        # Plot line
                        ax.plot(thresholds, voxels, marker='o', label=label, linewidth=2)

            ax.set_xlabel('Probability Threshold', fontsize=12)
            ax.set_ylabel('Number of Voxels', fontsize=12)
            ax.set_title(f'{roi_name} - Voxel Count vs Threshold', fontsize=14, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        save_path = self.analysis_dir / 'voxel_count_heatmaps.png'
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"\nVoxel count heatmaps saved to: {save_path}")
        plt.close(fig)
        plt.clf()

    def plot_parameter_effects(self):
        """Analyze effect of each parameter on voxel count"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Effect of threshold (averaged across other params)
        ax = axes[0, 0]
        for roi_name in self.df['roi_name'].unique():
            roi_df = self.df[self.df['roi_name'] == roi_name]
            grouped = roi_df.groupby('threshold')['n_voxels'].mean()
            ax.plot(grouped.index, grouped.values, marker='o', label=roi_name, linewidth=2)

        ax.set_xlabel('Threshold', fontsize=12)
        ax.set_ylabel('Mean Voxel Count', fontsize=12)
        ax.set_title('Effect of Threshold (averaged over other params)', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Effect of interpolation
        ax = axes[0, 1]
        interp_data = []
        for roi_name in self.df['roi_name'].unique():
            roi_df = self.df[self.df['roi_name'] == roi_name]
            for interp in self.df['interpolation'].unique():
                subset = roi_df[roi_df['interpolation'] == interp]
                interp_data.append({
                    'ROI': roi_name,
                    'Interpolation': interp,
                    'Mean Voxels': subset['n_voxels'].mean()
                })

        interp_df = pd.DataFrame(interp_data)
        pivot = interp_df.pivot(index='ROI', columns='Interpolation', values='Mean Voxels')
        pivot.plot(kind='bar', ax=ax, width=0.7)
        ax.set_xlabel('ROI', fontsize=12)
        ax.set_ylabel('Mean Voxel Count', fontsize=12)
        ax.set_title('Effect of Interpolation Method', fontsize=14, fontweight='bold')
        ax.legend(title='Interpolation')
        ax.grid(True, alpha=0.3, axis='y')

        # 3. Effect of binarization
        ax = axes[1, 0]
        bin_data = []
        for roi_name in self.df['roi_name'].unique():
            roi_df = self.df[self.df['roi_name'] == roi_name]
            for binarize in self.df['binarize_after_resample'].unique():
                subset = roi_df[roi_df['binarize_after_resample'] == binarize]
                bin_data.append({
                    'ROI': roi_name,
                    'Binarize': 'Yes' if binarize else 'No',
                    'Mean Voxels': subset['n_voxels'].mean()
                })

        bin_df = pd.DataFrame(bin_data)
        pivot = bin_df.pivot(index='ROI', columns='Binarize', values='Mean Voxels')
        pivot.plot(kind='bar', ax=ax, width=0.7)
        ax.set_xlabel('ROI', fontsize=12)
        ax.set_ylabel('Mean Voxel Count', fontsize=12)
        ax.set_title('Effect of Binarization After Resampling', fontsize=14, fontweight='bold')
        ax.legend(title='Binarize')
        ax.grid(True, alpha=0.3, axis='y')

        # 4. Coefficient of variation (variability) across parameters
        ax = axes[1, 1]
        cv_data = []
        for roi_name in self.df['roi_name'].unique():
            roi_df = self.df[self.df['roi_name'] == roi_name]
            cv = (roi_df['n_voxels'].std() / roi_df['n_voxels'].mean()) * 100
            cv_data.append({'ROI': roi_name, 'CV (%)': cv})

        cv_df = pd.DataFrame(cv_data)
        ax.bar(cv_df['ROI'], cv_df['CV (%)'], color='steelblue', edgecolor='black', linewidth=1.5)
        ax.set_xlabel('ROI', fontsize=12)
        ax.set_ylabel('Coefficient of Variation (%)', fontsize=12)
        ax.set_title('Parameter Sensitivity (CV across all configs)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        save_path = self.analysis_dir / 'parameter_effects.png'
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"Parameter effects plot saved to: {save_path}")
        plt.close(fig)
        plt.clf()

    def identify_optimal_configs(self):
        """Identify optimal configurations based on different criteria"""
        print("\n" + "="*70)
        print("OPTIMAL CONFIGURATIONS")
        print("="*70)

        optimal_configs = []

        for roi_name in self.df['roi_name'].unique():
            roi_df = self.df[self.df['roi_name'] == roi_name]

            # Criterion 1: Maximum voxels
            max_voxels_row = roi_df.loc[roi_df['n_voxels'].idxmax()]

            # Criterion 2: Median voxels (most stable)
            median_voxels = roi_df['n_voxels'].median()
            median_row = roi_df.iloc[(roi_df['n_voxels'] - median_voxels).abs().argsort()[:1]]

            # Criterion 3: Maximum coverage
            max_coverage_row = roi_df.loc[roi_df['coverage_pct'].idxmax()]

            print(f"\n{roi_name}:")
            print(f"  Maximum Voxels Configuration:")
            print(f"    Threshold: {max_voxels_row['threshold']}")
            print(f"    Interpolation: {max_voxels_row['interpolation']}")
            print(f"    Binarize: {max_voxels_row['binarize_after_resample']}")
            print(f"    Voxels: {max_voxels_row['n_voxels']}")

            optimal_configs.append({
                'roi_name': roi_name,
                'criterion': 'max_voxels',
                'threshold': max_voxels_row['threshold'],
                'interpolation': max_voxels_row['interpolation'],
                'binarize_after_resample': max_voxels_row['binarize_after_resample'],
                'n_voxels': max_voxels_row['n_voxels'],
                'mask_path': max_voxels_row['mask_path']
            })

        # Save optimal configs
        optimal_df = pd.DataFrame(optimal_configs)
        optimal_path = self.analysis_dir / 'optimal_configurations.csv'
        optimal_df.to_csv(optimal_path, index=False)
        print(f"\nOptimal configurations saved to: {optimal_path}")

        return optimal_df

    def create_comparison_table(self):
        """Create detailed comparison table in markdown"""
        md_path = self.analysis_dir / 'DETAILED_COMPARISON.md'

        with open(md_path, 'w') as f:
            f.write("# Detailed ROI Pipeline Results Comparison\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Results Directory:** `{self.results_dir}`\n\n")

            # Overall statistics
            f.write("## Overall Statistics\n\n")
            f.write(f"- Total configurations: {len(self.df)}\n")
            f.write(f"- ROIs analyzed: {', '.join(self.df['roi_name'].unique())}\n\n")

            # Detailed table for each ROI
            for roi_name in sorted(self.df['roi_name'].unique()):
                roi_df = self.df[self.df['roi_name'] == roi_name].copy()
                roi_df = roi_df.sort_values('n_voxels', ascending=False)

                f.write(f"## {roi_name}\n\n")

                f.write("### All Configurations (sorted by voxel count)\n\n")
                f.write("| Rank | Threshold | Interpolation | Binarize | Voxels | Coverage % | Shape Match | Affine Match |\n")
                f.write("|------|-----------|---------------|----------|--------|------------|-------------|-------------|\n")

                for rank, (_, row) in enumerate(roi_df.iterrows(), 1):
                    f.write(f"| {rank} | {row['threshold']:.2f} | {row['interpolation']} | "
                           f"{row['binarize_after_resample']} | {row['n_voxels']} | "
                           f"{row['coverage_pct']:.4f} | {row['shape_match']} | "
                           f"{row['affine_match']} |\n")

                f.write("\n")

                # Statistics
                f.write("### Statistics\n\n")
                f.write(f"- **Range:** {roi_df['n_voxels'].min()} - {roi_df['n_voxels'].max()} voxels\n")
                f.write(f"- **Mean:** {roi_df['n_voxels'].mean():.1f} voxels\n")
                f.write(f"- **Median:** {roi_df['n_voxels'].median():.1f} voxels\n")
                f.write(f"- **Std Dev:** {roi_df['n_voxels'].std():.1f} voxels\n")
                f.write(f"- **CV:** {(roi_df['n_voxels'].std() / roi_df['n_voxels'].mean() * 100):.1f}%\n\n")

        print(f"Detailed comparison table saved to: {md_path}")

    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("\n" + "#"*70)
        print("# ROI RESULTS DEEP ANALYSIS")
        print("#"*70)

        # Print summary
        self.print_summary()

        # Create visualizations
        print("\nGenerating visualizations...")
        self.plot_voxel_heatmaps()
        self.plot_parameter_effects()

        # Identify optimal configs
        optimal_df = self.identify_optimal_configs()

        # Create comparison table
        self.create_comparison_table()

        print("\n" + "#"*70)
        print("# ANALYSIS COMPLETE")
        print(f"# All outputs saved to: {self.analysis_dir}")
        print("#"*70 + "\n")

        return optimal_df


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_roi_results.py <results_directory>")
        print("\nExample:")
        print("  python analyze_roi_results.py derivatives/sub-P01/roi_pipeline_20241110_143022")
        sys.exit(1)

    results_dir = sys.argv[1]

    if not Path(results_dir).exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    # Run analysis
    analyzer = ROIResultsAnalyzer(results_dir)
    optimal_configs = analyzer.run_full_analysis()

    print("\nRecommended next steps:")
    print("1. Review the visualizations in the detailed_analysis/ directory")
    print("2. Check the optimal_configurations.csv for best parameter settings")
    print("3. Examine the DETAILED_COMPARISON.md for full results table")


if __name__ == '__main__':
    main()
