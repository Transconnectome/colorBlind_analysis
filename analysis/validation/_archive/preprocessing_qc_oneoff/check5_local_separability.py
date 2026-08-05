#!/usr/bin/env python3
"""
Check 5: Local Separability Analysis
=====================================
Tests whether CVD subjects show selectively reduced separability
for adjacent hue pairs compared to HC subjects.

Hypothesis: Global RDM structure is similar between CVD and HC,
but local (near-neighbor) color separability may be lower in CVD.

Analysis:
1. Compute within-subject RDMs from Procrustes-aligned amplitudes
2. Categorize 28 color pairs by hue distance (step 1-4)
3. Compare HC vs CVD (individual) for each distance category
4. Test protan/deutan confusion axis specifically
5. Per-pair CVD-HC difference profile

Color mapping (45° spacing, circular):
  color_1=red(0°), color_2=orange(45°), color_3=yellow(90°),
  color_4=green(135°), color_5=cyan(180°), color_6=blue(225°),
  color_7=purple(270°), color_8=magenta(315°)
"""

import numpy as np
import json
import os
from scipy.spatial.distance import pdist, squareform
from scipy.stats import mannwhitneyu, pearsonr, spearmanr
from itertools import combinations
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Configuration
# ============================================================
BASE = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis'
AMP_DIR = f'{BASE}/analysis/phase1_preprocess_decoding/results/full_dataset_C010'
OUT_DIR = f'{BASE}/analysis/validation/scripts/results/check5_local_separability'
os.makedirs(OUT_DIR, exist_ok=True)

HC_SUBS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBS = HC_SUBS + CVD_SUBS
ROIS = ['V1', 'V2', 'V3', 'hV4']
N_COLORS = 8

# Color labels and hue angles
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
COLOR_HUES = [0, 45, 90, 135, 180, 225, 270, 315]  # degrees

# Display colors for plotting
DISPLAY_COLORS = ['#FF0000', '#FF8000', '#FFD700', '#00AA00',
                  '#00CCCC', '#0000FF', '#8000FF', '#FF00FF']

# ============================================================
# Helper functions
# ============================================================
def compute_rdm(amplitudes):
    """Compute RDM from (n_runs, n_colors, n_voxels) using correlation distance."""
    # Average across runs
    mean_amp = np.nanmean(amplitudes, axis=0)  # (8, n_voxels)
    # Correlation distance RDM
    rdm = squareform(pdist(mean_amp, metric='correlation'))
    return rdm

def circular_distance(i, j, n=8):
    """Circular hue step distance between color indices (0-indexed)."""
    d = abs(i - j)
    return min(d, n - d)

def get_pair_categories():
    """Categorize all 28 pairs by hue step distance."""
    pairs = list(combinations(range(N_COLORS), 2))
    categories = {1: [], 2: [], 3: [], 4: []}  # step: [(i,j), ...]
    for i, j in pairs:
        step = circular_distance(i, j)
        categories[step].append((i, j))
    return categories

def get_confusion_axis_pairs():
    """Identify pairs along protan/deutan confusion axis (L-M cone)."""
    # Red-green confusion axis: pairs that cross the red-green boundary
    # Deutan/protan confuse colors differing primarily in L-M contrast
    # Key confusion pairs for CVD:
    confusion = {
        'red_green': [(0, 3)],       # red vs green (step 3)
        'red_cyan': [(0, 4)],        # red vs cyan (step 4)
        'orange_green': [(1, 3)],    # orange vs green (step 2)
        'orange_cyan': [(1, 4)],     # orange vs cyan (step 3)
        'yellow_green': [(2, 3)],    # yellow vs green (step 1) - adjacent
        'magenta_red': [(7, 0)],     # magenta vs red (step 1) - adjacent
        # L-M axis (warm vs cool): colors 1-4 vs 5-8
        'warm_cool_boundary': [(3, 4), (7, 0)],  # green-cyan, magenta-red
    }
    return confusion

# ============================================================
# Main Analysis
# ============================================================
print("=" * 70)
print("CHECK 5: LOCAL SEPARABILITY ANALYSIS")
print("=" * 70)

# 1. Compute RDMs for all subjects × ROIs
print("\n[1] Computing RDMs from Procrustes-aligned amplitudes...")
rdms = {}  # {(sub, roi): 8x8 matrix}
pair_categories = get_pair_categories()

