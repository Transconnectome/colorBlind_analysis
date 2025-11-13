#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_pca_components_4subjects.py
------------------------------------
Analyze PCA component requirements (for 90% variance) across 4 subjects

Based on finding: sub-01 requires only ~6 components for 90% variance
Question: Does this apply to other subjects?

Usage:
    python analyze_pca_components_4subjects.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ============================================================================
# Data Collection
# ============================================================================

print("="*70)
print("PCA Component Analysis Across 4 Test Subjects")
print("="*70)
print()

# Manually collected from logs (grep "Components for 90% variance")
data = {
    'Subject': [],
    'ROI': [],
    'Components_for_90pct': []
}

# sub-01
for roi in ['V1', 'V2', 'V3', 'hV4']:
    data['Subject'].append('01')
    data['ROI'].append(roi)
    data['Components_for_90pct'].append(6.0)

# sub-02
components_02 = {'V1': 7.0, 'V2': 7.0, 'V3': 6.0, 'hV4': 6.0}
for roi, comp in components_02.items():
    data['Subject'].append('02')
    data['ROI'].append(roi)
    data['Components_for_90pct'].append(comp)

# sub-03
components_03 = {'V1': 7.0, 'V2': 6.0, 'V3': 6.0, 'hV4': 6.0}
for roi, comp in components_03.items():
    data['Subject'].append('03')
    data['ROI'].append(roi)
    data['Components_for_90pct'].append(comp)

# sub-04
for roi in ['V1', 'V2', 'V3', 'hV4']:
    data['Subject'].append('04')
    data['ROI'].append(roi)
    data['Components_for_90pct'].append(6.0)

df = pd.DataFrame(data)

print(f"✓ Collected PCA data: {len(df)} ROI×Subject combinations")
print()

# ============================================================================
# Analysis 1: Pivot Table
# ============================================================================

print("Components Required for 90% Variance:")
print("="*70)
print()

pivot = df.pivot(index='ROI', columns='Subject', values='Components_for_90pct')
print(pivot.to_string())
print()

# ============================================================================
# Analysis 2: Summary Statistics
# ============================================================================

print("Summary Statistics by ROI:")
print("="*70)
print()

summary = df.groupby('ROI')['Components_for_90pct'].agg([
    ('Mean', 'mean'),
    ('SD', 'std'),
    ('Min', 'min'),
    ('Max', 'max'),
    ('Consistency', lambda x: '✓ Excellent' if x.std() == 0 else '⚠ Variable')
])

print(summary.to_string())
print()

# Overall statistics
print("Overall Statistics:")
print("-" * 70)
overall_mean = df['Components_for_90pct'].mean()
overall_std = df['Components_for_90pct'].std()
overall_min = df['Components_for_90pct'].min()
overall_max = df['Components_for_90pct'].max()

print(f"  Mean: {overall_mean:.1f} components")
print(f"  SD: {overall_std:.2f}")
print(f"  Range: {overall_min:.0f} - {overall_max:.0f} components")
print()

# Mode (most common)
mode_value = df['Components_for_90pct'].mode()[0]
mode_count = (df['Components_for_90pct'] == mode_value).sum()
mode_pct = mode_count / len(df) * 100

print(f"  Most common: {mode_value:.0f} components ({mode_count}/16 cases, {mode_pct:.0f}%)")
print()

# ============================================================================
# Analysis 3: Comparison with Current PCA-20
# ============================================================================

print("Comparison with Current Setting (PCA-20):")
print("="*70)
print()

print("Efficiency Analysis:")
print("-" * 70)
current_components = 20
recommended_components = overall_mean

print(f"  Current: {current_components} components")
print(f"  Required for 90%: {recommended_components:.1f} components")
print(f"  Overspecification: {current_components - recommended_components:.1f}× "
      f"({(current_components / recommended_components - 1) * 100:.0f}% excess)")
print()

print("Parameter Reduction:")
print("-" * 70)

# Example for V2 with 310 voxels
n_voxels_v2 = 310
n_samples = 40  # 5 runs × 8 colors

print(f"Example: V2 (310 voxels, 40 training samples)")
print()

scenarios = [
    ("No PCA", n_voxels_v2),
    ("PCA-20 (current)", 20),
    ("PCA-7 (recommended)", 7),
    ("PCA-6 (sub-01 finding)", 6),
    ("PCA-3 (overfitting test)", 3)
]

print(f"{'Method':<30} {'Features':<12} {'Sample:Feature':<18} {'Assessment'}")
print("-" * 80)

for method, n_features in scenarios:
    ratio = n_samples / n_features

    if ratio >= 10:
        assessment = "✓ Safe"
    elif ratio >= 5:
        assessment = "✓ Acceptable"
    elif ratio >= 3:
        assessment = "⚠ Borderline"
    else:
        assessment = "❌ Risky"

    print(f"{method:<30} {n_features:<12} {ratio:<18.1f} {assessment}")

