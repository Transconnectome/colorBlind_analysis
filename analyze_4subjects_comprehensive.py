#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_4subjects_comprehensive.py
-----------------------------------
Comprehensive analysis across 4 test subjects (01-04):
1. Temporal dynamics (optimal delay consistency)
2. PCA optimization (component analysis)
3. Z-score statistics (ROI consistency)

Usage:
    python analyze_4subjects_comprehensive.py
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# Configuration
# ============================================================================

SUBJECTS = ['01', '02', '03', '04']
ROIS = ['V1', 'V2', 'V3', 'hV4']

LOG_BASE = Path('logs')

# ============================================================================
# 1. Load Summary Data
# ============================================================================

print("="*70)
print("COMPREHENSIVE ANALYSIS: 4 TEST SUBJECTS (01-04)")
print("="*70)
print()

# Load all subjects summary
summary_csv = LOG_BASE / 'all_subjects_summary' / 'all_subjects_summary.csv'
if summary_csv.exists():
    df_summary = pd.read_csv(summary_csv)
    print(f"✓ Loaded summary data: {summary_csv}")
    print(f"  Subjects: {df_summary['Subject'].unique()}")
    print(f"  ROIs: {df_summary['ROI'].unique()}")
else:
    print(f"✗ Summary file not found: {summary_csv}")
    df_summary = None

print()

# ============================================================================
# 2. Temporal Dynamics Analysis (Optimal Delay Consistency)
# ============================================================================

print("="*70)
print("1. TEMPORAL DYNAMICS: Optimal Delay Consistency")
print("="*70)
print()

if df_summary is not None:
    # Pivot table: ROI × Subject
    delay_pivot = df_summary.pivot(index='ROI', columns='Subject', values='Optimal_delay_TRs')

    print("Optimal Delay (TRs) per ROI and Subject:")
    print(delay_pivot.to_string())
    print()

    # Statistics per ROI
    print("ROI-wise Statistics:")
    print("-" * 60)
    print(f"{'ROI':<6} {'Mean±SD':<15} {'Range':<12} {'CV (%)':<10} {'Consistency'}")
    print("-" * 60)

    delay_stats = []

    for roi in ROIS:
        roi_data = df_summary[df_summary['ROI'] == roi]['Optimal_delay_TRs']

        mean_delay = roi_data.mean()
        std_delay = roi_data.std()
        min_delay = roi_data.min()
        max_delay = roi_data.max()
        cv = (std_delay / mean_delay * 100) if mean_delay > 0 else 0

        # Consistency assessment
        if std_delay <= 0.5:
            consistency = "★★★ Excellent"
        elif std_delay <= 1.0:
            consistency = "★★☆ Good"
        elif std_delay <= 1.5:
            consistency = "★☆☆ Moderate"
        else:
            consistency = "☆☆☆ Poor"

        print(f"{roi:<6} {mean_delay:.1f}±{std_delay:.1f} TRs   {min_delay}-{max_delay} TRs    {cv:>6.1f}%   {consistency}")

        delay_stats.append({
            'ROI': roi,
            'Mean': mean_delay,
            'SD': std_delay,
            'CV': cv,
            'Range': f"{min_delay}-{max_delay}",
            'Consistency': consistency
        })

    print()

    # Convert to seconds
    TR = 1.5
    print("Optimal Delay (seconds):")
    print("-" * 60)
    for roi in ROIS:
        roi_data = df_summary[df_summary['ROI'] == roi]['Optimal_delay_TRs']
        delays_sec = roi_data * TR
        print(f"{roi:<6} {delays_sec.mean():.2f}±{delays_sec.std():.2f}s  (range: {delays_sec.min():.1f}-{delays_sec.max():.1f}s)")

    print()

    # Hierarchical analysis
    print("Hierarchical Pattern Analysis:")
    print("-" * 60)
    roi_means = {roi: df_summary[df_summary['ROI'] == roi]['Optimal_delay_TRs'].mean()
                 for roi in ROIS}
    sorted_rois = sorted(roi_means.items(), key=lambda x: x[1])

    print("ROI order by mean delay (early → late):")
    for roi, mean_delay in sorted_rois:
        print(f"  {roi}: {mean_delay:.1f} TRs ({mean_delay * TR:.1f}s)")

    print()

    # Expected hierarchical pattern
    print("Expected vs Observed:")
    expected_order = ['V1', 'V2', 'V3', 'hV4']  # Early to late visual hierarchy
    observed_order = [roi for roi, _ in sorted_rois]

    if expected_order == observed_order:
        print("  ✓ Matches visual hierarchy (V1 → V2 → V3 → hV4)")
    else:
        print(f"  ✗ Deviates from expected hierarchy")
        print(f"    Expected: {' → '.join(expected_order)}")
        print(f"    Observed: {' → '.join(observed_order)}")

    print()