for sub in ALL_SUBS:
    for roi in ROIS:
        roi_dir = roi if roi != 'hV4' else 'hV4'
        amp_path = f'{AMP_DIR}/{sub}/{roi_dir}/amplitudes_procrustes.npy'
        if not os.path.exists(amp_path):
            # Try V4 naming
            amp_path = f'{AMP_DIR}/{sub}/V4/amplitudes_procrustes.npy'
        if os.path.exists(amp_path):
            amp = np.load(amp_path)
            rdm = compute_rdm(amp)
            if not np.any(np.isnan(rdm)):
                rdms[(sub, roi)] = rdm
            else:
                print(f"  WARNING: NaN in RDM for {sub}/{roi}")
        else:
            print(f"  WARNING: Missing {sub}/{roi}")

print(f"  Computed {len(rdms)} valid RDMs")

# 2. Extract pair distances by category
print("\n[2] Extracting pair distances by hue step category...")
print(f"  Step 1 (adjacent, 45°): {len(pair_categories[1])} pairs")
print(f"  Step 2 (90°): {len(pair_categories[2])} pairs")
print(f"  Step 3 (135°): {len(pair_categories[3])} pairs")
print(f"  Step 4 (opposite, 180°): {len(pair_categories[4])} pairs")

# For each subject × ROI, compute mean distance per step
results = {}
for (sub, roi), rdm in rdms.items():
    step_distances = {}
    for step, pairs in pair_categories.items():
        dists = [rdm[i, j] for i, j in pairs]
        step_distances[step] = {
            'mean': float(np.mean(dists)),
            'std': float(np.std(dists)),
            'values': [float(d) for d in dists],
            'pairs': [(COLOR_NAMES[i], COLOR_NAMES[j]) for i, j in pairs]
        }
    results[(sub, roi)] = step_distances

# 3. Group comparison: HC vs CVD per step per ROI
print("\n[3] Group Comparison: HC vs CVD by hue step")
print("=" * 70)

group_results = {}
for roi in ROIS:
    print(f"\n--- {roi} ---")
    group_results[roi] = {}

    for step in [1, 2, 3, 4]:
        hc_means = [results[(s, roi)][step]['mean']
                     for s in HC_SUBS if (s, roi) in results]
        cvd_means = [results[(s, roi)][step]['mean']
                      for s in CVD_SUBS if (s, roi) in results]

        if len(hc_means) < 2 or len(cvd_means) < 2:
            continue

        hc_m, hc_sd = np.mean(hc_means), np.std(hc_means)
        cvd_m, cvd_sd = np.mean(cvd_means), np.std(cvd_means)
        diff = cvd_m - hc_m

        # Mann-Whitney U (non-parametric, appropriate for small n)
        if len(set(hc_means + cvd_means)) > 1:
            stat, p = mannwhitneyu(hc_means, cvd_means, alternative='two-sided')
        else:
            p = 1.0

        # Effect size (Hedges' g approximation)
        pooled_sd = np.sqrt(((len(hc_means)-1)*np.var(hc_means) +
                             (len(cvd_means)-1)*np.var(cvd_means)) /
                            (len(hc_means) + len(cvd_means) - 2))
        g = diff / pooled_sd if pooled_sd > 0 else 0

        # Selective reduction ratio: (CVD adj / CVD non-adj) vs (HC adj / HC non-adj)
        desc = f"Step {step} ({step*45}°)"
        direction = "CVD < HC" if diff < 0 else "CVD >= HC"
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."

        print(f"  {desc}: HC={hc_m:.4f}±{hc_sd:.4f}, CVD={cvd_m:.4f}±{cvd_sd:.4f}, "
              f"Δ={diff:+.4f}, g={g:.2f}, p={p:.3f} {sig} [{direction}]")

        group_results[roi][f'step_{step}'] = {
            'hc_mean': hc_m, 'hc_sd': hc_sd,
            'cvd_mean': cvd_m, 'cvd_sd': cvd_sd,
            'difference': diff, 'hedges_g': g, 'p_value': p,
            'direction': direction
        }

# 4. Selective reduction test: Is CVD deficit concentrated in adjacent pairs?
print("\n\n[4] Selective Reduction Test: Adjacent (step 1) vs Non-adjacent")
print("=" * 70)

