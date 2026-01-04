#!/usr/bin/env python3
"""
Phase 1 FULL Validation with baseline32_deob_determin

Validates ALL three key findings from Phase 1:
1. HC-HC consistency (low pairwise disparity)
2. HC-CVD individual differences (high disparity)
3. CVD average pattern loses individual distortions (no significant difference from HC)
"""

import numpy as np
from pathlib import Path
import pandas as pd
from scipy.stats import spearmanr, ttest_1samp
from itertools import combinations
import json

# Paths
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
OUTPUT_DIR = BASE_DIR / "results/group_level/phase1_baseline32_validation"

# Constants
HC_SUBJECTS = ['03', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']


def load_pattern(subject, roi):
    """Load pattern for a subject and ROI"""
    pattern = np.load(PATTERN_DIR / f"sub-{subject}" / f"{roi}_pattern.npy")
    return pattern


def load_hc_mean(roi):
    """Load HC mean pattern"""
    pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")
    return pattern


def ordinary_procrustes(X, Y):
    """
    Ordinary Procrustes (translation + rotation, NO scaling)

    Args:
        X: reference (8, n_voxels) - HC
        Y: target (8, n_voxels) - CVD

    Returns:
        disparity: normalized Frobenius norm
    """
    # Step 1: Center
    X_centered = X - X.mean(axis=0, keepdims=True)
    Y_centered = Y - Y.mean(axis=0, keepdims=True)

    # Step 2: Rotation
    M = Y_centered.T @ X_centered
    U, S, Vt = np.linalg.svd(M)
    R = U @ Vt

    # Step 3: Align
    Y_aligned = Y_centered @ R + X.mean(axis=0, keepdims=True)

    # Disparity
    disparity = np.linalg.norm(X - Y_aligned, ord='fro') / np.linalg.norm(X, ord='fro')

    return disparity


def compute_rdm(pattern):
    """Compute RDM"""
    n_colors = pattern.shape[0]
    pattern_centered = pattern - pattern.mean(axis=1, keepdims=True)

    rdm = np.zeros((n_colors, n_colors))
    for i in range(n_colors):
        for j in range(n_colors):
            if i != j:
                corr = np.corrcoef(pattern_centered[i], pattern_centered[j])[0, 1]
                rdm[i, j] = 1 - corr

    return rdm


def compute_rdm_similarity(rdm1, rdm2):
    """Compute RDM similarity"""
    upper_tri = np.triu_indices(8, k=1)
    rdm1_vec = rdm1[upper_tri]
    rdm2_vec = rdm2[upper_tri]
    corr, pval = spearmanr(rdm1_vec, rdm2_vec)
    return corr, pval


def align_voxels(patterns, min_voxels):
    """Align all patterns to same voxel count"""
    return [p[:, :min_voxels] for p in patterns]


def main():
    print("=" * 80)
    print("Phase 1 FULL Validation with baseline32_deob_determin")
    print("=" * 80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_hc_consistency = []
    results_cvd_individual = []
    results_cvd_average = []

    for roi in ROIS:
        print(f"\n{'='*80}")
        print(f"ROI: {roi}")
        print(f"{'='*80}")

        # Load all patterns
        print("\nLoading patterns...")
        hc_patterns = {}
        cvd_patterns = {}

        for subj in HC_SUBJECTS:
            hc_patterns[subj] = load_pattern(subj, roi)

        for subj in CVD_SUBJECTS:
            cvd_patterns[subj] = load_pattern(subj, roi)

        hc_mean = load_hc_mean(roi)

        # Determine minimum voxels
        all_patterns = list(hc_patterns.values()) + list(cvd_patterns.values()) + [hc_mean]
        min_voxels = min(p.shape[1] for p in all_patterns)

        print(f"Aligning to {min_voxels} voxels")

        # Align all patterns
        for subj in HC_SUBJECTS:
            hc_patterns[subj] = hc_patterns[subj][:, :min_voxels]

        for subj in CVD_SUBJECTS:
            cvd_patterns[subj] = cvd_patterns[subj][:, :min_voxels]

        hc_mean = hc_mean[:, :min_voxels]

        # =============================================================================
        # 1. HC-HC Consistency (Pairwise)
        # =============================================================================
        print(f"\n{'-'*80}")
        print("1. HC-HC Consistency (Pairwise Procrustes)")
        print(f"{'-'*80}")

        hc_pairs = list(combinations(HC_SUBJECTS, 2))

        for subj1, subj2 in hc_pairs:
            disp = ordinary_procrustes(hc_patterns[subj1], hc_patterns[subj2])
            print(f"  sub-{subj1} vs sub-{subj2}: {disp:.4f}")

            results_hc_consistency.append({
                'ROI': roi,
                'Subject1': f'sub-{subj1}',
                'Subject2': f'sub-{subj2}',
                'Disparity': disp
            })

        # Mean HC-HC disparity
        hc_disparities = [r['Disparity'] for r in results_hc_consistency if r['ROI'] == roi]
        mean_hc_disp = np.mean(hc_disparities)
        std_hc_disp = np.std(hc_disparities)
        print(f"\n  Mean HC-HC Disparity: {mean_hc_disp:.4f} ± {std_hc_disp:.4f}")

        # =============================================================================
        # 2. HC-CVD Individual Differences
        # =============================================================================
        print(f"\n{'-'*80}")
        print("2. HC-CVD Individual Differences (vs HC mean)")
        print(f"{'-'*80}")

        for cvd_subj in CVD_SUBJECTS:
            disp = ordinary_procrustes(hc_mean, cvd_patterns[cvd_subj])
            print(f"  sub-{cvd_subj} vs HC_mean: {disp:.4f}")

            results_cvd_individual.append({
                'ROI': roi,
                'Subject': f'sub-{cvd_subj}',
                'Disparity': disp
            })

        cvd_disparities = [r['Disparity'] for r in results_cvd_individual if r['ROI'] == roi]
        mean_cvd_disp = np.mean(cvd_disparities)
        std_cvd_disp = np.std(cvd_disparities)
        print(f"\n  Mean CVD-HC Disparity: {mean_cvd_disp:.4f} ± {std_cvd_disp:.4f}")

        # =============================================================================
        # 3. CVD Average Pattern
        # =============================================================================
        print(f"\n{'-'*80}")
        print("3. CVD Average Pattern (cancellation of individual distortions)")
        print(f"{'-'*80}")

        # Compute CVD average
        cvd_patterns_list = [cvd_patterns[subj] for subj in CVD_SUBJECTS]
        cvd_average = np.mean(cvd_patterns_list, axis=0)

        print(f"CVD average shape: {cvd_average.shape}")

        # Disparity: CVD average vs HC mean
        disp_cvd_avg = ordinary_procrustes(hc_mean, cvd_average)
        print(f"  CVD_average vs HC_mean: {disp_cvd_avg:.4f}")

        # RDM similarity
        rdm_cvd_avg = compute_rdm(cvd_average)
        rdm_hc = compute_rdm(hc_mean)
        rdm_sim_cvd_avg, rdm_pval = compute_rdm_similarity(rdm_cvd_avg, rdm_hc)
        print(f"  RDM Similarity: {rdm_sim_cvd_avg:.4f} (p={rdm_pval:.4e})")

        # Per-color activation differences
        cvd_avg_l2 = np.linalg.norm(cvd_average, axis=1)
        hc_mean_l2 = np.linalg.norm(hc_mean, axis=1)
        l2_diffs = cvd_avg_l2 - hc_mean_l2
        l2_ratios = cvd_avg_l2 / (hc_mean_l2 + 1e-10)

        print(f"\n  Per-color L2 differences (CVD_avg - HC_mean):")
        for i, color in enumerate(COLOR_NAMES):
            diff_pct = (l2_ratios[i] - 1.0) * 100
            print(f"    {color:12s}: {l2_diffs[i]:+7.3f} ({diff_pct:+6.2f}%)")

        # T-test: are L2 differences significantly different from 0?
        t_stat, t_pval = ttest_1samp(l2_diffs, 0)
        print(f"\n  T-test (H0: mean difference = 0):")
        print(f"    t = {t_stat:.4f}, p = {t_pval:.4f}")
        if t_pval > 0.05:
            print(f"    ✓ No significant difference (p > 0.05)")
        else:
            print(f"    ⚠️ Significant difference (p < 0.05)")

        results_cvd_average.append({
            'ROI': roi,
            'Disparity_CVD_avg': disp_cvd_avg,
            'RDM_Similarity': rdm_sim_cvd_avg,
            'RDM_p_value': rdm_pval,
            'L2_diff_mean': np.mean(l2_diffs),
            'L2_diff_std': np.std(l2_diffs),
            'T_statistic': t_stat,
            'T_p_value': t_pval
        })

        # =============================================================================
        # Comparison Summary
        # =============================================================================
        print(f"\n{'-'*80}")
        print(f"Summary Comparison for {roi}")
        print(f"{'-'*80}")
        print(f"  HC-HC mean disparity:       {mean_hc_disp:.4f} ± {std_hc_disp:.4f}")
        print(f"  CVD individual-HC disparity: {mean_cvd_disp:.4f} ± {std_cvd_disp:.4f}")
        print(f"  CVD average-HC disparity:   {disp_cvd_avg:.4f}")
        print()

        if mean_cvd_disp > mean_hc_disp:
            ratio = mean_cvd_disp / mean_hc_disp
            print(f"  ✓ CVD individuals show {ratio:.2f}× higher disparity than HC-HC")
        else:
            print(f"  ⚠️ CVD individuals do NOT show higher disparity than HC-HC")

        if disp_cvd_avg < mean_cvd_disp:
            reduction = (mean_cvd_disp - disp_cvd_avg) / mean_cvd_disp * 100
            print(f"  ✓ CVD averaging reduces disparity by {reduction:.1f}%")
        else:
            print(f"  ⚠️ CVD averaging does NOT reduce disparity")

    # =============================================================================
    # Save Results
    # =============================================================================
    print(f"\n{'='*80}")
    print("Saving Results")
    print(f"{'='*80}")

    # HC-HC consistency
    df_hc = pd.DataFrame(results_hc_consistency)
    hc_file = OUTPUT_DIR / "hc_hc_consistency.csv"
    df_hc.to_csv(hc_file, index=False)
    print(f"Saved: {hc_file}")

    # CVD individual
    df_cvd_ind = pd.DataFrame(results_cvd_individual)
    cvd_ind_file = OUTPUT_DIR / "cvd_individual_differences.csv"
    df_cvd_ind.to_csv(cvd_ind_file, index=False)
    print(f"Saved: {cvd_ind_file}")

    # CVD average
    df_cvd_avg = pd.DataFrame(results_cvd_average)
    cvd_avg_file = OUTPUT_DIR / "cvd_average_analysis.csv"
    df_cvd_avg.to_csv(cvd_avg_file, index=False)
    print(f"Saved: {cvd_avg_file}")

    # =============================================================================
    # Final Summary
    # =============================================================================
    print(f"\n{'='*80}")
    print("FINAL VALIDATION SUMMARY (baseline32)")
    print(f"{'='*80}")

    for roi in ROIS:
        print(f"\n{roi}:")

        # HC-HC
        hc_data = df_hc[df_hc['ROI'] == roi]
        hc_mean = hc_data['Disparity'].mean()
        hc_std = hc_data['Disparity'].std()

        # CVD individual
        cvd_ind_data = df_cvd_ind[df_cvd_ind['ROI'] == roi]
        cvd_ind_mean = cvd_ind_data['Disparity'].mean()
        cvd_ind_std = cvd_ind_data['Disparity'].std()

        # CVD average
        cvd_avg_data = df_cvd_avg[df_cvd_avg['ROI'] == roi].iloc[0]
        cvd_avg_disp = cvd_avg_data['Disparity_CVD_avg']
        cvd_avg_tpval = cvd_avg_data['T_p_value']

        print(f"  1. HC-HC consistency:       {hc_mean:.4f} ± {hc_std:.4f} (n={len(hc_data)})")
        print(f"  2. CVD individual-HC:       {cvd_ind_mean:.4f} ± {cvd_ind_std:.4f} (n={len(cvd_ind_data)})")
        print(f"  3. CVD average-HC:          {cvd_avg_disp:.4f} (t-test p={cvd_avg_tpval:.4f})")

        # Validate findings
        print(f"\n  Validation:")

        # Finding 1: HC-HC consistency
        if hc_std < 0.1:  # Arbitrary threshold
            print(f"    ✓ Finding 1: HC-HC consistency maintained (low variance)")
        else:
            print(f"    ⚠️ Finding 1: HC-HC shows high variance")

        # Finding 2: CVD individual differs from HC
        if cvd_ind_mean > hc_mean * 1.5:  # At least 1.5x higher
            ratio = cvd_ind_mean / hc_mean
            print(f"    ✓ Finding 2: CVD individuals differ from HC ({ratio:.2f}× higher disparity)")
        else:
            print(f"    ⚠️ Finding 2: CVD individuals do NOT show clear difference from HC")

        # Finding 3: CVD average reduces disparity
        if cvd_avg_disp < cvd_ind_mean and cvd_avg_tpval > 0.05:
            reduction = (cvd_ind_mean - cvd_avg_disp) / cvd_ind_mean * 100
            print(f"    ✓ Finding 3: CVD averaging cancels distortions ({reduction:.1f}% reduction, p={cvd_avg_tpval:.3f})")
        elif cvd_avg_disp < cvd_ind_mean:
            reduction = (cvd_ind_mean - cvd_avg_disp) / cvd_ind_mean * 100
            print(f"    ~ Finding 3: CVD averaging reduces disparity ({reduction:.1f}%) but still significant (p={cvd_avg_tpval:.3f})")
        else:
            print(f"    ⚠️ Finding 3: CVD averaging does NOT reduce disparity")

    # Compare with Phase 1 (baseline81)
    print(f"\n{'='*80}")
    print("Comparison with Phase 1 (baseline81)")
    print(f"{'='*80}")

    # From OPTION2D_COMPREHENSIVE_REPORT.md
    phase1_hc_v1 = 0.089  # Mean HC-HC disparity V1
    phase1_hc_v2 = 0.119  # Mean HC-HC disparity V2
    phase1_cvd_v1 = 0.304  # Mean CVD-HC disparity V1
    phase1_cvd_v2 = 0.298  # Mean CVD-HC disparity V2

    print("\nV1:")
    print(f"  HC-HC:       baseline81={phase1_hc_v1:.3f}, baseline32={df_hc[df_hc['ROI']=='V1']['Disparity'].mean():.3f}")
    print(f"  CVD-HC:      baseline81={phase1_cvd_v1:.3f}, baseline32={df_cvd_ind[df_cvd_ind['ROI']=='V1']['Disparity'].mean():.3f}")

    print("\nV2:")
    print(f"  HC-HC:       baseline81={phase1_hc_v2:.3f}, baseline32={df_hc[df_hc['ROI']=='V2']['Disparity'].mean():.3f}")
    print(f"  CVD-HC:      baseline81={phase1_cvd_v2:.3f}, baseline32={df_cvd_ind[df_cvd_ind['ROI']=='V2']['Disparity'].mean():.3f}")

    print("\n  → Absolute values differ, but RELATIVE PATTERNS should be preserved")

    print(f"\n{'='*80}")
    print("Phase 1 FULL Validation Complete")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