else:
    print("✗ Cannot perform temporal dynamics analysis (no summary data)")
    print()

# ============================================================================
# 3. Extract PCA and Z-score Information from Individual Logs
# ============================================================================

print("="*70)
print("2. PCA OPTIMIZATION & 3. Z-SCORE STATISTICS")
print("="*70)
print()

# Parse individual log files
log_data = []

for subject in SUBJECTS:
    for roi in ROIS:
        # Find log file
        log_patterns = [
            LOG_BASE / f'sub-{subject}' / '1112_23' / f'{roi}_universal_hrf' / 'log.txt',
            LOG_BASE / f'sub-{subject}' / '1112_23' / 'fir_reconstruction_uni_hrf' / f'{roi}_universal_hrf' / 'log.txt',
        ]

        log_file = None
        for pattern in log_patterns:
            if pattern.exists():
                log_file = pattern
                break

        if not log_file:
            continue

        # Parse log file
        with open(log_file, 'r') as f:
            log_content = f.read()

        # Extract information
        entry = {
            'Subject': subject,
            'ROI': roi,
            'log_path': str(log_file)
        }

        # Extract N voxels
        match = re.search(r'Number of voxels:\s*(\d+)', log_content)
        if match:
            entry['N_voxels'] = int(match.group(1))

        # Extract optimal delay
        match = re.search(r'Optimal delay:\s*(\d+)\s*TRs', log_content)
        if match:
            entry['Optimal_delay_TRs'] = int(match.group(1))

        # Extract PCA information (if PCA was used)
        match = re.search(r'Using PCA:\s*(True|False)', log_content)
        if match:
            entry['Use_PCA'] = match.group(1) == 'True'

        match = re.search(r'PCA components:\s*(\d+)', log_content)
        if match:
            entry['N_PCA_components'] = int(match.group(1))

        # Extract explained variance
        match = re.search(r'Explained variance ratio.*?:\s*([\d.]+)', log_content)
        if match:
            entry['PCA_explained_var'] = float(match.group(1))

        # Extract Z-score statistics
        match = re.search(r'Z-score range:\s*\[([-\d.]+),\s*([-\d.]+)\]', log_content)
        if match:
            entry['Z_min'] = float(match.group(1))
            entry['Z_max'] = float(match.group(2))

        match = re.search(r'Selective voxels.*?:\s*(\d+)\s*\(([\d.]+)%\)', log_content)
        if match:
            entry['N_selective_voxels'] = int(match.group(1))
            entry['Pct_selective_voxels'] = float(match.group(2))

        # Extract mean |z| per color
        match = re.search(r'Mean \|z\| per color:\s*\[([\d.\s]+)\]', log_content)
        if match:
            z_values = [float(x) for x in match.group(1).split()]
            entry['Mean_abs_z'] = np.mean(z_values)
            entry['SD_abs_z'] = np.std(z_values)

        # Extract classification accuracy
        match = re.search(r'Mean classification accuracy:\s*([\d.]+)', log_content)
        if match:
            entry['Classification_acc'] = float(match.group(1))

        # Extract reconstruction error
        match = re.search(r'Mean reconstruction error:\s*([\d.]+)', log_content)
        if match:
            entry['Reconstruction_error'] = float(match.group(1))

        # Extract novel color error
        match = re.search(r'Mean error \(novel colors\):\s*([\d.]+)', log_content)
        if match:
            entry['Novel_color_error'] = float(match.group(1))

        log_data.append(entry)

df_logs = pd.DataFrame(log_data)