selective_results = {}
for roi in ROIS:
    print(f"\n--- {roi} ---")
    selective_results[roi] = {}

    for sub in ALL_SUBS:
        if (sub, roi) not in results:
            continue

        adj_mean = results[(sub, roi)][1]['mean']  # step 1
        non_adj = []
        for step in [2, 3, 4]:
            non_adj.extend(results[(sub, roi)][step]['values'])
        non_adj_mean = np.mean(non_adj)

        # Ratio: adjacent / non-adjacent (lower = worse local separability)
        ratio = adj_mean / non_adj_mean if non_adj_mean > 0 else np.nan
        selective_results[roi][sub] = {
            'adjacent_mean': float(adj_mean),
            'non_adjacent_mean': float(non_adj_mean),
            'ratio': float(ratio)
        }

    # Group comparison of ratios
    hc_ratios = [selective_results[roi][s]['ratio'] for s in HC_SUBS
                 if s in selective_results[roi]]
    cvd_ratios = [selective_results[roi][s]['ratio'] for s in CVD_SUBS
                  if s in selective_results[roi]]

    if len(hc_ratios) >= 2 and len(cvd_ratios) >= 2:
        hc_r = np.mean(hc_ratios)
        cvd_r = np.mean(cvd_ratios)
        stat, p = mannwhitneyu(hc_ratios, cvd_ratios, alternative='two-sided')
        sig = "*" if p < 0.05 else "n.s."

        print(f"  Adjacent/Non-adjacent ratio:")
        print(f"    HC:  {hc_r:.4f} ± {np.std(hc_ratios):.4f} (n={len(hc_ratios)})")
        print(f"    CVD: {cvd_r:.4f} ± {np.std(cvd_ratios):.4f} (n={len(cvd_ratios)})")
        print(f"    p = {p:.3f} {sig}")

        if cvd_r < hc_r:
            print(f"    → CVD shows LOWER adj/non-adj ratio (selective local deficit)")
        else:
            print(f"    → CVD does NOT show selective local deficit")

# 5. Per-pair analysis: Which specific pairs differ?
print("\n\n[5] Per-Pair CVD-HC Difference Profile")
print("=" * 70)

pair_profile = {}
all_pairs = list(combinations(range(N_COLORS), 2))

for roi in ROIS:
    print(f"\n--- {roi} ---")
    pair_profile[roi] = {}

    for i, j in all_pairs:
        pair_name = f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}"
        step = circular_distance(i, j)

        hc_vals = [rdms[(s, roi)][i, j] for s in HC_SUBS if (s, roi) in rdms]
        cvd_vals = {s: rdms[(s, roi)][i, j] for s in CVD_SUBS if (s, roi) in rdms}

        if not hc_vals or not cvd_vals:
            continue

        hc_mean = np.mean(hc_vals)
        pair_profile[roi][pair_name] = {
            'step': step,
            'hc_mean': float(hc_mean),
            'hc_sd': float(np.std(hc_vals))
        }

        for sub, val in cvd_vals.items():
            diff = val - hc_mean
            z = diff / np.std(hc_vals) if np.std(hc_vals) > 0 else 0
            pair_profile[roi][pair_name][sub] = {
                'value': float(val),
                'diff_from_hc': float(diff),
                'z_score': float(z)
            }

    # Find pairs with largest CVD deficits (lower distance = worse separability)
    for sub in CVD_SUBS:
        deficits = []
        for pair_name, data in pair_profile[roi].items():
            if sub in data:
                deficits.append((pair_name, data[sub]['diff_from_hc'],
                                data[sub]['z_score'], data['step']))

        deficits.sort(key=lambda x: x[1])  # most negative first
        print(f"\n  {sub} - Top 5 deficits (lower distance than HC mean):")
        for name, diff, z, step in deficits[:5]:
            marker = " ← ADJACENT" if step == 1 else ""
            print(f"    {name} (step {step}): Δ={diff:+.4f}, z={z:+.2f}{marker}")

        print(f"  {sub} - Top 5 elevations (higher distance than HC mean):")
        for name, diff, z, step in deficits[-5:][::-1]:
            marker = " ← ADJACENT" if step == 1 else ""
            print(f"    {name} (step {step}): Δ={diff:+.4f}, z={z:+.2f}{marker}")

