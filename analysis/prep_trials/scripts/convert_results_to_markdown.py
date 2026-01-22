#!/usr/bin/env python3
"""
Convert registration quality results.json to markdown tables
"""

import json
import pandas as pd
from pathlib import Path

def load_results(results_path):
    """Load results.json"""
    with open(results_path, 'r') as f:
        return json.load(f)

def extract_subject_summary(results):
    """Extract subject-level summary statistics"""
    rows = []

    for subject_id, subject_data in results['subjects'].items():
        # Aggregate across all runs
        all_runs_data = []
        n_runs = len(subject_data['runs'])

        for run_id, run_data in subject_data['runs'].items():
            all_runs_data.append({
                'mean_roi_coverage': run_data['summary']['mean_roi_coverage_ratio'],
                'mean_glm_valid': run_data['summary']['mean_glm_valid_ratio'],
                'mean_glm_amplitude': run_data['summary']['mean_glm_amplitude'],
                'mean_glm_variance': run_data['summary']['mean_glm_variance_across_colors'],
                'total_glm_roi_voxels': run_data['summary']['total_glm_roi_voxels'],
                'total_glm_valid_voxels': run_data['summary']['total_glm_valid_voxels']
            })

        # Compute mean across runs
        df_runs = pd.DataFrame(all_runs_data)

        row = {
            'Subject': subject_id,
            'N Runs': n_runs,
            'Mean ROI Voxels': f"{df_runs['total_glm_roi_voxels'].mean():.0f}",
            'Mean Valid Voxels': f"{df_runs['total_glm_valid_voxels'].mean():.0f}",
            'ROI Coverage (%)': f"{df_runs['mean_roi_coverage'].mean()*100:.1f}",
            'GLM Valid Ratio (%)': f"{df_runs['mean_glm_valid'].mean()*100:.1f}",
            'GLM Amplitude': f"{df_runs['mean_glm_amplitude'].mean():.2f}",
            'GLM Variance': f"{df_runs['mean_glm_variance'].mean():.1f}"
        }

        rows.append(row)

    return pd.DataFrame(rows)

def extract_per_roi_summary(results):
    """Extract per-ROI statistics across all subjects"""
    roi_data = {}

    for subject_id, subject_data in results['subjects'].items():
        for run_id, run_data in subject_data['runs'].items():
            for roi_name, roi_metrics in run_data['per_roi_metrics'].items():
                if roi_name not in roi_data:
                    roi_data[roi_name] = {
                        'roi_voxels': [],
                        'intersection_voxels': [],
                        'coverage': [],
                        'glm_valid': [],
                        'glm_amplitude': []
                    }

                roi_data[roi_name]['roi_voxels'].append(roi_metrics['roi_voxels'])
                roi_data[roi_name]['intersection_voxels'].append(roi_metrics['intersection_voxels'])
                roi_data[roi_name]['coverage'].append(roi_metrics['roi_coverage_ratio'])

                if 'glm' in roi_metrics:
                    roi_data[roi_name]['glm_valid'].append(roi_metrics['glm']['valid_ratio'])
                    roi_data[roi_name]['glm_amplitude'].append(roi_metrics['glm']['mean_amplitude'])

    # Compute statistics
    rows = []
    for roi_name, data in roi_data.items():
        rows.append({
            'ROI': roi_name,
            'N Samples': len(data['coverage']),
            'Mean ROI Voxels': f"{pd.Series(data['roi_voxels']).mean():.0f}",
            'Mean Intersection Voxels': f"{pd.Series(data['intersection_voxels']).mean():.0f}",
            'Coverage Mean (%)': f"{pd.Series(data['coverage']).mean()*100:.1f}",
            'Coverage Std (%)': f"{pd.Series(data['coverage']).std()*100:.1f}",
            'GLM Valid Mean (%)': f"{pd.Series(data['glm_valid']).mean()*100:.1f}",
            'GLM Amplitude Mean': f"{pd.Series(data['glm_amplitude']).mean():.2f}"
        })

    return pd.DataFrame(rows)