if len(df_logs) > 0:
    print(f"✓ Parsed {len(df_logs)} log files")
    print(f"  Subjects: {sorted(df_logs['Subject'].unique())}")
    print(f"  ROIs: {sorted(df_logs['ROI'].unique())}")
    print()
else:
    print("✗ No log files found")
    print()

# ============================================================================
# 4. PCA Optimization Analysis
# ============================================================================

if len(df_logs) > 0 and 'PCA_explained_var' in df_logs.columns:
    print("-" * 70)
    print("PCA Component Analysis:")
    print("-" * 70)
    print()

    # Check if PCA was used
    if 'Use_PCA' in df_logs.columns:
        pca_usage = df_logs['Use_PCA'].value_counts()
        print(f"PCA Usage: {pca_usage.to_dict()}")
        print()

    # If PCA data exists
    pca_data = df_logs.dropna(subset=['PCA_explained_var'])

    if len(pca_data) > 0:
        print("Explained Variance by ROI:")
        print("-" * 60)
        print(f"{'ROI':<6} {'N':<4} {'Mean Expl. Var.':<18} {'Range'}")
        print("-" * 60)

        for roi in ROIS:
            roi_pca = pca_data[pca_data['ROI'] == roi]
            if len(roi_pca) > 0:
                mean_var = roi_pca['PCA_explained_var'].mean()
                std_var = roi_pca['PCA_explained_var'].std()
                min_var = roi_pca['PCA_explained_var'].min()
                max_var = roi_pca['PCA_explained_var'].max()

                print(f"{roi:<6} {len(roi_pca):<4} {mean_var:.1%} ± {std_var:.1%}    {min_var:.1%} - {max_var:.1%}")

        print()

        # Recommendation
        mean_explained = pca_data['PCA_explained_var'].mean()
        if mean_explained >= 0.90:
            recommendation = "✓ PCA components sufficient (≥90% variance)"
        elif mean_explained >= 0.80:
            recommendation = "⚠ Consider increasing components (80-90% variance)"
        else:
            recommendation = "✗ Increase PCA components (<80% variance)"

        print(f"Overall: {pca_data['PCA_explained_var'].mean():.1%} ± {pca_data['PCA_explained_var'].std():.1%}")
        print(f"Recommendation: {recommendation}")
        print()
    else:
        print("No PCA data available in logs")
        print()
else:
    print("-" * 70)
    print("PCA Analysis: No data available")
    print("-" * 70)
    print()

# ============================================================================
# 5. Z-Score Statistics Analysis
# ============================================================================

