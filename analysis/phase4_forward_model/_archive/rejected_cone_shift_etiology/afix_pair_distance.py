#!/usr/bin/env python3
"""
afix_pair_distance.py — A-fix: Compare cone-shift pair distance predictions
against SRM per-pair z-scores (28 pairs).

Key insight: Approach A's per-color δθ can predict HOW pair distances change
under cone shift. SRM pre-validation z-scores measure the actual HC-CVD
representation distance per pair. Correlation between the two validates
whether cone shift explains the observed CVD distortion pattern.

28 pairs = 3.5× more df than 8 per-color LOCO gaps → much stronger test.

Runs locally (conda env: srm).

Usage:
    cd analysis/phase4_forward_model
    python scripts/afix_pair_distance.py
"""

import json
import numpy as np
from pathlib import Path
from itertools import combinations
from scipy.stats import spearmanr, pearsonr

# Paths
BASE = Path(__file__).resolve().parent.parent  # phase4_forward_model
CONE_SHIFT_JSON = BASE / 'results' / 'cone_shift' / 'cone_shift_results.json'
SRM_RESULTS_JSON = (BASE.parent / 'phase5_filter_optimization' /
                    'pre_validation' / 'results' /
                    'filter_pre_validation_results.json')
OUTPUT_DIR = BASE / 'results' / 'cone_shift'

# Constants
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
N_COLORS = 8
PAIR_INDICES = list(combinations(range(N_COLORS), 2))  # 28 pairs
PAIR_LABELS = [f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}" for i, j in PAIR_INDICES]


def circular_distance(a, b):
    """Circular distance in degrees, range [0, 180]."""
    d = abs(a - b)
    return min(d, 360 - d)


def compute_pair_distance_change(hue_normal, delta_theta):
    """Compute predicted change in pair distances under cone shift.

    For each pair (i, j):
        d_normal  = |θ_i - θ_j|  (circular)
        d_shifted = |(θ_i + δθ_i) - (θ_j + δθ_j)|  (circular)
        Δd = d_shifted - d_normal

    Positive Δd = pair expands under shift.
    Negative Δd = pair compresses under shift.

    Args:
        hue_normal: (8,) opponent-space hue angles in degrees
        delta_theta: (8,) predicted hue shifts in degrees

    Returns:
        delta_dist: (28,) pair distance changes
        dist_normal: (28,) normal pair distances
        dist_shifted: (28,) shifted pair distances
    """
    hue_shifted = (hue_normal + delta_theta) % 360

    delta_dist = []
    dist_normal = []
    dist_shifted = []

    for i, j in PAIR_INDICES:
        d_n = circular_distance(hue_normal[i], hue_normal[j])
        d_s = circular_distance(hue_shifted[i], hue_shifted[j])
        dist_normal.append(d_n)
        dist_shifted.append(d_s)
        delta_dist.append(d_s - d_n)

    return np.array(delta_dist), np.array(dist_normal), np.array(dist_shifted)


def grid_search_pair_distance(wavelengths, L, M, S, srm_z_scores, cvd_type,
                              max_shift=40, step=1):
    """Grid search Δλ using 28-pair distance change vs SRM z-scores.

    Returns:
        best_dl: optimal Δλ
        results: dict per Δλ
    """
    from stockman_cone_shift import (
        compute_shifted_hue_angles, compute_xyz_to_lms_matrix,
        compute_hue_angles_for_colors, load_stockman_fundamentals,
    )

    grid = np.arange(0, max_shift + step, step)
    results = {}
    best_rho = -np.inf
    best_dl = 0

    for dl in grid:
        hue_n, hue_s, dt = compute_shifted_hue_angles(
            wavelengths, L, M, S, dl, cvd_type
        )

        dd, dn, ds = compute_pair_distance_change(hue_n, dt)

        # Correlate with SRM z-scores
        if np.std(dd) > 0 and np.std(srm_z_scores) > 0:
            rho, p_rho = spearmanr(dd, srm_z_scores)
            r_pearson, p_pearson = pearsonr(dd, srm_z_scores)
        else:
            rho, p_rho = 0.0, 1.0
            r_pearson, p_pearson = 0.0, 1.0

        results[float(dl)] = {
            'spearman_r': float(rho) if np.isfinite(rho) else 0.0,
            'spearman_p': float(p_rho) if np.isfinite(p_rho) else 1.0,
            'pearson_r': float(r_pearson) if np.isfinite(r_pearson) else 0.0,
            'pearson_p': float(p_pearson) if np.isfinite(p_pearson) else 1.0,
            'delta_dist': dd.tolist(),
        }

        if np.isfinite(rho) and rho > best_rho:
            best_rho = rho
            best_dl = float(dl)

    return best_dl, results


