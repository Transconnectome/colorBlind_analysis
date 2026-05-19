#!/usr/bin/env python3
"""
Create Publication-Quality Bar Graph for Permutation Analysis
"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

print("="*80)
print("Creating Permutation Bar Graph")
print("="*80)

# Load data
comparison_df = pd.read_csv('results/permutation_test/baseline_vs_permutation_bestK_comparison.csv')
rg_df = comparison_df[comparison_df['scenario'] == 'red_green_primary']

# ============================================================================
# Calculate Statistics
# ============================================================================
def cohens_d(data, population_mean=0):
    """Calculate Cohen's d for one-sample test"""
    mean_diff = data.mean() - population_mean
    std = data.std()
    return mean_diff / std if std > 0 else 0

results = {}

for group in ['HC', 'CVD', 'All']:
    if group == 'All':
        group_data = rg_df  # All data
    else:
        group_data = rg_df[rg_df['group'] == group]

    # Baseline Hit Rate (convert to percentage)
    baseline_hits = group_data['baseline_hit45'] * 100  # Convert to percentage
    baseline_mean = baseline_hits.mean()
    baseline_se = stats.sem(baseline_hits)

    # Permutation Hit Rate (convert to percentage)
    perm_hits = group_data['permutation_hit45'] * 100
    perm_mean = perm_hits.mean()
    perm_se = stats.sem(perm_hits)

    # Change (positive = degradation, hit rate decreased)
    hit_changes = group_data['hit_rate_change'].dropna() * 100  # Convert to percentage
    change_mean = hit_changes.mean()
    t_stat, p_value = stats.ttest_1samp(hit_changes, 0)
    d = cohens_d(hit_changes, 0)

    results[group] = {
        'baseline_mean': baseline_mean,
        'baseline_se': baseline_se,
        'perm_mean': perm_mean,
        'perm_se': perm_se,
        'change_mean': change_mean,
        'p_value': p_value,
        'd': d,
        'n': len(group_data)
    }

    print(f"\n{group}:")
    print(f"  Baseline Hit Rate: {baseline_mean:.2f}% ± {baseline_se:.2f}% (SE)")
    print(f"  Permutation Hit Rate: {perm_mean:.2f}% ± {perm_se:.2f}% (SE)")
    print(f"  Change: {change_mean:+.2f}%")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Cohen's d: {d:.2f}")

# ============================================================================
# Create Figure
# ============================================================================
print("\n\nCreating figure...")

fig, ax = plt.subplots(figsize=(14, 6))

# Positions
x_positions = [0, 1, 2]  # HC, CVD, All (equal spacing)
width = 0.35
gap = 0.15

# Colors
color_baseline = '#4A90E2'  # Blue
color_perm = '#E74C3C'      # Red

# Data arrays
groups = ['HC', 'CVD', 'All']
baseline_means = [results[g]['baseline_mean'] for g in groups]
baseline_ses = [results[g]['baseline_se'] for g in groups]
perm_means = [results[g]['perm_mean'] for g in groups]
perm_ses = [results[g]['perm_se'] for g in groups]
cohens_ds = [results[g]['d'] for g in groups]
p_values = [results[g]['p_value'] for g in groups]

# Plot bars
bars1 = ax.bar([x - width/2 - gap/2 for x in x_positions], baseline_means, width,
               yerr=baseline_ses, label='Original', color=color_baseline,
               alpha=0.85, edgecolor='black', linewidth=1.5, capsize=5,
               error_kw={'linewidth': 2, 'ecolor': 'black'})

bars2 = ax.bar([x + width/2 + gap/2 for x in x_positions], perm_means, width,
               yerr=perm_ses, label='Permutation', color=color_perm,
               alpha=0.85, edgecolor='black', linewidth=1.5, capsize=5,
               error_kw={'linewidth': 2, 'ecolor': 'black'})

# Add value labels on bars (raised higher to avoid overlap)
for idx, (bar1, bar2) in enumerate(zip(bars1, bars2)):
    # Baseline bar
    height1 = bar1.get_height()
    err1 = baseline_ses[idx]
    ax.text(bar1.get_x() + bar1.get_width()/2., height1 + err1 + 1,
            f'{height1:.1f}%',
            ha='center', va='bottom', fontsize=15, fontweight='bold')

    # Permutation bar
    height2 = bar2.get_height()
    err2 = perm_ses[idx]
    ax.text(bar2.get_x() + bar2.get_width()/2., height2 + err2 + 1,
            f'{height2:.1f}%',
            ha='center', va='bottom', fontsize=15, fontweight='bold')