if len(df_logs) > 0 and 'Pct_selective_voxels' in df_logs.columns:
    print("-" * 70)
    print("Z-Score Statistics (ROI Consistency):")
    print("-" * 70)
    print()

    zscore_data = df_logs.dropna(subset=['Pct_selective_voxels'])

    if len(zscore_data) > 0:
        print("Voxel Selectivity (|z| > 2.3, p < 0.01) by ROI:")
        print("-" * 60)
        print(f"{'ROI':<6} {'N Subj':<8} {'% Selective Voxels':<25} {'Consistency'}")
        print("-" * 60)

        for roi in ROIS:
            roi_z = zscore_data[zscore_data['ROI'] == roi]
            if len(roi_z) > 0:
                mean_pct = roi_z['Pct_selective_voxels'].mean()
                std_pct = roi_z['Pct_selective_voxels'].std()
                min_pct = roi_z['Pct_selective_voxels'].min()
                max_pct = roi_z['Pct_selective_voxels'].max()

                # Consistency based on CV
                cv = (std_pct / mean_pct * 100) if mean_pct > 0 else 0
                if cv <= 15:
                    consistency = "★★★ Excellent"
                elif cv <= 30:
                    consistency = "★★☆ Good"
                elif cv <= 50:
                    consistency = "★☆☆ Moderate"
                else:
                    consistency = "☆☆☆ Poor"

                print(f"{roi:<6} {len(roi_z):<8} {mean_pct:>5.1f}% ± {std_pct:>4.1f}%  ({min_pct:.1f}-{max_pct:.1f}%)   {consistency}")

        print()

        # Mean |z| analysis
        if 'Mean_abs_z' in zscore_data.columns:
            print("Mean |Z-score| by ROI:")
            print("-" * 60)
            print(f"{'ROI':<6} {'Mean |z|':<15} {'Range'}")
            print("-" * 60)

            for roi in ROIS:
                roi_z = zscore_data[zscore_data['ROI'] == roi]
                if len(roi_z) > 0 and roi_z['Mean_abs_z'].notna().any():
                    mean_z = roi_z['Mean_abs_z'].mean()
                    std_z = roi_z['Mean_abs_z'].std()
                    min_z = roi_z['Mean_abs_z'].min()
                    max_z = roi_z['Mean_abs_z'].max()

                    print(f"{roi:<6} {mean_z:.2f} ± {std_z:.2f}    {min_z:.2f} - {max_z:.2f}")

            print()

        # Hierarchical pattern
        print("Hierarchical Pattern (Selectivity):")
        print("-" * 60)
        roi_selectivity = {roi: zscore_data[zscore_data['ROI'] == roi]['Pct_selective_voxels'].mean()
                          for roi in ROIS if len(zscore_data[zscore_data['ROI'] == roi]) > 0}
        sorted_selectivity = sorted(roi_selectivity.items(), key=lambda x: x[1], reverse=True)

        print("ROI order by selectivity (high → low):")
        for roi, pct in sorted_selectivity:
            print(f"  {roi}: {pct:.1f}% selective voxels")

        print()

        # Expected: Early visual areas (V1, V2) should have higher selectivity
        if len(sorted_selectivity) >= 2:
            top_roi = sorted_selectivity[0][0]
            if top_roi in ['V1', 'V2']:
                print("  ✓ Matches expected pattern (early visual areas more selective)")
            else:
                print("  ⚠ Unexpected pattern (late visual area most selective)")

        print()
    else:
        print("No Z-score data available in logs")
        print()
else:
    print("-" * 70)
    print("Z-Score Analysis: No data available")
    print("-" * 70)
    print()

# ============================================================================
# 6. Performance Summary
# ============================================================================

print("="*70)
print("PERFORMANCE SUMMARY ACROSS 4 SUBJECTS")
print("="*70)
print()

if df_summary is not None:
    print("Classification Accuracy:")
    print("-" * 60)
    for roi in ROIS:
        roi_data = df_summary[df_summary['ROI'] == roi]['Classification_accuracy']
        print(f"{roi:<6} {roi_data.mean()*100:>6.1f}% (all subjects: {(roi_data == 1.0).sum()}/{len(roi_data)} perfect)")
    print()

    print("Reconstruction Error (degrees):")
    print("-" * 60)
    print(f"{'ROI':<6} {'Mean±SD':<20} {'Range':<15} {'Best'}")
    print("-" * 60)
    for roi in ROIS:
        roi_data = df_summary[df_summary['ROI'] == roi]['Reconstruction_error_deg']
        mean_err = roi_data.mean()
        std_err = roi_data.std()
        min_err = roi_data.min()
        max_err = roi_data.max()
        best_subj = df_summary[(df_summary['ROI'] == roi) &
                               (df_summary['Reconstruction_error_deg'] == min_err)]['Subject'].values[0]

        print(f"{roi:<6} {mean_err:>5.2f}° ± {std_err:>4.2f}°    {min_err:.2f}° - {max_err:.2f}°    sub-{best_subj}")
    print()

    print("Novel Color Error (degrees):")
    print("-" * 60)
    print(f"{'ROI':<6} {'Mean±SD':<20} {'Range':<15} {'Best'}")
    print("-" * 60)
    for roi in ROIS:
        roi_data = df_summary[df_summary['ROI'] == roi]['Novel_color_error_deg']
        mean_err = roi_data.mean()
        std_err = roi_data.std()
        min_err = roi_data.min()
        max_err = roi_data.max()
        best_subj = df_summary[(df_summary['ROI'] == roi) &
                               (df_summary['Novel_color_error_deg'] == min_err)]['Subject'].values[0]

        print(f"{roi:<6} {mean_err:>5.2f}° ± {std_err:>4.2f}°    {min_err:.2f}° - {max_err:.2f}°    sub-{best_subj}")
    print()

