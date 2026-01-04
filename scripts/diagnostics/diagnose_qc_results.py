#!/usr/bin/env python3
"""
QC TSV 진단 스크립트

목적:
1. ROI 0 voxel run 식별 (변환 문제)
2. Coreg 낮은 run 식별 (정합 문제)
3. Dropout 높은 run 식별 (물리적 dropout)

사용법:
  python diagnose_qc_results.py derivatives/QC/qc_runwise_sub-*.tsv
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# THRESHOLDS (동료 제안 기준)
# ============================================================================

DICE_EXCELLENT = 0.90
DICE_ACCEPTABLE = 0.85
DICE_POOR = 0.80

OVERLAP_FRAC_EXCELLENT = 0.90
OVERLAP_FRAC_ACCEPTABLE = 0.85
OVERLAP_FRAC_POOR = 0.80

DROPOUT_METRIC1_SEVERE = 0.50
DROPOUT_METRIC1_MODERATE = 0.70

DROPOUT_METRIC2_SEVERE = 0.60
DROPOUT_METRIC2_MODERATE = 0.75

# ============================================================================
# LOAD AND MERGE DATA
# ============================================================================

def load_qc_data(tsv_files):
    """Load all QC TSV files and merge"""
    dfs = []
    for f in tsv_files:
        if Path(f).exists():
            df = pd.read_csv(f, sep='\t')
            dfs.append(df)

    if not dfs:
        print("❌ No valid TSV files found!")
        sys.exit(1)

    return pd.concat(dfs, ignore_index=True)

# ============================================================================
# CLASSIFICATION FUNCTIONS
# ============================================================================

def classify_run(row):
    """
    동료의 3단계 분류:
    1. ROI_ZERO: ROI 0 voxel (변환 문제)
    2. COREG_POOR: Coreg 낮음 (정합 문제)
    3. DROPOUT_HIGH: Dropout 높음 (물리적)
    4. OK: 정상
    """

    # Priority 1: ROI 0 voxel
    if pd.isna(row['roi_vox']) or row['roi_vox'] == 0:
        return 'ROI_ZERO'

    # Priority 2: Coreg poor
    if pd.isna(row['dice']) or row['dice'] < DICE_POOR:
        return 'COREG_POOR'

    if pd.isna(row['overlap_frac']) or row['overlap_frac'] < OVERLAP_FRAC_POOR:
        return 'COREG_POOR'

    # Priority 3: Dropout
    dropout1 = row.get('dropout_metric1', np.nan)
    dropout2 = row.get('dropout_metric2', np.nan)

    if (not pd.isna(dropout1) and dropout1 < DROPOUT_METRIC1_SEVERE) or \
       (not pd.isna(dropout2) and dropout2 < DROPOUT_METRIC2_SEVERE):
        return 'DROPOUT_SEVERE'

    if (not pd.isna(dropout1) and dropout1 < DROPOUT_METRIC1_MODERATE) or \
       (not pd.isna(dropout2) and dropout2 < DROPOUT_METRIC2_MODERATE):
        return 'DROPOUT_MODERATE'

    # Check if excellent
    if row['dice'] >= DICE_EXCELLENT and row['overlap_frac'] >= OVERLAP_FRAC_EXCELLENT:
        return 'EXCELLENT'

    return 'ACCEPTABLE'

# ============================================================================
# DIAGNOSTIC REPORTS
# ============================================================================

def print_summary(df):
    """Overall summary statistics"""
    print("\n" + "="*80)
    print("QC DIAGNOSTIC SUMMARY")
    print("="*80 + "\n")

    # Dataset info
    n_subjects = df['sub'].nunique()
    n_runs = df.groupby(['sub', 'run']).ngroups
    n_rois = len(df)

    print(f"Dataset:")
    print(f"  Subjects: {n_subjects}")
    print(f"  Runs: {n_runs}")
    print(f"  ROI measurements: {n_rois}")
    print()

    # Classification distribution
    df['status'] = df.apply(classify_run, axis=1)
    status_counts = df['status'].value_counts()

    print(f"Run Classification:")
    for status, count in status_counts.items():
        pct = 100 * count / len(df)
        print(f"  {status:20s}: {count:4d} ({pct:5.1f}%)")
    print()

    # Coreg statistics
    print(f"Registration Quality:")
    print(f"  Dice coefficient:")
    print(f"    Mean:   {df['dice'].mean():.3f}")
    print(f"    Median: {df['dice'].median():.3f}")
    print(f"    Min:    {df['dice'].min():.3f}")
    print(f"    Max:    {df['dice'].max():.3f}")
    print()
    print(f"  Overlap fraction:")
    print(f"    Mean:   {df['overlap_frac'].mean():.3f}")
    print(f"    Median: {df['overlap_frac'].median():.3f}")
    print(f"    Min:    {df['overlap_frac'].min():.3f}")
    print(f"    Max:    {df['overlap_frac'].max():.3f}")
    print()

def print_problematic_runs(df):
    """Detailed report on problematic runs"""
    df['status'] = df.apply(classify_run, axis=1)

    print("\n" + "="*80)
    print("PROBLEMATIC RUNS - DETAILED BREAKDOWN")
    print("="*80 + "\n")

    # Category 1: ROI ZERO
    roi_zero = df[df['status'] == 'ROI_ZERO']
    if len(roi_zero) > 0:
        print(f"🚨 PRIORITY 1: ROI_ZERO (n={len(roi_zero)})")
        print(f"   Issue: ROI generation/transformation failed")
        print(f"   Action: Fix Wang atlas transformation pipeline")
        print()

        for _, row in roi_zero.iterrows():
            print(f"   sub-{row['sub']:02d} run-{row['run']} {row['roi']:3s}: "
                  f"roi_vox={row['roi_vox']:.0f}, dice={row['dice']:.3f}")
        print()

    # Category 2: COREG POOR
    coreg_poor = df[df['status'] == 'COREG_POOR']
    if len(coreg_poor) > 0:
        print(f"⚠️  PRIORITY 2: COREG_POOR (n={len(coreg_poor)})")
        print(f"   Issue: Registration quality below threshold")
        print(f"   Action: Recheck SDC/DOF/init for these runs only")
        print()

        for _, row in coreg_poor.iterrows():
            print(f"   sub-{row['sub']:02d} run-{row['run']} {row['roi']:3s}: "
                  f"dice={row['dice']:.3f}, overlap_frac={row['overlap_frac']:.3f}")
        print()

    # Category 3: DROPOUT SEVERE
    dropout_severe = df[df['status'] == 'DROPOUT_SEVERE']
    if len(dropout_severe) > 0:
        print(f"💧 PRIORITY 3: DROPOUT_SEVERE (n={len(dropout_severe)})")
        print(f"   Issue: Severe signal dropout (physical)")
        print(f"   Action: Consider ROI rescue strategies (dilation, threshold)")
        print()

        for _, row in dropout_severe.iterrows():
            m1 = row.get('dropout_metric1', np.nan)
            m2 = row.get('dropout_metric2', np.nan)
            print(f"   sub-{row['sub']:02d} run-{row['run']} {row['roi']:3s}: "
                  f"dropout_m1={m1:.3f}, dropout_m2={m2:.3f}, "
                  f"dice={row['dice']:.3f}")
        print()

def print_subject_summary(df):
    """Per-subject summary"""
    df['status'] = df.apply(classify_run, axis=1)

    print("\n" + "="*80)
    print("PER-SUBJECT SUMMARY")
    print("="*80 + "\n")

    for sub in sorted(df['sub'].unique()):
        sub_df = df[df['sub'] == sub]

        n_total = len(sub_df)
        n_zero = len(sub_df[sub_df['status'] == 'ROI_ZERO'])
        n_coreg = len(sub_df[sub_df['status'] == 'COREG_POOR'])
        n_dropout_sev = len(sub_df[sub_df['status'] == 'DROPOUT_SEVERE'])
        n_dropout_mod = len(sub_df[sub_df['status'] == 'DROPOUT_MODERATE'])
        n_ok = len(sub_df[sub_df['status'].isin(['EXCELLENT', 'ACCEPTABLE'])])

        print(f"Sub-{sub:02d}:")
        print(f"  Total: {n_total:3d} | "
              f"ROI_ZERO: {n_zero:3d} | "
              f"COREG_POOR: {n_coreg:3d} | "
              f"DROPOUT_SEV: {n_dropout_sev:3d} | "
              f"DROPOUT_MOD: {n_dropout_mod:3d} | "
              f"OK: {n_ok:3d}")

        # Dice statistics for this subject
        dice_mean = sub_df['dice'].mean()
        dice_min = sub_df['dice'].min()
        print(f"  Dice: mean={dice_mean:.3f}, min={dice_min:.3f}")
        print()

def generate_action_plan(df):
    """Generate specific action items"""
    df['status'] = df.apply(classify_run, axis=1)

    print("\n" + "="*80)
    print("RECOMMENDED ACTION PLAN")
    print("="*80 + "\n")

    # Action 1: Fix ROI pipeline
    roi_zero = df[df['status'] == 'ROI_ZERO']
    if len(roi_zero) > 0:
        affected_subs = roi_zero['sub'].unique()
        affected_runs = roi_zero.groupby('sub')['run'].apply(list).to_dict()

        print("ACTION 1 (CRITICAL): Fix ROI transformation pipeline")
        print("-" * 80)
        print(f"Affected: {len(affected_subs)} subjects, {len(roi_zero)} ROI measurements")
        print()
        print("Steps:")
        print("  1. Verify Wang atlas files exist in MNI space")
        print("  2. Check MNI→T1w transform (.h5 file) is valid")
        print("  3. Check T1w→boldref transform (.txt file) is valid")
        print("  4. Verify transform inversion direction: [xfm, 1] means inverse")
        print("  5. Check intermediate outputs in work directory")
        print()
        print("Affected subjects and runs:")
        for sub in sorted(affected_subs):
            runs = affected_runs[sub]
            print(f"  sub-{sub:02d}: runs {sorted(set(runs))}")
        print("\n")

    # Action 2: Recheck specific runs
    coreg_poor = df[df['status'] == 'COREG_POOR']
    if len(coreg_poor) > 0:
        print("ACTION 2 (HIGH PRIORITY): Recheck registration for specific runs")
        print("-" * 80)
        print(f"Affected: {len(coreg_poor)} ROI measurements")
        print()
        print("For each run, try:")
        print("  1. Check SDC application in HTML report")
        print("  2. Verify BIDS metadata (PhaseEncodingDirection, TotalReadoutTime)")
        print("  3. Compare DOF 6 vs 9")
        print("  4. Compare BBR init: header vs register vs center")
        print()
        print("Only do this for specific problematic runs, not all data!")
        print("\n")

    # Action 3: ROI rescue strategies
    dropout_severe = df[df['status'] == 'DROPOUT_SEVERE']
    if len(dropout_severe) > 0:
        print("ACTION 3 (CONDITIONAL): ROI rescue for severe dropout")
        print("-" * 80)
        print(f"Affected: {len(dropout_severe)} ROI measurements")
        print()
        print("Only if Dice >= 0.85 (coreg is good but dropout is physical):")
        print("  1. Try lower probability threshold (35 or 20)")
        print("  2. Try 2-voxel dilation (with brain mask clip)")
        print("  3. Consider surface-based analysis")
        print()
        print("CAUTION: This is 'rescue mode', not default!")
        print("\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_qc_results.py <tsv_file1> [tsv_file2] ...")
        print("Example: python diagnose_qc_results.py derivatives/QC/qc_runwise_sub-*.tsv")
        sys.exit(1)

    tsv_files = sys.argv[1:]

    print("\n" + "="*80)
    print("LOADING QC DATA")
    print("="*80 + "\n")
    print(f"Files to process: {len(tsv_files)}")
    for f in tsv_files:
        print(f"  - {f}")

    df = load_qc_data(tsv_files)

    # Run diagnostics
    print_summary(df)
    print_problematic_runs(df)
    print_subject_summary(df)
    generate_action_plan(df)

    # Save classified data
    output_file = "derivatives/QC/qc_classified.tsv"
    df['status'] = df.apply(classify_run, axis=1)
    df.to_csv(output_file, sep='\t', index=False)
    print(f"\n✅ Classified data saved to: {output_file}\n")

if __name__ == "__main__":
    main()