# 6. Protan/Deutan confusion axis analysis
print("\n\n[6] Protan/Deutan Confusion Axis Analysis")
print("=" * 70)

# Pairs along L-M axis (red-green confusion)
# For deutan/protan, the main confusion is along L-M opponent channel
# In our 8-color space, this maps to:
# - Red(0°) confused with Green(135°): pair (0,3)
# - Orange(45°) confused with Green(135°): pair (1,3)
# - Red(0°) confused with Cyan(180°) is tritan, not L-M
# Most relevant for deutan: red-green pairs and nearby

confusion_pairs = {
    'L-M axis (CVD-critical)': [(0, 3), (1, 3), (0, 4), (1, 4)],
    'S-cone axis (control)': [(2, 6), (3, 7), (1, 5)],
    'Adjacent warm': [(0, 1), (1, 2), (2, 3)],
    'Adjacent cool': [(4, 5), (5, 6), (6, 7)],
    'Warm-cool boundary': [(3, 4), (7, 0)],
}

for roi in ['V1', 'V2']:  # Focus on ROIs with significant effects
    print(f"\n--- {roi} ---")
    for axis_name, pairs in confusion_pairs.items():
        hc_all = []
        cvd_all = {s: [] for s in CVD_SUBS}

        for i, j in pairs:
            for s in HC_SUBS:
                if (s, roi) in rdms:
                    hc_all.append(rdms[(s, roi)][i, j])
            for s in CVD_SUBS:
                if (s, roi) in rdms:
                    cvd_all[s].append(rdms[(s, roi)][i, j])

        hc_m = np.mean(hc_all) if hc_all else np.nan
        print(f"\n  {axis_name}:")
        print(f"    HC mean: {hc_m:.4f}")
        for s in CVD_SUBS:
            if cvd_all[s]:
                cvd_m = np.mean(cvd_all[s])
                diff = cvd_m - hc_m
                print(f"    {s}: {cvd_m:.4f} (Δ={diff:+.4f})")

# 7. Summary statistics
print("\n\n[7] SUMMARY: Is there evidence for selective local separability deficit?")
print("=" * 70)

for roi in ROIS:
    print(f"\n--- {roi} ---")
    if f'step_1' in group_results.get(roi, {}):
        s1 = group_results[roi]['step_1']
        s4_key = 'step_4' if 'step_4' in group_results[roi] else 'step_3'
        s_far = group_results[roi].get(s4_key, {})

        adj_sig = s1['p_value'] < 0.05
        adj_dir = s1['difference'] < 0  # CVD < HC

        if adj_sig and adj_dir:
            verdict = "SUPPORTED - CVD shows reduced adjacent separability"
        elif adj_dir and not adj_sig:
            verdict = "TREND - CVD lower but not significant (n=3 limits power)"
        else:
            verdict = "NOT SUPPORTED - No selective adjacent deficit"

        print(f"  Adjacent (step 1): CVD-HC = {s1['difference']:+.4f}, p={s1['p_value']:.3f}")
        print(f"  Verdict: {verdict}")

# ============================================================
# Visualization
# ============================================================
print("\n\n[8] Generating visualizations...")

fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('Check 5: Local Separability Analysis\nAdjacent vs Non-adjacent Color Pair Distances',
             fontsize=14, fontweight='bold')