# ============================================================================
# 7. Save Comprehensive Report
# ============================================================================

output_file = Path('COMPREHENSIVE_ANALYSIS_4SUBJECTS.md')

with open(output_file, 'w') as f:
    f.write("# Comprehensive Analysis: 4 Test Subjects (01-04)\n\n")
    f.write("Analysis Date: 2025-11-13\n\n")
    f.write("---\n\n")

    # 1. Temporal Dynamics
    f.write("## 1. Temporal Dynamics: Optimal Delay Consistency\n\n")

    if df_summary is not None:
        f.write("### Optimal Delay (TRs) by ROI and Subject\n\n")
        f.write("| ROI | sub-01 | sub-02 | sub-03 | sub-04 | Mean±SD | CV (%) | Consistency |\n")
        f.write("|-----|--------|--------|--------|--------|---------|--------|-------------|\n")

        for roi in ROIS:
            roi_data = df_summary[df_summary['ROI'] == roi]
            delays = {str(s).zfill(2): roi_data[roi_data['Subject'] == s]['Optimal_delay_TRs'].values[0]
                     if len(roi_data[roi_data['Subject'] == s]) > 0 else '-'
                     for s in SUBJECTS}

            mean_delay = roi_data['Optimal_delay_TRs'].mean()
            std_delay = roi_data['Optimal_delay_TRs'].std()
            cv = (std_delay / mean_delay * 100) if mean_delay > 0 else 0

            if std_delay <= 0.5:
                consistency = "★★★"
            elif std_delay <= 1.0:
                consistency = "★★☆"
            elif std_delay <= 1.5:
                consistency = "★☆☆"
            else:
                consistency = "☆☆☆"

            f.write(f"| {roi} | {delays['01']} | {delays['02']} | {delays['03']} | {delays['04']} | "
                   f"{mean_delay:.1f}±{std_delay:.1f} | {cv:.1f}% | {consistency} |\n")

        f.write("\n")

        f.write("### Optimal Delay (seconds, TR=1.5s)\n\n")
        f.write("| ROI | Mean±SD (s) | Range (s) |\n")
        f.write("|-----|-------------|----------|\n")

        for roi in ROIS:
            roi_data = df_summary[df_summary['ROI'] == roi]['Optimal_delay_TRs']
            delays_sec = roi_data * 1.5
            f.write(f"| {roi} | {delays_sec.mean():.2f}±{delays_sec.std():.2f} | "
                   f"{delays_sec.min():.1f}-{delays_sec.max():.1f} |\n")

        f.write("\n")

        # Hierarchical pattern
        f.write("### Hierarchical Pattern\n\n")
        roi_means = {roi: df_summary[df_summary['ROI'] == roi]['Optimal_delay_TRs'].mean()
                     for roi in ROIS}
        sorted_rois = sorted(roi_means.items(), key=lambda x: x[1])

        f.write("ROI order by mean delay (early → late):\n\n")
        for roi, mean_delay in sorted_rois:
            f.write(f"- **{roi}**: {mean_delay:.1f} TRs ({mean_delay * 1.5:.1f}s)\n")

        f.write("\n")

        expected_order = ['V1', 'V2', 'V3', 'hV4']
        observed_order = [roi for roi, _ in sorted_rois]

        if expected_order == observed_order:
            f.write("✓ **Matches visual hierarchy** (V1 → V2 → V3 → hV4)\n\n")
        else:
            f.write("✗ **Deviates from expected hierarchy**\n\n")
            f.write(f"- Expected: {' → '.join(expected_order)}\n")
            f.write(f"- Observed: {' → '.join(observed_order)}\n\n")

    f.write("---\n\n")

    # 2. PCA Optimization
    f.write("## 2. PCA Optimization\n\n")

    if len(df_logs) > 0 and 'PCA_explained_var' in df_logs.columns:
        pca_data = df_logs.dropna(subset=['PCA_explained_var'])

        if len(pca_data) > 0:
            f.write("### Explained Variance by ROI\n\n")
            f.write("| ROI | N Subjects | Mean Expl. Var. | Range |\n")
            f.write("|-----|------------|-----------------|-------|\n")

            for roi in ROIS:
                roi_pca = pca_data[pca_data['ROI'] == roi]
                if len(roi_pca) > 0:
                    mean_var = roi_pca['PCA_explained_var'].mean()
                    std_var = roi_pca['PCA_explained_var'].std()
                    min_var = roi_pca['PCA_explained_var'].min()
                    max_var = roi_pca['PCA_explained_var'].max()

                    f.write(f"| {roi} | {len(roi_pca)} | {mean_var:.1%} ± {std_var:.1%} | "
                           f"{min_var:.1%} - {max_var:.1%} |\n")

            f.write("\n")

            mean_explained = pca_data['PCA_explained_var'].mean()
            if mean_explained >= 0.90:
                f.write("✓ **PCA components sufficient** (≥90% variance explained)\n\n")
            elif mean_explained >= 0.80:
                f.write("⚠ **Consider increasing components** (80-90% variance explained)\n\n")
            else:
                f.write("✗ **Increase PCA components** (<80% variance explained)\n\n")
        else:
            f.write("*No PCA data available*\n\n")
    else:
        f.write("*No PCA data available*\n\n")

    f.write("---\n\n")

    # 3. Z-Score Statistics
    f.write("## 3. Z-Score Statistics: ROI Consistency\n\n")

    if len(df_logs) > 0 and 'Pct_selective_voxels' in df_logs.columns:
        zscore_data = df_logs.dropna(subset=['Pct_selective_voxels'])

        if len(zscore_data) > 0:
            f.write("### Voxel Selectivity (|z| > 2.3, p < 0.01)\n\n")
            f.write("| ROI | N Subjects | % Selective Voxels | Consistency |\n")
            f.write("|-----|------------|-------------------|-------------|\n")

            for roi in ROIS:
                roi_z = zscore_data[zscore_data['ROI'] == roi]
                if len(roi_z) > 0:
                    mean_pct = roi_z['Pct_selective_voxels'].mean()
                    std_pct = roi_z['Pct_selective_voxels'].std()
                    min_pct = roi_z['Pct_selective_voxels'].min()
                    max_pct = roi_z['Pct_selective_voxels'].max()

                    cv = (std_pct / mean_pct * 100) if mean_pct > 0 else 0
                    if cv <= 15:
                        consistency = "★★★"
                    elif cv <= 30:
                        consistency = "★★☆"
                    elif cv <= 50:
                        consistency = "★☆☆"
                    else:
                        consistency = "☆☆☆"

                    f.write(f"| {roi} | {len(roi_z)} | {mean_pct:.1f}% ± {std_pct:.1f}% "
                           f"({min_pct:.1f}-{max_pct:.1f}%) | {consistency} |\n")

            f.write("\n")

            # Hierarchical pattern
            f.write("### Hierarchical Pattern (Selectivity)\n\n")
            roi_selectivity = {roi: zscore_data[zscore_data['ROI'] == roi]['Pct_selective_voxels'].mean()
                              for roi in ROIS if len(zscore_data[zscore_data['ROI'] == roi]) > 0}
            sorted_selectivity = sorted(roi_selectivity.items(), key=lambda x: x[1], reverse=True)

            f.write("ROI order by selectivity (high → low):\n\n")
            for roi, pct in sorted_selectivity:
                f.write(f"- **{roi}**: {pct:.1f}% selective voxels\n")

            f.write("\n")

            if len(sorted_selectivity) >= 2:
                top_roi = sorted_selectivity[0][0]
                if top_roi in ['V1', 'V2']:
                    f.write("✓ **Matches expected pattern** (early visual areas more selective)\n\n")
                else:
                    f.write("⚠ **Unexpected pattern** (late visual area most selective)\n\n")
        else:
            f.write("*No Z-score data available*\n\n")
    else:
        f.write("*No Z-score data available*\n\n")

    f.write("---\n\n")

    # 4. Performance Summary
    f.write("## 4. Performance Summary\n\n")

    if df_summary is not None:
        f.write("### Classification Accuracy\n\n")
        f.write("| ROI | Mean | Perfect (n/4) |\n")
        f.write("|-----|------|---------------|\n")

        for roi in ROIS:
            roi_data = df_summary[df_summary['ROI'] == roi]['Classification_accuracy']
            n_perfect = (roi_data == 1.0).sum()
            f.write(f"| {roi} | {roi_data.mean()*100:.1f}% | {n_perfect}/4 |\n")

        f.write("\n")

        f.write("### Reconstruction Error (degrees)\n\n")
        f.write("| ROI | Mean±SD | Range | Best Subject |\n")
        f.write("|-----|---------|-------|-------------|\n")

        for roi in ROIS:
            roi_data = df_summary[df_summary['ROI'] == roi]['Reconstruction_error_deg']
            mean_err = roi_data.mean()
            std_err = roi_data.std()
            min_err = roi_data.min()
            max_err = roi_data.max()
            best_subj = df_summary[(df_summary['ROI'] == roi) &
                                   (df_summary['Reconstruction_error_deg'] == min_err)]['Subject'].values[0]

            f.write(f"| {roi} | {mean_err:.2f}° ± {std_err:.2f}° | "
                   f"{min_err:.2f}° - {max_err:.2f}° | sub-{best_subj} |\n")

        f.write("\n")

        f.write("### Novel Color Error (degrees)\n\n")
        f.write("| ROI | Mean±SD | Range | Best Subject |\n")
        f.write("|-----|---------|-------|-------------|\n")

        for roi in ROIS:
            roi_data = df_summary[df_summary['ROI'] == roi]['Novel_color_error_deg']
            mean_err = roi_data.mean()
            std_err = roi_data.std()
            min_err = roi_data.min()
            max_err = roi_data.max()
            best_subj = df_summary[(df_summary['ROI'] == roi) &
                                   (df_summary['Novel_color_error_deg'] == min_err)]['Subject'].values[0]

            f.write(f"| {roi} | {mean_err:.2f}° ± {std_err:.2f}° | "
                   f"{min_err:.2f}° - {max_err:.2f}° | sub-{best_subj} |\n")

        f.write("\n")

    f.write("---\n\n")

    # Conclusions
    f.write("## Key Findings\n\n")

    if df_summary is not None:
        # 1. Temporal dynamics
        f.write("### 1. Temporal Dynamics\n\n")

        # Check consistency
        consistent_rois = []
        for roi in ROIS:
            roi_data = df_summary[df_summary['ROI'] == roi]['Optimal_delay_TRs']
            if roi_data.std() <= 1.0:
                consistent_rois.append(roi)

        if len(consistent_rois) >= 3:
            f.write(f"- ✓ **High consistency** across subjects in {', '.join(consistent_rois)}\n")
        else:
            f.write(f"- ⚠ **Variable HRF timing** across subjects\n")

        f.write("\n")

        # 2. Classification
        f.write("### 2. Classification Performance\n\n")

        perfect_classification = (df_summary['Classification_accuracy'] == 1.0).mean()
        if perfect_classification >= 0.75:
            f.write(f"- ✓ **Excellent classification** ({perfect_classification*100:.0f}% of ROI×Subject combinations achieve 100%)\n")
        elif perfect_classification >= 0.50:
            f.write(f"- ⚠ **Good classification** ({perfect_classification*100:.0f}% achieve 100%, but some variability)\n")
        else:
            f.write(f"- ✗ **Inconsistent classification** (only {perfect_classification*100:.0f}% achieve 100%)\n")

        f.write("\n")

        # 3. Reconstruction
        f.write("### 3. Reconstruction Accuracy\n\n")

        best_roi_recon = df_summary.groupby('ROI')['Reconstruction_error_deg'].mean().idxmin()
        best_err = df_summary.groupby('ROI')['Reconstruction_error_deg'].mean().min()

        f.write(f"- **Best ROI**: {best_roi_recon} ({best_err:.2f}° mean error)\n")

        if best_err < 5.0:
            f.write(f"- ✓ **Excellent reconstruction** (<5° error)\n")
        elif best_err < 10.0:
            f.write(f"- ⚠ **Good reconstruction** (5-10° error)\n")
        else:
            f.write(f"- ⚠ **Moderate reconstruction** (>10° error)\n")

        f.write("\n")

print(f"✓ Saved comprehensive report: {output_file}")
print()
print("="*70)
print("ANALYSIS COMPLETE")
print("="*70)
