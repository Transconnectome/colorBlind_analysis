"""
RDM Correlation Visualization — Group-Level CIs + Per-CVD Profiles

Panel A: Grouped bar chart with bootstrap 95% CIs
   HC-HC, HC-CVD, CVD-CVD per ROI
Panel B: Per-CVD pairwise profile
   Each CVD subject's mean RDM correlation with 7 HC subjects per ROI

Usage:
  conda activate srm
  mpirun -np 1 python visualize_rdm_correlation.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform, pdist
import json
import os
import sys

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'phase1_preprocess_decoding', 'results', 'full_dataset_C010')
BOOTSTRAP_CI_FILE = os.path.join(BASE_DIR, 'validation', 'bootstrap_ci_results.json')
OUTPUT_DIR = os.path.join(BASE_DIR, 'visualization')

HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 3}
CVD_LABELS = {'sub-08': 'sub-08\n(deutan)', 'sub-09': 'sub-09\n(protan)', 'sub-10': 'sub-10\n(deutan)'}
N_BOOTSTRAP = 10000
SEED = 42


def load_amplitudes(subject, roi):
    """Load Procrustes-aligned amplitudes for a subject-ROI pair."""
    roi_dir = ROI_DIRS[roi]
    fpath = os.path.join(DATA_DIR, subject, roi_dir, 'amplitudes_procrustes.npy')
    return np.load(fpath)  # (6, 8, n_voxels)


def compute_rdm(patterns):
    """Compute RDM from mean patterns (8 colors x n_voxels) using correlation distance."""
    return squareform(pdist(patterns, metric='correlation'))


def train_hc_only_srm(roi, k):
    """Train SRM on HC subjects only and transform all subjects."""
    from brainiak.funcalign.srm import SRM

    hc_data = []
    for subj in HC_SUBJECTS:
        amp = load_amplitudes(subj, roi)  # (6, 8, n_voxels)
        # Average across runs -> (8, n_voxels) -> transpose to (n_voxels, 8)
        mean_amp = amp.mean(axis=0)
        hc_data.append(mean_amp.T)  # (n_voxels, 8) for SRM

    srm = SRM(n_iter=20, features=k)
    srm.fit(hc_data)

    # Transform HC via trained W
    hc_aligned = []
    for i, subj in enumerate(HC_SUBJECTS):
        transformed = srm.w_[i].T @ load_amplitudes(subj, roi).mean(axis=0).T  # (k, 8)
        hc_aligned.append(transformed.T)  # (8, k)

    # Transform CVD via SVD projection
    S = srm.s_  # shared response (k, 8)
    cvd_aligned = []
    for subj in CVD_SUBJECTS:
        X = load_amplitudes(subj, roi).mean(axis=0).T  # (n_voxels, 8)
        U, _, Vt = np.linalg.svd(X @ np.linalg.pinv(S), full_matrices=False)
        W_new = U[:, :k] @ Vt[:k, :]
        transformed = W_new.T @ X  # (k, 8)
        cvd_aligned.append(transformed.T)  # (8, k)

    return hc_aligned, cvd_aligned


def compute_pairwise_rdm_correlations(hc_aligned, cvd_aligned):
    """Compute all pairwise RDM correlations. Returns per-pair values."""
    mask = np.triu(np.ones((8, 8), dtype=bool), k=1)
    all_patterns = hc_aligned + cvd_aligned
    all_labels = ['HC'] * len(hc_aligned) + ['CVD'] * len(cvd_aligned)

    rdms = [compute_rdm(p) for p in all_patterns]
    rdm_vectors = [r[mask] for r in rdms]

    # Per-pair correlations
    hc_hc_pairs, hc_cvd_pairs, cvd_cvd_pairs = [], [], []
    # Per-CVD-subject: correlations with each HC subject
    per_cvd_to_hc = {subj: [] for subj in CVD_SUBJECTS}

    n_hc = len(hc_aligned)
    n_cvd = len(cvd_aligned)

    for i in range(n_hc + n_cvd):
        for j in range(i + 1, n_hc + n_cvd):
            r, _ = spearmanr(rdm_vectors[i], rdm_vectors[j])
            if not np.isfinite(r):
                continue
            li, lj = all_labels[i], all_labels[j]
            if li == 'HC' and lj == 'HC':
                hc_hc_pairs.append(r)
            elif li == 'HC' and lj == 'CVD':
                hc_cvd_pairs.append(r)
                cvd_idx = j - n_hc
                per_cvd_to_hc[CVD_SUBJECTS[cvd_idx]].append(r)
            elif li == 'CVD' and lj == 'HC':
                hc_cvd_pairs.append(r)
                cvd_idx = i - n_hc
                per_cvd_to_hc[CVD_SUBJECTS[cvd_idx]].append(r)
            elif li == 'CVD' and lj == 'CVD':
                cvd_cvd_pairs.append(r)

    return hc_hc_pairs, hc_cvd_pairs, cvd_cvd_pairs, per_cvd_to_hc


def bootstrap_ci(values, n_boot=N_BOOTSTRAP, ci=95, seed=SEED):
    """Bootstrap confidence interval for the mean."""
    rng = np.random.RandomState(seed)
    values = np.array(values)
    boot_means = [np.mean(rng.choice(values, size=len(values), replace=True)) for _ in range(n_boot)]
    alpha = (100 - ci) / 2
    return np.mean(values), np.percentile(boot_means, alpha), np.percentile(boot_means, 100 - alpha)


def load_canonical_cis():
    """Load validated bootstrap CIs from canonical results file."""
    with open(BOOTSTRAP_CI_FILE) as f:
        data = json.load(f)
    canonical = {}
    for roi in ROIS:
        r = data['results'][roi]['rdm_correlations']
        canonical[roi] = {
            'HC-HC': (r['hc_hc_rdm']['observed'], r['hc_hc_rdm']['ci_lower'], r['hc_hc_rdm']['ci_upper']),
            'HC-CVD': (r['hc_cvd_rdm']['observed'], r['hc_cvd_rdm']['ci_lower'], r['hc_cvd_rdm']['ci_upper']),
            'CVD-CVD': (r['cvd_cvd_rdm']['observed'], r['cvd_cvd_rdm']['ci_lower'], r['cvd_cvd_rdm']['ci_upper']),
        }
    return canonical


def create_figure(all_roi_data, per_cvd_profiles):
    """Create two-panel figure."""
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={'width_ratios': [1.2, 1]})

    # --- Colors ---
    colors = {'HC-HC': '#2196F3', 'HC-CVD': '#FF9800', 'CVD-CVD': '#E91E63'}
    cvd_colors = {'sub-08': '#4CAF50', 'sub-09': '#9C27B0', 'sub-10': '#795548'}

    # --- Significance data ---
    # Panel A: Group disparity permutation test p-values (HC-CVD difference)
    group_perm_p = {'V1': 0.062, 'V2': 0.075, 'V3': 0.395, 'hV4': 0.559}
    # Panel B: Crawford & Howell individual p-values (one-tailed)
    crawford_p = {
        'sub-08': {'V1': 0.157, 'V2': 0.040, 'V3': 0.052, 'hV4': 0.411},
        'sub-09': {'V1': 0.007, 'V2': 0.181, 'V3': 0.466, 'hV4': 0.150},
        'sub-10': {'V1': 0.483, 'V2': 0.433, 'V3': 0.884, 'hV4': 0.945},
    }

    def sig_label(p):
        if p < 0.01:
            return '**'
        elif p < 0.05:
            return '*'
        elif p < 0.1:
            return '\u2020'  # dagger for trending
        return ''

    # ===== Panel A: Grouped Bar Chart with CIs =====
    ax_a.set_title('A. RDM Correlation by Group Pair (SRM Space)', fontsize=12, fontweight='bold', pad=12)

    bar_width = 0.22
    x = np.arange(len(ROIS))
    groups = ['HC-HC', 'HC-CVD', 'CVD-CVD']
    offsets = [-bar_width, 0, bar_width]

    max_heights = [0.0] * len(ROIS)  # track max bar+CI height per ROI

    for g_idx, group in enumerate(groups):
        means, ci_lows, ci_highs = [], [], []
        for roi in ROIS:
            m, lo, hi = all_roi_data[roi][group]
            means.append(m)
            ci_lows.append(m - lo)
            ci_highs.append(hi - m)

        bars = ax_a.bar(x + offsets[g_idx], means, bar_width,
                        yerr=[ci_lows, ci_highs], capsize=3,
                        color=colors[group], alpha=0.85,
                        edgecolor='white', linewidth=0.5,
                        error_kw={'linewidth': 1.2, 'color': '#333333'},
                        label=group, zorder=3)

        # Value labels on bars
        for i, (bar, m) in enumerate(zip(bars, means)):
            top = bar.get_height() + ci_highs[i]
            ax_a.text(bar.get_x() + bar.get_width() / 2, top + 0.015,
                      f'{m:.3f}', ha='center', va='bottom', fontsize=7, color='#555555')
            max_heights[i] = max(max_heights[i], top + 0.045)

    # Significance brackets for group difference (disparity perm test)
    for i, roi in enumerate(ROIS):
        sl = sig_label(group_perm_p[roi])
        if sl:
            y_bracket = max_heights[i] + 0.02
            x_left = i - bar_width   # HC-HC bar center
            x_right = i             # HC-CVD bar center
            ax_a.plot([x_left, x_left, x_right, x_right],
                      [y_bracket - 0.01, y_bracket, y_bracket, y_bracket - 0.01],
                      color='#333333', linewidth=1, zorder=10)
            ax_a.text((x_left + x_right) / 2, y_bracket + 0.005, sl,
                      ha='center', va='bottom', fontsize=10, fontweight='bold', color='#333333')

    ax_a.set_xticks(x)
    ax_a.set_xticklabels([f'{roi} (k={K_VALUES[roi]})' for roi in ROIS], fontsize=10)
    ax_a.set_ylabel('RDM Correlation (Spearman r)', fontsize=10)
    ax_a.set_ylim(-0.05, 0.90)
    ax_a.axhline(y=0, color='gray', linewidth=0.5, linestyle='--', zorder=1)
    ax_a.spines['top'].set_visible(False)
    ax_a.spines['right'].set_visible(False)
    ax_a.grid(axis='y', alpha=0.2, zorder=0)

    # Noise ceiling annotation
    noise_ceilings = {'V1': 0.582, 'V2': 0.635, 'V3': 0.525, 'hV4': 0.697}
    for i, roi in enumerate(ROIS):
        nc = noise_ceilings[roi]
        ax_a.plot([i - 0.35, i + 0.35], [nc, nc], color='#999999', linewidth=1, linestyle=':', zorder=2)
    ax_a.plot([], [], color='#999999', linewidth=1, linestyle=':', label='Noise ceiling')
    ax_a.legend(fontsize=8, loc='upper left', framealpha=0.9)

    # Footnote for significance
    ax_a.text(0.01, -0.12, '**p<0.01  *p<0.05  \u2020p<0.1 (group disparity permutation test)',
              transform=ax_a.transAxes, fontsize=7, color='#666666')

    # ===== Panel B: Per-CVD Pairwise Profile =====
    ax_b.set_title('B. Individual CVD RDM Correlation with HC', fontsize=12, fontweight='bold', pad=12)

    x_b = np.arange(len(ROIS))
    marker_styles = {'sub-08': 's', 'sub-09': '^', 'sub-10': 'D'}

    # HC-HC reference band
    hc_means = [all_roi_data[roi]['HC-HC'][0] for roi in ROIS]
    hc_ci_lo = [all_roi_data[roi]['HC-HC'][1] for roi in ROIS]
    hc_ci_hi = [all_roi_data[roi]['HC-HC'][2] for roi in ROIS]
    ax_b.fill_between(x_b, hc_ci_lo, hc_ci_hi, alpha=0.15, color='#2196F3', label='HC-HC 95% CI')
    ax_b.plot(x_b, hc_means, '--', color='#2196F3', linewidth=1.5, alpha=0.6, label='HC-HC mean')

    # Per-CVD lines with significance markers
    for subj in CVD_SUBJECTS:
        means_cvd = [per_cvd_profiles[roi][subj] for roi in ROIS]
        ax_b.plot(x_b, means_cvd, color=cvd_colors[subj],
                  marker=marker_styles[subj], markersize=8, linewidth=2,
                  label=CVD_LABELS[subj], zorder=5)

        # Annotate values with significance
        for i, (roi, m) in enumerate(zip(ROIS, means_cvd)):
            sl = sig_label(crawford_p[subj][roi])
            offset_y = 0.025 if subj != 'sub-10' else -0.035
            label_text = f'{m:.3f}{sl}'
            ax_b.text(i + 0.08, m + offset_y, label_text, fontsize=7,
                      color=cvd_colors[subj], fontweight='bold')

    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels([f'{roi} (k={K_VALUES[roi]})' for roi in ROIS], fontsize=10)
    ax_b.set_ylabel('Mean RDM Correlation with HC (Spearman r)', fontsize=10)
    ax_b.set_ylim(-0.1, 0.8)
    ax_b.axhline(y=0, color='gray', linewidth=0.5, linestyle='--', zorder=1)
    ax_b.legend(fontsize=8, loc='upper left', framealpha=0.9)
    ax_b.spines['top'].set_visible(False)
    ax_b.spines['right'].set_visible(False)
    ax_b.grid(axis='y', alpha=0.2, zorder=0)

    # Footnote for significance
    ax_b.text(0.01, -0.12, '**p<0.01  *p<0.05  \u2020p<0.1 (Crawford & Howell single-case test)',
              transform=ax_b.transAxes, fontsize=7, color='#666666')

    plt.tight_layout(w_pad=3)
    return fig


def main():
    print("=" * 60)
    print("RDM Correlation Visualization")
    print("=" * 60)

    # Panel A: Use canonical bootstrap CIs (validated, 10K iterations)
    all_roi_data = load_canonical_cis()
    print("Panel A: Loaded canonical bootstrap CIs from validated results")
    for roi in ROIS:
        d = all_roi_data[roi]
        for g in ['HC-HC', 'HC-CVD', 'CVD-CVD']:
            m, lo, hi = d[g]
            print(f"  {roi} {g}: {m:.3f} [{lo:.3f}, {hi:.3f}]")

    # Panel B: Compute per-CVD profiles (requires fresh SRM)
    per_cvd_profiles = {}
    print("\nPanel B: Computing per-CVD profiles via HC-only SRM...")

    for roi in ROIS:
        print(f"\n--- {roi} (k={K_VALUES[roi]}) ---")
        hc_aligned, cvd_aligned = train_hc_only_srm(roi, K_VALUES[roi])
        _, _, _, per_cvd_to_hc = compute_pairwise_rdm_correlations(hc_aligned, cvd_aligned)

        per_cvd_profiles[roi] = {}
        for subj in CVD_SUBJECTS:
            mean_r = np.mean(per_cvd_to_hc[subj]) if per_cvd_to_hc[subj] else 0
            per_cvd_profiles[roi][subj] = mean_r
            print(f"  {subj} mean RDM corr with HC: {mean_r:.3f} (n={len(per_cvd_to_hc[subj])})")

    # Create figure
    fig = create_figure(all_roi_data, per_cvd_profiles)

    out_path = os.path.join(OUTPUT_DIR, 'rdm_correlation_figure.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nSaved: {out_path}")

    plt.close()

    # Save numerical results
    results = {
        'group_level': {roi: {g: {'mean': v[0], 'ci_lower': v[1], 'ci_upper': v[2]}
                              for g, v in d.items()} for roi, d in all_roi_data.items()},
        'per_cvd': per_cvd_profiles,
    }
    json_path = os.path.join(OUTPUT_DIR, 'rdm_correlation_data.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {json_path}")


if __name__ == '__main__':
    main()
