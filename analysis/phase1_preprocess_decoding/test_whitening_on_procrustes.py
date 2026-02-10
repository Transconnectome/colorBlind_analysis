#!/usr/bin/env python3
"""
Test Whitening on Procrustes-Aligned C010 Data

Compare three stages:
1. Raw C010 amplitudes
2. Procrustes-aligned
3. Procrustes-aligned + Whitening
"""

import numpy as np
import json
from pathlib import Path
from scipy.stats import spearmanr
from scipy.linalg import orthogonal_procrustes
from sklearn.covariance import LedoitWolf
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / 'scripts' / 'utils'))
from noise_ceiling import compute_split_half_reliability, compute_split_half_odd_even

# Constants
N_RUNS = 6
N_COLORS = 8
SUBJECTS = [f'sub-{i:02d}' for i in range(1, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']

def apply_procrustes_alignment(amplitudes):
    """Apply Procrustes alignment (same as before)"""
    n_runs, n_colors, n_voxels = amplitudes.shape
    aligned = np.zeros_like(amplitudes)

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

    return aligned

def preprocess_residuals_run_wise(residuals, n_runs=6):
    """Remove run-wise intercepts from residuals"""
    n_samples, n_voxels = residuals.shape
    samples_per_run = n_samples // n_runs

    residuals_centered = residuals.copy()

    # Remove mean per run, per voxel
    for run_idx in range(n_runs):
        start_idx = run_idx * samples_per_run
        end_idx = start_idx + samples_per_run if run_idx < n_runs - 1 else n_samples

        run_residuals = residuals[start_idx:end_idx]
        run_mean = run_residuals.mean(axis=0, keepdims=True)
        residuals_centered[start_idx:end_idx] = run_residuals - run_mean

    return residuals_centered

def estimate_noise_covariance(residuals):
    """Estimate noise covariance using Ledoit-Wolf"""
    lw = LedoitWolf(assume_centered=False)
    lw.fit(residuals)

    cov_matrix = lw.covariance_
    shrinkage = lw.shrinkage_

    return cov_matrix, shrinkage

def whiten_amplitudes(amplitudes, cov_noise):
    """
    Apply whitening transformation to amplitudes

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        cov_noise: (n_voxels, n_voxels) - Noise covariance matrix

    Returns:
        amplitudes_whitened: (n_runs, n_colors, n_voxels)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Compute whitening matrix: W = Σ^(-1/2)
    # Using eigenvalue decomposition: Σ = V @ diag(λ) @ V.T
    eigenvalues, eigenvectors = np.linalg.eigh(cov_noise)

    # Regularize small eigenvalues to avoid numerical issues
    eigenvalues = np.maximum(eigenvalues, 1e-10)

    # Whitening matrix: V @ diag(1/sqrt(λ)) @ V.T
    whitening_matrix = eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T

    # Apply whitening to each run
    amplitudes_whitened = np.zeros_like(amplitudes)

    for run_idx in range(n_runs):
        patterns = amplitudes[run_idx]  # (n_colors, n_voxels)

        # Whiten: patterns_white = patterns @ W
        patterns_whitened = patterns @ whitening_matrix
        amplitudes_whitened[run_idx] = patterns_whitened

    return amplitudes_whitened

def compute_rdm_reliability(amplitudes):
    """Compute RDM reliability using odd/even split"""
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split runs
    odd_runs = amplitudes[0::2]
    even_runs = amplitudes[1::2]

    # Average within each group
    odd_avg = odd_runs.mean(axis=0)
    even_avg = even_runs.mean(axis=0)

    # Compute RDMs
    rdm_odd = 1 - np.corrcoef(odd_avg)
    rdm_even = 1 - np.corrcoef(even_avg)

    # Vectorize upper triangle
    triu_idx = np.triu_indices(n_colors, k=1)
    rdm_odd_vec = rdm_odd[triu_idx]
    rdm_even_vec = rdm_even[triu_idx]

    # Spearman correlation
    rho, _ = spearmanr(rdm_odd_vec, rdm_even_vec)

    return rho

def estimate_noise_cov_from_amplitudes(amplitudes):
    """
    Estimate noise covariance directly from amplitudes
    Uses run-to-run variability as noise estimate
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Reshape: (n_runs * n_colors, n_voxels)
    patterns_all = amplitudes.reshape(-1, n_voxels)

    # Center patterns (remove mean pattern)
    patterns_centered = patterns_all - patterns_all.mean(axis=0, keepdims=True)

    # Estimate covariance using Ledoit-Wolf
    lw = LedoitWolf(assume_centered=True)  # Already centered
    lw.fit(patterns_centered)

    return lw.covariance_, lw.shrinkage_

def analyze_pair(subject, roi, base_dir):
    """Analyze one subject-ROI pair with three stages"""
    amp_path = base_dir / subject / roi / 'amplitudes_raw.npy'

    if not amp_path.exists():
        print(f"  ❌ Not found: {subject}/{roi}")
        return None

    # Load data
    amplitudes_raw = np.load(amp_path)

    # === STAGE 1: RAW ===
    nc_raw = compute_split_half_odd_even(amplitudes_raw)['corrected']
    rdm_raw = compute_rdm_reliability(amplitudes_raw)

    # === STAGE 2: PROCRUSTES ===
    amplitudes_proc = apply_procrustes_alignment(amplitudes_raw)
    nc_proc = compute_split_half_odd_even(amplitudes_proc)['corrected']
    rdm_proc = compute_rdm_reliability(amplitudes_proc)

    # === STAGE 3: PROCRUSTES + WHITENING ===
    # Estimate noise covariance from Procrustes-aligned amplitudes
    # Using run-to-run variability as noise estimate
    cov_noise, shrinkage = estimate_noise_cov_from_amplitudes(amplitudes_proc)

    # Apply whitening to Procrustes-aligned amplitudes
    amplitudes_whitened = whiten_amplitudes(amplitudes_proc, cov_noise)

    nc_whitened = compute_split_half_odd_even(amplitudes_whitened)['corrected']
    rdm_whitened = compute_rdm_reliability(amplitudes_whitened)

    # === COMPUTE IMPROVEMENTS ===
    proc_improvement = rdm_proc - rdm_raw
    whitening_improvement = rdm_whitened - rdm_proc
    total_improvement = rdm_whitened - rdm_raw

    results = {
        'subject': subject,
        'roi': roi,
        'n_voxels': amplitudes_raw.shape[2],

        # Stage 1: Raw
        'raw': {
            'nc_oddeven': float(nc_raw),
            'rdm_reliability': float(rdm_raw),
        },

        # Stage 2: Procrustes
        'procrustes': {
            'nc_oddeven': float(nc_proc),
            'rdm_reliability': float(rdm_proc),
        },

        # Stage 3: Procrustes + Whitening
        'whitened': {
            'nc_oddeven': float(nc_whitened),
            'rdm_reliability': float(rdm_whitened),
            'shrinkage': float(shrinkage),
        },

        # Improvements
        'improvement': {
            'procrustes': float(proc_improvement),
            'whitening': float(whitening_improvement),
            'total': float(total_improvement),
            'proc_percent': float(100 * proc_improvement / (abs(rdm_raw) + 1e-10)) if rdm_raw != 0 else np.nan,
            'whitening_percent': float(100 * whitening_improvement / (abs(rdm_proc) + 1e-10)) if rdm_proc != 0 else np.nan,
        }
    }

    return results

def main():
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/preprocess_detrend_temp/full_dataset_C010')

    print("=" * 80)
    print("Whitening Effect Analysis on Procrustes-Aligned C010 Data")
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
                proc_rdm = result['procrustes']['rdm_reliability']
                white_rdm = result['whitened']['rdm_reliability']

                print(f"  {roi}: {raw_rdm:+.3f} → {proc_rdm:+.3f} → {white_rdm:+.3f} "
                      f"(Proc: {result['improvement']['procrustes']:+.3f}, "
                      f"White: {result['improvement']['whitening']:+.3f})")

    print()
    print("=" * 80)

    # === AGGREGATE STATISTICS ===
    raw_rdm = [r['raw']['rdm_reliability'] for r in all_results]
    proc_rdm = [r['procrustes']['rdm_reliability'] for r in all_results]
    white_rdm = [r['whitened']['rdm_reliability'] for r in all_results]

    proc_improvements = [r['improvement']['procrustes'] for r in all_results]
    white_improvements = [r['improvement']['whitening'] for r in all_results]
    total_improvements = [r['improvement']['total'] for r in all_results]

    raw_nc = [r['raw']['nc_oddeven'] for r in all_results]
    proc_nc = [r['procrustes']['nc_oddeven'] for r in all_results]
    white_nc = [r['whitened']['nc_oddeven'] for r in all_results]

    print(f"\n📊 OVERALL STATISTICS ({len(all_results)} pairs)")
    print("=" * 80)

    print("\n1. RDM Reliability Progression")
    print(f"   Raw (C010):            {np.mean(raw_rdm):.3f} ± {np.std(raw_rdm):.3f}")
    print(f"   + Procrustes:          {np.mean(proc_rdm):.3f} ± {np.std(proc_rdm):.3f} ({np.mean(proc_improvements):+.3f})")
    print(f"   + Whitening:           {np.mean(white_rdm):.3f} ± {np.std(white_rdm):.3f} ({np.mean(white_improvements):+.3f})")
    print(f"   Total improvement:     {np.mean(total_improvements):+.3f}")

    print("\n2. Noise Ceiling Progression")
    print(f"   Raw:                   {np.mean(raw_nc):.3f} ± {np.std(raw_nc):.3f}")
    print(f"   + Procrustes:          {np.mean(proc_nc):.3f} ± {np.std(proc_nc):.3f}")
    print(f"   + Whitening:           {np.mean(white_nc):.3f} ± {np.std(white_nc):.3f}")

    print("\n3. Quality Metrics")
    raw_positive = sum(1 for x in raw_rdm if x > 0)
    proc_positive = sum(1 for x in proc_rdm if x > 0)
    white_positive = sum(1 for x in white_rdm if x > 0)

    print(f"   Positive RDM reliability:")
    print(f"     Raw:                 {raw_positive}/{len(all_results)} ({100*raw_positive/len(all_results):.1f}%)")
    print(f"     + Procrustes:        {proc_positive}/{len(all_results)} ({100*proc_positive/len(all_results):.1f}%)")
    print(f"     + Whitening:         {white_positive}/{len(all_results)} ({100*white_positive/len(all_results):.1f}%)")

    print("\n4. Improvement Breakdown")
    proc_better = sum(1 for x in proc_improvements if x > 0)
    white_better = sum(1 for x in white_improvements if x > 0)

    print(f"   Procrustes improves:   {proc_better}/{len(all_results)} pairs ({100*proc_better/len(all_results):.1f}%)")
    print(f"   Whitening improves:    {white_better}/{len(all_results)} pairs ({100*white_better/len(all_results):.1f}%)")

    print("\n5. Top 10 Whitening Improvements")
    sorted_results = sorted(all_results, key=lambda x: x['improvement']['whitening'], reverse=True)
    for i, r in enumerate(sorted_results[:10], 1):
        proc = r['procrustes']['rdm_reliability']
        white = r['whitened']['rdm_reliability']
        improvement = r['improvement']['whitening']
        print(f"   {i}. {r['subject']}_{r['roi']}: {proc:+.3f} → {white:+.3f} ({improvement:+.3f})")

    print("\n6. By ROI")
    for roi in ROIS:
        roi_results = [r for r in all_results if r['roi'] == roi]
        roi_raw = np.mean([r['raw']['rdm_reliability'] for r in roi_results])
        roi_proc = np.mean([r['procrustes']['rdm_reliability'] for r in roi_results])
        roi_white = np.mean([r['whitened']['rdm_reliability'] for r in roi_results])
        white_improvement = np.mean([r['improvement']['whitening'] for r in roi_results])
        print(f"   {roi}: {roi_raw:+.3f} → {roi_proc:+.3f} → {roi_white:+.3f} (White: {white_improvement:+.3f})")

    # Save results
    output_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/preprocess_detrend_temp')

    # Individual results
    with open(output_dir / 'whitening_improvement_detailed.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    # Summary statistics
    summary = {
        'n_pairs': len(all_results),
        'raw': {
            'rdm_reliability_mean': float(np.mean(raw_rdm)),
            'rdm_reliability_std': float(np.std(raw_rdm)),
            'nc_oddeven_mean': float(np.mean(raw_nc)),
            'positive_count': int(raw_positive),
        },
        'procrustes': {
            'rdm_reliability_mean': float(np.mean(proc_rdm)),
            'rdm_reliability_std': float(np.std(proc_rdm)),
            'nc_oddeven_mean': float(np.mean(proc_nc)),
            'positive_count': int(proc_positive),
            'improvement_mean': float(np.mean(proc_improvements)),
        },
        'whitened': {
            'rdm_reliability_mean': float(np.mean(white_rdm)),
            'rdm_reliability_std': float(np.std(white_rdm)),
            'nc_oddeven_mean': float(np.mean(white_nc)),
            'positive_count': int(white_positive),
            'improvement_over_proc': float(np.mean(white_improvements)),
            'improvement_total': float(np.mean(total_improvements)),
        }
    }

    with open(output_dir / 'whitening_improvement_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Results saved:")
    print(f"   - whitening_improvement_detailed.json")
    print(f"   - whitening_improvement_summary.json")
    print()

if __name__ == '__main__':
    main()
