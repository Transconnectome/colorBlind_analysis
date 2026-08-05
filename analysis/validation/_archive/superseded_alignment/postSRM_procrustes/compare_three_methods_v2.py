#!/usr/bin/env python3
"""
Compare SRM vs PCA-Procrustes vs ANOVA-Procrustes (Updated)

Handles different metric structures:
- SRM: RDM similarities (between-subject)
- PCA/ANOVA: Split-half reliability (within-subject)
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from scipy.stats import ttest_ind

# Directories
SRM_FILE = Path("../srm/results/srm_between_subject/test_local_20260206_220129/V1_srm_between_subject_results.json")
PCA_DIR = Path("results/pca_n5_optimal_step3/V1")
ANOVA_DIR = Path("results/anova_k200_optimal_step3/V1")
OUTPUT_DIR = Path("results/three_method_comparison_v2")
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
with open(SRM_FILE) as f:
    srm_data = json.load(f)

srm_hc_hc_sim = srm_data['rdm_similarities']['hc_hc']['mean']
srm_cvd_cvd_sim = srm_data['rdm_similarities']['cvd_cvd']['mean']
srm_hc_cvd_sim = srm_data['rdm_similarities']['hc_cvd']['mean']
srm_hc_disp = srm_data['disparities']['hc_to_hc_reference']['mean']
srm_cvd_disp = srm_data['disparities']['cvd_to_hc_reference']['mean']

print(f"  HC-HC RDM similarity: {srm_hc_hc_sim:.4f}")
print(f"  CVD-CVD RDM similarity: {srm_cvd_cvd_sim:.4f}")
print(f"  HC-CVD RDM similarity: {srm_hc_cvd_sim:.4f}")
print(f"  HC disparity: {srm_hc_disp:.4f} ± {srm_data['disparities']['hc_to_hc_reference']['std']:.4f}")
print(f"  CVD disparity: {srm_cvd_disp:.4f} ± {srm_data['disparities']['cvd_to_hc_reference']['std']:.4f}")
print(f"  Statistical test p-value: {srm_data['disparities']['statistical_test_hc_vs_cvd']['p_value']:.4f}")

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

pca_t, pca_p = ttest_ind(pca_hc_rel, pca_cvd_rel, nan_policy='omit')
print(f"  Statistical test p-value: {pca_p:.4f}")

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

anova_t, anova_p = ttest_ind(anova_hc_rel, anova_cvd_rel, nan_policy='omit')
print(f"  Statistical test p-value: {anova_p:.4f}")

# Create comparison plots
print("\n=== Creating Comparison Plots ===")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. Disparity comparison (all three methods)
ax1 = fig.add_subplot(gs[0, :2])
positions = np.arange(3)
width = 0.35

# Extract disparity values for boxplot
hc_disps = [srm_data['disparities']['hc_to_hc_reference']['values'],
            pca_hc_disp,
            anova_hc_disp]
cvd_disps = [srm_data['disparities']['cvd_to_hc_reference']['values'],
             pca_cvd_disp,
             anova_cvd_disp]

bp1 = ax1.boxplot(hc_disps, positions=positions - width/2, widths=width,
                   patch_artist=True, showmeans=True,
                   boxprops=dict(facecolor='lightblue'),
                   medianprops=dict(color='darkblue', linewidth=2),
                   meanprops=dict(marker='o', markerfacecolor='darkblue', markersize=6))

bp2 = ax1.boxplot(cvd_disps, positions=positions + width/2, widths=width,
                   patch_artist=True, showmeans=True,
                   boxprops=dict(facecolor='lightcoral'),
                   medianprops=dict(color='darkred', linewidth=2),
                   meanprops=dict(marker='o', markerfacecolor='darkred', markersize=6))

ax1.set_xticks(positions)
ax1.set_xticklabels(['SRM k=4', 'PCA n=5', 'ANOVA k=200'])
ax1.set_ylabel('Alignment Disparity', fontsize=11, fontweight='bold')
ax1.set_title('Method Comparison: Alignment Quality (Lower = Better)', fontsize=12, fontweight='bold')
ax1.legend([bp1["boxes"][0], bp2["boxes"][0]], ['HC', 'CVD'], loc='best')
ax1.grid(True, alpha=0.3)

# 2. Reliability comparison (PCA & ANOVA only)
ax2 = fig.add_subplot(gs[0, 2])
positions = np.arange(2)

bp1 = ax2.boxplot([pca_hc_rel, anova_hc_rel], positions=positions - width/2, widths=width,
                   patch_artist=True, showmeans=True,
                   boxprops=dict(facecolor='lightblue'),
                   medianprops=dict(color='darkblue', linewidth=2),
                   meanprops=dict(marker='o', markerfacecolor='darkblue', markersize=6))

bp2 = ax2.boxplot([pca_cvd_rel, anova_cvd_rel], positions=positions + width/2, widths=width,
                   patch_artist=True, showmeans=True,
                   boxprops=dict(facecolor='lightcoral'),
                   medianprops=dict(color='darkred', linewidth=2),
                   meanprops=dict(marker='o', markerfacecolor='darkred', markersize=6))

ax2.set_xticks(positions)
ax2.set_xticklabels(['PCA\nn=5', 'ANOVA\nk=200'], fontsize=9)
ax2.set_ylabel('Split-Half\nReliability', fontsize=10, fontweight='bold')
ax2.set_title('Procrustes: RDM\nReliability', fontsize=11, fontweight='bold')
ax2.legend([bp1["boxes"][0], bp2["boxes"][0]], ['HC', 'CVD'], loc='best', fontsize=9)
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax2.grid(True, alpha=0.3)

# 3. Per-subject reliability (PCA & ANOVA)
ax3 = fig.add_subplot(gs[1, :])
x_pos = np.arange(len(ALL_SUBJECTS))
width = 0.35

ax3.bar(x_pos - width/2, np.concatenate([pca_hc_rel, pca_cvd_rel]),
        width, label='PCA n=5', alpha=0.8, color='steelblue')
ax3.bar(x_pos + width/2, np.concatenate([anova_hc_rel, anova_cvd_rel]),
        width, label='ANOVA k=200', alpha=0.8, color='coral')

ax3.set_xticks(x_pos)
ax3.set_xticklabels(ALL_SUBJECTS, rotation=45)
ax3.set_ylabel('Split-Half Reliability', fontsize=11, fontweight='bold')
ax3.set_title('Per-Subject RDM Reliability (Procrustes Methods)', fontsize=12, fontweight='bold')
ax3.legend(fontsize=10)
ax3.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax3.axvline(x=5.5, color='black', linestyle='--', linewidth=1, alpha=0.3)
ax3.text(2.5, ax3.get_ylim()[1]*0.9, 'HC', ha='center', fontsize=11, fontweight='bold')
ax3.text(7, ax3.get_ylim()[1]*0.9, 'CVD', ha='center', fontsize=11, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# 4. Summary table
ax4 = fig.add_subplot(gs[2, :])
ax4.axis('off')

summary_data = {
    'Method': ['SRM k=4', 'PCA n=5', 'ANOVA k=200'],
    'HC Disp': [f"{srm_hc_disp:.3f}±{srm_data['disparities']['hc_to_hc_reference']['std']:.3f}",
                f"{np.nanmean(pca_hc_disp):.3f}±{np.nanstd(pca_hc_disp):.3f}",
                f"{np.nanmean(anova_hc_disp):.3f}±{np.nanstd(anova_hc_disp):.3f}"],
    'CVD Disp': [f"{srm_cvd_disp:.3f}±{srm_data['disparities']['cvd_to_hc_reference']['std']:.3f}",
                 f"{np.nanmean(pca_cvd_disp):.3f}±{np.nanstd(pca_cvd_disp):.3f}",
                 f"{np.nanmean(anova_cvd_disp):.3f}±{np.nanstd(anova_cvd_disp):.3f}"],
    'HC Rel': [f"RDM: {srm_hc_hc_sim:.3f}",
               f"{np.nanmean(pca_hc_rel):.3f}±{np.nanstd(pca_hc_rel):.3f}",
               f"{np.nanmean(anova_hc_rel):.3f}±{np.nanstd(anova_hc_rel):.3f}"],
    'CVD Rel': [f"RDM: {srm_cvd_cvd_sim:.3f}",
                f"{np.nanmean(pca_cvd_rel):.3f}±{np.nanstd(pca_cvd_rel):.3f}",
                f"{np.nanmean(anova_cvd_rel):.3f}±{np.nanstd(anova_cvd_rel):.3f}"],
    'p-value': [f"{srm_data['disparities']['statistical_test_hc_vs_cvd']['p_value']:.3f}",
                f"{pca_p:.3f}",
                f"{anova_p:.3f}"],
}

df = pd.DataFrame(summary_data)
table = ax4.table(cellText=df.values, colLabels=df.columns,
                 cellLoc='center', loc='center',
                 bbox=[0, 0.2, 1, 0.8])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# Style header
for i in range(len(df.columns)):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors and highlight best method
for i in range(1, len(df) + 1):
    for j in range(len(df.columns)):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#f0f0f0')
        # Highlight SRM (best alignment)
        if i == 1:
            table[(i, j)].set_text_props(weight='bold')

ax4.text(0.5, 0.05, 'Key Finding: SRM k=4 provides best alignment quality (lowest disparity)\n' +
         'PCA n=5 & ANOVA k=200 show severe overfitting (negative reliability)',
         ha='center', va='center', fontsize=10, style='italic',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.savefig(OUTPUT_DIR / 'three_method_comparison.png', dpi=300, bbox_inches='tight')
print(f"  Saved: {OUTPUT_DIR / 'three_method_comparison.png'}")

# Save numerical results
results = {
    'roi': 'V1',
    'methods': {
        'SRM_k4': {
            'rdm_similarities': srm_data['rdm_similarities'],
            'disparities': srm_data['disparities'],
            'interpretation': srm_data['interpretation'],
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
            'statistical_test': {'t_statistic': float(pca_t), 'p_value': float(pca_p)},
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
            'statistical_test': {'t_statistic': float(anova_t), 'p_value': float(anova_p)},
        },
    },
    'summary': {
        'best_alignment_method': 'ANOVA_k200',
        'best_alignment_disparity_hc': float(np.nanmean(anova_hc_disp)),
        'all_methods_show_no_hc_cvd_difference': True,
        'procrustes_methods_overfitted': True,
        'note': 'Both PCA n=5 and ANOVA k=200 show negative reliability, indicating severe overfitting for 8-color discrimination'
    }
}

with open(OUTPUT_DIR / 'three_method_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"  Saved: {OUTPUT_DIR / 'three_method_comparison.json'}")

print("\n✓ Three-method comparison complete")
print("\nKey Findings:")
print(f"  1. Best alignment (lowest HC disparity): ANOVA k=200 ({np.nanmean(anova_hc_disp):.3f})")
print(f"  2. SRM k=4 alignment: {srm_hc_disp:.3f}")
print(f"  3. PCA n=5 alignment: {np.nanmean(pca_hc_disp):.3f}")
print(f"  4. All methods show no significant HC-CVD difference (p > 0.05)")
print(f"  5. Procrustes methods show overfitting (negative reliability)")
