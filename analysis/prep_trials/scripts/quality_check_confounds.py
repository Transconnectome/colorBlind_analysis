#!/usr/bin/env python3
"""
Quality Check for Confounds Files

Analyzes motion and confound quality across all subjects and runs
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (15, 10)

# Paths
CONFOUNDS_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/data/confounds')
OUTPUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/qc_results')
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

print("="*80)
print("Confounds Quality Check")
print("="*80)
print()

# Load all confounds files
confounds_files = sorted(CONFOUNDS_DIR.glob('*_desc-confounds_timeseries.tsv'))
print(f"Found {len(confounds_files)} confounds files")
print()

# Collect statistics
motion_stats = []

for f in confounds_files:
    # Parse filename
    parts = f.stem.split('_')
    subject = parts[0].replace('sub-', '')
    run = parts[2].replace('run-', '')

    # Load confounds
    df = pd.read_csv(f, sep='\t')

    # Calculate statistics
    fd = df['framewise_displacement']

    stats = {
        'subject': subject,
        'run': int(run),
        'n_volumes': len(df),
        'mean_fd': fd.mean(),
        'median_fd': fd.median(),
        'max_fd': fd.max(),
        'std_fd': fd.std(),
        'fd_gt_0.5': (fd > 0.5).sum(),
        'fd_gt_0.5_pct': (fd > 0.5).sum() / len(fd) * 100,
        'fd_gt_0.9': (fd > 0.9).sum(),
        'fd_gt_0.9_pct': (fd > 0.9).sum() / len(fd) * 100,
        'mean_trans': df[['trans_x', 'trans_y', 'trans_z']].abs().mean().mean(),
        'max_trans': df[['trans_x', 'trans_y', 'trans_z']].abs().max().max(),
        'mean_rot': df[['rot_x', 'rot_y', 'rot_z']].abs().mean().mean(),
        'max_rot': df[['rot_x', 'rot_y', 'rot_z']].abs().max().max(),
    }

    motion_stats.append(stats)

# Create DataFrame
motion_df = pd.DataFrame(motion_stats)

print("="*80)
print("Overall Statistics")
print("="*80)
print()
print(f"Total subjects: {motion_df['subject'].nunique()}")
print(f"Total runs: {len(motion_df)}")
print(f"Volumes per run: {motion_df['n_volumes'].iloc[0]}")
print()

print("Motion Summary (all data):")
print(f"  Mean FD: {motion_df['mean_fd'].mean():.4f} mm (±{motion_df['mean_fd'].std():.4f})")
print(f"  Median FD: {motion_df['median_fd'].median():.4f} mm")
print(f"  Max FD: {motion_df['max_fd'].max():.4f} mm")
print(f"  High motion volumes (>0.5mm): {motion_df['fd_gt_0.5_pct'].mean():.1f}% (±{motion_df['fd_gt_0.5_pct'].std():.1f})")
print(f"  Very high motion volumes (>0.9mm): {motion_df['fd_gt_0.9_pct'].mean():.1f}% (±{motion_df['fd_gt_0.9_pct'].std():.1f})")
print()

# Per-subject summary
print("="*80)
print("Per-Subject Summary")
print("="*80)
print()

subject_summary = motion_df.groupby('subject').agg({
    'mean_fd': ['mean', 'std'],
    'max_fd': 'max',
    'fd_gt_0.5_pct': 'mean',
    'fd_gt_0.9_pct': 'mean'
}).round(3)

print(subject_summary)
print()

# Identify problematic subjects/runs
print("="*80)
print("Quality Assessment")
print("="*80)
print()

# Thresholds (from literature)
MEAN_FD_THRESHOLD = 0.5  # mm
HIGH_MOTION_PCT_THRESHOLD = 30  # %

problematic_runs = motion_df[
    (motion_df['mean_fd'] > MEAN_FD_THRESHOLD) |
    (motion_df['fd_gt_0.5_pct'] > HIGH_MOTION_PCT_THRESHOLD)
]

if len(problematic_runs) > 0:
    print(f"⚠️  Problematic runs (n={len(problematic_runs)}):")
    print(f"   (mean FD > {MEAN_FD_THRESHOLD}mm OR high motion > {HIGH_MOTION_PCT_THRESHOLD}%)")
    print()
    for _, row in problematic_runs.iterrows():
        print(f"   sub-{row['subject']} run-{row['run']}: "
              f"mean FD={row['mean_fd']:.3f}mm, "
              f"high motion={row['fd_gt_0.5_pct']:.1f}%")
    print()
else:
    print("✅ All runs have acceptable motion quality")
    print()

# Check for outliers (> 3 SD from mean)
mean_fd_mean = motion_df['mean_fd'].mean()
mean_fd_std = motion_df['mean_fd'].std()
outliers = motion_df[motion_df['mean_fd'] > mean_fd_mean + 3*mean_fd_std]

if len(outliers) > 0:
    print(f"⚠️  Statistical outliers (n={len(outliers)}):")
    print(f"   (mean FD > {mean_fd_mean + 3*mean_fd_std:.3f}mm)")
    for _, row in outliers.iterrows():
        print(f"   sub-{row['subject']} run-{row['run']}: mean FD={row['mean_fd']:.3f}mm")
    print()

# Save summary CSV
motion_df.to_csv(OUTPUT_DIR / 'motion_summary.csv', index=False)
print(f"✅ Summary saved: {OUTPUT_DIR / 'motion_summary.csv'}")
print()

# =========================================================================
# Visualization
# =========================================================================

print("="*80)
print("Generating Visualizations")
print("="*80)
print()

# Figure 1: FD distribution per subject
fig, axes = plt.subplots(2, 5, figsize=(20, 8), sharey=True)
axes = axes.flatten()

for idx, subject in enumerate(sorted(motion_df['subject'].unique())):
    ax = axes[idx]
    subject_data = motion_df[motion_df['subject'] == subject]

    runs = subject_data['run'].values
    mean_fds = subject_data['mean_fd'].values

    ax.bar(runs, mean_fds, color='steelblue', alpha=0.7)
    ax.axhline(y=0.5, color='orange', linestyle='--', label='0.5mm threshold')
    ax.set_xlabel('Run')
    ax.set_ylabel('Mean FD (mm)')
    ax.set_title(f'Subject {subject}')
    ax.set_xticks(runs)

    if idx == 0:
        ax.legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'fd_per_subject.png', dpi=150, bbox_inches='tight')
print(f"✅ Plot saved: {OUTPUT_DIR / 'fd_per_subject.png'}")

# Figure 2: Overall FD distribution
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Histogram
axes[0].hist(motion_df['mean_fd'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
axes[0].axvline(x=mean_fd_mean, color='red', linestyle='--', label=f'Mean: {mean_fd_mean:.3f}mm')
axes[0].axvline(x=0.5, color='orange', linestyle='--', label='0.5mm threshold')
axes[0].set_xlabel('Mean FD (mm)')
axes[0].set_ylabel('Count')
axes[0].set_title('Distribution of Mean FD Across Runs')
axes[0].legend()

# Box plot by subject
subject_order = sorted(motion_df['subject'].unique())
axes[1].boxplot([motion_df[motion_df['subject'] == s]['mean_fd'].values
                 for s in subject_order],
                labels=subject_order)
axes[1].axhline(y=0.5, color='orange', linestyle='--', alpha=0.5)
axes[1].set_xlabel('Subject')
axes[1].set_ylabel('Mean FD (mm)')
axes[1].set_title('FD Distribution by Subject')
axes[1].grid(axis='y', alpha=0.3)

# High motion percentage
axes[2].hist(motion_df['fd_gt_0.5_pct'], bins=20, color='coral', alpha=0.7, edgecolor='black')
axes[2].axvline(x=motion_df['fd_gt_0.5_pct'].mean(), color='red', linestyle='--',
               label=f'Mean: {motion_df["fd_gt_0.5_pct"].mean():.1f}%')
axes[2].set_xlabel('High Motion Volumes (%)')
axes[2].set_ylabel('Count')
axes[2].set_title('Percentage of High Motion Volumes (FD > 0.5mm)')
axes[2].legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'fd_distribution.png', dpi=150, bbox_inches='tight')
print(f"✅ Plot saved: {OUTPUT_DIR / 'fd_distribution.png'}")

# Figure 3: Heatmap
fig, ax = plt.subplots(figsize=(10, 8))

pivot = motion_df.pivot(index='subject', columns='run', values='mean_fd')
sns.heatmap(pivot, annot=True, fmt='.3f', cmap='YlOrRd', ax=ax,
            cbar_kws={'label': 'Mean FD (mm)'})
ax.set_title('Mean FD Heatmap (All Subjects × Runs)')
ax.set_xlabel('Run')
ax.set_ylabel('Subject')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'fd_heatmap.png', dpi=150, bbox_inches='tight')
print(f"✅ Plot saved: {OUTPUT_DIR / 'fd_heatmap.png'}")

print()

# =========================================================================
# Recommendations
# =========================================================================

print("="*80)
print("Recommendations for Analysis Pipeline")
print("="*80)
print()

# Calculate overall quality
overall_mean_fd = motion_df['mean_fd'].mean()
overall_high_motion_pct = motion_df['fd_gt_0.5_pct'].mean()

print(f"Data Quality: ", end='')
if overall_mean_fd < 0.3 and overall_high_motion_pct < 20:
    print("EXCELLENT ✅")
    quality = 'excellent'
elif overall_mean_fd < 0.5 and overall_high_motion_pct < 30:
    print("GOOD ✅")
    quality = 'good'
elif overall_mean_fd < 0.7 and overall_high_motion_pct < 40:
    print("ACCEPTABLE ⚠️")
    quality = 'acceptable'
else:
    print("POOR ❌")
    quality = 'poor'

print()

# Confound strategy
print("Recommended Confound Strategy:")
print()

if quality in ['excellent', 'good']:
    print("✅ Standard confound regression (no scrubbing needed)")
    print()
    print("   Use confounds:")
    print("   - Motion: trans_x, trans_y, trans_z, rot_x, rot_y, rot_z")
    print("   - Tissue: white_matter, csf")
    print("   - Drift: cosine00, cosine01, ...")
    print()
    print("   Optional:")
    print("   - Add global_signal if preferred")
    print("   - Add motion derivatives for better denoising")
    scrubbing_needed = False

elif quality == 'acceptable':
    print("⚠️  Standard confound regression + consider scrubbing high-motion volumes")
    print()
    print("   1. Basic confound regression (same as above)")
    print("   2. Optional: Flag volumes with FD > 0.5mm for scrubbing")
    print(f"      Affected volumes: {motion_df['fd_gt_0.5_pct'].mean():.1f}% on average")
    scrubbing_needed = True

else:
    print("❌ Requires aggressive denoising")
    print()
    print("   1. Use all available confounds")
    print("   2. Scrubbing: Remove volumes with FD > 0.5mm")
    print("   3. Consider ICA-AROMA or alternative denoising")
    scrubbing_needed = True

print()

# Pipeline modification decision
print("="*80)
print("Pipeline Modification Decision")
print("="*80)
print()

if not scrubbing_needed:
    print("✅ SIMPLE RE-RUN IS SUFFICIENT")
    print()
    print("   Modify pipeline to add confounds parameter:")
    print()
    print("   confounds = pd.read_csv(confounds_file, sep='\\t')")
    print("   confound_cols = ['trans_x', 'trans_y', 'trans_z',")
    print("                    'rot_x', 'rot_y', 'rot_z',")
    print("                    'white_matter', 'csf',")
    print("                    'cosine00', 'cosine01', ...]  # all cosines")
    print()
    print("   first_level_model.fit(bold_img, events=events,")
    print("                         confounds=confounds[confound_cols])")
    print()
    print("   No scrubbing or complex modifications needed!")

else:
    print("⚠️  NEEDS MODIFICATION + SCRUBBING")
    print()
    print("   1. Add confound regression (as above)")
    print("   2. Add scrubbing logic:")
    print()
    print("   # Identify high-motion volumes")
    print("   fd = confounds['framewise_displacement']")
    print("   scrub_mask = fd <= 0.5  # Keep volumes with FD <= 0.5mm")
    print()
    print("   # Apply mask to BOLD and events")
    print("   # (Implementation depends on your analysis framework)")

print()
print("="*80)
print("Quality Check Complete")
print("="*80)
print()
print(f"Results saved to: {OUTPUT_DIR}")
print()