# Add arrows showing increase (from baseline bar top to permutation bar top)
# Arrow shows actual magnitude of change
for i, x in enumerate(x_positions):
    baseline_y = baseline_means[i]
    perm_y = perm_means[i]
    change = perm_y - baseline_y

    # Lower the arrow by 8 units
    baseline_y_arrow = baseline_y - 8
    perm_y_arrow = perm_y - 8

    # Arrow from top of baseline bar to top of permutation bar
    arrow_x_start = x - width/2 - gap/2
    arrow_x_end = x + width/2 + gap/2

    # Draw arrow with dark red edge and white fill (thicker with larger head)
    ax.annotate('', xy=(arrow_x_end, perm_y_arrow), xytext=(arrow_x_start, baseline_y_arrow),
                arrowprops=dict(arrowstyle='->,head_length=1.2,head_width=0.8',  # Larger arrowhead
                              edgecolor='#B22222',  # Dark red (firebrick)
                              facecolor='white',     # White fill
                              lw=7,                  # Edge thickness (increased to 7)
                              shrinkA=0, shrinkB=0))

    # Add significance asterisk
    sig_text = ''
    if p_values[i] < 0.001:
        sig_text = '***'
    elif p_values[i] < 0.01:
        sig_text = '**'
    elif p_values[i] < 0.05:
        sig_text = '*'
    else:
        sig_text = 'ns'

    # Text showing increase (well above the higher bar)
    text_y = max(baseline_y, perm_y) + max(baseline_ses[i], perm_ses[i]) + 6
    ax.text(x, text_y,
            f'Δ={change:+.1f}% {sig_text}',
            ha='center', va='bottom', fontsize=16, fontweight='bold',
            color='#B22222')  # Dark red to match arrow

# Styling
ax.set_ylabel('45° Hit Rate (%, ↑)',
              fontsize=14, fontweight='bold')
ax.set_xlabel('')
ax.set_xticks(x_positions)

# X-axis labels with Cohen's d
x_labels = []
for group, d in zip(groups, cohens_ds):
    x_labels.append(f"{group}\n(Cohen's d = {d:.2f})")

ax.set_xticklabels(x_labels, fontsize=15, fontweight='bold')

# Make y-axis tick labels larger and bold
ax.tick_params(axis='y', labelsize=14)
for label in ax.get_yticklabels():
    label.set_fontweight('bold')

ax.set_title('Permutation Test: Red-Green Primary Scenario\nHit Rate at 45° Threshold (Original vs Permutation)',
             fontsize=15, fontweight='bold', pad=20)

# Legend (moved to upper right)
ax.legend(loc='upper right', fontsize=12, frameon=True, edgecolor='black',
          fancybox=True, shadow=True)

# Grid
ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.7)
ax.set_axisbelow(True)

# Y-axis limits (increased to accommodate raised text)
y_max = max(perm_means) + max(perm_ses) + 15
ax.set_ylim([0, y_max])

# Add horizontal line at 50% (chance level)
ax.axhline(y=50, color='gray', linestyle=':', linewidth=2, alpha=0.5)

# Tighten layout
plt.tight_layout()

# Save
output_file = 'results/permutation_test/permutation_bar_graph_publication.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved: {output_file}")

# Also save as PDF for publication
output_pdf = 'results/permutation_test/permutation_bar_graph_publication.pdf'
plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
print(f"✓ Saved: {output_pdf}")

plt.show()

print("\n" + "="*80)
print("Figure created successfully!")
print("="*80)

# Print statistics for figure caption
print("\n\nFigure Caption:")
print("-" * 80)
print("""
Figure: Permutation test results for red-green primary scenario showing
hit rate (45° threshold) for original (blue) and permutation (red) conditions.
Error bars represent standard error of the mean. Arrows indicate hit rate decrease
from original to permutation condition. HC group shows significant performance
degradation under permutation (Δ=+{:.1f}%, p={:.3f}*, Cohen's d={:.2f}),
indicating color-specific neural representations. CVD group shows minimal effect
(Δ=+{:.1f}%, p={:.3f} ns, Cohen's d={:.2f}), suggesting alternative encoding
mechanisms. Overall effect (All): Δ=+{:.1f}%, p={:.3f}*, Cohen's d={:.2f}.
Asterisks denote statistical significance: *p<0.05, **p<0.01, ***p<0.001,
ns=not significant. Higher hit rate indicates better performance.
Positive Δ indicates performance degradation (expected under permutation).
""".format(
    results['HC']['change_mean'], results['HC']['p_value'], results['HC']['d'],
    results['CVD']['change_mean'], results['CVD']['p_value'], results['CVD']['d'],
    results['All']['change_mean'], results['All']['p_value'], results['All']['d']
))

print("="*80)
