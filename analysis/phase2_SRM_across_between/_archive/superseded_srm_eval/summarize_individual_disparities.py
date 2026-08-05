#!/usr/bin/env python3
"""
Summarize Individual Subject Disparities from SRM Analysis

Extracts and organizes per-subject disparity values from SRM results,
with focus on CVD subjects (sub-08, 09, 10).

Author: Claude Code
Date: 2026-02-10
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np

# Paths
RESULTS_BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/SRM/results/c010/separated")
OUTPUT_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/SRM/results/c010")

# ROIs and timestamps (latest results)
ROI_RESULTS = {
    'V1': '20260209_131717',
    'V2': '20260209_131551',
    'V3': '20260209_131719',
    'V4': '20260209_131720'
}

# Subject IDs
HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']


def load_srm_results(roi: str, timestamp: str, method: str = 'procrustes') -> dict:
    """Load SRM results JSON file"""
    result_file = RESULTS_BASE / timestamp / f"{roi}_{method}_srm_results.json"

    if not result_file.exists():
        print(f"  ⚠️  File not found: {result_file}")
        return None

    with open(result_file, 'r') as f:
        return json.load(f)


def extract_disparities_table(method='procrustes'):
    """
    Extract disparity values for all subjects across all ROIs

    Returns:
        DataFrame with subjects as rows, ROIs as columns
    """

    print(f"\n{'='*80}")
    print(f"Extracting Individual Disparities - {method.upper()} Method")
    print(f"{'='*80}\n")

    # Storage for all data
    disparity_data = []

    for roi, timestamp in ROI_RESULTS.items():
        print(f"Processing {roi}...")

        results = load_srm_results(roi, timestamp, method)

        if results is None:
            continue

        # Extract HC disparities
        hc_disparities = results['results']['disparities']['hc_to_hc_reference']['values']
        hc_subjects = results['subjects']['hc']

        for subject_id, disparity in zip(hc_subjects, hc_disparities):
            disparity_data.append({
                'subject_id': subject_id,
                'subject_num': subject_id.replace('sub-', ''),
                'group': 'HC',
                'roi': roi,
                'disparity': disparity,
                'reference': 'HC_mean'
            })

        # Extract CVD disparities
        cvd_disparities = results['results']['disparities']['cvd_to_hc_reference']['values']
        cvd_subjects = results['subjects']['cvd']

        for subject_id, disparity in zip(cvd_subjects, cvd_disparities):
            disparity_data.append({
                'subject_id': subject_id,
                'subject_num': subject_id.replace('sub-', ''),
                'group': 'CVD',
                'roi': roi,
                'disparity': disparity,
                'reference': 'HC_mean'
            })

    # Create DataFrame
    df = pd.DataFrame(disparity_data)

    return df


def create_summary_tables(df):
    """Create various summary tables"""

    tables = {}

    # 1. Wide format: Subjects x ROIs
    df_wide = df.pivot_table(
        index=['subject_num', 'subject_id', 'group'],
        columns='roi',
        values='disparity'
    ).reset_index()

    # Reorder columns
    roi_cols = ['V1', 'V2', 'V3', 'V4']
    df_wide = df_wide[['subject_num', 'subject_id', 'group'] + roi_cols]

    # Sort by subject number
    df_wide['subject_num_int'] = df_wide['subject_num'].astype(int)
    df_wide = df_wide.sort_values('subject_num_int').drop('subject_num_int', axis=1)

    tables['subjects_by_rois'] = df_wide

    # 2. CVD-specific table (focus on CVD subjects)
    df_cvd = df_wide[df_wide['group'] == 'CVD'].copy()
    tables['cvd_subjects'] = df_cvd

    # 3. Summary statistics by group and ROI
    df_summary = df.groupby(['group', 'roi'])['disparity'].agg(['mean', 'std', 'min', 'max']).reset_index()
    df_summary_wide = df_summary.pivot_table(
        index='group',
        columns='roi',
        values=['mean', 'std']
    )
    tables['group_summary'] = df_summary_wide

    # 4. Per-subject average across ROIs
    df_subject_avg = df.groupby(['subject_num', 'subject_id', 'group'])['disparity'].mean().reset_index()
    df_subject_avg.columns = ['subject_num', 'subject_id', 'group', 'mean_disparity_across_rois']
    df_subject_avg['subject_num_int'] = df_subject_avg['subject_num'].astype(int)
    df_subject_avg = df_subject_avg.sort_values('subject_num_int').drop('subject_num_int', axis=1)
    tables['subject_averages'] = df_subject_avg

    return tables


def print_summary_report(tables):
    """Print formatted summary report"""

    print(f"\n{'='*80}")
    print("INDIVIDUAL DISPARITY SUMMARY REPORT")
    print(f"{'='*80}\n")

    # Table 1: All subjects x ROIs
    print("Table 1: Disparity by Subject and ROI (to HC reference)")
    print("-" * 80)
    df_display = tables['subjects_by_rois'].copy()
    print(df_display.to_string(index=False, float_format=lambda x: f'{x:.4f}'))
    print("")

    # Table 2: CVD subjects only
    print("\nTable 2: CVD Subjects - Detailed View")
    print("-" * 80)
    df_cvd = tables['cvd_subjects'].copy()
    print(df_cvd.to_string(index=False, float_format=lambda x: f'{x:.4f}'))
    print("")

    # Print CVD ranking per ROI
    print("\nCVD Subject Rankings by ROI (lowest disparity = most similar to HC):")
    print("-" * 80)
    for roi in ['V1', 'V2', 'V3', 'V4']:
        print(f"\n  {roi}:")
        cvd_roi = df_cvd.sort_values(roi)[['subject_id', roi]]
        for idx, row in cvd_roi.iterrows():
            print(f"    {row['subject_id']}: {row[roi]:.4f}")

    # Table 3: Group averages
    print("\n\nTable 3: Group Statistics by ROI")
    print("-" * 80)
    print(tables['group_summary'].to_string(float_format=lambda x: f'{x:.4f}'))
    print("")

    # Table 4: Per-subject averages
    print("\n\nTable 4: Average Disparity Across All ROIs (per subject)")
    print("-" * 80)
    df_avg = tables['subject_averages']
    print(df_avg.to_string(index=False, float_format=lambda x: f'{x:.4f}'))
    print("")

    # CVD-specific insights
    print("\n" + "="*80)
    print("CVD-SPECIFIC INSIGHTS")
    print("="*80)

    df_cvd_avg = df_avg[df_avg['group'] == 'CVD'].copy()
    df_cvd_avg = df_cvd_avg.sort_values('mean_disparity_across_rois')

    print("\nCVD subjects ranked by average disparity (across all ROIs):")
    for idx, row in df_cvd_avg.iterrows():
        print(f"  {row['subject_id']}: {row['mean_disparity_across_rois']:.4f}")

    # HC baseline for comparison
    hc_mean = df_avg[df_avg['group'] == 'HC']['mean_disparity_across_rois'].mean()
    print(f"\nHC baseline (mean across HC subjects): {hc_mean:.4f}")

    print("\nExcess disparity (CVD - HC baseline):")
    for idx, row in df_cvd_avg.iterrows():
        excess = row['mean_disparity_across_rois'] - hc_mean
        pct = (excess / hc_mean) * 100
        print(f"  {row['subject_id']}: +{excess:.4f} (+{pct:.1f}%)")


def save_results(tables, df_long):
    """Save results to CSV files"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save all tables
    tables['subjects_by_rois'].to_csv(OUTPUT_DIR / 'individual_disparities_wide.csv', index=False)
    print(f"\n✓ Saved: {OUTPUT_DIR / 'individual_disparities_wide.csv'}")

    tables['cvd_subjects'].to_csv(OUTPUT_DIR / 'cvd_disparities_wide.csv', index=False)
    print(f"✓ Saved: {OUTPUT_DIR / 'cvd_disparities_wide.csv'}")

    tables['subject_averages'].to_csv(OUTPUT_DIR / 'subject_average_disparities.csv', index=False)
    print(f"✓ Saved: {OUTPUT_DIR / 'subject_average_disparities.csv'}")

    # Save long format (for plotting)
    df_long.to_csv(OUTPUT_DIR / 'individual_disparities_long.csv', index=False)
    print(f"✓ Saved: {OUTPUT_DIR / 'individual_disparities_long.csv'}")

    # Save group summary
    tables['group_summary'].to_csv(OUTPUT_DIR / 'group_summary_by_roi.csv')
    print(f"✓ Saved: {OUTPUT_DIR / 'group_summary_by_roi.csv'}")


def main():
    """Main execution"""

    print(f"\n{'='*80}")
    print("Individual Subject Disparity Analysis")
    print(f"{'='*80}\n")
    print("Data source: SRM Between-Subject Analysis (Procrustes method)")
    print(f"ROIs: {list(ROI_RESULTS.keys())}")
    print(f"HC subjects (n={len(HC_SUBJECTS)}): {', '.join([f'sub-{s}' for s in HC_SUBJECTS])}")
    print(f"CVD subjects (n={len(CVD_SUBJECTS)}): {', '.join([f'sub-{s}' for s in CVD_SUBJECTS])}")

    # Extract data
    df_long = extract_disparities_table(method='procrustes')

    if df_long is None or len(df_long) == 0:
        print("\n❌ No data extracted. Check file paths.")
        return

    print(f"\n✓ Extracted {len(df_long)} disparity values")

    # Create summary tables
    tables = create_summary_tables(df_long)

    # Print report
    print_summary_report(tables)

    # Save results
    save_results(tables, df_long)

    print(f"\n{'='*80}")
    print("✅ Analysis complete!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
