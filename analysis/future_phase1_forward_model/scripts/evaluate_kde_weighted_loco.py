#!/usr/bin/env python3
"""
evaluate_kde_weighted_loco.py — KDE-weighted LOCO evaluation.

Tests whether weighting voxels by tuning sharpness improves LOCO performance.

Tuning sharpness: how strongly each voxel prefers one color over others.
Sharp voxels carry more color information → higher weight in correlation.

Three weighting methods:
  A) selectivity: max(mean_resp) - mean(mean_resp) / std
  B) entropy: 1 - H(softmax(mean_resp)) / log(8)  (low entropy = sharp)
  C) kurtosis: excess kurtosis of response profile (peaked = high kurtosis)

Runs locally using C010 data.
"""

import sys
import numpy as np
import json
from pathlib import Path
from scipy.special import softmax

sys.path.insert(0, str(Path(__file__).parent))
from utils_forward_model import (
    load_amplitudes, create_basis_matrix, fit_W_ridge, gcv_select_alpha,
    predict_patterns, voxel_pattern_correlation,
    ROIS, HUE_ANGLES, HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS
)

LOCAL_BASELINE = Path(__file__).parent.parent.parent / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

# Per-ROI optimal K from basis-channel tradeoff analysis
OPTIMAL_K = {'V1': 2, 'V2': 3, 'V3': 8, 'V4': 3}


def compute_tuning_sharpness(amplitudes):
    """Compute per-voxel tuning sharpness from 8-color responses.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        dict of {method_name: (n_voxels,) weight arrays}, all non-negative
    """
    mean_resp = amplitudes.mean(axis=0)  # (8, n_voxels)
    n_voxels = mean_resp.shape[1]

    weights = {}

    # Method A: Selectivity index
    # (max - mean) / std — how much the best color stands out
    vmax = mean_resp.max(axis=0)
    vmean = mean_resp.mean(axis=0)
    vstd = mean_resp.std(axis=0, ddof=0)
    vstd[vstd == 0] = 1e-10
    sel = (vmax - vmean) / vstd
    sel = np.maximum(sel, 0)
    weights['selectivity'] = sel

    # Method B: 1 - normalized entropy of softmax
    # Temperature parameter to make softmax more discriminative
    sm = softmax(mean_resp * 10, axis=0)  # (8, n_voxels), temperature=0.1
    entropy = -np.sum(sm * np.log(sm + 1e-10), axis=0)  # (n_voxels,)
    max_entropy = np.log(8)
    sharpness = 1 - entropy / max_entropy  # 0 = uniform, 1 = one-hot
    weights['entropy'] = np.maximum(sharpness, 0)

    # Method C: Kurtosis of response profile
    # High kurtosis = peaked distribution = well-tuned
    from scipy.stats import kurtosis
    kurt = kurtosis(mean_resp, axis=0, fisher=True)  # excess kurtosis
    kurt = np.maximum(kurt, 0)  # only positive (peaked) kurtosis
    weights['kurtosis'] = kurt

    return weights


def weighted_corr(x, y, w):
    """Weighted Pearson correlation.

    Args:
        x, y: (n,) arrays
        w: (n,) non-negative weights

    Returns:
        r: weighted correlation coefficient
    """
    w_norm = w / (w.sum() + 1e-10)
    mx = np.sum(w_norm * x)
    my = np.sum(w_norm * y)
    dx = x - mx
    dy = y - my
    cov = np.sum(w_norm * dx * dy)
    sx = np.sqrt(np.sum(w_norm * dx ** 2))
    sy = np.sqrt(np.sum(w_norm * dy ** 2))
    if sx < 1e-10 or sy < 1e-10:
        return 0.0
    return cov / (sx * sy)


