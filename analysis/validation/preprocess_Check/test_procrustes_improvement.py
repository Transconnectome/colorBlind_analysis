#!/usr/bin/env python3
"""
Test Procrustes Alignment Effect on Noise Ceiling
Compare C010 raw vs Procrustes-aligned metrics
"""

import numpy as np
import json
from pathlib import Path
from scipy.stats import spearmanr
from scipy.linalg import orthogonal_procrustes
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / 'scripts' / 'utils'))
from noise_ceiling import compute_split_half_reliability, compute_split_half_odd_even

# Constants
N_RUNS = 6
N_COLORS = 8
SUBJECTS = [f'sub-{i:02d}' for i in range(1, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']

def compute_rdm(patterns, metric='correlation'):
    """Compute RDM from patterns (n_conditions, n_voxels)"""
    n_conditions = patterns.shape[0]
    rdm = np.zeros((n_conditions, n_conditions))

    for i in range(n_conditions):
        for j in range(n_conditions):
            if metric == 'correlation':
                corr = np.corrcoef(patterns[i], patterns[j])[0, 1]
                rdm[i, j] = 1 - corr
            else:
                raise ValueError(f"Unknown metric: {metric}")

    return rdm

def apply_procrustes_alignment(amplitudes):
    """
    Apply Procrustes alignment to align all runs to run 0

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        aligned_amplitudes: (n_runs, n_colors, n_voxels)
        disparities: list of disparity values per run
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    aligned = np.zeros_like(amplitudes)
    disparities = []

    # Reference: first run
    reference = amplitudes[0].copy()
    aligned[0] = reference

    # Align subsequent runs
    for run_idx in range(1, n_runs):
        target = amplitudes[run_idx]

        # Procrustes: find optimal rotation R
        R, scale = orthogonal_procrustes(target.T, reference.T)

        # Apply transformation
        aligned_run = (target.T @ R).T
        aligned[run_idx] = aligned_run

        # Compute disparity (normalized)
        disparity = np.sum((aligned_run - reference) ** 2) / n_voxels
        disparities.append(disparity)

    return aligned, disparities

def compute_rdm_reliability(amplitudes):
    """
    Compute RDM reliability using odd/even split

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        reliability: Spearman correlation between odd/even RDMs
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split runs
    odd_runs = amplitudes[0::2]  # runs 0, 2, 4
    even_runs = amplitudes[1::2]  # runs 1, 3, 5

    # Average within each group
    odd_avg = odd_runs.mean(axis=0)  # (n_colors, n_voxels)
    even_avg = even_runs.mean(axis=0)

    # Compute RDMs
    rdm_odd = compute_rdm(odd_avg, metric='correlation')
    rdm_even = compute_rdm(even_avg, metric='correlation')

    # Vectorize upper triangle
    triu_idx = np.triu_indices(n_colors, k=1)
    rdm_odd_vec = rdm_odd[triu_idx]
    rdm_even_vec = rdm_even[triu_idx]

    # Spearman correlation
    rho, _ = spearmanr(rdm_odd_vec, rdm_even_vec)

    return rho

def analyze_pair(subject, roi, base_dir):
    """Analyze one subject-ROI pair"""
    amp_path = base_dir / subject / roi / 'amplitudes_raw.npy'

    if not amp_path.exists():
        print(f"  ❌ Not found: {subject}/{roi}")
        return None

    # Load raw amplitudes
    amplitudes = np.load(amp_path)  # (n_runs, n_colors, n_voxels)

    # === RAW METRICS ===
    # Noise ceiling
    nc_random_raw_dict = compute_split_half_reliability(amplitudes, n_iterations=1000, random_seed=42)
    nc_oddeven_raw_dict = compute_split_half_odd_even(amplitudes)

    nc_random_raw = nc_random_raw_dict['corrected']
    nc_oddeven_raw = nc_oddeven_raw_dict['corrected']

    # RDM reliability
    rdm_rel_raw = compute_rdm_reliability(amplitudes)

    # Method difference
    method_diff_raw = abs(nc_random_raw - nc_oddeven_raw)

    # === PROCRUSTES ALIGNMENT ===
    aligned_amplitudes, disparities = apply_procrustes_alignment(amplitudes)

    # Procrustes disparity (mean across runs)
    proc_disparity = np.mean(disparities)

    # === ALIGNED METRICS ===
    # Noise ceiling
    nc_random_aligned_dict = compute_split_half_reliability(aligned_amplitudes, n_iterations=1000, random_seed=42)
    nc_oddeven_aligned_dict = compute_split_half_odd_even(aligned_amplitudes)

    nc_random_aligned = nc_random_aligned_dict['corrected']
    nc_oddeven_aligned = nc_oddeven_aligned_dict['corrected']

    # RDM reliability
    rdm_rel_aligned = compute_rdm_reliability(aligned_amplitudes)

    # Method difference
    method_diff_aligned = abs(nc_random_aligned - nc_oddeven_aligned)

    # === COMPUTE IMPROVEMENTS ===
    rdm_improvement = rdm_rel_aligned - rdm_rel_raw
    nc_improvement = nc_oddeven_aligned - nc_oddeven_raw
    method_diff_improvement = method_diff_raw - method_diff_aligned  # Lower is better, so raw - aligned

    results = {
        'subject': subject,
        'roi': roi,
        'n_voxels': amplitudes.shape[2],

        # Raw metrics
        'raw': {
            'nc_random': float(nc_random_raw),
            'nc_oddeven': float(nc_oddeven_raw),
            'rdm_reliability': float(rdm_rel_raw),
            'method_difference': float(method_diff_raw),
        },

        # Aligned metrics
        'aligned': {
            'nc_random': float(nc_random_aligned),
            'nc_oddeven': float(nc_oddeven_aligned),
            'rdm_reliability': float(rdm_rel_aligned),
            'method_difference': float(method_diff_aligned),
            'proc_disparity': float(proc_disparity),
        },

        # Improvements
        'improvement': {
            'rdm_reliability': float(rdm_improvement),
            'nc_oddeven': float(nc_improvement),
            'method_difference': float(method_diff_improvement),
            'rdm_rel_percent': float(100 * rdm_improvement / (abs(rdm_rel_raw) + 1e-10)) if rdm_rel_raw != 0 else np.nan,
        }
    }

    return results

def main():
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/preprocess_detrend_temp/full_dataset_C010')

    print("=" * 80)
    print("Procrustes Alignment Effect Analysis (C010)")
    print("=" * 80)
    print()

    all_results = []

    for subject in SUBJECTS:
        print(f"Processing {subject}...")
        for roi in ROIS:
            result = analyze_pair(subject, roi, base_dir)
            if result is not None:
                all_results.append(result)

                # Print summary
                raw_rdm = result['raw']['rdm_reliability']
                aligned_rdm = result['aligned']['rdm_reliability']
                improvement = result['improvement']['rdm_reliability']

                print(f"  {roi}: RDM {raw_rdm:+.3f} → {aligned_rdm:+.3f} "
                      f"({improvement:+.3f}, {result['improvement']['rdm_rel_percent']:+.1f}%)")

    print()
    print("=" * 80)

    # === AGGREGATE STATISTICS ===
    raw_rdm = [r['raw']['rdm_reliability'] for r in all_results]
    aligned_rdm = [r['aligned']['rdm_reliability'] for r in all_results]
    improvements = [r['improvement']['rdm_reliability'] for r in all_results]

    raw_nc = [r['raw']['nc_oddeven'] for r in all_results]
    aligned_nc = [r['aligned']['nc_oddeven'] for r in all_results]
    nc_improvements = [r['improvement']['nc_oddeven'] for r in all_results]

    raw_method_diff = [r['raw']['method_difference'] for r in all_results]
    aligned_method_diff = [r['aligned']['method_difference'] for r in all_results]
    method_diff_improvements = [r['improvement']['method_difference'] for r in all_results]

    print("\n📊 OVERALL STATISTICS (40 pairs)")
    print("=" * 80)

    print("\n1. RDM Reliability")
    print(f"   Raw (C010):       {np.mean(raw_rdm):.3f} ± {np.std(raw_rdm):.3f}")
    print(f"   Aligned:          {np.mean(aligned_rdm):.3f} ± {np.std(aligned_rdm):.3f}")
    print(f"   Improvement:      {np.mean(improvements):+.3f} ± {np.std(improvements):.3f}")
    print(f"   Relative gain:    {100 * np.mean(improvements) / (abs(np.mean(raw_rdm)) + 1e-10):+.1f}%")

    print("\n2. Noise Ceiling (Odd/Even)")
    print(f"   Raw (C010):       {np.mean(raw_nc):.3f} ± {np.std(raw_nc):.3f}")
    print(f"   Aligned:          {np.mean(aligned_nc):.3f} ± {np.std(aligned_nc):.3f}")
    print(f"   Improvement:      {np.mean(nc_improvements):+.3f} ± {np.std(nc_improvements):.3f}")

    print("\n3. Method Difference (Temporal Drift)")
    print(f"   Raw (C010):       {np.mean(raw_method_diff):.3f} ± {np.std(raw_method_diff):.3f}")
    print(f"   Aligned:          {np.mean(aligned_method_diff):.3f} ± {np.std(aligned_method_diff):.3f}")
    print(f"   Improvement:      {np.mean(method_diff_improvements):+.3f} ± {np.std(method_diff_improvements):.3f}")

    print("\n4. Quality Metrics")
    raw_positive = sum(1 for x in raw_rdm if x > 0)
    aligned_positive = sum(1 for x in aligned_rdm if x > 0)
    print(f"   Positive RDM reliability:")
    print(f"     Raw:            {raw_positive}/40 ({100*raw_positive/40:.1f}%)")
    print(f"     Aligned:        {aligned_positive}/40 ({100*aligned_positive/40:.1f}%)")

    raw_nc_positive = sum(1 for x in raw_nc if x > 0)
    aligned_nc_positive = sum(1 for x in aligned_nc if x > 0)
    print(f"   Positive noise ceiling:")
    print(f"     Raw:            {raw_nc_positive}/40 ({100*raw_nc_positive/40:.1f}%)")
    print(f"     Aligned:        {aligned_nc_positive}/40 ({100*aligned_nc_positive/40:.1f}%)")

    print("\n5. Top 10 Improvements")
    sorted_results = sorted(all_results, key=lambda x: x['improvement']['rdm_reliability'], reverse=True)
    for i, r in enumerate(sorted_results[:10], 1):
        raw = r['raw']['rdm_reliability']
        aligned = r['aligned']['rdm_reliability']
        improvement = r['improvement']['rdm_reliability']
        print(f"   {i}. {r['subject']}_{r['roi']}: {raw:+.3f} → {aligned:+.3f} ({improvement:+.3f})")

    print("\n6. By ROI")
    for roi in ROIS:
        roi_results = [r for r in all_results if r['roi'] == roi]
        roi_raw = np.mean([r['raw']['rdm_reliability'] for r in roi_results])
        roi_aligned = np.mean([r['aligned']['rdm_reliability'] for r in roi_results])
        roi_improvement = np.mean([r['improvement']['rdm_reliability'] for r in roi_results])
        print(f"   {roi}: {roi_raw:+.3f} → {roi_aligned:+.3f} ({roi_improvement:+.3f})")

    # Save results
    output_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/preprocess_detrend_temp')

    # Individual results
    with open(output_dir / 'procrustes_improvement_detailed.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    # Summary statistics
    summary = {
        'n_pairs': len(all_results),
        'raw': {
            'rdm_reliability_mean': float(np.mean(raw_rdm)),
            'rdm_reliability_std': float(np.std(raw_rdm)),
            'nc_oddeven_mean': float(np.mean(raw_nc)),
            'nc_oddeven_std': float(np.std(raw_nc)),
            'method_difference_mean': float(np.mean(raw_method_diff)),
            'positive_rdm_count': int(raw_positive),
            'positive_nc_count': int(raw_nc_positive),
        },
        'aligned': {
            'rdm_reliability_mean': float(np.mean(aligned_rdm)),
            'rdm_reliability_std': float(np.std(aligned_rdm)),
            'nc_oddeven_mean': float(np.mean(aligned_nc)),
            'nc_oddeven_std': float(np.std(aligned_nc)),
            'method_difference_mean': float(np.mean(aligned_method_diff)),
            'positive_rdm_count': int(aligned_positive),
            'positive_nc_count': int(aligned_nc_positive),
        },
        'improvement': {
            'rdm_reliability_mean': float(np.mean(improvements)),
            'rdm_reliability_std': float(np.std(improvements)),
            'relative_gain_percent': float(100 * np.mean(improvements) / (abs(np.mean(raw_rdm)) + 1e-10)),
            'nc_oddeven_mean': float(np.mean(nc_improvements)),
            'method_difference_mean': float(np.mean(method_diff_improvements)),
        }
    }

    with open(output_dir / 'procrustes_improvement_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Results saved:")
    print(f"   - procrustes_improvement_detailed.json")
    print(f"   - procrustes_improvement_summary.json")
    print()

if __name__ == '__main__':
    main()
