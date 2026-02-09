#!/usr/bin/env python3
"""
Compare SRM vs PCA-Procrustes vs ANOVA-Procrustes

Loads results from all three methods and creates comprehensive comparison.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from scipy.stats import ttest_ind

# Directories
SRM_DIR = Path("../results/srm_between_subject/test_local_20260206_220129/V1")
PCA_DIR = Path("results/pca_n5_optimal_step3/V1")
ANOVA_DIR = Path("results/anova_k200_optimal_step3/V1")
OUTPUT_DIR = Path("results/three_method_comparison")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Subject groups
HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

def load_reliability(method_dir, subjects):
    """Load split-half reliability for all subjects."""
    reliabilities = []
    for subj in subjects:
        reliability_path = method_dir / f"{subj}_split_half_reliability.json"
        if reliability_path.exists():
            with open(reliability_path) as f:
                data = json.load(f)
                reliabilities.append(data['split_half_reliability'])
        else:
            reliabilities.append(np.nan)
    return np.array(reliabilities)

def load_disparities(procrustes_dir, subjects):
    """Load Procrustes disparities for subjects."""
    disparities = []
    for subj in subjects:
        disparity_path = procrustes_dir / f"{subj}_disparity.json"
        if disparity_path.exists():
            with open(disparity_path) as f:
                data = json.load(f)
                disparities.append(data['disparity_odd'])
        else:
            disparities.append(np.nan)
    return np.array(disparities)

print("=== Loading Results ===")

# Load SRM results
print("\nSRM k=4:")
srm_hc_rel = load_reliability(SRM_DIR, HC_SUBJECTS)
srm_cvd_rel = load_reliability(SRM_DIR, CVD_SUBJECTS)
print(f"  HC reliability: {np.nanmean(srm_hc_rel):.4f} ± {np.nanstd(srm_hc_rel):.4f}")
print(f"  CVD reliability: {np.nanmean(srm_cvd_rel):.4f} ± {np.nanstd(srm_cvd_rel):.4f}")

# Load PCA results
print("\nPCA n=5:")
pca_hc_rel = load_reliability(PCA_DIR, HC_SUBJECTS)
pca_cvd_rel = load_reliability(PCA_DIR, CVD_SUBJECTS)
print(f"  HC reliability: {np.nanmean(pca_hc_rel):.4f} ± {np.nanstd(pca_hc_rel):.4f}")
print(f"  CVD reliability: {np.nanmean(pca_cvd_rel):.4f} ± {np.nanstd(pca_cvd_rel):.4f}")

# Load PCA disparities
pca_procrustes_dir = Path("results/pca_n5_optimal_step2/V1")
pca_hc_disp = load_disparities(pca_procrustes_dir, HC_SUBJECTS)
pca_cvd_disp = load_disparities(pca_procrustes_dir, CVD_SUBJECTS)
print(f"  HC disparity: {np.nanmean(pca_hc_disp):.4f} ± {np.nanstd(pca_hc_disp):.4f}")
print(f"  CVD disparity: {np.nanmean(pca_cvd_disp):.4f} ± {np.nanstd(pca_cvd_disp):.4f}")

# Load ANOVA results
print("\nANOVA k=200:")
anova_hc_rel = load_reliability(ANOVA_DIR, HC_SUBJECTS)
anova_cvd_rel = load_reliability(ANOVA_DIR, CVD_SUBJECTS)
print(f"  HC reliability: {np.nanmean(anova_hc_rel):.4f} ± {np.nanstd(anova_hc_rel):.4f}")
print(f"  CVD reliability: {np.nanmean(anova_cvd_rel):.4f} ± {np.nanstd(anova_cvd_rel):.4f}")

# Load ANOVA disparities
anova_procrustes_dir = Path("results/anova_k200_optimal_step2/V1")
anova_hc_disp = load_disparities(anova_procrustes_dir, HC_SUBJECTS)
anova_cvd_disp = load_disparities(anova_procrustes_dir, CVD_SUBJECTS)
print(f"  HC disparity: {np.nanmean(anova_hc_disp):.4f} ± {np.nanstd(anova_hc_disp):.4f}")
print(f"  CVD disparity: {np.nanmean(anova_cvd_disp):.4f} ± {np.nanstd(anova_cvd_disp):.4f}")

# Statistical comparison
print("\n=== Statistical Comparison (HC vs CVD) ===")
methods = ['SRM k=4', 'PCA n=5', 'ANOVA k=200']
hc_rels = [srm_hc_rel, pca_hc_rel, anova_hc_rel]
cvd_rels = [srm_cvd_rel, pca_cvd_rel, anova_cvd_rel]

for method, hc_rel, cvd_rel in zip(methods, hc_rels, cvd_rels):
    t_stat, p_val = ttest_ind(hc_rel, cvd_rel, nan_policy='omit')
    print(f"{method}: t={t_stat:.3f}, p={p_val:.4f}")

# Create comparison plots
print("\n=== Creating Comparison Plots ===")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Reliability comparison boxplot
ax = axes[0, 0]
positions = np.arange(3)
width = 0.35

hc_data = [srm_hc_rel, pca_hc_rel, anova_hc_rel]
cvd_data = [srm_cvd_rel, pca_cvd_rel, anova_cvd_rel]

bp1 = ax.boxplot(hc_data, positions=positions - width/2, widths=width,
                  patch_artist=True, showmeans=True,
                  boxprops=dict(facecolor='lightblue'),
                  medianprops=dict(color='darkblue', linewidth=2),
                  meanprops=dict(marker='o', markerfacecolor='darkblue', markersize=6))

bp2 = ax.boxplot(cvd_data, positions=positions + width/2, widths=width,
                  patch_artist=True, showmeans=True,
                  boxprops=dict(facecolor='lightcoral'),
                  medianprops=dict(color='darkred', linewidth=2),
                  meanprops=dict(marker='o', markerfacecolor='darkred', markersize=6))

ax.set_xticks(positions)
ax.set_xticklabels(['SRM k=4', 'PCA n=5', 'ANOVA k=200'])
ax.set_ylabel('Split-Half Reliability')
ax.set_title('RDM Reliability Comparison')
ax.legend([bp1["boxes"][0], bp2["boxes"][0]], ['HC', 'CVD'], loc='best')
ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax.grid(True, alpha=0.3)

# 2. Disparity comparison boxplot (Procrustes only)
ax = axes[0, 1]
positions = np.arange(2)

disp_hc_data = [pca_hc_disp, anova_hc_disp]
disp_cvd_data = [pca_cvd_disp, anova_cvd_disp]

bp1 = ax.boxplot(disp_hc_data, positions=positions - width/2, widths=width,
                  patch_artist=True, showmeans=True,
                  boxprops=dict(facecolor='lightblue'),
                  medianprops=dict(color='darkblue', linewidth=2),
                  meanprops=dict(marker='o', markerfacecolor='darkblue', markersize=6))

bp2 = ax.boxplot(disp_cvd_data, positions=positions + width/2, widths=width,
                  patch_artist=True, showmeans=True,
                  boxprops=dict(facecolor='lightcoral'),
                  medianprops=dict(color='darkred', linewidth=2),
                  meanprops=dict(marker='o', markerfacecolor='darkred', markersize=6))

ax.set_xticks(positions)
ax.set_xticklabels(['PCA n=5', 'ANOVA k=200'])
ax.set_ylabel('Procrustes Disparity')
ax.set_title('Procrustes Disparity Comparison')
ax.legend([bp1["boxes"][0], bp2["boxes"][0]], ['HC', 'CVD'], loc='best')
ax.grid(True, alpha=0.3)

# 3. Per-subject reliability comparison
ax = axes[1, 0]
x_pos = np.arange(len(ALL_SUBJECTS))
width = 0.25

ax.bar(x_pos - width, np.concatenate([srm_hc_rel, srm_cvd_rel]),
       width, label='SRM k=4', alpha=0.8)
ax.bar(x_pos, np.concatenate([pca_hc_rel, pca_cvd_rel]),
       width, label='PCA n=5', alpha=0.8)
ax.bar(x_pos + width, np.concatenate([anova_hc_rel, anova_cvd_rel]),
       width, label='ANOVA k=200', alpha=0.8)

ax.set_xticks(x_pos)
ax.set_xticklabels(ALL_SUBJECTS, rotation=45)
ax.set_ylabel('Split-Half Reliability')
ax.set_title('Per-Subject Reliability Comparison')
ax.legend()
ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax.axvline(x=5.5, color='black', linestyle='--', linewidth=1, alpha=0.3)
ax.text(2.5, ax.get_ylim()[1]*0.9, 'HC', ha='center', fontsize=10, fontweight='bold')
ax.text(7, ax.get_ylim()[1]*0.9, 'CVD', ha='center', fontsize=10, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# 4. Summary table
ax = axes[1, 1]
ax.axis('off')

# Create summary statistics
summary_data = {
    'Method': ['SRM k=4', 'PCA n=5', 'ANOVA k=200'],
    'HC Rel': [f"{np.nanmean(srm_hc_rel):.3f}±{np.nanstd(srm_hc_rel):.3f}",
               f"{np.nanmean(pca_hc_rel):.3f}±{np.nanstd(pca_hc_rel):.3f}",
               f"{np.nanmean(anova_hc_rel):.3f}±{np.nanstd(anova_hc_rel):.3f}"],
    'CVD Rel': [f"{np.nanmean(srm_cvd_rel):.3f}±{np.nanstd(srm_cvd_rel):.3f}",
                f"{np.nanmean(pca_cvd_rel):.3f}±{np.nanstd(pca_cvd_rel):.3f}",
                f"{np.nanmean(anova_cvd_rel):.3f}±{np.nanstd(anova_cvd_rel):.3f}"],
    'HC Disp': ['-',
                f"{np.nanmean(pca_hc_disp):.3f}±{np.nanstd(pca_hc_disp):.3f}",
                f"{np.nanmean(anova_hc_disp):.3f}±{np.nanstd(anova_hc_disp):.3f}"],
    'CVD Disp': ['-',
                 f"{np.nanmean(pca_cvd_disp):.3f}±{np.nanstd(pca_cvd_disp):.3f}",
                 f"{np.nanmean(anova_cvd_disp):.3f}±{np.nanstd(anova_cvd_disp):.3f}"],
}

df = pd.DataFrame(summary_data)
table = ax.table(cellText=df.values, colLabels=df.columns,
                cellLoc='center', loc='center',
                bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Style header
for i in range(len(df.columns)):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(df) + 1):
    for j in range(len(df.columns)):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#f0f0f0')

ax.set_title('Summary Statistics\n(Mean±SD)', fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'three_method_comparison.png', dpi=300, bbox_inches='tight')
print(f"  Saved: {OUTPUT_DIR / 'three_method_comparison.png'}")

# Save numerical results
results = {
    'roi': 'V1',
    'methods': {
        'SRM_k4': {
            'hc_reliability': {'mean': float(np.nanmean(srm_hc_rel)),
                              'std': float(np.nanstd(srm_hc_rel)),
                              'values': srm_hc_rel.tolist()},
            'cvd_reliability': {'mean': float(np.nanmean(srm_cvd_rel)),
                               'std': float(np.nanstd(srm_cvd_rel)),
                               'values': srm_cvd_rel.tolist()},
        },
        'PCA_n5': {
            'hc_reliability': {'mean': float(np.nanmean(pca_hc_rel)),
                              'std': float(np.nanstd(pca_hc_rel)),
                              'values': pca_hc_rel.tolist()},
            'cvd_reliability': {'mean': float(np.nanmean(pca_cvd_rel)),
                               'std': float(np.nanstd(pca_cvd_rel)),
                               'values': pca_cvd_rel.tolist()},
            'hc_disparity': {'mean': float(np.nanmean(pca_hc_disp)),
                            'std': float(np.nanstd(pca_hc_disp)),
                            'values': pca_hc_disp.tolist()},
            'cvd_disparity': {'mean': float(np.nanmean(pca_cvd_disp)),
                             'std': float(np.nanstd(pca_cvd_disp)),
                             'values': pca_cvd_disp.tolist()},
        },
        'ANOVA_k200': {
            'hc_reliability': {'mean': float(np.nanmean(anova_hc_rel)),
                              'std': float(np.nanstd(anova_hc_rel)),
                              'values': anova_hc_rel.tolist()},
            'cvd_reliability': {'mean': float(np.nanmean(anova_cvd_rel)),
                               'std': float(np.nanstd(anova_cvd_rel)),
                               'values': anova_cvd_rel.tolist()},
            'hc_disparity': {'mean': float(np.nanmean(anova_hc_disp)),
                            'std': float(np.nanstd(anova_hc_disp)),
                            'values': anova_hc_disp.tolist()},
            'cvd_disparity': {'mean': float(np.nanmean(anova_cvd_disp)),
                             'std': float(np.nanstd(anova_cvd_disp)),
                             'values': anova_cvd_disp.tolist()},
        },
    },
    'statistical_tests': {
        'SRM_k4': {
            't_statistic': float(ttest_ind(srm_hc_rel, srm_cvd_rel, nan_policy='omit')[0]),
            'p_value': float(ttest_ind(srm_hc_rel, srm_cvd_rel, nan_policy='omit')[1]),
        },
        'PCA_n5': {
            't_statistic': float(ttest_ind(pca_hc_rel, pca_cvd_rel, nan_policy='omit')[0]),
            'p_value': float(ttest_ind(pca_hc_rel, pca_cvd_rel, nan_policy='omit')[1]),
        },
        'ANOVA_k200': {
            't_statistic': float(ttest_ind(anova_hc_rel, anova_cvd_rel, nan_policy='omit')[0]),
            'p_value': float(ttest_ind(anova_hc_rel, anova_cvd_rel, nan_policy='omit')[1]),
        },
    }
}

with open(OUTPUT_DIR / 'three_method_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"  Saved: {OUTPUT_DIR / 'three_method_comparison.json'}")

print("\n✓ Three-method comparison complete")