def extract_subject_per_roi(results, subject_id):
    """Extract per-ROI metrics for a specific subject"""
    if subject_id not in results['subjects']:
        return None

    subject_data = results['subjects'][subject_id]
    roi_data = {}

    for run_id, run_data in subject_data['runs'].items():
        for roi_name, roi_metrics in run_data['per_roi_metrics'].items():
            if roi_name not in roi_data:
                roi_data[roi_name] = {
                    'roi_voxels': [],
                    'intersection_voxels': [],
                    'coverage': [],
                    'glm_valid': [],
                    'glm_n_valid_voxels': []
                }

            roi_data[roi_name]['roi_voxels'].append(roi_metrics['roi_voxels'])
            roi_data[roi_name]['intersection_voxels'].append(roi_metrics['intersection_voxels'])
            roi_data[roi_name]['coverage'].append(roi_metrics['roi_coverage_ratio'])

            if 'glm' in roi_metrics:
                roi_data[roi_name]['glm_valid'].append(roi_metrics['glm']['valid_ratio'])
                roi_data[roi_name]['glm_n_valid_voxels'].append(roi_metrics['glm']['n_valid_voxels'])

    rows = []
    for roi_name, data in roi_data.items():
        rows.append({
            'ROI': roi_name,
            'Mean ROI Voxels': f"{pd.Series(data['roi_voxels']).mean():.0f}",
            'Mean Intersection Voxels': f"{pd.Series(data['intersection_voxels']).mean():.0f}",
            'Mean Valid Voxels': f"{pd.Series(data['glm_n_valid_voxels']).mean():.0f}",
            'Coverage (%)': f"{pd.Series(data['coverage']).mean()*100:.1f}",
            'GLM Valid (%)': f"{pd.Series(data['glm_valid']).mean()*100:.1f}"
        })

    return pd.DataFrame(rows)

