"""
Analyze and compare results from zscore and voxelSelect methods
Date: 2025-11-17
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

# Define directories
base_dir = Path("logs")
zscore_dir = base_dir / "20251117_021334"
voxelselect_dir = base_dir / "20251117_021329"

# Define subjects and ROIs
subjects = ["sub-01", "sub-02", "sub-03", "sub-04"]
rois = ["V1", "V2", "V3", "hV4"]

# Subject groups
non_cvd_subjects = ["sub-01", "sub-02"]
cvd_subjects = ["sub-03", "sub-04"]

def collect_all_results():
    """Collect all summary.csv results from both methods"""
    all_results = []

    # Collect zscore results
    for subject in subjects:
        for roi in rois:
            csv_path = zscore_dir / subject / "fir_reconstruction_uni_hrf" / "zScore" / f"{roi}_universal_hrf" / "summary.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                df['Subject'] = subject
                df['Analysis_method'] = 'zscore'
                all_results.append(df)
            else:
                print(f"Missing: {csv_path}")

    # Collect voxelSelect results
    for subject in subjects:
        for roi in rois:
            csv_path = voxelselect_dir / subject / "fir_reconstruction_uni_hrf" / "voxelSelect" / f"{roi}_universal_hrf" / "summary.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                df['Subject'] = subject
                df['Analysis_method'] = 'voxelSelect'
                all_results.append(df)
            else:
                print(f"Missing: {csv_path}")

    # Combine all results
    combined_df = pd.concat(all_results, ignore_index=True)

    # Add subject group
    combined_df['Group'] = combined_df['Subject'].apply(
        lambda x: 'Non-CVD' if x in non_cvd_subjects else 'CVD'
    )

    return combined_df

def create_comparison_tables(df):
    """Create comprehensive comparison tables"""

    print("\n" + "="*80)
    print("COMPREHENSIVE RESULTS SUMMARY")
    print("="*80)

    # 1. By Subject, ROI, and Method
    print("\n1. RESULTS BY SUBJECT, ROI, AND METHOD")
    print("-"*80)
    pivot_table = df.pivot_table(
        index=['Subject', 'ROI', 'Analysis_method'],
        values=['N_voxels', 'Classification_accuracy',
                'Reconstruction_error_deg', 'Novel_color_error_deg'],
        aggfunc='first'
    )
    print(pivot_table.to_string())

    # 2. Average by Method and ROI
    print("\n\n2. AVERAGE BY METHOD AND ROI")
    print("-"*80)
    method_roi_avg = df.groupby(['Analysis_method', 'ROI'])[
        ['N_voxels', 'Classification_accuracy',
         'Reconstruction_error_deg', 'Novel_color_error_deg']
    ].mean()
    print(method_roi_avg.to_string())

    # 3. Average by Group (CVD vs Non-CVD)
    print("\n\n3. AVERAGE BY GROUP (Non-CVD vs CVD)")
    print("-"*80)
    group_avg = df.groupby(['Group', 'Analysis_method', 'ROI'])[
        ['N_voxels', 'Classification_accuracy',
         'Reconstruction_error_deg', 'Novel_color_error_deg']
    ].mean()
    print(group_avg.to_string())

    # 4. Overall statistics by Method
    print("\n\n4. OVERALL STATISTICS BY METHOD")
    print("-"*80)
    method_stats = df.groupby('Analysis_method')[
        ['N_voxels', 'Classification_accuracy',
         'Reconstruction_error_deg', 'Novel_color_error_deg']
    ].agg(['mean', 'std', 'min', 'max'])
    print(method_stats.to_string())

    # 5. Group comparison (Non-CVD vs CVD) by Method
    print("\n\n5. GROUP COMPARISON (Non-CVD vs CVD) BY METHOD")
    print("-"*80)
    for method in df['Analysis_method'].unique():
        print(f"\n{method.upper()}:")
        method_data = df[df['Analysis_method'] == method]
        group_comparison = method_data.groupby('Group')[
            ['Classification_accuracy', 'Reconstruction_error_deg',
             'Novel_color_error_deg']
        ].agg(['mean', 'std'])
        print(group_comparison.to_string())

    # 6. Best performing configurations
    print("\n\n6. BEST PERFORMING CONFIGURATIONS")
    print("-"*80)
    print("\nBest Classification Accuracy:")
    best_class = df.nlargest(5, 'Classification_accuracy')[
        ['Subject', 'ROI', 'Analysis_method', 'Classification_accuracy',
         'Reconstruction_error_deg', 'Novel_color_error_deg']
    ]
    print(best_class.to_string(index=False))

    print("\nLowest Reconstruction Error:")
    best_recon = df.nsmallest(5, 'Reconstruction_error_deg')[
        ['Subject', 'ROI', 'Analysis_method', 'Classification_accuracy',
         'Reconstruction_error_deg', 'Novel_color_error_deg']
    ]
    print(best_recon.to_string(index=False))

    print("\nLowest Novel Color Error:")
    best_novel = df.nsmallest(5, 'Novel_color_error_deg')[
        ['Subject', 'ROI', 'Analysis_method', 'Classification_accuracy',
         'Reconstruction_error_deg', 'Novel_color_error_deg']
    ]
    print(best_novel.to_string(index=False))

    return pivot_table, method_roi_avg, group_avg

def create_visualizations(df):
    """Create comprehensive visualizations"""

    fig = plt.figure(figsize=(20, 24))

    # 1. Classification Accuracy by ROI and Method
    ax1 = plt.subplot(4, 3, 1)
    sns.barplot(data=df, x='ROI', y='Classification_accuracy',
                hue='Analysis_method', ax=ax1)
    ax1.set_title('Classification Accuracy by ROI and Method', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Accuracy')
    ax1.set_ylim([0, 1.05])

    # 2. Classification Accuracy by Subject and Method
    ax2 = plt.subplot(4, 3, 2)
    sns.barplot(data=df, x='Subject', y='Classification_accuracy',
                hue='Analysis_method', ax=ax2)
    ax2.set_title('Classification Accuracy by Subject and Method', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Accuracy')
    ax2.set_ylim([0, 1.05])

    # 3. Classification Accuracy: Non-CVD vs CVD
    ax3 = plt.subplot(4, 3, 3)
    sns.barplot(data=df, x='Group', y='Classification_accuracy',
                hue='Analysis_method', ax=ax3)
    ax3.set_title('Classification Accuracy: Non-CVD vs CVD', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Accuracy')
    ax3.set_ylim([0, 1.05])

    # 4. Reconstruction Error by ROI and Method
    ax4 = plt.subplot(4, 3, 4)
    sns.barplot(data=df, x='ROI', y='Reconstruction_error_deg',
                hue='Analysis_method', ax=ax4)
    ax4.set_title('Reconstruction Error by ROI and Method', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Error (degrees)')

    # 5. Reconstruction Error by Subject and Method
    ax5 = plt.subplot(4, 3, 5)
    sns.barplot(data=df, x='Subject', y='Reconstruction_error_deg',
                hue='Analysis_method', ax=ax5)
    ax5.set_title('Reconstruction Error by Subject and Method', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Error (degrees)')

    # 6. Reconstruction Error: Non-CVD vs CVD
    ax6 = plt.subplot(4, 3, 6)
    sns.barplot(data=df, x='Group', y='Reconstruction_error_deg',
                hue='Analysis_method', ax=ax6)
    ax6.set_title('Reconstruction Error: Non-CVD vs CVD', fontsize=12, fontweight='bold')
    ax6.set_ylabel('Error (degrees)')

    # 7. Novel Color Error by ROI and Method
    ax7 = plt.subplot(4, 3, 7)
    sns.barplot(data=df, x='ROI', y='Novel_color_error_deg',
                hue='Analysis_method', ax=ax7)
    ax7.set_title('Novel Color Error by ROI and Method', fontsize=12, fontweight='bold')
    ax7.set_ylabel('Error (degrees)')

    # 8. Novel Color Error by Subject and Method
    ax8 = plt.subplot(4, 3, 8)
    sns.barplot(data=df, x='Subject', y='Novel_color_error_deg',
                hue='Analysis_method', ax=ax8)
    ax8.set_title('Novel Color Error by Subject and Method', fontsize=12, fontweight='bold')
    ax8.set_ylabel('Error (degrees)')

    # 9. Novel Color Error: Non-CVD vs CVD
    ax9 = plt.subplot(4, 3, 9)
    sns.barplot(data=df, x='Group', y='Novel_color_error_deg',
                hue='Analysis_method', ax=ax9)
    ax9.set_title('Novel Color Error: Non-CVD vs CVD', fontsize=12, fontweight='bold')
    ax9.set_ylabel('Error (degrees)')

    # 10. N_voxels by ROI and Method
    ax10 = plt.subplot(4, 3, 10)
    sns.barplot(data=df, x='ROI', y='N_voxels',
                hue='Analysis_method', ax=ax10)
    ax10.set_title('Number of Voxels by ROI and Method', fontsize=12, fontweight='bold')
    ax10.set_ylabel('N voxels')
    ax10.set_yscale('log')

    # 11. Scatter: Reconstruction vs Novel Color Error
    ax11 = plt.subplot(4, 3, 11)
    for method in df['Analysis_method'].unique():
        method_data = df[df['Analysis_method'] == method]
        ax11.scatter(method_data['Reconstruction_error_deg'],
                    method_data['Novel_color_error_deg'],
                    label=method, alpha=0.6, s=100)
    ax11.set_xlabel('Reconstruction Error (deg)')
    ax11.set_ylabel('Novel Color Error (deg)')
    ax11.set_title('Reconstruction vs Novel Color Error', fontsize=12, fontweight='bold')
    ax11.legend()
    ax11.grid(True, alpha=0.3)

    # 12. Heatmap: Average performance by ROI and Group
    ax12 = plt.subplot(4, 3, 12)
    heatmap_data = df.groupby(['ROI', 'Group'])['Reconstruction_error_deg'].mean().unstack()
    sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='RdYlGn_r', ax=ax12)
    ax12.set_title('Average Reconstruction Error by ROI and Group', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig('analysis_comparison_20251117.png', dpi=300, bbox_inches='tight')
    print("\nVisualization saved to: analysis_comparison_20251117.png")

    return fig

def main():
    """Main analysis function"""

    print("Collecting all results...")
    df = collect_all_results()

    # Save combined results
    df.to_csv('combined_results_20251117.csv', index=False)
    print(f"\nCombined results saved to: combined_results_20251117.csv")
    print(f"Total records: {len(df)}")

    # Create comparison tables
    pivot_table, method_roi_avg, group_avg = create_comparison_tables(df)

    # Save detailed tables
    pivot_table.to_csv('detailed_results_by_subject_20251117.csv')
    method_roi_avg.to_csv('average_by_method_roi_20251117.csv')
    group_avg.to_csv('average_by_group_20251117.csv')

    # Create visualizations
    fig = create_visualizations(df)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nGenerated files:")
    print("  - combined_results_20251117.csv")
    print("  - detailed_results_by_subject_20251117.csv")
    print("  - average_by_method_roi_20251117.csv")
    print("  - average_by_group_20251117.csv")
    print("  - analysis_comparison_20251117.png")

    return df

if __name__ == "__main__":
    df = main()
    plt.show()