def main():
    import sys
    # Add scripts dir to path for stockman_cone_shift imports
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from stockman_cone_shift import (
        load_stockman_fundamentals, compute_shifted_hue_angles,
        CVD_TYPE,
    )

    # Load data
    print("=" * 60)
    print("A-fix: Pair Distance Analysis")
    print("Comparing cone-shift predictions vs SRM per-pair z-scores")
    print("=" * 60)

    print("\n[1] Loading cone shift results...")
    with open(CONE_SHIFT_JSON) as f:
        cone_shift = json.load(f)

    print("[2] Loading SRM pre-validation results...")
    with open(SRM_RESULTS_JSON) as f:
        srm_data = json.load(f)

    srm_pair_labels = srm_data['config']['pair_labels']
    hv4_data = srm_data['results']['hV4']
    srm_z = hv4_data['B1_permutation']['observed_individual_z']

    # Verify pair ordering
    assert srm_pair_labels == PAIR_LABELS, "Pair label mismatch!"
    print(f"    28 pair labels verified: {PAIR_LABELS[0]} ... {PAIR_LABELS[-1]}")

    # Load cone fundamentals
    print("\n[3] Loading Stockman cone fundamentals...")
    wavelengths, L, M, S = load_stockman_fundamentals()

    all_results = {}

    for cvd_subj in ['sub-08', 'sub-09', 'sub-10']:
        subj_key = cvd_subj
        cvd_type = cone_shift[subj_key]['cvd_type']
        subj_id = cvd_subj.split('-')[1]

        print(f"\n{'=' * 60}")
        print(f"[4] {subj_key} (type={cvd_type})")

        # Get SRM z-scores for this subject
        z_scores = np.array(srm_z[subj_key])
        print(f"    SRM z-scores: mean={z_scores.mean():.2f}, "
              f"max={z_scores.max():.2f}, min={z_scores.min():.2f}")

        # Get opponent hue angles and delta_theta from Approach A
        hue_normal = np.array(cone_shift[subj_key]['hue_normal_deg'])
        dt_pred = np.array(cone_shift[subj_key]['delta_theta_pred_deg'])
        dl_best = cone_shift[subj_key]['best_delta_lambda_nm']

        print(f"\n    --- Using existing Δλ*={dl_best}nm (from per-color fit) ---")

        # Compute pair distance change at this Δλ*
        dd, dn, ds = compute_pair_distance_change(hue_normal, dt_pred)

        rho, p_rho = spearmanr(dd, z_scores)
        r_p, p_p = pearsonr(dd, z_scores)
        print(f"    Δdist vs SRM z-scores:")
        print(f"      Spearman r = {rho:.3f} (p = {p_rho:.3f})")
        print(f"      Pearson  r = {r_p:.3f} (p = {p_p:.3f})")

        # Top 5 pairs by |Δdist|
        sort_idx = np.argsort(np.abs(dd))[::-1]
        print(f"\n    Top 5 pairs by |Δdist|:")
        for rank, idx in enumerate(sort_idx[:5]):
            print(f"      {rank+1}. {PAIR_LABELS[idx]:20s}  "
                  f"Δdist={dd[idx]:+6.1f}°  z={z_scores[idx]:+5.2f}")

        # Top 5 pairs by z-score
        sort_z = np.argsort(z_scores)[::-1]
        print(f"\n    Top 5 pairs by SRM z-score:")
        for rank, idx in enumerate(sort_z[:5]):
            print(f"      {rank+1}. {PAIR_LABELS[idx]:20s}  "
                  f"z={z_scores[idx]:+5.2f}  Δdist={dd[idx]:+6.1f}°")

        # Grid search with pair-distance target
        print(f"\n    --- Grid search: Δλ optimized for pair-distance target ---")
        effective_type = cvd_type if cvd_type in ('deutan', 'protan') else 'deutan'
        best_dl_pair, grid_results = grid_search_pair_distance(
            wavelengths, L, M, S, z_scores, effective_type,
            max_shift=40, step=1
        )
        best_info = grid_results[best_dl_pair]
        print(f"    Best Δλ (pair target) = {best_dl_pair} nm")
        print(f"      Spearman r = {best_info['spearman_r']:.3f} "
              f"(p = {best_info['spearman_p']:.3f})")
        print(f"      Pearson  r = {best_info['pearson_r']:.3f} "
              f"(p = {best_info['pearson_p']:.3f})")

        # Compare original Δλ* vs pair-optimized Δλ*
        print(f"\n    Δλ comparison:")
        print(f"      Per-color target: Δλ*={dl_best}nm")
        print(f"      Pair-dist target: Δλ*={best_dl_pair}nm")

        # Show top-5 Δλ by Spearman from grid
        sorted_grid = sorted(grid_results.items(),
                             key=lambda x: x[1]['spearman_r'], reverse=True)
        print(f"\n    Top 5 Δλ by Spearman (pair-dist):")
        for dl_val, info in sorted_grid[:5]:
            print(f"      Δλ={dl_val:5.1f}nm  rho={info['spearman_r']:+.3f}  "
                  f"p={info['spearman_p']:.3f}")

        all_results[subj_key] = {
            'cvd_type': cvd_type,
            'original_delta_lambda_nm': dl_best,
            'pair_optimized_delta_lambda_nm': best_dl_pair,
            'at_original_dl': {
                'spearman_r': float(rho) if np.isfinite(rho) else 0.0,
                'spearman_p': float(p_rho) if np.isfinite(p_rho) else 1.0,
                'pearson_r': float(r_p) if np.isfinite(r_p) else 0.0,
                'pearson_p': float(p_p) if np.isfinite(p_p) else 1.0,
            },
            'at_pair_optimized_dl': {
                'spearman_r': best_info['spearman_r'],
                'spearman_p': best_info['spearman_p'],
                'pearson_r': best_info['pearson_r'],
                'pearson_p': best_info['pearson_p'],
            },
            'grid_top5': {str(k): {kk: vv for kk, vv in v.items()
                                    if kk != 'delta_dist'}
                          for k, v in sorted_grid[:5]},
        }

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY: A-fix Pair-Distance Analysis")
    print(f"{'=' * 60}")
    for subj_key, res in all_results.items():
        orig = res['at_original_dl']
        pair = res['at_pair_optimized_dl']
        print(f"\n  {subj_key} ({res['cvd_type']}):")
        print(f"    Original Δλ*={res['original_delta_lambda_nm']}nm → "
              f"rho={orig['spearman_r']:+.3f} (p={orig['spearman_p']:.3f})")
        print(f"    Pair-opt Δλ*={res['pair_optimized_delta_lambda_nm']}nm → "
              f"rho={pair['spearman_r']:+.3f} (p={pair['spearman_p']:.3f})")

    # Save
    out_path = OUTPUT_DIR / 'afix_pair_distance_results.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[5] Results saved to {out_path}")


if __name__ == '__main__':
    main()
