#!/usr/bin/env python3
"""
Phase 1 Analysis with baseline32_deob_determin Data

Validates that Phase 2A "Before Filtering" disparity values are consistent
with Phase 1 methodology applied to the same voxel set.

Purpose:
- Verify voxel selection (32% vs 81%) is the source of disparity differences
- Confirm Phase 1 and Phase 2A use consistent Procrustes methods
"""

import numpy as np
from pathlib import Path
import pandas as pd
from scipy.stats import spearmanr
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
    Following OPTION2D_COMPREHENSIVE_REPORT.md method

    Args:
        X: reference (8, n_voxels) - HC
        Y: target (8, n_voxels) - CVD

    Returns:
        disparity: normalized Frobenius norm
        Y_aligned: aligned Y to X
    """
    # Step 1: Center (translation)
    X_centered = X - X.mean(axis=0, keepdims=True)
    Y_centered = Y - Y.mean(axis=0, keepdims=True)

    # Step 2: Rotation (no scaling!)
    M = Y_centered.T @ X_centered
    U, S, Vt = np.linalg.svd(M)
    R = U @ Vt

    # Step 3: Align
    Y_aligned = Y_centered @ R + X.mean(axis=0, keepdims=True)

    # Disparity (normalized Frobenius norm)
    disparity = np.linalg.norm(X - Y_aligned, ord='fro') / np.linalg.norm(X, ord='fro')

    return disparity, Y_aligned


def compute_rdm(pattern):
    """
    Compute Representational Dissimilarity Matrix

    Args:
        pattern: (8, n_voxels)

    Returns:
        rdm: (8, 8) dissimilarity matrix
    """
    n_colors = pattern.shape[0]
    pattern_centered = pattern - pattern.mean(axis=1, keepdims=True)

    rdm = np.zeros((n_colors, n_colors))
    for i in range(n_colors):
        for j in range(n_colors):
            if i != j:
                corr = np.corrcoef(pattern_centered[i], pattern_centered[j])[0, 1]
                rdm[i, j] = 1 - corr
            else:
                rdm[i, j] = 0.0

    return rdm


def compute_rdm_similarity(rdm1, rdm2):
    """Compute RDM similarity using Spearman correlation"""
    # Upper triangle only (exclude diagonal)
    upper_tri = np.triu_indices(8, k=1)
    rdm1_vec = rdm1[upper_tri]
    rdm2_vec = rdm2[upper_tri]

    corr, pval = spearmanr(rdm1_vec, rdm2_vec)
    return corr, pval


def compute_activation_stats(pattern):
    """
    Compute activation statistics

    Args:
        pattern: (8, n_voxels)

    Returns:
        dict with L2 norms and means per color
    """
    l2_norms = np.linalg.norm(pattern, axis=1)  # (8,)
    means = np.mean(pattern, axis=1)  # (8,)

    return {
        'l2_norms': l2_norms.tolist(),
        'means': means.tolist()
    }


def main():
    print("=" * 80)
    print("Phase 1 Validation with baseline32_deob_determin")
    print("=" * 80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Results storage
    procrustes_results = []
    rdm_results = []
    activation_results = []

    for roi in ROIS:
        print(f"\n{'='*80}")
        print(f"ROI: {roi}")
        print(f"{'='*80}")

        # Load HC mean
        H = load_hc_mean(roi)
        rdm_hc = compute_rdm(H)
        print(f"\nHC mean pattern: {H.shape}")

        # Analyze each CVD subject
        for cvd_subj in CVD_SUBJECTS:
            print(f"\n{'-'*80}")
            print(f"CVD Subject: {cvd_subj}")
            print(f"{'-'*80}")

            # Load CVD pattern
            Y = load_pattern(cvd_subj, roi)

            # Align voxel counts
            min_voxels = min(Y.shape[1], H.shape[1])
            Y = Y[:, :min_voxels]
            H_aligned = H[:, :min_voxels]

            print(f"Pattern shape: {Y.shape} (aligned to {min_voxels} voxels)")

            # Procrustes analysis
            disparity, Y_aligned = ordinary_procrustes(H_aligned, Y)
            print(f"Procrustes Disparity: {disparity:.4f}")

            procrustes_results.append({
                'Subject': f'sub-{cvd_subj}',
                'ROI': roi,
                'N_Voxels': min_voxels,
                'Disparity': disparity
            })

            # RDM similarity
            rdm_cvd = compute_rdm(Y)
            rdm_sim, rdm_pval = compute_rdm_similarity(rdm_cvd, compute_rdm(H_aligned))
            print(f"RDM Similarity (Spearman): {rdm_sim:.4f} (p={rdm_pval:.4e})")

            rdm_results.append({
                'Subject': f'sub-{cvd_subj}',
                'ROI': roi,
                'RDM_Similarity': rdm_sim,
                'RDM_p_value': rdm_pval
            })

            # Activation statistics
            cvd_stats = compute_activation_stats(Y)
            hc_stats = compute_activation_stats(H_aligned)

            # Per-color differences
            l2_diffs = np.array(cvd_stats['l2_norms']) - np.array(hc_stats['l2_norms'])
            l2_ratios = np.array(cvd_stats['l2_norms']) / (np.array(hc_stats['l2_norms']) + 1e-10)
            mean_diffs = np.array(cvd_stats['means']) - np.array(hc_stats['means'])

            for i, color in enumerate(COLOR_NAMES):
                activation_results.append({
                    'Subject': f'sub-{cvd_subj}',
                    'ROI': roi,
                    'Color': color,
                    'HC_L2': hc_stats['l2_norms'][i],
                    'CVD_L2': cvd_stats['l2_norms'][i],
                    'L2_Diff': l2_diffs[i],
                    'L2_Ratio': l2_ratios[i],
                    'L2_Diff_Percent': (l2_ratios[i] - 1.0) * 100,
                    'HC_Mean': hc_stats['means'][i],
                    'CVD_Mean': cvd_stats['means'][i],
                    'Mean_Diff': mean_diffs[i]
                })

    # Save results
    print(f"\n{'='*80}")
    print("Saving Results")
    print(f"{'='*80}")

    # Procrustes
    df_procrustes = pd.DataFrame(procrustes_results)
    procrustes_file = OUTPUT_DIR / "procrustes_results.csv"
    df_procrustes.to_csv(procrustes_file, index=False)
    print(f"Saved: {procrustes_file}")

    # RDM
    df_rdm = pd.DataFrame(rdm_results)
    rdm_file = OUTPUT_DIR / "rdm_similarity.csv"
    df_rdm.to_csv(rdm_file, index=False)
    print(f"Saved: {rdm_file}")

    # Activation
    df_activation = pd.DataFrame(activation_results)
    activation_file = OUTPUT_DIR / "activation_differences.csv"
    df_activation.to_csv(activation_file, index=False)
    print(f"Saved: {activation_file}")

    # Summary
    print(f"\n{'='*80}")
    print("Procrustes Disparity Summary (baseline32)")
    print(f"{'='*80}")
    print(df_procrustes.to_string(index=False))

    print(f"\n{'='*80}")
    print("RDM Similarity Summary (baseline32)")
    print(f"{'='*80}")
    print(df_rdm.to_string(index=False))

    # Compare with Phase 2A "Before Filtering"
    print(f"\n{'='*80}")
    print("Comparison with Phase 2A 'Before Filtering'")
    print(f"{'='*80}")

    # Load Phase 2A results
    phase2a_procrustes_file = BASE_DIR / "results/group_level/phase2a_data/metrics/procrustes_summary.csv"
    if phase2a_procrustes_file.exists():
        df_phase2a = pd.read_csv(phase2a_procrustes_file)
        df_phase2a = df_phase2a[df_phase2a['roi'].isin(['V1', 'V2'])]
        df_phase2a['Subject'] = 'sub-' + df_phase2a['subject'].astype(str)
        df_phase2a = df_phase2a.rename(columns={'roi': 'ROI', 'disparity': 'Phase2A_Disparity'})
        df_phase2a = df_phase2a[['Subject', 'ROI', 'Phase2A_Disparity']]

        # Merge
        df_compare = df_procrustes.merge(df_phase2a, on=['Subject', 'ROI'], how='left')
        df_compare['Difference'] = df_compare['Disparity'] - df_compare['Phase2A_Disparity']
        df_compare['Diff_Percent'] = df_compare['Difference'] / df_compare['Phase2A_Disparity'] * 100

        print("\nDisparity Comparison:")
        print(df_compare.to_string(index=False))

        # Statistical summary
        print(f"\nMean Absolute Difference: {df_compare['Difference'].abs().mean():.6f}")
        print(f"Max Absolute Difference: {df_compare['Difference'].abs().max():.6f}")

        if df_compare['Difference'].abs().mean() < 0.01:
            print("\n✓ Phase 1 (baseline32) matches Phase 2A 'Before Filtering' (< 1% difference)")
        else:
            print("\n⚠️ WARNING: Phase 1 (baseline32) differs from Phase 2A 'Before Filtering'")

        # Save comparison
        compare_file = OUTPUT_DIR / "comparison_with_phase2a.csv"
        df_compare.to_csv(compare_file, index=False)
        print(f"\nSaved comparison: {compare_file}")

    # Summary statistics by ROI
    print(f"\n{'='*80}")
    print("Summary by ROI")
    print(f"{'='*80}")

    for roi in ROIS:
        roi_data = df_procrustes[df_procrustes['ROI'] == roi]
        print(f"\n{roi}:")
        print(f"  Mean Disparity: {roi_data['Disparity'].mean():.4f}")
        print(f"  Std Disparity: {roi_data['Disparity'].std():.4f}")
        print(f"  Range: {roi_data['Disparity'].min():.4f} ~ {roi_data['Disparity'].max():.4f}")

        roi_rdm = df_rdm[df_rdm['ROI'] == roi]
        print(f"  Mean RDM Similarity: {roi_rdm['RDM_Similarity'].mean():.4f}")
        print(f"  Range: {roi_rdm['RDM_Similarity'].min():.4f} ~ {roi_rdm['RDM_Similarity'].max():.4f}")

    print(f"\n{'='*80}")
    print("Phase 1 baseline32 Validation Complete")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