for idx, roi in enumerate(ROIS):
    ax = axes[idx // 2][idx % 2]

    # Plot mean distance by step for HC and each CVD
    steps = [1, 2, 3, 4]
    step_labels = ['45°\n(adj)', '90°', '135°', '180°\n(opp)']

    # HC individual traces (thin gray)
    for sub in HC_SUBS:
        if (sub, roi) in results:
            vals = [results[(sub, roi)][s]['mean'] for s in steps]
            ax.plot(steps, vals, 'o-', color='gray', alpha=0.2, linewidth=0.5, markersize=3)

    # HC mean
    hc_step_means = []
    hc_step_sds = []
    for s in steps:
        vals = [results[(sub, roi)][s]['mean'] for sub in HC_SUBS if (sub, roi) in results]
        hc_step_means.append(np.mean(vals))
        hc_step_sds.append(np.std(vals))

    ax.errorbar(steps, hc_step_means, yerr=hc_step_sds,
                fmt='s-', color='black', linewidth=2, markersize=8,
                capsize=5, label=f'HC mean (n={len([s for s in HC_SUBS if (s,roi) in results])})',
                zorder=10)

    # CVD individuals
    cvd_colors = {'sub-08': '#E74C3C', 'sub-09': '#3498DB', 'sub-10': '#2ECC71'}
    cvd_labels = {'sub-08': 'sub-08 (deutan)', 'sub-09': 'sub-09 (protan)', 'sub-10': 'sub-10 (deutan)'}

    for sub in CVD_SUBS:
        if (sub, roi) in results:
            vals = [results[(sub, roi)][s]['mean'] for s in steps]
            ax.plot(steps, vals, 'D-', color=cvd_colors[sub], linewidth=2,
                    markersize=8, label=cvd_labels[sub], zorder=10)

    ax.set_xticks(steps)
    ax.set_xticklabels(step_labels)
    ax.set_xlabel('Hue Step Distance')
    ax.set_ylabel('Mean RDM Distance (correlation)')
    ax.set_title(f'{roi}', fontsize=13, fontweight='bold')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)

    # Highlight adjacent region
    ax.axvspan(0.7, 1.3, alpha=0.1, color='red', label='_nolegend_')

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/local_separability_by_step.png', dpi=150, bbox_inches='tight')
print(f"  Saved: {OUT_DIR}/local_separability_by_step.png")

# Figure 2: Per-pair heatmap (CVD - HC difference)
fig, axes = plt.subplots(len(CVD_SUBS), len(ROIS), figsize=(20, 12))
fig.suptitle('Per-Pair RDM Distance: CVD - HC Mean\n(Blue = CVD lower separability, Red = CVD higher)',
             fontsize=14, fontweight='bold')

for ci, sub in enumerate(CVD_SUBS):
    for ri, roi in enumerate(ROIS):
        ax = axes[ci][ri]

        if (sub, roi) not in rdms:
            ax.set_visible(False)
            continue

        # Compute HC mean RDM for this ROI
        hc_rdms = [rdms[(s, roi)] for s in HC_SUBS if (s, roi) in rdms]
        hc_mean_rdm = np.mean(hc_rdms, axis=0)

        # Difference
        diff_rdm = rdms[(sub, roi)] - hc_mean_rdm

        # Plot
        vmax = np.max(np.abs(diff_rdm[np.triu_indices(8, k=1)]))
        im = ax.imshow(diff_rdm, cmap='RdBu_r', vmin=-vmax, vmax=vmax)

        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels([c[:3] for c in COLOR_NAMES], fontsize=7, rotation=45)
        ax.set_yticklabels([c[:3] for c in COLOR_NAMES], fontsize=7)

        # Highlight adjacent pairs
        for i in range(8):
            j = (i + 1) % 8
            if i < j:
                ax.plot(j, i, 'k*', markersize=6)
            else:
                ax.plot(i, j, 'k*', markersize=6)

        ax.set_title(f'{sub} - {roi}', fontsize=10)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/per_pair_difference_heatmap.png', dpi=150, bbox_inches='tight')
print(f"  Saved: {OUT_DIR}/per_pair_difference_heatmap.png")

# Figure 3: Circular color wheel with separability
fig, axes = plt.subplots(len(CVD_SUBS), len(['V1', 'V2']), figsize=(14, 18))
fig.suptitle('Adjacent Pair Separability on Color Wheel\n(Line thickness ∝ RDM distance; Red = lower than HC)',
             fontsize=14, fontweight='bold')

