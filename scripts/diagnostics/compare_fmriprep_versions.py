#!/usr/bin/env python3
"""
Compare QC metrics between fMRIPrep versions

Usage:
  python compare_fmriprep_versions.py preps/qc_runwise_sub-*.tsv derivatives/QC_new/qc_runwise_sub-*.tsv
"""

import pandas as pd
import sys
import glob
from pathlib import Path

def load_qc_data(pattern):
    """Load and combine QC TSV files"""
    files = glob.glob(pattern)
    if not files:
        return None

    dfs = []
    for f in files:
        df = pd.read_csv(f, sep='\t')
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

def classify_status(df):
    """Classify runs by QC status"""
    df = df.copy()
    df['status'] = 'UNKNOWN'

    for idx, row in df.iterrows():
        if pd.isna(row['roi_vox']) or row['roi_vox'] == 0:
            df.loc[idx, 'status'] = 'ROI_ZERO'
        elif pd.isna(row['dice']) or row['dice'] < 0.80:
            df.loc[idx, 'status'] = 'COREG_POOR'
        elif row['dice'] >= 0.90:
            df.loc[idx, 'status'] = 'EXCELLENT'
        elif row['dice'] >= 0.85:
            df.loc[idx, 'status'] = 'GOOD'
        else:
            df.loc[idx, 'status'] = 'ACCEPTABLE'

    return df

def print_summary(df, label):
    """Print summary statistics"""
    print("=" * 80)
    print(f"{label}")
    print("=" * 80)

    dice_valid = df['dice'].dropna()
    print(f"\n📊 Overall (n={len(df)}):")
    print(f"   Dice: {dice_valid.mean():.3f} ± {dice_valid.std():.3f} (range: {dice_valid.min():.3f}-{dice_valid.max():.3f})")
    print(f"   Overlap frac: {df['overlap_frac'].mean():.3f} ± {df['overlap_frac'].std():.3f}")

    status_counts = df['status'].value_counts()
    print(f"\n🎯 Status:")
    for status in ['EXCELLENT', 'GOOD', 'ACCEPTABLE', 'COREG_POOR', 'ROI_ZERO']:
        count = status_counts.get(status, 0)
        pct = 100 * count / len(df)
        emoji = '✅' if status in ['EXCELLENT', 'GOOD'] else ('⚠️' if status == 'ACCEPTABLE' else '❌')
        print(f"   {emoji} {status:15s}: {count:3d}/{len(df)} ({pct:5.1f}%)")

    print(f"\n👥 By Subject:")
    print(f"{'Sub':>4s} | {'Dice':>6s} | {'Overlap':>7s} | {'ROI_0%':>7s} | {'Pass%':>6s}")
    print("-" * 50)

    for sub in sorted(df['sub'].unique()):
        sub_df = df[df['sub'] == sub]
        dice_mean = sub_df['dice'].mean()
        overlap_mean = sub_df['overlap_frac'].mean()
        roi_zero_pct = 100 * (sub_df['roi_vox'] == 0).sum() / len(sub_df)
        pass_pct = 100 * (sub_df['dice'] >= 0.80).sum() / len(sub_df)

        print(f"{int(sub):>4d} | {dice_mean:6.3f} | {overlap_mean:7.3f} | {roi_zero_pct:6.1f}% | {pass_pct:5.1f}%")

def compare_versions(old_df, new_df):
    """Compare two versions"""
    print("\n" + "=" * 80)
    print("📈 IMPROVEMENT ANALYSIS")
    print("=" * 80)

    old_dice = old_df['dice'].mean()
    new_dice = new_df['dice'].mean()
    dice_delta = new_dice - old_dice

    old_pass = 100 * (old_df['dice'] >= 0.80).sum() / len(old_df)
    new_pass = 100 * (new_df['dice'] >= 0.80).sum() / len(new_df)

    old_roi_zero = 100 * (old_df['roi_vox'] == 0).sum() / len(old_df)
    new_roi_zero = 100 * (new_df['roi_vox'] == 0).sum() / len(new_df)

    print(f"\nDice Coefficient:")
    print(f"   Old: {old_dice:.3f}")
    print(f"   New: {new_dice:.3f}")
    print(f"   Δ:   {dice_delta:+.3f} ({100*dice_delta/old_dice:+.1f}%)")

    print(f"\nPass Rate (Dice >= 0.80):")
    print(f"   Old: {old_pass:.1f}%")
    print(f"   New: {new_pass:.1f}%")
    print(f"   Δ:   {new_pass - old_pass:+.1f}pp")

    print(f"\nROI Generation Failure:")
    print(f"   Old: {old_roi_zero:.1f}%")
    print(f"   New: {new_roi_zero:.1f}%")
    print(f"   Δ:   {new_roi_zero - old_roi_zero:+.1f}pp")

    print("\n" + "=" * 80)
    print("🎯 DECISION")
    print("=" * 80)

    if new_dice >= 0.85:
        print("✅ PROBLEM SOLVED!")
        print("   → New Dice >= 0.85 target")
        print("   → Proceed to baseline analysis")
    elif new_dice >= 0.70:
        print("⚠️  PARTIAL IMPROVEMENT")
        print("   → Dice improved but still below target")
        print("   → Investigate remaining failures")
        print("   → Consider per-run fixes")
    else:
        print("❌ INSUFFICIENT IMPROVEMENT")
        print("   → Dice still < 0.70")
        print("   → Need deeper investigation:")
        print("      1. Check transform inversion (ACTION 1)")
        print("      2. Analyze T1/BOLD mask mismatch (ACTION 2)")
        print("      3. Visual inspection (ACTION 3)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python compare_fmriprep_versions.py <old_pattern> [new_pattern]")
        print("\nExample:")
        print("  python compare_fmriprep_versions.py preps/qc_runwise_sub-*.tsv")
        print("  python compare_fmriprep_versions.py preps/qc_runwise_sub-*.tsv derivatives/QC_new/qc_runwise_sub-*.tsv")
        sys.exit(1)

    # Load old version
    old_pattern = sys.argv[1]
    old_df = load_qc_data(old_pattern)
    if old_df is None:
        print(f"❌ No files found matching: {old_pattern}")
        sys.exit(1)

    old_df = classify_status(old_df)
    print_summary(old_df, f"OLD VERSION: {old_pattern}")

    # Load new version if provided
    if len(sys.argv) >= 3:
        new_pattern = sys.argv[2]
        new_df = load_qc_data(new_pattern)
        if new_df is None:
            print(f"❌ No files found matching: {new_pattern}")
            sys.exit(1)

        new_df = classify_status(new_df)
        print("\n")
        print_summary(new_df, f"NEW VERSION: {new_pattern}")

        compare_versions(old_df, new_df)
    else:
        print("\n⏳ New version not provided - showing old version only")
        print("   Run again with new QC files to compare")