print()

# ============================================================================
# Analysis 4: Recommendations
# ============================================================================

print("Recommendations:")
print("="*70)
print()

# ROI-specific recommendations
print("ROI-Specific Component Recommendations:")
print("-" * 70)

for roi in ['V1', 'V2', 'V3', 'hV4']:
    roi_data = df[df['ROI'] == roi]['Components_for_90pct']
    roi_mean = roi_data.mean()
    roi_max = roi_data.max()
    roi_std = roi_data.std()

    if roi_std == 0:
        recommendation = f"{roi_mean:.0f} components (consistent across all subjects)"
        safety_margin = roi_mean
    else:
        # Add safety margin: max observed
        recommendation = f"{roi_max:.0f} components (max observed, covers all subjects)"
        safety_margin = roi_max

    print(f"  {roi}: {recommendation}")

print()

# Overall recommendation
print("Overall Recommendation:")
print("-" * 70)

# Conservative approach: use max observed
max_components = df['Components_for_90pct'].max()
print(f"  Conservative: {max_components:.0f} components (covers all ROI×Subject combinations)")
print(f"  Current PCA-20: {current_components - max_components:.0f}× overspecified")
print()

print("  Trade-offs:")
print(f"    - PCA-{max_components:.0f}: Optimal efficiency, 90% variance")
print(f"    - PCA-20: Current setting, 100% variance (likely overfitting)")
print(f"    - PCA-3: Overfitting test (if accuracy stays high, signal is robust)")
print()

# ============================================================================
# Analysis 5: Subject Variability
# ============================================================================

print("Subject-Level Analysis:")
print("="*70)
print()

print("Components Needed by Subject (averaged across ROIs):")
print("-" * 70)

for subject in ['01', '02', '03', '04']:
    subj_data = df[df['Subject'] == subject]['Components_for_90pct']
    subj_mean = subj_data.mean()
    subj_std = subj_data.std()
    subj_range = f"{subj_data.min():.0f}-{subj_data.max():.0f}"

    print(f"  sub-{subject}: {subj_mean:.1f} ± {subj_std:.2f} (range: {subj_range})")

print()

# ============================================================================
# Save Results
# ============================================================================

output_file = Path('PCA_COMPONENTS_ANALYSIS_4SUBJECTS.md')