for ci, sub in enumerate(CVD_SUBS):
    for ri, roi in enumerate(['V1', 'V2']):
        ax = axes[ci][ri]

        if (sub, roi) not in rdms:
            ax.set_visible(False)
            continue

        hc_rdms_roi = [rdms[(s, roi)] for s in HC_SUBS if (s, roi) in rdms]
        hc_mean = np.mean(hc_rdms_roi, axis=0)
        hc_sd = np.std(hc_rdms_roi, axis=0)

        # Draw color wheel
        angles = np.linspace(0, 2*np.pi, N_COLORS, endpoint=False) - np.pi/2  # start at top
        radius = 1.0
        xs = radius * np.cos(angles)
        ys = radius * np.sin(angles)

        # Plot color nodes
        for k in range(N_COLORS):
            ax.scatter(xs[k], ys[k], c=DISPLAY_COLORS[k], s=300, zorder=10,
                      edgecolors='black', linewidth=1.5)
            ax.annotate(COLOR_NAMES[k], (xs[k]*1.25, ys[k]*1.25),
                       ha='center', va='center', fontsize=8, fontweight='bold')

        # Draw all adjacent pairs
        for i in range(N_COLORS):
            j = (i + 1) % N_COLORS
            cvd_dist = rdms[(sub, roi)][i, j]
            hc_dist = hc_mean[i, j]
            hc_s = hc_sd[i, j]

            diff = cvd_dist - hc_dist
            z = diff / hc_s if hc_s > 0 else 0

            # Color: red if CVD < HC (deficit), blue if CVD > HC
            if z < -1:
                color = '#FF0000'
                lw = 3
            elif z < 0:
                color = '#FF8888'
                lw = 2
            elif z > 1:
                color = '#0000FF'
                lw = 3
            else:
                color = '#8888FF'
                lw = 2

            ax.plot([xs[i], xs[j]], [ys[i], ys[j]], color=color,
                    linewidth=lw, alpha=0.7, zorder=5)

            # Annotate with z-score
            mx, my = (xs[i]+xs[j])/2, (ys[i]+ys[j])/2
            ax.annotate(f'z={z:.1f}', (mx*0.75, my*0.75), fontsize=6,
                       ha='center', color=color, fontweight='bold')

        ax.set_xlim(-1.8, 1.8)
        ax.set_ylim(-1.8, 1.8)
        ax.set_aspect('equal')
        ax.set_title(f'{sub} - {roi}', fontsize=11, fontweight='bold')
        ax.axis('off')

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/color_wheel_separability.png', dpi=150, bbox_inches='tight')
print(f"  Saved: {OUT_DIR}/color_wheel_separability.png")

# ============================================================
# Save results as JSON
# ============================================================
save_data = {
    'group_comparison_by_step': {},
    'selective_reduction': {},
    'individual_pair_deficits': {},
    'summary_verdict': {}
}

for roi in ROIS:
    save_data['group_comparison_by_step'][roi] = {}
    for step_key, data in group_results.get(roi, {}).items():
        save_data['group_comparison_by_step'][roi][step_key] = {
            k: round(v, 6) if isinstance(v, float) else v
            for k, v in data.items()
        }

for roi in ROIS:
    save_data['selective_reduction'][roi] = {}
    for sub, data in selective_results.get(roi, {}).items():
        save_data['selective_reduction'][roi][sub] = {
            k: round(v, 6) for k, v in data.items()
        }

# Per-pair deficits for CVD subjects
for roi in ROIS:
    save_data['individual_pair_deficits'][roi] = {}
    for sub in CVD_SUBS:
        deficits = []
        for pair_name, data in pair_profile.get(roi, {}).items():
            if sub in data:
                deficits.append({
                    'pair': pair_name,
                    'step': data['step'],
                    'cvd_value': round(data[sub]['value'], 6),
                    'hc_mean': round(data['hc_mean'], 6),
                    'diff': round(data[sub]['diff_from_hc'], 6),
                    'z_score': round(data[sub]['z_score'], 2)
                })
        deficits.sort(key=lambda x: x['diff'])
        save_data['individual_pair_deficits'][roi][sub] = deficits

# Summary verdict
for roi in ROIS:
    if f'step_1' in group_results.get(roi, {}):
        s1 = group_results[roi]['step_1']
        adj_deficit = s1['difference'] < 0
        adj_sig = s1['p_value'] < 0.05

        if adj_sig and adj_deficit:
            verdict = "SUPPORTED"
        elif adj_deficit and not adj_sig:
            verdict = "TREND_NOT_SIGNIFICANT"
        else:
            verdict = "NOT_SUPPORTED"

        save_data['summary_verdict'][roi] = {
            'hypothesis': 'CVD shows selectively reduced adjacent-pair separability',
            'verdict': verdict,
            'adjacent_cvd_hc_diff': round(s1['difference'], 6),
            'p_value': round(s1['p_value'], 4),
            'hedges_g': round(s1['hedges_g'], 3)
        }

with open(f'{OUT_DIR}/check5_results.json', 'w') as f:
    json.dump(save_data, f, indent=2)
print(f"\n  Saved: {OUT_DIR}/check5_results.json")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