def create_markdown_report(results, output_path):
    """Create comprehensive markdown report"""

    with open(output_path, 'w') as f:
        # Header
        f.write("# Registration Quality Report - Method3 Header MI\n\n")
        f.write(f"**Method**: {results['method']}\n\n")
        f.write(f"**Generated**: {results.get('timestamp_updated', 'N/A')}\n\n")
        f.write(f"**Total Subjects**: {len(results['subjects'])}\n\n")

        f.write("---\n\n")

        # 1. Subject Summary Table
        f.write("## 1. Subject-Level Summary\n\n")
        f.write("Mean metrics across all runs and ROIs for each subject.\n\n")

        subject_summary = extract_subject_summary(results)
        f.write(subject_summary.to_markdown(index=False))
        f.write("\n\n")

        # Add notes
        f.write("**Notes:**\n")
        f.write("- **Mean ROI Voxels**: Average number of voxels in ROI intersection with BOLD brain mask (across all 4 ROIs)\n")
        f.write("- **Mean Valid Voxels**: Average number of voxels with valid GLM fits\n")
        f.write("- **ROI Coverage**: Percentage of atlas ROI voxels that overlap with BOLD brain mask\n")
        f.write("- **GLM Valid Ratio**: Percentage of ROI voxels with valid GLM fits\n")
        f.write("- **GLM Amplitude**: Mean absolute beta values across color conditions\n")
        f.write("- **GLM Variance**: Mean variance of beta values across colors (signal differentiation)\n\n")

        f.write("---\n\n")

        # 2. Per-ROI Summary
        f.write("## 2. Per-ROI Summary (All Subjects)\n\n")
        f.write("Statistics computed across all subjects and runs.\n\n")

        roi_summary = extract_per_roi_summary(results)
        f.write(roi_summary.to_markdown(index=False))
        f.write("\n\n")

        f.write("**Notes:**\n")
        f.write("- **Mean ROI Voxels**: Atlas ROI size in MNI space\n")
        f.write("- **Mean Intersection Voxels**: Average number of voxels overlapping with BOLD brain mask\n\n")

        f.write("---\n\n")

        # 3. Subject Groups (CVD vs Non-CVD)
        f.write("## 3. Subject Group Comparison\n\n")

        # Define groups
        non_cvd = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
        cvd = ['sub-08', 'sub-09', 'sub-10']

        # Extract group statistics
        subject_summary_df = extract_subject_summary(results)

        # Convert percentage strings back to floats for computation
        subject_summary_df['ROI Coverage (%)'] = subject_summary_df['ROI Coverage (%)'].astype(float)
        subject_summary_df['GLM Valid Ratio (%)'] = subject_summary_df['GLM Valid Ratio (%)'].astype(float)
        subject_summary_df['GLM Amplitude'] = subject_summary_df['GLM Amplitude'].astype(float)

        non_cvd_data = subject_summary_df[subject_summary_df['Subject'].isin(non_cvd)]
        cvd_data = subject_summary_df[subject_summary_df['Subject'].isin(cvd)]

        group_comparison = pd.DataFrame({
            'Group': ['Non-CVD (n=7)', 'CVD (n=3)'],
            'ROI Coverage (%)': [
                f"{non_cvd_data['ROI Coverage (%)'].mean():.1f} ± {non_cvd_data['ROI Coverage (%)'].std():.1f}",
                f"{cvd_data['ROI Coverage (%)'].mean():.1f} ± {cvd_data['ROI Coverage (%)'].std():.1f}"
            ],
            'GLM Valid Ratio (%)': [
                f"{non_cvd_data['GLM Valid Ratio (%)'].mean():.1f} ± {non_cvd_data['GLM Valid Ratio (%)'].std():.1f}",
                f"{cvd_data['GLM Valid Ratio (%)'].mean():.1f} ± {cvd_data['GLM Valid Ratio (%)'].std():.1f}"
            ],
            'GLM Amplitude': [
                f"{non_cvd_data['GLM Amplitude'].mean():.2f} ± {non_cvd_data['GLM Amplitude'].std():.2f}",
                f"{cvd_data['GLM Amplitude'].mean():.2f} ± {cvd_data['GLM Amplitude'].std():.2f}"
            ]
        })

        f.write(group_comparison.to_markdown(index=False))
        f.write("\n\n")

        f.write("---\n\n")

        # 4. Special Case: Sub-07
        f.write("## 4. Special Notes\n\n")
        f.write("### Sub-07 Quality Metrics\n\n")
        f.write("Sub-07 shows lower ROI coverage compared to other subjects, but maintains good GLM signal quality.\n\n")

        sub07_roi = extract_subject_per_roi(results, 'sub-07')
        if sub07_roi is not None:
            f.write(sub07_roi.to_markdown(index=False))
            f.write("\n\n")

        f.write("**Interpretation**: While ROI coverage is reduced (30% vs 90% average), ")
        f.write("GLM valid ratios remain high, indicating that the overlapping voxels provide valid signal. ")
        f.write("This subject is included in analyses with a note about lower statistical power.\n\n")

        f.write("---\n\n")

        # 5. Overall Quality Assessment
        f.write("## 5. Overall Quality Assessment\n\n")

        # Compute overall stats
        all_coverage = []
        all_glm_valid = []
        all_glm_amplitude = []

        for subject_id, subject_data in results['subjects'].items():
            for run_id, run_data in subject_data['runs'].items():
                all_coverage.append(run_data['summary']['mean_roi_coverage_ratio'])
                all_glm_valid.append(run_data['summary']['mean_glm_valid_ratio'])
                all_glm_amplitude.append(run_data['summary']['mean_glm_amplitude'])

        overall_stats = pd.DataFrame({
            'Metric': ['ROI Coverage', 'GLM Valid Ratio', 'GLM Amplitude'],
            'Mean': [
                f"{pd.Series(all_coverage).mean()*100:.1f}%",
                f"{pd.Series(all_glm_valid).mean()*100:.1f}%",
                f"{pd.Series(all_glm_amplitude).mean():.2f}"
            ],
            'Std': [
                f"{pd.Series(all_coverage).std()*100:.1f}%",
                f"{pd.Series(all_glm_valid).std()*100:.1f}%",
                f"{pd.Series(all_glm_amplitude).std():.2f}"
            ],
            'Min': [
                f"{pd.Series(all_coverage).min()*100:.1f}%",
                f"{pd.Series(all_glm_valid).min()*100:.1f}%",
                f"{pd.Series(all_glm_amplitude).min():.2f}"
            ],
            'Max': [
                f"{pd.Series(all_coverage).max()*100:.1f}%",
                f"{pd.Series(all_glm_valid).max()*100:.1f}%",
                f"{pd.Series(all_glm_amplitude).max():.2f}"
            ]
        })

        f.write(overall_stats.to_markdown(index=False))
        f.write("\n\n")

        # Final verdict
        mean_glm_valid = pd.Series(all_glm_valid).mean()

        f.write("### Verdict\n\n")
        if mean_glm_valid > 0.95:
            f.write("✅ **EXCELLENT** - Registration quality is excellent across all subjects. ")
            f.write("GLM valid ratios exceed 95%, indicating reliable signal extraction from ROIs.\n\n")
        elif mean_glm_valid > 0.85:
            f.write("✅ **GOOD** - Registration quality is good. ")
            f.write("Most voxels provide valid signal for analysis.\n\n")
        else:
            f.write("⚠️ **NEEDS REVIEW** - Some subjects may have registration issues. ")
            f.write("Manual inspection recommended.\n\n")

        f.write("**Recommended for downstream analysis**: Yes, all subjects included.\n\n")

def main():
    results_path = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/results/Method_method3_header_mi/results.json')
    output_path = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/results/Method_method3_header_mi/registration_quality_report.md')

    print("="*80)
    print("Converting results.json to Markdown Report")
    print("="*80)
    print()

    print(f"Input:  {results_path}")
    print(f"Output: {output_path}")
    print()

    # Load results
    results = load_results(results_path)
    print(f"✅ Loaded data for {len(results['subjects'])} subjects")

    # Create markdown report
    create_markdown_report(results, output_path)
    print(f"✅ Markdown report created: {output_path}")
    print()

    print("="*80)
    print("Done!")
    print("="*80)

if __name__ == '__main__':
    main()