with open(output_file, 'w') as f:
    f.write("# PCA Component Analysis Across 4 Test Subjects\n\n")
    f.write("**Analysis Date**: 2025-11-13\n\n")
    f.write("**Question**: Can we reduce PCA components from 20 to ~6 (as found in sub-01)?\n\n")
    f.write("---\n\n")

    # Table
    f.write("## Components Required for 90% Variance\n\n")
    f.write("| ROI | sub-01 | sub-02 | sub-03 | sub-04 | Mean±SD | Consistency |\n")
    f.write("|-----|--------|--------|--------|--------|---------|-------------|\n")

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_data = df[df['ROI'] == roi]
        values = {}
        for subj in ['01', '02', '03', '04']:
            val = roi_data[roi_data['Subject'] == subj]['Components_for_90pct'].values[0]
            values[subj] = int(val)

        mean_val = roi_data['Components_for_90pct'].mean()
        std_val = roi_data['Components_for_90pct'].std()

        consistency = "✓ Perfect" if std_val == 0 else "⚠ Variable"

        f.write(f"| {roi} | {values['01']} | {values['02']} | {values['03']} | {values['04']} | "
               f"{mean_val:.1f}±{std_val:.2f} | {consistency} |\n")

    f.write("\n")

    # Overall statistics
    f.write("## Overall Statistics\n\n")
    f.write(f"- **Mean**: {overall_mean:.1f} components\n")
    f.write(f"- **Range**: {overall_min:.0f} - {overall_max:.0f} components\n")
    f.write(f"- **Most common**: {mode_value:.0f} components ({mode_pct:.0f}% of cases)\n\n")

    # Key findings
    f.write("## Key Findings\n\n")
    f.write("### 1. Consistency Across Subjects\n\n")

    if overall_std < 0.5:
        f.write("✓ **Excellent consistency** across subjects\n\n")
    else:
        f.write("⚠️ **Some variability** across subjects\n\n")

    f.write("**ROI-wise consistency**:\n\n")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_data = df[df['ROI'] == roi]['Components_for_90pct']
        if roi_data.std() == 0:
            f.write(f"- **{roi}**: ✓ Perfect (all subjects need {roi_data.mean():.0f} components)\n")
        else:
            f.write(f"- **{roi}**: ⚠ Variable ({roi_data.min():.0f}-{roi_data.max():.0f} components)\n")

    f.write("\n")

    f.write("### 2. Comparison with Current PCA-20\n\n")
    f.write(f"- **Current setting**: 20 components\n")
    f.write(f"- **Required for 90% variance**: {overall_mean:.1f} components\n")
    f.write(f"- **Overspecification**: {(current_components / overall_mean):.1f}× (using {(current_components / overall_mean - 1) * 100:.0f}% more than needed)\n\n")

    f.write("### 3. Sample:Feature Ratio Improvement\n\n")
    f.write("With 40 training samples:\n\n")
    f.write("| Method | Features | Sample:Feature Ratio | Assessment |\n")
    f.write("|--------|----------|---------------------|------------|\n")
    f.write(f"| PCA-20 (current) | 20 | {n_samples/20:.1f}:1 | ⚠ Borderline (risk of overfitting) |\n")
    f.write(f"| PCA-7 (recommended) | 7 | {n_samples/7:.1f}:1 | ✓ Acceptable |\n")
    f.write(f"| PCA-6 (sub-01 finding) | 6 | {n_samples/6:.1f}:1 | ✓ Safe |\n")
    f.write(f"| PCA-3 (test) | 3 | {n_samples/3:.1f}:1 | ✓ Very safe |\n\n")

    f.write("**Recommendation**: Using 6-7 components would:\n")
    f.write("- ✓ Capture 90% of variance\n")
    f.write("- ✓ Improve sample:feature ratio from 2:1 to 5.7-6.7:1\n")
    f.write("- ✓ Reduce overfitting risk\n")
    f.write("- ✓ Maintain performance (based on sub-01 results)\n\n")

    # Recommendations
    f.write("## Recommendations\n\n")
    f.write("### Conservative Approach (Recommended)\n\n")
    f.write(f"**Use PCA-{max_components:.0f}** (maximum observed across all subjects)\n\n")
    f.write("- Covers all ROI×Subject combinations\n")
    f.write("- Captures ≥90% variance for all cases\n")
    f.write("- Still 3× more efficient than PCA-20\n")
    f.write("- Lower overfitting risk\n\n")

    f.write("### Aggressive Approach (For Testing)\n\n")
    f.write("**Use PCA-6** (most common value)\n\n")
    f.write(f"- Covers {mode_pct:.0f}% of cases\n")
    f.write("- Maximal efficiency\n")
    f.write("- May need subject-specific adjustment for V1/V2 in some subjects\n\n")

    f.write("### Validation Test (Critical)\n\n")
    f.write("**Run PCA-3 test** to validate overfitting hypothesis\n\n")
    f.write("```bash\n")
    f.write("# If PCA-3 maintains >85% accuracy:\n")
    f.write("# → Signal is robust, current 100% is real\n")
    f.write("# → PCA-6 or PCA-7 is safe\n\n")
    f.write("# If PCA-3 drops to <70% accuracy:\n")
    f.write("# → PCA-20 is overfitting\n")
    f.write("# → Should use PCA-6 or PCA-7\n")
    f.write("```\n\n")

    # Subject-specific notes
    f.write("## Subject-Specific Notes\n\n")
    f.write("### sub-01\n")
    f.write("- ✓ **Perfect consistency**: All ROIs need exactly 6 components\n\n")

    f.write("### sub-02\n")
    f.write("- ⚠ **V1, V2 need 7 components** (vs 6 for V3, hV4)\n")
    f.write("- Suggests slightly more complex signal structure in early visual areas\n\n")

    f.write("### sub-03\n")
    f.write("- ⚠ **V1 needs 7 components** (vs 6 for others)\n")
    f.write("- Similar pattern to sub-02\n\n")

    f.write("### sub-04\n")
    f.write("- ✓ **Perfect consistency**: All ROIs need exactly 6 components\n\n")

    # Conclusion
    f.write("---\n\n")
    f.write("## Conclusion\n\n")
    f.write("✅ **YES, the PCA-6 finding from sub-01 generalizes well to other subjects!**\n\n")
    f.write(f"- **{mode_pct:.0f}% of cases** can use 6 components\n")
    f.write(f"- **100% of cases** can use ≤{max_components:.0f} components\n")
    f.write("- Current PCA-20 is likely **overspecified by 3×**\n\n")
    f.write("**Recommended action**: Switch to **PCA-7** (covers all cases) or **PCA-6** (covers most)\n\n")
    f.write("**Critical test**: Run PCA-3 validation to confirm signal robustness\n")

print(f"✓ Saved detailed report: {output_file}")
print()
print("="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print()

# Print key takeaway
print("🎯 KEY FINDING:")
print("-" * 70)
print(f"  ✅ PCA-6 finding from sub-01 APPLIES to other subjects!")
print(f"  • {mode_pct:.0f}% of cases need ≤6 components")
print(f"  • 100% of cases need ≤{max_components:.0f} components")
print(f"  • Current PCA-20 is {(current_components/overall_mean):.1f}× overspecified")
print()
print("  📊 Recommendation: Use PCA-7 (safe for all subjects)")
print()