def run_loco_weighted(amplitudes, n_channels, weight_dict):
    """Run LOCO with standard and weighted voxel correlation.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        n_channels: K for FE basis
        weight_dict: {method: (n_voxels,) weights}

    Returns:
        results: dict with standard and weighted LOCO scores
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Pooled data: average across runs
    X_pooled = amplitudes.mean(axis=0)  # (8, n_voxels)

    # Full basis for this K
    C_full = create_basis_matrix(HUE_ANGLES, n_channels, basis_type='fe')

    # GCV alpha on full data
    best_alpha, _ = gcv_select_alpha(C_full, X_pooled)

    # LOCO: leave one color out
    standard_corrs = []
    weighted_corrs = {m: [] for m in weight_dict}

    for hold_out in range(n_colors):
        # Train indices
        train_idx = [i for i in range(n_colors) if i != hold_out]

        C_train = C_full[train_idx]
        X_train = X_pooled[train_idx]  # (7, n_voxels)

        # Fit W on training colors
        W = fit_W_ridge(C_train, X_train, best_alpha)  # (K, n_voxels)

        # Predict held-out pattern
        C_test = C_full[hold_out:hold_out + 1]  # (1, K)
        Y_pred = predict_patterns(W, C_test)  # (1, n_voxels)
        Y_real = X_pooled[hold_out:hold_out + 1]  # (1, n_voxels)

        # Standard correlation
        r_std = np.corrcoef(Y_pred[0], Y_real[0])[0, 1]
        if not np.isfinite(r_std):
            r_std = 0.0
        standard_corrs.append(r_std)

        # Weighted correlations
        for method, w in weight_dict.items():
            r_w = weighted_corr(Y_pred[0], Y_real[0], w)
            weighted_corrs[method].append(r_w)

    results = {
        'standard': {
            'per_color': standard_corrs,
            'mean': float(np.mean(standard_corrs))
        }
    }
    for method in weight_dict:
        results[method] = {
            'per_color': [float(x) for x in weighted_corrs[method]],
            'mean': float(np.mean(weighted_corrs[method]))
        }

    return results


def main():
    baseline_dir = LOCAL_BASELINE
    output_dir = Path(__file__).parent.parent / 'results' / 'kde_weighted_loco'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("KDE-Weighted LOCO Evaluation")
    print("=" * 70)
    print(f"Data: {baseline_dir}")
    print()

    all_results = {}

    for roi in ROIS:
        K = OPTIMAL_K[roi]
        print(f"ROI: {roi} (K={K})")

        for subject in ALL_SUBJECTS:
            group = 'HC' if subject in HC_SUBJECTS else 'CVD'

            try:
                amp = load_amplitudes(baseline_dir, subject, roi)
            except FileNotFoundError:
                print(f"  sub-{subject}: MISSING")
                continue

            # Compute tuning weights
            weight_dict = compute_tuning_sharpness(amp)

            # Run LOCO
            results = run_loco_weighted(amp, K, weight_dict)
            results['group'] = group
            results['n_voxels'] = int(amp.shape[2])
            results['K'] = K

            all_results[f"sub-{subject}_{roi}"] = results

            std = results['standard']['mean']
            sel = results['selectivity']['mean']
            ent = results['entropy']['mean']
            kur = results['kurtosis']['mean']
            delta_best = max(sel, ent, kur) - std
            print(f"  sub-{subject} ({group}): std={std:.4f}  "
                  f"sel={sel:.4f}  ent={ent:.4f}  kur={kur:.4f}  "
                  f"Δbest={delta_best:+.4f}")

        print()

    # Summary statistics
    print("=" * 70)
    print("SUMMARY: Mean LOCO voxel_corr by weighting method")
    print("=" * 70)

    for roi in ROIS:
        print(f"\n{roi}:")
        for group_name, group_subs in [('HC', HC_SUBJECTS), ('CVD', CVD_SUBJECTS)]:
            methods = ['standard', 'selectivity', 'entropy', 'kurtosis']
            means = {m: [] for m in methods}
            for sub in group_subs:
                key = f"sub-{sub}_{roi}"
                if key in all_results:
                    for m in methods:
                        means[m].append(all_results[key][m]['mean'])
            if means['standard']:
                line = f"  {group_name}: "
                for m in methods:
                    arr = np.array(means[m])
                    line += f"{m[:3]}={arr.mean():.4f}±{arr.std(ddof=1):.4f}  "
                print(line)

    # Paired comparison (HC): weighted - standard
    print("\n" + "=" * 70)
    print("PAIRED DIFFERENCE: weighted - standard (HC, per subject)")
    print("=" * 70)
    from scipy.stats import ttest_rel

    for roi in ROIS:
        print(f"\n{roi}:")
        std_vals = []
        for sub in HC_SUBJECTS:
            key = f"sub-{sub}_{roi}"
            if key in all_results:
                std_vals.append(all_results[key]['standard']['mean'])

        for method in ['selectivity', 'entropy', 'kurtosis']:
            w_vals = []
            for sub in HC_SUBJECTS:
                key = f"sub-{sub}_{roi}"
                if key in all_results:
                    w_vals.append(all_results[key][method]['mean'])

            if len(w_vals) >= 3:
                deltas = np.array(w_vals) - np.array(std_vals)
                t, p = ttest_rel(w_vals, std_vals)
                print(f"  {method:12s}: Δ={np.mean(deltas):+.4f}±{np.std(deltas, ddof=1):.4f}, "
                      f"t={t:.3f}, p={p:.4f}")

    # Save
    out_file = output_dir / 'kde_weighted_loco_results.json'
    with open(out_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved: {out_file}")


if __name__ == '__main__':
    main()
